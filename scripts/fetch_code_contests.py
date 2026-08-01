"""Download DeepMind CodeContests statements into a local cache.

Why a separate fetch step: the dataset rows carry every accepted and rejected
solution ever submitted, which is ~200 KB per problem and roughly 2 GB across
the corpus. None of that is wanted here — we import the *statement*, its
sample tests and its limits. So the heavy fields are dropped the moment a
batch is parsed, and only the slim records are written to disk. Re-running
resumes from whatever offset the cache already reached rather than starting
over.

Licence: the CodeContests dataset is Apache 2.0 (code) / CC BY 4.0 (non-code
content, which is what a problem statement is). Attribution is recorded on
every imported problem as ``source_attribution`` so the provenance travels
with the data instead of living only in a commit message.

Usage:
    python scripts/fetch_code_contests.py            # fetch everything
    python scripts/fetch_code_contests.py --limit 200
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

CACHE = Path(__file__).resolve().parents[1] / "data" / "code_contests_raw.jsonl"
ENDPOINT = "https://datasets-server.huggingface.co/rows"
DATASET = "deepmind/code_contests"

# The row payload is dominated by these. Dropping them before anything else
# touches the batch is what keeps the fetch to megabytes instead of gigabytes.
_DROP = ("solutions", "incorrect_solutions", "generated_tests", "private_tests")

# Kept deliberately small. Each row can be hundreds of KB before the drop, so a
# large batch risks a gateway timeout on the dataset server rather than going
# faster.
BATCH = 20


def _slim(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """One cache record, or None when the row has nothing usable.

    A statement with no sample test cannot be turned into a gradeable problem —
    there would be nothing to show as an example and nothing to check a
    submission against — so it is dropped here rather than half-imported.
    """
    description = (row.get("description") or "").strip()
    public = row.get("public_tests") or {}
    inputs = public.get("input") or []
    outputs = public.get("output") or []
    if not description or not inputs or len(inputs) != len(outputs):
        return None

    limit = row.get("time_limit") or {}
    return {
        "name": row.get("name") or "",
        "description": description,
        "difficulty": row.get("difficulty"),
        "cf_rating": row.get("cf_rating"),
        "cf_tags": [t for t in (row.get("cf_tags") or []) if t],
        "source": row.get("source"),
        "public_tests": {"input": inputs, "output": outputs},
        "time_limit_seconds": limit.get("seconds"),
        "memory_limit_bytes": row.get("memory_limit_bytes"),
    }


def _fetch(offset: int, length: int, retries: int = 4) -> Dict[str, Any]:
    """One batch, retrying the dataset server's intermittent 502s.

    The server fronts a large parquet store and returns a gateway error under
    load often enough that a single failure is not a reason to abandon a fetch
    that is otherwise minutes from finishing.
    """
    params = urllib.parse.urlencode(
        {
            "dataset": DATASET,
            "config": "default",
            "split": "train",
            "offset": offset,
            "length": length,
        }
    )
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(f"{ENDPOINT}?{params}", timeout=180) as resp:
                return json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last = exc
            # Linear backoff: the failures are load-related, and hammering a
            # struggling server immediately makes the next attempt likelier to
            # fail too.
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"offset {offset} failed after {retries} attempts: {last}")


def _already_cached() -> int:
    if not CACHE.exists():
        return 0
    with CACHE.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


def stream(limit: Optional[int] = None) -> Iterator[Dict[str, Any]]:
    """Yield slim records, resuming from whatever the cache already holds."""
    seen = _already_cached()
    if seen:
        print(f"resuming: {seen} records already cached")

    total: Optional[int] = None
    offset = seen
    while total is None or offset < total:
        payload = _fetch(offset, BATCH)
        total = payload.get("num_rows_total") or 0
        rows = payload.get("rows") or []
        if not rows:
            break
        for entry in rows:
            row = entry.get("row") or {}
            for key in _DROP:
                row.pop(key, None)
            record = _slim(row)
            if record:
                yield record
        offset += len(rows)
        print(f"  {offset}/{total}", flush=True)
        if limit and offset >= limit:
            break


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="stop after N rows")
    args = parser.parse_args()

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    # Appended, not rewritten: a fetch this long will sometimes be interrupted,
    # and losing an hour of downloads to a dropped connection is avoidable.
    with CACHE.open("a", encoding="utf-8") as handle:
        for record in stream(args.limit):
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
            handle.flush()
    print(f"wrote {written} records to {CACHE}")


if __name__ == "__main__":
    main()
