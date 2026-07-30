"""Isolated execution backends for running untrusted candidate code.

Candidate submissions are hostile input. Running them with ``subprocess`` on the
API server — as this service used to — hands them the server's own interpreter,
working directory, environment (API keys included), and network.

Three backends satisfy the same contract, and the layered resolver picks the
first one that can run a given language:

1. :class:`PistonSandbox` — an HTTP call to a Piston instance, which is
   purpose-built to run untrusted code (its own container, process and memory
   caps, no network). Needs no Docker on the API host.
2. :class:`ContainerSandbox` — a throwaway Docker container: no network, capped
   memory and CPU, read-only root, non-root user, wall-clock kill.
3. :class:`LocalSandbox` — a plain subprocess. **Weak isolation**: candidate code
   can read the filesystem and reach the network. Off unless
   ``ALLOW_LOCAL_CODE_EXEC`` is set, so production can never silently land here.

Isolation is *required*, not best-effort. When no backend can run a language the
runner raises :class:`SandboxUnavailable` and the caller reports an honest
error. It must never report a pass for code that was not actually executed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from app.core.config import settings

# Hard caps. These bound a single submission, not the whole feature.
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MEMORY = "256m"
DEFAULT_CPUS = "0.5"
DEFAULT_PIDS_LIMIT = 128
MAX_OUTPUT_CHARS = 64_000

# Grace added to the `docker run` timeout so the container's own SIGKILL and
# teardown are what we observe, rather than racing our client-side timeout.
_DOCKER_OVERHEAD_SECONDS = 15.0

# Printed to stderr by the Docker staging script between the compile and run
# steps. Both share one container (and so one stderr stream), so this is the only
# way to tell a compiler error from a runtime crash. Backends strip it and report
# the distinction as `SandboxResult.compile_ok` instead of leaking it upstream.
COMPILE_OK_SENTINEL = "__AIV_COMPILED_OK__"


class SandboxUnavailable(RuntimeError):
    """No backend can execute this code, so nothing was run."""


@dataclass
class SandboxResult:
    """Outcome of one sandboxed run."""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: float
    # False only when a compile step ran and failed. Languages with no compile
    # step are vacuously True, so callers can branch on this uniformly.
    compile_ok: bool = True


def _truncate(text: str) -> str:
    if len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + "\n… [output truncated]"
    return text


def _write_sources(work: Path, files: Dict[str, str]) -> None:
    """Materialise submitted sources under `work`, refusing to escape it."""
    root = work.resolve()
    for rel_name, content in files.items():
        # Guard against a crafted problem definition escaping the dir.
        target = (work / rel_name).resolve()
        if not str(target).startswith(str(root)):
            raise ValueError(f"Unsafe sandbox file path: {rel_name!r}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


# ── Piston (HTTP) ─────────────────────────────────────────────────────────────


class PistonSandbox:
    """Executes code on a Piston instance over HTTP.

    Piston compiles and runs from source files alone — there is no command to
    pass and no image to pull, so ``spec.run_cmd`` / ``spec.compile_cmd`` are
    unused here. The instance itself provides the isolation.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        raw = base_url if base_url is not None else settings.PISTON_URL
        self._base = (raw or "").rstrip("/")
        self._timeout = timeout or settings.PISTON_TIMEOUT_SECONDS
        # language name (and alias) → concrete version string. Piston's execute
        # endpoint requires an explicit version, so this doubles as the
        # availability probe. None means "not yet probed".
        self._runtimes: Optional[Dict[str, str]] = None

    @property
    def name(self) -> str:
        return "piston"

    def _load_runtimes(self) -> Dict[str, str]:
        if self._runtimes is not None:
            return self._runtimes
        if not self._base:
            self._runtimes = {}
            return self._runtimes
        try:
            resp = requests.get(f"{self._base}/api/v2/runtimes", timeout=self._timeout)
            resp.raise_for_status()
            table: Dict[str, str] = {}
            for entry in resp.json():
                version = entry.get("version") or ""
                for key in [entry.get("language")] + list(entry.get("aliases") or []):
                    if key and key not in table:
                        table[key] = version
            self._runtimes = table
            logger.info(f"Piston at {self._base}: {len(table)} runtimes available")
        except Exception as exc:
            logger.warning(f"Piston unreachable at {self._base or '<unset>'}: {exc}")
            self._runtimes = {}
        return self._runtimes

    def available(self) -> bool:
        return bool(self._load_runtimes())

    def supports(self, spec: Any) -> bool:
        return bool(spec.piston) and spec.piston in self._load_runtimes()

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> SandboxResult:
        runtimes = self._load_runtimes()
        version = runtimes.get(spec.piston)
        if version is None:
            raise SandboxUnavailable(
                f"Piston has no runtime for {spec.name}."
            )

        # The entry point must come first; Piston infers the run target from it.
        ordered = [{"name": spec.source_name, "content": files[spec.source_name]}]
        ordered += [
            {"name": n, "content": c} for n, c in files.items() if n != spec.source_name
        ]

        payload = {
            "language": spec.piston,
            "version": version,
            "files": ordered,
            "stdin": "",
            "compile_timeout": int(timeout * 1000) + 10_000,
            "run_timeout": int(timeout * 1000),
        }

        start = time.time()
        try:
            resp = requests.post(
                f"{self._base}/api/v2/execute",
                json=payload,
                timeout=self._timeout + timeout,
            )
        except Exception as exc:
            raise SandboxUnavailable(f"Piston request failed: {exc}") from exc
        elapsed = round((time.time() - start) * 1000, 2)

        if resp.status_code != 200:
            raise SandboxUnavailable(
                f"Piston returned HTTP {resp.status_code}: {resp.text[:300]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise SandboxUnavailable(f"Piston returned non-JSON response: {exc}") from exc

        compile_stage = body.get("compile") or {}
        run_stage = body.get("run") or {}
        compile_ok = compile_stage.get("code", 0) in (0, None)

        if not compile_ok:
            return SandboxResult(
                exit_code=compile_stage.get("code") or 1,
                stdout=_truncate(compile_stage.get("stdout") or ""),
                stderr=_truncate(compile_stage.get("stderr") or ""),
                timed_out=False,
                duration_ms=elapsed,
                compile_ok=False,
            )

        # Piston kills an over-running program rather than returning an exit
        # code, so a SIGKILL with no exit code is the timeout signal.
        signal = run_stage.get("signal")
        code = run_stage.get("code")
        timed_out = code is None and signal in ("SIGKILL", "SIGXCPU")

        if timed_out:
            return SandboxResult(
                exit_code=124,
                stdout=_truncate(run_stage.get("stdout") or ""),
                stderr=f"Time Limit Exceeded ({timeout:g}s)",
                timed_out=True,
                duration_ms=elapsed,
                compile_ok=True,
            )

        stderr = (compile_stage.get("stderr") or "") + (run_stage.get("stderr") or "")
        return SandboxResult(
            exit_code=code if code is not None else 1,
            stdout=_truncate(run_stage.get("stdout") or ""),
            stderr=_truncate(stderr),
            timed_out=False,
            duration_ms=elapsed,
            compile_ok=True,
        )


# ── Docker ────────────────────────────────────────────────────────────────────


class ContainerSandbox:
    """Runs a single file in a disposable, network-less container."""

    def __init__(self, docker_path: Optional[str] = None) -> None:
        self._docker = docker_path or shutil.which("docker")
        self._daemon_ok: Optional[bool] = None

    @property
    def name(self) -> str:
        return "docker"

    @property
    def docker_cli_present(self) -> bool:
        return bool(self._docker)

    def available(self) -> bool:
        """True when the Docker CLI exists *and* the daemon answers.

        A present CLI is not enough: Docker Desktop can be installed but
        stopped, in which case every `docker run` fails. Probed once and
        cached, so we don't pay a daemon round-trip per test run.
        """
        if self._daemon_ok is not None:
            return self._daemon_ok
        if not self._docker:
            self._daemon_ok = False
            return False
        try:
            probe = subprocess.run(
                [self._docker, "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=20.0,
            )
            self._daemon_ok = probe.returncode == 0
            if not self._daemon_ok:
                logger.warning(
                    f"Docker CLI found but daemon unreachable: {probe.stderr.strip()[:200]}"
                )
        except Exception as exc:
            logger.warning(f"Docker availability probe failed: {exc}")
            self._daemon_ok = False
        return self._daemon_ok

    def supports(self, spec: Any) -> bool:
        return self.image_present(spec.image)

    def image_present(self, image: str) -> bool:
        """True when `image` is already pulled locally.

        We never pull implicitly: a multi-hundred-megabyte download inside a
        request would blow the timeout and look like a hang. Missing images are
        reported to the caller as an unsupported language instead.
        """
        if not self.available():
            return False
        try:
            res = subprocess.run(
                [self._docker, "image", "inspect", image],
                capture_output=True,
                text=True,
                timeout=20.0,
            )
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def _staged(spec: Any, run: bool = True) -> List[str]:
        """Build the in-container shell command: stage source, compile, run.

        ``/sandbox`` is mounted read-only so candidate code cannot rewrite its
        own source mid-run; compilers need a writable directory, so the source is
        staged into the ``/build`` tmpfs first.

        Compilation and execution are emitted as a single command because
        ``/build`` is a per-container tmpfs — splitting them across two
        ``docker run`` calls would throw away the compiled artifact.
        """
        def _q(cmd: List[str]) -> str:
            return " ".join(f"'{c}'" for c in cmd)

        steps = [f"cp /sandbox/'{spec.source_name}' /build/"]
        if spec.compile_cmd:
            steps.append(_q(spec.compile_cmd))
            steps.append(f"echo {COMPILE_OK_SENTINEL} >&2")
        if run:
            # `exec` so the program replaces the shell and receives the signal
            # directly when the container is killed at timeout.
            steps.append("exec " + _q(spec.run_cmd))
        return ["sh", "-c", " && ".join(steps)]

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        memory: str = DEFAULT_MEMORY,
        cpus: str = DEFAULT_CPUS,
        network: bool = False,
    ) -> SandboxResult:
        """Write `files` into a temp dir, mount it read-only, build and run.

        Raises:
            SandboxUnavailable: Docker is not usable. Callers must surface this
                as an error — never as a passing test result.
        """
        if not self.available():
            raise SandboxUnavailable(
                "Code execution requires Docker, which is not available on this host."
            )

        command = self._staged(spec, run=not compile_only)

        with tempfile.TemporaryDirectory(prefix="sandbox_") as workdir:
            work = Path(workdir)
            _write_sources(work, files)

            name = f"aiv-exec-{uuid.uuid4().hex[:12]}"
            argv = [
                self._docker,
                "run",
                "--rm",
                "--name", name,
                "--network", "bridge" if network else "none",
                "--memory", memory,
                "--memory-swap", memory,   # equal to memory ⇒ no swap escape hatch
                "--cpus", cpus,
                "--pids-limit", str(DEFAULT_PIDS_LIMIT),
                "--read-only",             # root fs immutable…
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                # …so compilers get a writable scratch dir that cannot hold
                # an executable, while /sandbox stays read-only source.
                "--tmpfs", "/build:rw,nosuid,size=128m",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges",
                "--user", "65534:65534",   # nobody
                "-v", f"{work.resolve()}:/sandbox:ro",
                "-w", "/build",
                spec.image,
            ]
            argv.extend(command)

            start = time.time()
            try:
                proc = subprocess.run(
                    argv,
                    capture_output=True,
                    text=True,
                    timeout=timeout + _DOCKER_OVERHEAD_SECONDS,
                )
            except subprocess.TimeoutExpired:
                self._force_remove(name)
                return SandboxResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Time Limit Exceeded ({timeout:g}s)",
                    timed_out=True,
                    duration_ms=round((time.time() - start) * 1000, 2),
                )
            except Exception as exc:
                self._force_remove(name)
                raise SandboxUnavailable(f"Sandbox execution failed: {exc}") from exc

            compiled = COMPILE_OK_SENTINEL in proc.stderr
            stderr = proc.stderr.replace(COMPILE_OK_SENTINEL + "\n", "").replace(
                COMPILE_OK_SENTINEL, ""
            )
            return SandboxResult(
                exit_code=proc.returncode,
                stdout=_truncate(proc.stdout),
                stderr=_truncate(stderr),
                timed_out=False,
                duration_ms=round((time.time() - start) * 1000, 2),
                compile_ok=compiled or not spec.compile_cmd,
            )

    def _force_remove(self, name: str) -> None:
        """Kill a container that outlived its timeout so it can't linger."""
        try:
            subprocess.run(
                [self._docker, "rm", "-f", name],
                capture_output=True,
                text=True,
                timeout=20.0,
            )
        except Exception:
            logger.warning(f"Could not force-remove sandbox container {name}")


