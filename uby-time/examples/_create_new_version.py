"""Create a new version of the Zenodo deposition to allow file modifications."""
import json
import os
import sys

import requests

token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    sys.exit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"
deposition_id = 20763218

# First, discard any pending edit (to start clean)
r = requests.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=60,
)
d = r.json()
print(f"Current state: {d.get('state')}")
print(f"Submitted: {d.get('submitted')}")

# Try to discard the edit we just opened (to start clean)
discard_url = d.get("links", {}).get("discard")
if discard_url:
    print("\nDiscarding current edit to restore published state...")
    r_discard = requests.post(discard_url, params={"access_token": token}, timeout=60)
    print(f"Discard status: {r_discard.status_code}")
    if r_discard.ok and r_discard.text.strip():
        d = r_discard.json()
        print(f"State after discard: {d.get('state')}")
    elif r_discard.ok:
        # 204 No Content - re-fetch the deposition
        r_refetch = requests.get(
            f"{api}/deposit/depositions/{deposition_id}",
            params={"access_token": token},
            timeout=60,
        )
        d = r_refetch.json()
        print(f"State after discard (refetched): {d.get('state')}")

# Create a new version
print("\n--- Creating new version ---")
newversion_url = d.get("links", {}).get("newversion")
if not newversion_url:
    # Re-fetch to get links
    r = requests.get(
        f"{api}/deposit/depositions/{deposition_id}",
        params={"access_token": token},
        timeout=60,
    )
    d = r.json()
    newversion_url = d.get("links", {}).get("newversion")

print(f"Newversion URL: {newversion_url}")
r_new = requests.post(newversion_url, params={"access_token": token}, timeout=60)
print(f"Newversion status: {r_new.status_code}")
if r_new.ok:
    new_dep = r_new.json()
    print(f"\nNew deposition ID: {new_dep['id']}")
    print(f"State: {new_dep.get('state')}")
    print(f"Submitted: {new_dep.get('submitted')}")
    print(f"Concept DOI: {new_dep.get('conceptrecid')}")
    print(f"\nNew links:")
    for k, v in new_dep.get("links", {}).items():
        print(f"  {k}: {v}")
    print(f"\nFiles in new version: {len(new_dep.get('files', []))}")

    # Save new deposition ID for the upload script
    state_path = os.path.join(
        os.path.dirname(__file__), "..", "data_release", "uby-time-dataset-v0.1.0", ".zenodo_upload_state.json"
    )
    state_path = os.path.abspath(state_path)
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {}

    state["deposition_id"] = new_dep["id"]
    state["links"] = new_dep.get("links", {})
    state["new_version_of"] = deposition_id
    state["created_at_unix"] = new_dep.get("created")
    state["uploaded_files"] = {}  # Reset upload state for new version

    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    print(f"\nUpdated local state file: {state_path}")
    print(f"New deposition ID saved: {new_dep['id']}")
else:
    print(r_new.text[:2000])
