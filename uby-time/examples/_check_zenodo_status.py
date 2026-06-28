"""Check Zenodo deposition status (token read from environment variable)."""
import os
import sys

import requests

token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
if not token:
    sys.exit("No ZENODO_TOKEN in environment")

api = "https://zenodo.org/api"

# Search for UBY depositions
r = requests.get(
    f"{api}/deposit/depositions",
    params={"access_token": token, "q": "UBY"},
    timeout=60,
)
print(f"Status: {r.status_code}")
if not r.ok:
    print(r.text[:1000])
    sys.exit(1)

data = r.json()
print(f"Total depositions found: {len(data)}")
for d in data[:10]:
    title = d.get("title", "")[:70]
    print(f"  - ID: {d['id']}  State: {d.get('state')}  Submitted: {d.get('submitted')}")
    print(f"    Title: {title}")

# Specifically fetch deposition 20763218
print("\n--- Fetching deposition 20763218 ---")
r2 = requests.get(
    f"{api}/deposit/depositions/20763218",
    params={"access_token": token},
    timeout=60,
)
print(f"Status: {r2.status_code}")
if r2.ok:
    d = r2.json()
    print(f"ID: {d['id']}")
    print(f"State: {d.get('state')}")
    print(f"Submitted: {d.get('submitted')}")
    print(f"Title: {d.get('title','')[:80]}")
    files = d.get("files", [])
    print(f"Files: {len(files)}")
    if files:
        total_size = sum(int(f.get("filesize", 0)) for f in files)
        print(f"Total size: {total_size:,} bytes ({total_size / (1024**3):.2f} GiB)")
else:
    print(r2.text[:1000])
