"""Reset upload state to force fresh upload of all files."""
import json
from pathlib import Path

state_path = Path("uby-time/data_release/uby-time-dataset-v0.1.0/.zenodo_upload_state.json")
state = json.loads(state_path.read_text(encoding="utf-8"))

# Keep deposition info, reset upload tracking
state["uploaded_files"] = {}
state["reset_at"] = "2026-06-28T15:00:00Z"
state["reset_reason"] = "All files deleted from new version draft; fresh upload required"

state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
print(f"Reset upload state. Deposition ID: {state['deposition_id']}")
print(f"Uploaded files tracking cleared. Ready for fresh upload.")