# ── Local subprocess (development only) ───────────────────────────────────────

# `dotnet run --project` needs a generated project file, which only the Docker
# image provides. Rather than invent one and let the missing-project error surface
# as if the candidate's code were at fault, C# is not offered locally.
_LOCAL_EXCLUDED = {"C#"}


class LocalSandbox:
    """Runs code as a subprocess on this host. Weak isolation — dev only.

    A scrubbed environment and a throwaway working directory keep the API
    server's secrets out of reach, but nothing here stops candidate code from
    reading the filesystem or opening a socket. Disabled unless
    ``ALLOW_LOCAL_CODE_EXEC`` is set.
    """

    def __init__(self, enabled: Optional[bool] = None) -> None:
        self._enabled = settings.ALLOW_LOCAL_CODE_EXEC if enabled is None else enabled
        if self._enabled:
            logger.warning(
                "ALLOW_LOCAL_CODE_EXEC is set: candidate code may run as a local "
                "subprocess with weak isolation. Do not use this in production."
            )

    @property
    def name(self) -> str:
        return "local"

    def available(self) -> bool:
        return self._enabled

    def supports(self, spec: Any) -> bool:
        if not self._enabled or spec.name in _LOCAL_EXCLUDED:
            return False
        for cmd in (spec.compile_cmd, spec.run_cmd):
            if not cmd:
                continue
            exe = cmd[0]
            # A `/build/...` head is the compiled artifact, not a host tool.
            if exe.startswith("/build/"):
                continue
            if shutil.which(exe) is None:
                return False
        return True

    @staticmethod
    def _localise(cmd: List[str], work: Path) -> List[str]:
        """Rewrite the container's `/build` paths onto the temp working dir."""
        out = []
        for part in cmd:
            if part.startswith("/build/"):
                out.append(str(work / part[len("/build/"):]))
            elif part == "/build":
                out.append(str(work))
            else:
                out.append(part)
        return out

    @staticmethod
    def _env() -> Dict[str, str]:
        """A minimal environment: no API keys, no app config."""
        keep = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "HOME", "LANG")
        env = {k: os.environ[k] for k in keep if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return env

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> SandboxResult:
        if not self._enabled:
            raise SandboxUnavailable(
                "Local code execution is disabled (set ALLOW_LOCAL_CODE_EXEC to enable)."
            )

        with tempfile.TemporaryDirectory(prefix="localexec_") as workdir:
            work = Path(workdir)
            _write_sources(work, files)
            env = self._env()
            start = time.time()

            def _elapsed() -> float:
                return round((time.time() - start) * 1000, 2)

            if spec.compile_cmd:
                try:
                    built = subprocess.run(
                        self._localise(spec.compile_cmd, work),
                        cwd=str(work),
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=timeout + _DOCKER_OVERHEAD_SECONDS,
                    )
                except subprocess.TimeoutExpired:
                    return SandboxResult(
                        exit_code=124,
                        stdout="",
                        stderr=f"Compilation timed out ({timeout:g}s)",
                        timed_out=True,
                        duration_ms=_elapsed(),
                        compile_ok=False,
                    )
                except Exception as exc:
                    raise SandboxUnavailable(f"Local compile failed to start: {exc}") from exc

                if built.returncode != 0:
                    return SandboxResult(
                        exit_code=built.returncode,
                        stdout=_truncate(built.stdout),
                        stderr=_truncate(built.stderr),
                        timed_out=False,
                        duration_ms=_elapsed(),
                        compile_ok=False,
                    )

            if compile_only:
                return SandboxResult(
                    exit_code=0,
                    stdout="",
                    stderr="",
                    timed_out=False,
                    duration_ms=_elapsed(),
                    compile_ok=True,
                )

            try:
                proc = subprocess.run(
                    self._localise(spec.run_cmd, work),
                    cwd=str(work),
                    env=env,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Time Limit Exceeded ({timeout:g}s)",
                    timed_out=True,
                    duration_ms=_elapsed(),
                )
            except Exception as exc:
                raise SandboxUnavailable(f"Local execution failed to start: {exc}") from exc

            return SandboxResult(
                exit_code=proc.returncode,
                stdout=_truncate(proc.stdout),
                stderr=_truncate(proc.stderr),
                timed_out=False,
                duration_ms=_elapsed(),
            )


# ── Layered resolver ──────────────────────────────────────────────────────────


class LayeredSandbox:
    """Delegates each run to the first backend that supports the language.

    The choice is per-language, not global: Piston may cover Python while only
    the Docker image can build Objective-C. When no backend supports a language,
    ``run`` raises rather than guessing.
    """

    def __init__(self, backends: Optional[List[Any]] = None) -> None:
        self.backends: List[Any] = (
            backends
            if backends is not None
            else [PistonSandbox(), ContainerSandbox(), LocalSandbox()]
        )

    def available(self) -> bool:
        return any(b.available() for b in self.backends)

    def backend_for(self, spec: Any) -> Optional[Any]:
        for backend in self.backends:
            try:
                if backend.supports(spec):
                    return backend
            except Exception as exc:
                logger.warning(f"Sandbox backend {backend.name} probe failed: {exc}")
        return None

    def supports(self, spec: Any) -> bool:
        return self.backend_for(spec) is not None

    def describe(self) -> str:
        ready = [b.name for b in self.backends if b.available()]
        return ", ".join(ready) if ready else "none"

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> SandboxResult:
        backend = self.backend_for(spec)
        if backend is None:
            raise SandboxUnavailable(
                f"No execution backend available for {spec.name} on this host."
            )
        return backend.run(spec, files, compile_only=compile_only, timeout=timeout)


_sandbox: Optional[LayeredSandbox] = None


def get_sandbox() -> LayeredSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = LayeredSandbox()
    return _sandbox
