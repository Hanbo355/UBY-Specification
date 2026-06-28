"""Compare Zenodo deposition files with the new manifest to plan cleanup."""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "data_release" / "uby-time-dataset-v0.1.0"
MANIFEST_PATH = RELEASE_DIR / "dataset_manifest.json"
STATE_PATH = RELEASE_DIR / ".zenodo_upload_state.json"

token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    sys.exit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"
deposition_id = 20763218

# 1. Get current deposition files
r = requests.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=60,
)
r.raise_for_status()
deposition = r.json()
remote_files = {f["filename"]: f for f in deposition.get("files", [])}
print(f"Remote files on deposition {deposition_id}: {len(remote_files)}")

# 2. Get desired files from manifest + release metadata
def iter_desired_files():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        relative_path = entry["path"]
        upload_name = relative_path.replace("/", "__").replace("\\", "__")
        yield upload_name, Path(ROOT) / relative_path
    for path in sorted(RELEASE_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name == STATE_PATH.name:
            continue
        upload_name = f"release_metadata__{path.name}"
        yield upload_name, path

desired = dict(iter_desired_files())
print(f"Desired files (manifest + release metadata): {len(desired)}")

# 3. Find obsolete files (on remote but not in desired)
obsolete = [name for name in remote_files if name not in desired]
print(f"\nObsolete files to delete ({len(obsolete)}):")
for name in sorted(obsolete):
    size = remote_files[name].get("filesize", 0)
    print(f"  - {name}  ({size:,} bytes)")

# 4. Find missing files (in desired but not on remote)
missing = [name for name in desired if name not in remote_files]
print(f"\nMissing files to upload ({len(missing)}):")
for name in sorted(missing):
    size = desired[name].stat().st_size
    print(f"  - {name}  ({size:,} bytes)")

# 5. Find files that need refresh (on remote, in desired, but small enough to have changed)
small_threshold = 2 * 1024 * 1024  # 2 MiB
to_refresh = []
for name in desired:
    if name in remote_files and int(remote_files[name].get("filesize", 0)) < small_threshold:
        to_refresh.append(name)
print(f"\nSmall files to refresh ({len(to_refresh)}):")
for name in sorted(to_refresh):
    size = remote_files[name].get("filesize", 0)
    print(f"  - {name}  ({size:,} bytes)")
