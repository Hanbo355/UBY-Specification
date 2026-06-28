"""Sync local upload state with actual files on Zenodo deposition."""
import json
from pathlib import Path

import requests

token_env = None
import os
token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    raise SystemExit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"
deposition_id = 21003260

# Get current files on Zenodo
r = requests.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=30,
)
r.raise_for_status()
d = r.json()
remote_files = {f["filename"]: f for f in d.get("files", [])}
print(f"Files on Zenodo deposition {deposition_id}: {len(remote_files)}")

# Load state
state_path = Path("uby-time/data_release/uby-time-dataset-v0.1.0/.zenodo_upload_state.json")
state = json.loads(state_path.read_text(encoding="utf-8"))

# Sync uploaded_files with reality
uploaded = state.setdefault("uploaded_files", {})
for name, entry in remote_files.items():
    if name not in uploaded:
        uploaded[name] = {
            "path": name.replace("__", "/").replace("release_metadata__", ""),
            "size_bytes": entry.get("filesize", 0),
            "status": "already_present",
        }
        print(f"  Synced: {name} ({entry.get('filesize', 0):,} bytes)")

state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
print(f"\nState file updated. Total uploaded_files: {len(uploaded)}")
print("Ready to resume upload for remaining files.")
