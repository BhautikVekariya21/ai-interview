import os
import sys
import time
from urllib import error, request


def parse_targets(raw: str) -> list[tuple[str, str]]:
    targets = []
    for line in raw.splitlines():
        item = line.strip()
        if not item:
            continue
        if "|" in item:
            name, url = item.split("|", 1)
            targets.append((name.strip(), url.strip()))
        else:
            targets.append((item, item))
    return targets


def check_target(name: str, url: str, retries: int, delay_seconds: float) -> tuple[bool, str]:
    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            req = request.Request(url, headers={"User-Agent": "ai-interview-smoke-check"})
            with request.urlopen(req, timeout=15) as response:
                status = response.getcode()
                if 200 <= status < 400:
                    return True, f"{name}: {status}"
                last_error = f"{name}: unexpected status {status}"
        except error.HTTPError as exc:
            last_error = f"{name}: HTTP {exc.code}"
        except Exception as exc:
            last_error = f"{name}: {exc}"
        if attempt < retries:
            time.sleep(delay_seconds)
    return False, last_error


def main() -> int:
    raw_targets = os.environ.get("SMOKE_TARGETS", "").strip()
    if not raw_targets:
        print("No smoke test targets configured.")
        return 0

    retries = int(os.environ.get("SMOKE_RETRIES", "5"))
    delay_seconds = float(os.environ.get("SMOKE_DELAY_SECONDS", "10"))
    failures: list[str] = []

    for name, url in parse_targets(raw_targets):
        ok, message = check_target(name, url, retries, delay_seconds)
        print(message)
        if not ok:
            failures.append(message)

    if failures:
        print("\nSmoke checks failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
