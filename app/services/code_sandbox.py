"""Isolated execution backends for running untrusted candidate code.

Candidate submissions are hostile input. Running them with a bare ``subprocess``
on the API server hands them the server's own interpreter, working directory,
environment (API keys included), and network.

Three backends satisfy the same contract, and the layered resolver picks the
first one that can run a given language:

1. :class:`PistonSandbox` — an HTTP call to a Piston instance. Strongest
   isolation, but off by default because it needs infrastructure to point at.
2. :class:`ContainerSandbox` — a throwaway Docker container. Only usable where a
   Docker socket is reachable, which the shipped image does not have.
3. :class:`SubprocessSandbox` — a rlimit-confined child process on this host.
   The default, because it is the only backend that needs no extra
   infrastructure. Isolation is real but weaker than a container: see the class
   docstring for exactly what is and is not contained.

Backend order is configurable via ``CODE_EXEC_BACKENDS``, so an operator who
does provision Piston or Docker gets the stronger isolation without a code
change.

Isolation is *required*, not best-effort. When no backend can run a language the
runner raises :class:`SandboxUnavailable` and the caller reports an honest
error. It must never report a pass for code that was not actually executed.
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:  # POSIX only; absent on Windows dev machines.
    import resource
except ImportError:  # pragma: no cover - platform dependent
    resource = None  # type: ignore[assignment]

# Windows has neither SIGKILL nor rlimits, so there is no CPU-limit death to
# recognise there — the wall-clock timeout is the only bound.
_SIGKILL = getattr(signal, "SIGKILL", None)
_SIGXCPU = getattr(signal, "SIGXCPU", None)

# Deaths a candidate can actually cause, translated out of signal numbers. The
# kernel writes nothing to stderr when it kills a process, so these are the only
# explanation the candidate would otherwise get.
_SIGNAL_EXPLANATIONS = {
    getattr(signal, "SIGXFSZ", None): "wrote more data than the sandbox file size limit allows",
    getattr(signal, "SIGSEGV", None): "segmentation fault (invalid memory access)",
    getattr(signal, "SIGABRT", None): "aborted (an assertion or allocation failure)",
    getattr(signal, "SIGFPE", None): "arithmetic error (such as integer division by zero)",
    getattr(signal, "SIGBUS", None): "bus error (misaligned or invalid memory access)",
}
_SIGNAL_EXPLANATIONS.pop(None, None)

import requests
from loguru import logger

from app.core.config import settings

# Hard caps. These bound a single submission, not the whole feature.
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MEMORY = "256m"
DEFAULT_CPUS = "0.5"
DEFAULT_PIDS_LIMIT = 128
MAX_OUTPUT_CHARS = 64_000

# Subprocess-backend rlimits. A compile step legitimately writes an executable,
# so the file cap is generous.
MAX_FILE_BYTES = 64 * 1024 * 1024

# Address-space ceiling for the subprocess backend. Deliberately far above
# DEFAULT_MEMORY: RLIMIT_AS counts *reserved* virtual address space, and managed
# runtimes reserve enormous ranges up front (the JVM ~1 GB, Go's heap arena
# similar) while touching very little of it. Capping at the real memory figure
# would make those runtimes fail to start at all, which reads to a candidate as
# "my correct code is broken". This still stops an unbounded allocation loop
# from taking the API server down with it.
MAX_ADDRESS_SPACE_BYTES = 2 * 1024 * 1024 * 1024

# Grace added to the `docker run` timeout so the container's own SIGKILL and
# teardown are what we observe, rather than racing our client-side timeout.
_DOCKER_OVERHEAD_SECONDS = 15.0

# Compilers are slower than the programs they build, so a compile step gets the
# run timeout plus this much before it is considered hung.
_COMPILE_EXTRA_SECONDS = 20.0

# How long to wait for a killed process's pipes to close before giving up.
_DRAIN_TIMEOUT_SECONDS = 5.0

# Hosts whose use should be flagged loudly: code sent to a public execution
# service leaves this machine.
_PUBLIC_EXEC_HOSTS = ("emkc.org", "ce.judge0.com", "judge0.com")

# How long to leave an HTTP backend marked unreachable after a failed probe, so
# a down host costs one timeout per minute rather than one per submission.
_HTTP_BACKEND_RETRY_SECONDS = 60.0

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


def _warn_if_public(url: str, setting: str) -> None:
    """Say plainly when submitted code is about to leave this machine."""
    if any(host in url for host in _PUBLIC_EXEC_HOSTS):
        logger.warning(
            f"Code execution is using the PUBLIC instance at {url}: submitted "
            f"code leaves this host and the rate limit is shared with everyone "
            f"else using it. Point {setting} at your own instance before "
            f"running real interviews."
        )


# ── Piston (HTTP) ─────────────────────────────────────────────────────────────


class PistonSandbox:
    """Executes code on a Piston instance over HTTP.

    Piston compiles and runs from source files alone — there is no command to
    pass and no image to pull, so ``spec.run_cmd`` / ``spec.compile_cmd`` are
    unused here. The instance itself provides the isolation.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        raw = base_url if base_url is not None else settings.PISTON_URL
        self._api = self._api_root(raw or "")
        self._timeout = timeout or settings.PISTON_TIMEOUT_SECONDS
        # language name (and alias) → concrete version string. Piston's execute
        # endpoint requires an explicit version, so this doubles as the
        # availability probe. None means "not yet probed".
        self._runtimes: Optional[Dict[str, str]] = None
        # Monotonic deadline before which a failed probe is not retried. Without
        # this, one blip at startup would disable Piston until a restart; with a
        # bare retry, every run would pay a full timeout while the host is down.
        self._retry_after = 0.0

    @staticmethod
    def _api_root(raw: str) -> str:
        """Normalise a configured URL to the prefix that `/execute` hangs off.

        Self-hosted Piston serves `/api/v2/execute` at the server root, but the
        public instance is mounted under a path (`emkc.org/api/v2/piston`). One
        setting has to accept both, so a URL that already names an API version
        is taken as-is and a bare host gets the default suffix appended.
        """
        base = raw.strip().rstrip("/")
        if not base:
            return ""
        return base if "/api/v" in base else f"{base}/api/v2"

    @property
    def name(self) -> str:
        return "piston"

    def _load_runtimes(self) -> Dict[str, str]:
        if self._runtimes:
            return self._runtimes
        if not self._api:
            self._runtimes = {}
            return self._runtimes
        # An empty (not None) table means a previous probe failed; back off.
        if self._runtimes is not None and time.monotonic() < self._retry_after:
            return self._runtimes
        try:
            resp = requests.get(f"{self._api}/runtimes", timeout=self._timeout)
            resp.raise_for_status()
            table: Dict[str, str] = {}
            for entry in resp.json():
                version = entry.get("version") or ""
                for key in [entry.get("language")] + list(entry.get("aliases") or []):
                    if key and key not in table:
                        table[key] = version
            self._runtimes = table
            logger.info(f"Piston at {self._api}: {len(table)} runtimes available")
            _warn_if_public(self._api, "PISTON_URL")
        except Exception as exc:
            logger.warning(f"Piston unreachable at {self._api or '<unset>'}: {exc}")
            self._runtimes = {}
            self._retry_after = time.monotonic() + _HTTP_BACKEND_RETRY_SECONDS
        return self._runtimes

    def _disable(self, seconds: float = _HTTP_BACKEND_RETRY_SECONDS) -> None:
        """Mark the instance unusable so the resolver stops choosing it."""
        self._runtimes = {}
        self._retry_after = time.monotonic() + seconds

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
        stdin: str = "",
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
            "stdin": stdin,
            "compile_timeout": int(timeout * 1000) + 10_000,
            "run_timeout": int(timeout * 1000),
        }

        start = time.time()
        try:
            resp = requests.post(
                f"{self._api}/execute",
                json=payload,
                timeout=self._timeout + timeout,
            )
        except Exception as exc:
            raise SandboxUnavailable(f"Piston request failed: {exc}") from exc
        elapsed = round((time.time() - start) * 1000, 2)

        # `/runtimes` is open even where `/execute` is not — the public instance
        # went whitelist-only in Feb 2026 and answers 401 here. Without this the
        # backend would keep claiming every language and failing every run.
        if resp.status_code in (401, 403):
            self._disable()
            raise SandboxUnavailable(
                f"Piston rejected the request (HTTP {resp.status_code}). "
                "The public instance is whitelist-only; set PISTON_URL to a "
                "self-hosted instance."
            )
        # The public instance rate-limits per IP. That is a queueing problem on
        # our side, not a fault in the submitted code, so say so plainly rather
        # than letting it read as a failed run.
        if resp.status_code == 429:
            raise SandboxUnavailable(
                "Piston rate limit reached — too many runs at once. Try again "
                "in a few seconds."
            )
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

        # Piston has no compile-only mode, so the program has already run by the
        # time we get here. Report the compile stage alone anyway: the caller
        # asked "does this build?", and letting a non-zero *run* exit code
        # through would surface a missing `main` as a compilation error.
        if compile_only:
            return SandboxResult(
                exit_code=0,
                stdout="",
                stderr="",
                timed_out=False,
                duration_ms=elapsed,
                compile_ok=True,
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


# ── Judge0 (HTTP) ─────────────────────────────────────────────────────────────


class Judge0Sandbox:
    """Executes code on a Judge0 instance over HTTP.

    Like Piston, Judge0 needs only the source and a language id — the instance
    provides the isolation. It exists here because it is the one keyless remote
    option left: the public Piston API went whitelist-only in Feb 2026, so on a
    host with no Docker and no local toolchain this is what makes Ruby, PHP,
    Swift, Haskell and friends run at all.
    """

    # Judge0 status ids. Anything above 4 is a failure of some kind; these are
    # the three that need distinct handling rather than "the program errored".
    _STATUS_TLE = 5
    _STATUS_COMPILE_ERROR = 6
    _STATUS_INTERNAL = {13, 14}

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[float] = None) -> None:
        raw = base_url if base_url is not None else settings.JUDGE0_URL
        self._base = (raw or "").strip().rstrip("/")
        self._timeout = timeout or settings.JUDGE0_TIMEOUT_SECONDS
        self._headers = {}
        if settings.JUDGE0_API_KEY:
            # RapidAPI-hosted instances authenticate this way; self-hosted ones
            # ignore the header, so sending it unconditionally is harmless.
            self._headers = {
                "X-RapidAPI-Key": settings.JUDGE0_API_KEY,
                "X-Auth-Token": settings.JUDGE0_API_KEY,
            }
        # Prefix (e.g. "Ruby (") → language id. None means "not yet probed".
        self._languages: Optional[Dict[str, int]] = None
        self._retry_after = 0.0

    @property
    def name(self) -> str:
        return "judge0"

    def _load_languages(self) -> Dict[str, int]:
        if self._languages:
            return self._languages
        if not self._base:
            self._languages = {}
            return self._languages
        if self._languages is not None and time.monotonic() < self._retry_after:
            return self._languages
        try:
            resp = requests.get(
                f"{self._base}/languages", timeout=self._timeout, headers=self._headers
            )
            resp.raise_for_status()
            table: Dict[str, int] = {}
            for entry in resp.json():
                label = entry.get("name") or ""
                ident = entry.get("id")
                if not label or ident is None:
                    continue
                prefix = label.split("(")[0] + "("
                # Ids grow monotonically as runtimes are added, so the highest
                # id for a prefix is the newest version of that language.
                if ident > table.get(prefix, -1):
                    table[prefix] = ident
            self._languages = table
            logger.info(f"Judge0 at {self._base}: {len(table)} languages available")
            _warn_if_public(self._base, "JUDGE0_URL")
        except Exception as exc:
            logger.warning(f"Judge0 unreachable at {self._base or '<unset>'}: {exc}")
            self._languages = {}
            self._retry_after = time.monotonic() + _HTTP_BACKEND_RETRY_SECONDS
        return self._languages

    def available(self) -> bool:
        return bool(self._load_languages())

    def supports(self, spec: Any) -> bool:
        return bool(spec.judge0) and spec.judge0 in self._load_languages()

    def _disable(self, seconds: float = _HTTP_BACKEND_RETRY_SECONDS) -> None:
        """Mark the instance unusable so the resolver stops choosing it."""
        self._languages = {}
        self._retry_after = time.monotonic() + seconds

    @staticmethod
    def _adapt_source(spec: Any, source: str) -> str:
        """Reconcile the submission with Judge0's fixed filename.

        Judge0 takes one unnamed blob and writes it to `Main.<ext>`, which only
        matters for Java: the language requires the public class to match the
        file, so a candidate's `public class Solution` fails to compile there
        while building fine on every other backend. Renaming the class — every
        reference to it, since this is a single file — is the standard
        adaptation and is semantically inert for a self-contained program.
        """
        if not spec.judge0.startswith("Java (") or "class Main" in source:
            return source
        match = re.search(r"\bpublic\s+(?:final\s+|abstract\s+)?class\s+(\w+)", source)
        if match is None or match.group(1) == "Main":
            return source
        return re.sub(rf"\b{re.escape(match.group(1))}\b", "Main", source)

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        stdin: str = "",
    ) -> SandboxResult:
        language_id = self._load_languages().get(spec.judge0)
        if language_id is None:
            raise SandboxUnavailable(f"Judge0 has no runtime for {spec.name}.")

        payload = {
            "language_id": language_id,
            "source_code": self._adapt_source(spec, files[spec.source_name]),
            "stdin": stdin,
            "cpu_time_limit": timeout,
            "wall_time_limit": min(timeout + 5, 20),
        }

        start = time.time()
        try:
            resp = requests.post(
                f"{self._base}/submissions?base64_encoded=false&wait=true",
                json=payload,
                timeout=self._timeout + timeout,
                headers=self._headers,
            )
        except Exception as exc:
            raise SandboxUnavailable(f"Judge0 request failed: {exc}") from exc
        elapsed = round((time.time() - start) * 1000, 2)

        if resp.status_code in (401, 403):
            # Credentials are wrong or the instance is closed to us. That will
            # not fix itself within a run, so stop advertising the backend and
            # let the resolver fall through to one that works.
            self._disable()
            raise SandboxUnavailable(
                f"Judge0 rejected the request (HTTP {resp.status_code}). "
                "Check JUDGE0_URL / JUDGE0_API_KEY."
            )
        if resp.status_code == 429:
            raise SandboxUnavailable(
                "Judge0 rate limit reached — too many runs at once. Try again "
                "in a few seconds."
            )
        if resp.status_code not in (200, 201):
            raise SandboxUnavailable(
                f"Judge0 returned HTTP {resp.status_code}: {resp.text[:300]}"
            )
        try:
            body = resp.json()
        except ValueError as exc:
            raise SandboxUnavailable(f"Judge0 returned non-JSON response: {exc}") from exc

        # Instances that disable `wait=true` answer with a bare token instead.
        if "status" not in body and body.get("token"):
            body = self._poll(body["token"], timeout)
            elapsed = round((time.time() - start) * 1000, 2)

        return self._to_result(body, compile_only, timeout, elapsed)

    def _poll(self, token: str, timeout: float) -> Dict[str, Any]:
        """Await a queued submission, for instances without `wait=true`."""
        deadline = time.monotonic() + self._timeout + timeout
        while time.monotonic() < deadline:
            time.sleep(0.4)
            try:
                resp = requests.get(
                    f"{self._base}/submissions/{token}?base64_encoded=false",
                    timeout=self._timeout,
                    headers=self._headers,
                )
                resp.raise_for_status()
                body = resp.json()
            except Exception as exc:
                raise SandboxUnavailable(f"Judge0 poll failed: {exc}") from exc
            # 1 = In Queue, 2 = Processing; anything else is terminal.
            if (body.get("status") or {}).get("id", 0) > 2:
                return body
        raise SandboxUnavailable("Judge0 did not return a verdict in time.")

    def _to_result(
        self,
        body: Dict[str, Any],
        compile_only: bool,
        timeout: float,
        elapsed: float,
    ) -> SandboxResult:
        status = (body.get("status") or {}).get("id")
        stdout = body.get("stdout") or ""
        stderr = body.get("stderr") or ""
        compile_output = body.get("compile_output") or ""

        if status in self._STATUS_INTERNAL:
            raise SandboxUnavailable(
                f"Judge0 internal error: {body.get('message') or 'unknown'}"
            )

        if status == self._STATUS_COMPILE_ERROR:
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=_truncate(compile_output or stderr),
                timed_out=False,
                duration_ms=elapsed,
                compile_ok=False,
            )

        # Judge0 has no compile-only mode either, so the program has already
        # run. Reaching here means it compiled, which is the whole question.
        if compile_only:
            return SandboxResult(
                exit_code=0,
                stdout="",
                stderr="",
                timed_out=False,
                duration_ms=elapsed,
                compile_ok=True,
            )

        if status == self._STATUS_TLE:
            return SandboxResult(
                exit_code=124,
                stdout=_truncate(stdout),
                stderr=f"Time Limit Exceeded ({timeout:g}s)",
                timed_out=True,
                duration_ms=elapsed,
                compile_ok=True,
            )

        # `exit_code` is absent on older instances; fall back to the status,
        # where 3 (Accepted) and 4 (Wrong Answer, unused here) both mean the
        # program ran to completion.
        exit_code = body.get("exit_code")
        if exit_code is None:
            exit_code = 0 if status in (3, 4) else 1
        # A signalled or errored run often carries its only explanation in
        # `message` ("Exited with error status 1"), so don't drop it.
        message = body.get("message") or ""
        if exit_code and message and message not in stderr:
            stderr = (stderr + "\n" + message).strip()

        return SandboxResult(
            exit_code=exit_code,
            stdout=_truncate(stdout),
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


# ── Rlimit-confined subprocess (default backend) ──────────────────────────────

# `dotnet run --project` needs a generated project file, which only the Docker
# image provides. Rather than invent one and let the missing-project error surface
# as if the candidate's code were at fault, C# is not offered here.
_SUBPROCESS_EXCLUDED = {"C#"}


class SubprocessSandbox:
    """Runs code as a child process confined by POSIX resource limits.

    What is contained:

    * **CPU time** — ``RLIMIT_CPU`` makes the kernel SIGKILL a spinning process
      even if it never returns to our event loop. The wall-clock timeout below
      is the backstop for a process that sleeps rather than spins.
    * **Memory** — ``RLIMIT_AS`` caps the address space, so a runaway allocation
      raises MemoryError in the child instead of OOM-killing the API server.
    * **Disk** — ``RLIMIT_FSIZE`` caps written bytes, and the child's cwd is a
      per-run temp dir removed afterwards.
    * **Secrets** — the child gets a scrubbed environment, so the API keys in the
      server's own environment are not readable.
    * **Orphans** — the child leads its own process group, which is killed as a
      group on timeout so grandchildren cannot outlive the run.

    What is *not* contained: the child runs as the same OS user as the API
    server, so it can read any file that user can read, and it can open sockets.
    Nor is the process count capped — ``RLIMIT_NPROC`` is per-UID, so setting it
    here would count the server's own uvicorn workers and starve them; a fork
    bomb is only stopped by the group kill at the wall-clock timeout. Deploy this
    as a non-root user (the shipped Dockerfile does), and prefer Piston or Docker
    via ``CODE_EXEC_BACKENDS`` where the infrastructure exists.
    """

    def __init__(self, enabled: bool = True) -> None:
        self._enabled = enabled

    @property
    def name(self) -> str:
        return "subprocess"

    def available(self) -> bool:
        return self._enabled

    def supports(self, spec: Any) -> bool:
        if not self._enabled or spec.name in _SUBPROCESS_EXCLUDED:
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
    def _env(work: Path) -> Dict[str, str]:
        """A minimal environment: no API keys, no app config."""
        keep = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "LANG")
        env = {k: os.environ[k] for k in keep if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        # Point every toolchain's scratch space at the disposable work dir so
        # compilers don't scatter caches into the server user's home.
        env["HOME"] = str(work)
        env["TMPDIR"] = str(work)
        env["TEMP"] = str(work)
        env["TMP"] = str(work)
        env["GOCACHE"] = str(work / ".gocache")
        env["GOPATH"] = str(work / ".gopath")
        env["CARGO_HOME"] = str(work / ".cargo")
        env["npm_config_cache"] = str(work / ".npm")
        return env

    @staticmethod
    def _limits(cpu_seconds: int):
        """Build the child-side pre-exec hook applying rlimits, or None.

        Returns None on Windows, where none of this exists — the wall-clock
        timeout is then the only bound, which is why Windows is dev-only.
        """
        if resource is None or not hasattr(os, "setsid"):
            return None

        def _apply() -> None:  # pragma: no cover - runs in the forked child
            # The new session comes from Popen's start_new_session; calling
            # setsid() again here would fail with EPERM and kill the child.
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1))
            resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            try:
                resource.setrlimit(
                    resource.RLIMIT_AS,
                    (MAX_ADDRESS_SPACE_BYTES, MAX_ADDRESS_SPACE_BYTES),
                )
            except (ValueError, OSError):
                pass

        return _apply

    def _spawn(
        self,
        argv: List[str],
        work: Path,
        timeout: float,
        stdin: str,
    ) -> subprocess.CompletedProcess:
        """Run one command under the limits, killing the group on timeout.

        `subprocess.run(timeout=...)` only kills the process it started, so a
        program that forks would leave its children running and holding the
        pipes open. Popen plus a group kill is what actually reaps the tree.
        """
        proc = subprocess.Popen(
            argv,
            cwd=str(work),
            env=self._env(work),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=self._limits(int(timeout) + 1),
            start_new_session=hasattr(os, "setsid"),
        )
        try:
            out, err = proc.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired:
            self._kill_tree(proc)
            # Drain the pipes so the fds are closed, but never block forever
            # doing it: a grandchild that called setsid() escapes the group
            # kill and could hold stdout open indefinitely. Leaking that
            # process is bad; hanging a request thread on it is worse.
            try:
                proc.communicate(timeout=_DRAIN_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Sandbox pipes still held after group kill; abandoning drain"
                )
            raise
        return subprocess.CompletedProcess(argv, proc.returncode, out, err)

    @staticmethod
    def _kill_tree(proc: subprocess.Popen) -> None:
        """SIGKILL the child's whole process group; fall back to the child."""
        try:
            if hasattr(os, "killpg") and _SIGKILL is not None:
                os.killpg(os.getpgid(proc.pid), _SIGKILL)
                return
        except (ProcessLookupError, PermissionError, OSError):
            pass
        try:
            proc.kill()
        except OSError:  # pragma: no cover - already dead
            pass

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        stdin: str = "",
    ) -> SandboxResult:
        if not self._enabled:
            raise SandboxUnavailable("Subprocess code execution is disabled.")

        with tempfile.TemporaryDirectory(prefix="codeexec_") as workdir:
            work = Path(workdir)
            _write_sources(work, files)
            start = time.time()

            def _elapsed() -> float:
                return round((time.time() - start) * 1000, 2)

            if spec.compile_cmd:
                try:
                    built = self._spawn(
                        self._localise(spec.compile_cmd, work),
                        work,
                        timeout + _COMPILE_EXTRA_SECONDS,
                        "",
                    )
                except subprocess.TimeoutExpired:
                    return SandboxResult(
                        exit_code=124,
                        stdout="",
                        stderr=(
                            "Compilation timed out "
                            f"({timeout + _COMPILE_EXTRA_SECONDS:g}s)"
                        ),
                        timed_out=True,
                        duration_ms=_elapsed(),
                        compile_ok=False,
                    )
                except OSError as exc:
                    raise SandboxUnavailable(f"Compiler failed to start: {exc}") from exc

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
                proc = self._spawn(
                    self._localise(spec.run_cmd, work),
                    work,
                    timeout,
                    stdin,
                )
            except subprocess.TimeoutExpired:
                return SandboxResult(
                    exit_code=124,
                    stdout="",
                    stderr=f"Time Limit Exceeded ({timeout:g}s)",
                    timed_out=True,
                    duration_ms=_elapsed(),
                )
            except OSError as exc:
                raise SandboxUnavailable(f"Execution failed to start: {exc}") from exc

            # A process killed by a limit dies on a signal with nothing written
            # to stderr, so without this the candidate sees an empty failure and
            # a negative exit code. Name the limit that stopped them instead.
            if proc.returncode is not None and proc.returncode < 0:
                killed_by = -proc.returncode
                if killed_by in (_SIGKILL, _SIGXCPU):
                    return SandboxResult(
                        exit_code=124,
                        stdout=_truncate(proc.stdout),
                        stderr=f"Time Limit Exceeded ({timeout:g}s)",
                        timed_out=True,
                        duration_ms=_elapsed(),
                    )
                explanation = _SIGNAL_EXPLANATIONS.get(killed_by)
                if explanation:
                    stderr = (proc.stderr or "") + f"\nProcess terminated: {explanation}"
                    return SandboxResult(
                        exit_code=proc.returncode,
                        stdout=_truncate(proc.stdout),
                        stderr=_truncate(stderr.strip()),
                        timed_out=False,
                        duration_ms=_elapsed(),
                    )

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
    a local toolchain can build Objective-C. Order comes from
    ``CODE_EXEC_BACKENDS`` so an operator can prefer stronger isolation where
    the infrastructure exists. When no backend supports a language, ``run``
    raises rather than guessing.
    """

    def __init__(self, backends: Optional[List[Any]] = None) -> None:
        self.backends: List[Any] = (
            backends if backends is not None else _configured_backends()
        )

    def available(self) -> bool:
        return any(b.available() for b in self.backends)

    def _candidates(self, spec: Any) -> List[Any]:
        """Every backend that claims this language, in configured order."""
        found = []
        for backend in self.backends:
            try:
                if backend.supports(spec):
                    found.append(backend)
            except Exception as exc:
                logger.warning(f"Sandbox backend {backend.name} probe failed: {exc}")
        return found

    def backend_for(self, spec: Any) -> Optional[Any]:
        candidates = self._candidates(spec)
        return candidates[0] if candidates else None

    def supports(self, spec: Any) -> bool:
        return bool(self._candidates(spec))

    def image_present(self, image: str) -> bool:
        """True when some backend could run `image`'s language.

        Only the Docker backend has a real notion of images; this exists so
        callers and tests can ask one question of the resolver instead of
        reaching past it into a specific backend.
        """
        for backend in self.backends:
            probe = getattr(backend, "image_present", None)
            if probe is not None and probe(image):
                return True
        return False

    def describe(self) -> str:
        ready = [b.name for b in self.backends if b.available()]
        return ", ".join(ready) if ready else "none"

    def run(
        self,
        spec: Any,
        files: Dict[str, str],
        compile_only: bool = False,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        stdin: str = "",
    ) -> SandboxResult:
        candidates = self._candidates(spec)
        if not candidates:
            raise SandboxUnavailable(
                f"No execution backend available for {spec.name} on this host."
            )

        # A backend can claim a language and still be unable to run it right now
        # — a remote instance rate-limits us, an image was pruned. Falling
        # through to the next candidate turns that into a slower run instead of
        # a failed one. Only a genuinely unusable backend raises here; a program
        # that merely exits non-zero returns a result and stops the loop.
        last: Optional[SandboxUnavailable] = None
        for backend in candidates:
            try:
                # Docker does not forward stdin yet, so don't pass an argument
                # it would reject; the others take it natively.
                if stdin and not isinstance(backend, ContainerSandbox):
                    return backend.run(
                        spec, files, compile_only=compile_only, timeout=timeout, stdin=stdin
                    )
                return backend.run(spec, files, compile_only=compile_only, timeout=timeout)
            except SandboxUnavailable as exc:
                logger.warning(f"Sandbox backend {backend.name} unavailable: {exc}")
                last = exc

        raise SandboxUnavailable(
            f"No execution backend could run {spec.name}: {last}"
        )


_BACKEND_FACTORIES = {
    "piston": PistonSandbox,
    "judge0": Judge0Sandbox,
    "docker": ContainerSandbox,
    "subprocess": SubprocessSandbox,
}


def _configured_backends() -> List[Any]:
    """Instantiate the backends named in ``CODE_EXEC_BACKENDS``, in order."""
    names = [n.strip().lower() for n in settings.CODE_EXEC_BACKENDS.split(",") if n.strip()]
    backends = []
    for name in names:
        factory = _BACKEND_FACTORIES.get(name)
        if factory is None:
            logger.warning(f"Unknown code execution backend '{name}' — ignoring")
            continue
        backends.append(factory())
    if not backends:
        logger.warning("No valid code execution backends configured; falling back to subprocess")
        backends.append(SubprocessSandbox())
    return backends


_sandbox: Optional[LayeredSandbox] = None


def get_sandbox() -> LayeredSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = LayeredSandbox()
        logger.info(f"Code execution backends ready: {_sandbox.describe()}")
    return _sandbox
