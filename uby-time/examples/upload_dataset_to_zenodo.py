#!/usr/bin/env python3
"""
Upload the UBY Time Dataset v0.1.0 to Zenodo as a Dataset deposition.

The script reads:
- data_release/uby-time-dataset-v0.1.0/zenodo_metadata.json
- data_release/uby-time-dataset-v0.1.0/dataset_manifest.json

It uploads:
- every processed data file listed in dataset_manifest.json
- every release metadata/documentation file in data_release/uby-time-dataset-v0.1.0

Token handling:
- Preferred: set ZENODO_TOKEN or ZENODO_ACCESS_TOKEN in the environment.
- Fallback: read the current Windows clipboard if it looks like a Zenodo token.

The token is not written to project files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests


ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "data_release" / "uby-time-dataset-v0.1.0"
MANIFEST_PATH = RELEASE_DIR / "dataset_manifest.json"
METADATA_PATH = RELEASE_DIR / "zenodo_metadata.json"
STATE_PATH = RELEASE_DIR / ".zenodo_upload_state.json"

ZENODO_API = "https://zenodo.org/api"
REQUEST_TIMEOUT = 180
CHUNK_SIZE = 1024 * 1024


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_clipboard() -> str:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def get_token() -> str:
    token = os.environ.get("ZENODO_TOKEN") or os.environ.get("ZENODO_ACCESS_TOKEN")
    if token:
        return token.strip()

    clipboard = read_clipboard()
    # Zenodo tokens are normally long alphanumeric strings.  This avoids using
    # accidental copied URLs or prose.
    if len(clipboard) >= 40 and clipboard.replace("_", "").replace("-", "").isalnum():
        return clipboard.strip()

    raise SystemExit(
        "Missing Zenodo token. Set ZENODO_TOKEN/ZENODO_ACCESS_TOKEN, "
        "or copy the Zenodo token to the clipboard and rerun."
    )


def request_json(method: str, url: str, token: str, **kwargs: Any) -> dict[str, Any]:
    params = dict(kwargs.pop("params", {}) or {})
    params["access_token"] = token
    response = requests.request(method, url, params=params, timeout=REQUEST_TIMEOUT, **kwargs)
    if not response.ok:
        raise RuntimeError(
            f"{method} {url} failed with HTTP {response.status_code}:\n{response.text[:3000]}"
        )
    if response.text.strip():
        return response.json()
    return {}


def normalize_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "title",
        "upload_type",
        "description",
        "creators",
        "version",
        "license",
        "access_right",
        "keywords",
        "related_identifiers",
        "notes",
        "communities",
        "references",
    }
    metadata = {
        key: value
        for key, value in raw.items()
        if key in allowed and value not in (None, "", [], {})
    }

    # Zenodo rejects empty ORCID strings.
    creators = []
    for creator in metadata.get("creators", []):
        clean = {key: value for key, value in creator.items() if value not in (None, "")}
        creators.append(clean)
    metadata["creators"] = creators

    metadata.setdefault("upload_type", "dataset")
    metadata.setdefault("access_right", "open")
    metadata.setdefault("license", "cc-by-4.0")
    return metadata


def load_state() -> dict[str, Any]:
    if STATE_PATH.exists():
        return load_json(STATE_PATH)
    return {}


def create_or_resume_deposition(token: str, state: dict[str, Any]) -> dict[str, Any]:
    deposition_id = state.get("deposition_id")
    if deposition_id:
        deposition = request_json("GET", f"{ZENODO_API}/deposit/depositions/{deposition_id}", token)
        print(f"Resuming existing Zenodo draft deposition: {deposition_id}")
        return deposition

    deposition = request_json("POST", f"{ZENODO_API}/deposit/depositions", token, json={})
    state["deposition_id"] = deposition["id"]
    state["created_at_unix"] = time.time()
    state["links"] = deposition.get("links", {})
    save_json(STATE_PATH, state)
    print(f"Created Zenodo draft deposition: {deposition['id']}")
    return deposition


def update_metadata(token: str, deposition: dict[str, Any]) -> dict[str, Any]:
    raw_metadata = load_json(METADATA_PATH)
    metadata = normalize_metadata(raw_metadata)
    updated = request_json(
        "PUT",
        f"{ZENODO_API}/deposit/depositions/{deposition['id']}",
        token,
        json={"metadata": metadata},
    )
    print("Updated Zenodo deposition metadata.")
    return updated


def iter_upload_files() -> list[tuple[str, Path]]:
    manifest = load_json(MANIFEST_PATH)
    files: list[tuple[str, Path]] = []

    for entry in manifest["files"]:
        relative_path = entry["path"]
        path = ROOT / relative_path
        if not path.is_file():
            raise FileNotFoundError(path)
        upload_name = relative_path.replace("/", "__").replace("\\", "__")
        files.append((upload_name, path))

    for path in sorted(RELEASE_DIR.iterdir()):
        if not path.is_file():
            continue
        if path.name == STATE_PATH.name:
            continue
        upload_name = f"release_metadata__{path.name}"
        files.append((upload_name, path))

    # Deduplicate while preserving order.
    seen: set[str] = set()
    unique: list[tuple[str, Path]] = []
    for upload_name, path in files:
        if upload_name in seen:
            continue
        seen.add(upload_name)
        unique.append((upload_name, path))
    return unique


def existing_files(token: str, deposition_id: int) -> dict[str, dict[str, Any]]:
    deposition = request_json("GET", f"{ZENODO_API}/deposit/depositions/{deposition_id}", token)
    output: dict[str, dict[str, Any]] = {}
    for item in deposition.get("files", []):
        filename = item.get("filename")
        if filename:
            output[filename] = item
    return output


def upload_file(token: str, bucket_url: str, upload_name: str, path: Path) -> None:
    url = f"{bucket_url}/{quote(upload_name, safe='')}"
    size = path.stat().st_size
    print(f"Uploading {upload_name} ({size:,} bytes)")

    last_error: Exception | None = None
    for attempt in range(1, 6):
        try:
            with path.open("rb") as file:
                response = requests.put(
                    url,
                    params={"access_token": token},
                    data=file,
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=(30, 3600),
                )

            if response.ok:
                return

            message = (
                f"Upload failed for {upload_name} with HTTP {response.status_code}:\n"
                f"{response.text[:3000]}"
            )
            last_error = RuntimeError(message)

            # Retry transient server/network failures.  For client-side validation
            # errors, fail immediately so the user can inspect the Zenodo message.
            if response.status_code < 500 and response.status_code not in {408, 409, 429}:
                raise last_error

        except requests.exceptions.RequestException as exc:
            last_error = exc

        if attempt < 5:
            sleep_seconds = min(60, 5 * attempt)
            print(
                f"Transient upload error for {upload_name}; "
                f"retrying in {sleep_seconds}s ({attempt}/5): {last_error}"
            )
            time.sleep(sleep_seconds)

    raise RuntimeError(f"Upload failed for {upload_name} after retries: {last_error}")


def cleanup_obsolete_files(
    token: str, deposition: dict[str, Any], state: dict[str, Any]
) -> None:
    """Delete files already uploaded to the deposition that are no longer in the manifest/release metadata."""
    deposition_id = deposition["id"]
    desired_names = {name for name, _ in iter_upload_files()}
    current = existing_files(token, deposition_id)
    uploaded_state = state.setdefault("uploaded_files", {})

    obsolete = [name for name in current if name not in desired_names]
    if not obsolete:
        print("No obsolete files to delete on Zenodo.")
        return

    print(f"Obsolete files to delete ({len(obsolete)}):")
    for name in obsolete:
        print(f"  - {name}")

    for name in obsolete:
        file_id = current[name].get("id")
        if not file_id:
            print(f"  Skipping {name}: no file id available.")
            continue
        url = f"{ZENODO_API}/deposit/depositions/{deposition_id}/files/{file_id}"
        response = requests.delete(url, params={"access_token": token}, timeout=REQUEST_TIMEOUT)
        if response.ok:
            print(f"  Deleted: {name}")
            uploaded_state.pop(name, None)
            save_json(STATE_PATH, state)
        else:
            print(
                f"  Failed to delete {name}: HTTP {response.status_code}: {response.text[:500]}"
            )


def delete_remote_file(
    token: str, deposition_id: int, upload_name: str, file_entry: dict[str, Any]
) -> bool:
    file_id = file_entry.get("id")
    if not file_id:
        return False
    url = f"{ZENODO_API}/deposit/depositions/{deposition_id}/files/{file_id}"
    response = requests.delete(url, params={"access_token": token}, timeout=REQUEST_TIMEOUT)
    return response.ok


def refresh_small_files(
    token: str, deposition: dict[str, Any], state: dict[str, Any], size_limit: int = 2 * 1024 * 1024
) -> None:
    """Delete remote files smaller than size_limit so they are re-uploaded with fresh content.

    Large data files (sqlite, big CSVs) are left untouched if their size is unchanged;
    they are not regenerated by the release-package build step.
    """
    deposition_id = deposition["id"]
    current = existing_files(token, deposition_id)
    uploaded_state = state.setdefault("uploaded_files", {})

    to_refresh = [
        name
        for name, entry in current.items()
        if int(entry.get("filesize", 0)) < size_limit
    ]
    if not to_refresh:
        print("No small files to refresh on Zenodo.")
        return

    print(f"Refreshing small files ({len(to_refresh)}, each < {size_limit} bytes):")
    for name in to_refresh:
        if delete_remote_file(token, deposition_id, name, current[name]):
            print(f"  Deleted for refresh: {name}")
            uploaded_state.pop(name, None)
        else:
            print(f"  Failed to delete for refresh: {name}")
    save_json(STATE_PATH, state)


def upload_all_files(token: str, deposition: dict[str, Any], state: dict[str, Any]) -> None:
    deposition_id = deposition["id"]
    bucket_url = deposition["links"]["bucket"]
    files = iter_upload_files()
    total_size = sum(path.stat().st_size for _, path in files)

    print(f"Files to upload: {len(files)}")
    print(f"Total upload size: {total_size:,} bytes ({total_size / (1024 ** 3):.2f} GiB)")

    current = existing_files(token, deposition_id)
    uploaded_state = state.setdefault("uploaded_files", {})

    for index, (upload_name, path) in enumerate(files, start=1):
        local_size = path.stat().st_size
        remote = current.get(upload_name)
        if remote and int(remote.get("filesize", -1)) == local_size:
            print(f"[{index}/{len(files)}] Skipping existing file: {upload_name}")
            uploaded_state[upload_name] = {
                "path": str(path.relative_to(ROOT).as_posix()),
                "size_bytes": local_size,
                "status": "already_present",
            }
            save_json(STATE_PATH, state)
            continue

        print(f"[{index}/{len(files)}]", end=" ")
        upload_file(token, bucket_url, upload_name, path)
        uploaded_state[upload_name] = {
            "path": str(path.relative_to(ROOT).as_posix()),
            "size_bytes": local_size,
            "status": "uploaded",
            "uploaded_at_unix": time.time(),
        }
        save_json(STATE_PATH, state)

    print("All files uploaded to the Zenodo draft deposition.")


def publish_deposition(token: str, deposition_id: int) -> dict[str, Any]:
    published = request_json(
        "POST",
        f"{ZENODO_API}/deposit/depositions/{deposition_id}/actions/publish",
        token,
    )
    print("Published Zenodo deposition.")
    return published


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publish the Zenodo deposition after upload. Without this flag, a draft is created/updated only.",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete files already uploaded to the deposition that are no longer in the manifest/release metadata.",
    )
    parser.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Delete small remote files (< 2 MiB) so they are re-uploaded with fresh content.",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}")
    if not METADATA_PATH.exists():
        raise SystemExit(f"Missing metadata: {METADATA_PATH}")

    token = get_token()
    state = load_state()

    deposition = create_or_resume_deposition(token, state)
    deposition = update_metadata(token, deposition)
    state["deposition_id"] = deposition["id"]
    state["links"] = deposition.get("links", {})
    save_json(STATE_PATH, state)

    if args.cleanup:
        cleanup_obsolete_files(token, deposition, state)

    if args.refresh_metadata:
        refresh_small_files(token, deposition, state)

    upload_all_files(token, deposition, state)

    final = request_json("GET", f"{ZENODO_API}/deposit/depositions/{deposition['id']}", token)
    if args.publish:
        final = publish_deposition(token, deposition["id"])

    state["latest_response_summary"] = {
        "id": final.get("id"),
        "conceptrecid": final.get("conceptrecid"),
        "doi": final.get("doi"),
        "submitted": final.get("submitted"),
        "state": final.get("state"),
        "links": final.get("links", {}),
    }
    save_json(STATE_PATH, state)

    print("\nZenodo deposition summary")
    print(json.dumps(state["latest_response_summary"], indent=2, ensure_ascii=False))
    print(f"\nLocal upload state: {STATE_PATH}")
    if not args.publish:
        print("\nThe data are uploaded to a Zenodo draft. Review the draft in Zenodo and publish it when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
