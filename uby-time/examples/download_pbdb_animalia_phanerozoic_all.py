#!/usr/bin/env python3
"""
Download all available PBDB Animalia/Phanerozoic occurrence records in batches.

This script expands the UBY paleobiology layer beyond fixed 50k/100k samples by
paging through the Paleobiology Database API until a final partial batch is
returned.

Output:
- data/raw/pbdb/pbdb_animalia_phanerozoic_occurrences_offset_000000.csv
- data/raw/pbdb/pbdb_animalia_phanerozoic_occurrences_offset_050000.csv
- ...
- data/raw/pbdb/pbdb_animalia_phanerozoic_download_manifest.json
"""

from __future__ import annotations

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "pbdb"
MANIFEST_OUT = RAW_DIR / "pbdb_animalia_phanerozoic_download_manifest.json"

BASE_URL = "https://paleobiodb.org/data1.2/occs/list.csv"
LIMIT = 10000
REQUEST_PAUSE_SECONDS = 0.5
MAX_RETRIES = 5
USER_AGENT = "uby-time/0.1.0 research data downloader (https://github.com/)"

BASE_PARAMS = {
    "base_name": "Animalia",
    "interval": "Phanerozoic",
    "show": "coords,phylo,ident,attr,strat,time",
    "limit": str(LIMIT),
}


def _batch_path(offset: int) -> Path:
    return RAW_DIR / f"pbdb_animalia_phanerozoic_occurrences_offset_{offset:06d}.csv"


def _legacy_batch_path(offset: int) -> Path:
    if offset == 0:
        return RAW_DIR / "pbdb_animalia_phanerozoic_occurrences_50k.csv"
    return RAW_DIR / f"pbdb_animalia_phanerozoic_occurrences_50k_offset_{offset}.csv"


def _row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    with path.open("r", encoding="utf-8", newline="") as file:
        return sum(1 for _ in csv.DictReader(file))


def _download_batch(offset: int, output_path: Path) -> None:
    params = dict(BASE_PARAMS)
    if offset:
        params["offset"] = str(offset)

    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                payload = response.read()
            output_path.write_bytes(payload)
            return
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
            last_error = error
            wait_seconds = min(60, attempt * attempt * 2)
            print(
                f"download retry offset={offset} attempt={attempt}/{MAX_RETRIES} "
                f"wait={wait_seconds}s error={error}"
            )
            time.sleep(wait_seconds)

    raise RuntimeError(f"Failed to download PBDB batch offset={offset}") from last_error


def download_all() -> list[dict[str, object]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    batches: list[dict[str, object]] = []
    offset = 0
    total_rows = 0
    started = time.perf_counter()

    while True:
        path = _batch_path(offset)
        legacy_path = _legacy_batch_path(offset)

        if path.exists():
            status = "existing"
        elif legacy_path.exists():
            path.write_bytes(legacy_path.read_bytes())
            status = "copied_from_legacy"
        else:
            _download_batch(offset, path)
            status = "downloaded"

        rows = _row_count(path)
        total_rows += rows
        batch_info = {
            "offset": offset,
            "limit": LIMIT,
            "rows": rows,
            "bytes": path.stat().st_size if path.exists() else 0,
            "path": str(path.as_posix()),
            "status": status,
        }
        batches.append(batch_info)

        print(
            f"offset={offset} rows={rows} bytes={batch_info['bytes']} "
            f"status={status} path={path}"
        )

        if rows < LIMIT:
            break

        # Advance by the actual row count so existing 50k legacy batches can be
        # reused while newer downloads proceed with smaller, more reliable 10k
        # requests.
        offset += rows
        time.sleep(REQUEST_PAUSE_SECONDS)

    wall_seconds = time.perf_counter() - started
    manifest = {
        "dataset": "Paleobiology Database Animalia Phanerozoic occurrences",
        "source_api": BASE_URL,
        "base_params": BASE_PARAMS,
        "batch_limit": LIMIT,
        "batch_count": len(batches),
        "total_rows": total_rows,
        "wall_seconds": wall_seconds,
        "rows_per_second": total_rows / wall_seconds if wall_seconds else 0,
        "batches": batches,
    }
    MANIFEST_OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Total rows: {total_rows}")
    print(f"Batch count: {len(batches)}")
    print(f"Manifest: {MANIFEST_OUT}")
    print(f"Wall seconds: {wall_seconds:.6f}")
    print(f"Rows/s: {total_rows / wall_seconds if wall_seconds else 0:.2f}")

    return batches


def main() -> int:
    download_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
