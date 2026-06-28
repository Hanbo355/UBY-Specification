"""Inspect deposition state in detail to understand bucket lock."""
import json
import os
import sys

import requests

token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    sys.exit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"
deposition_id = 20763218

# Fetch deposition
r = requests.get(
    f"{api}/deposit/depositions/{deposition_id}",
    params={"access_token": token},
    timeout=60,
)
print(f"GET status: {r.status_code}")
if not r.ok:
    print(r.text[:2000])
    sys.exit(1)

d = r.json()
print("\n--- Deposition summary ---")
print(f"ID: {d['id']}")
print(f"State: {d.get('state')}")
print(f"Submitted: {d.get('submitted')}")
print(f"Title: {d.get('title','')[:80]}")
print(f"Owner: {d.get('owner')}")
print(f"Record_id: {d.get('record_id')}")
print(f"Conceptrecid: {d.get('conceptrecid')}")

print("\n--- Links ---")
links = d.get("links", {})
for k, v in links.items():
    print(f"  {k}: {v}")

print(f"\nFiles: {len(d.get('files', []))}")
print(f"Files URL: {links.get('files')}")

# Try edit action to unlock the draft
print("\n--- Trying 'edit' action to unlock draft ---")
edit_url = links.get("edit")
if edit_url:
    r2 = requests.post(edit_url, params={"access_token": token}, timeout=60)
    print(f"Edit action status: {r2.status_code}")
    if r2.ok:
        d2 = r2.json()
        print(f"New state: {d2.get('state')}")
        print(f"Submitted: {d2.get('submitted')}")
        print("\n--- Updated links ---")
        for k, v in d2.get("links", {}).items():
            print(f"  {k}: {v}")
    else:
        print(r2.text[:1000])
else:
    print("No edit link found.")
