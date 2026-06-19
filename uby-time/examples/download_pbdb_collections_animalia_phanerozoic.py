#!/usr/bin/env python3
"""
Download PBDB collection-level records for Animalia/Phanerozoic in batches.

This expands the UBY paleobiology database from occurrence-only records to a
collection-level sampling-control layer.  The collection layer is needed for
publication-grade tests of whether apparent last appearances are biological
signals or PBDB sampling artifacts.

Output:
- data/raw/pbdb_collections/pbdb_collections_animalia_phanerozoic_offset_000000.csv
- data/raw/pbdb_collections/pbdb_collections_animalia_phanerozoic_offset_010000.csv
- ...
- data/raw/pbdb_collections/pbdb_collections_animalia_phanerozoic_download_manifest.json
"""

from __future__ import annotations

import csv
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw" / "pbdb_collections"
MANIFEST_OUT = RAW_DIR / "pbdb_collections_animalia_phanerozoic_download_manifest.json"

BASE_URL = "https://paleobiodb.org/data1.2/colls/list.csv"
LIMIT = 5000
REQUEST_PAUSE_SECONDS = 0.5
MAX_RETRIES = 5
USER_AGENT = "uby-time/0.1.0 research collection-level downloader (https://github.com/)"

BASE_PARAMS = {
    "base_name": "Animalia",
    "interval": "Phanerozoic",
    # Collection API show-blocks differ from occurrence API show-blocks.
    # Use only valid collection show-blocks; coordinates are included via loc/locext.
    "show": "full,loc,locext,paleoloc,strat,lith,env,time,ref,refattr",
    "limit": str(LIMIT),
}


def _batch_path(offset: int) -> Path:
    return RAW_DIR / f"pbdb_collections_animalia_phanerozoic_offset_{offset:06d}.csv"


def _fieldnames(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file).fieldnames or [])


def _is_valid_collection_csv(path: Path) -> bool:
    fields = set(_fieldnames(path))
    return "collection_no" in fields and "record_type" in fields


def _row_count(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    if not _is_valid_collection_csv(path):
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
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, http.client.IncompleteRead) as error:
            last_error = error
            wait_seconds = min(60, attempt * attempt * 2)
            print(
                f"download retry offset={offset} attempt={attempt}/{MAX_RETRIES} "
                f"wait={wait_seconds}s error={error}"
            )
            time.sleep(wait_seconds)

    raise RuntimeError(f"Failed to download PBDB collection batch offset={offset}") from last_error


def download_all() -> list[dict[str, object]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    batches: list[dict[str, object]] = []
    offset = 0
    total_rows = 0
    started = time.perf_counter()

    while True:
        path = _batch_path(offset)
        if path.exists() and _is_valid_collection_csv(path):
            status = "existing"
        else:
            had_existing_file = path.exists()
            _download_batch(offset, path)
            if not _is_valid_collection_csv(path):
                raise RuntimeError(
                    f"Downloaded PBDB collection batch is not a valid collection CSV: {path}; "
                    f"fieldnames={_fieldnames(path)}"
                )
            status = "downloaded_or_replaced" if had_existing_file else "downloaded"

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

        offset += rows
        time.sleep(REQUEST_PAUSE_SECONDS)

    wall_seconds = time.perf_counter() - started
    manifest = {
        "dataset": "Paleobiology Database Animalia Phanerozoic collections",
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
