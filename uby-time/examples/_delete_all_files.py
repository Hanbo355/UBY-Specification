"""Delete all files from a Zenodo deposition draft (with retry logic)."""
import os
import sys
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    sys.exit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"
deposition_id = 21003260  # New version draft

# Session with retry
session = requests.Session()
retries = Retry(
    total=5, backoff_factor=2,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "DELETE"],
)
session.mount("https://", HTTPAdapter(max_retries=retries))

# Get current files
r = session.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=60,
)
r.raise_for_status()
d = r.json()
files = d.get("files", [])
print(f"Files on deposition {deposition_id}: {len(files)}")

# Delete all files
deleted = 0
failed = 0
for i, f in enumerate(files, 1):
    file_id = f.get("id")
    filename = f.get("filename", "?")
    if not file_id:
        print(f"  [{i}/{len(files)}] SKIP (no id): {filename}")
        failed += 1
        continue
    url = f"{api}/deposit/depositions/{deposition_id}/files/{file_id}"
    success = False
    for attempt in range(4):
        try:
            r_del = session.delete(url, params={"access_token": token}, timeout=120)
            if r_del.ok:
                success = True
                break
            elif r_del.status_code in (500, 502, 503, 504):
                wait = 3 * (attempt + 1)
                print(f"  [{i}/{len(files)}] Retry {attempt+1} after {wait}s (HTTP {r_del.status_code})")
                time.sleep(wait)
            else:
                print(f"  [{i}/{len(files)}] FAILED ({r_del.status_code}): {filename}: {r_del.text[:200]}")
                break
        except requests.exceptions.RequestException as e:
            wait = 5 * (attempt + 1)
            print(f"  [{i}/{len(files)}] Error, retry {attempt+1} after {wait}s: {type(e).__name__}")
            time.sleep(wait)

    if success:
        deleted += 1
        if i % 10 == 0 or i == len(files):
            print(f"  [{i}/{len(files)}] Deleted: {filename}")
    else:
        failed += 1

    # Small delay every 15 files
    if i % 15 == 0:
        time.sleep(1)

print(f"\nDeleted: {deleted}")
print(f"Failed: {failed}")

# Verify
r = session.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=60,
)
d = r.json()
print(f"Files remaining: {len(d.get('files', []))}")
