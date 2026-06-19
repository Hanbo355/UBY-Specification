from __future__ import annotations

import hashlib
import json
from pathlib import Path

from examples import build_zenodo_release_package as release


def test_zenodo_release_package_manifest_and_metadata() -> None:
    manifest = release.build_release_package()

    release_dir = release.RELEASE_DIR
    assert release_dir.exists()

    required_files = [
        "README_DATASET.md",
        "DATA_DICTIONARY.md",
        "DATA_AVAILABILITY.md",
        "CODE_AVAILABILITY.md",
        "LICENSE_DATA_CC_BY_4.0.md",
        "LICENSES_AND_ATTRIBUTION.md",
        "QUALITY_CONTROL.md",
        "quality_control_report.json",
        "dataset_manifest.json",
        "checksums_sha256.txt",
        "zenodo_metadata.json",
        "GITHUB_ZENODO_RELEASE_GUIDE.md",
    ]
    for name in required_files:
        path = release_dir / name
        assert path.exists()
        assert path.stat().st_size > 0

    assert (release.ROOT / ".zenodo.json").exists()

    manifest_path = release_dir / "dataset_manifest.json"
    manifest_from_disk = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_from_disk["release_id"] == release.RELEASE_ID
    assert manifest_from_disk["release_version"] == release.RELEASE_VERSION
    assert manifest_from_disk["file_count"] == manifest["file_count"]
    assert manifest_from_disk["file_count"] > 0
    assert manifest_from_disk["total_size_bytes"] > 0

    files = manifest_from_disk["files"]
    assert files
    assert all(item["sha256"] for item in files)
    assert all(item["size_bytes"] > 0 for item in files)

    roles = {item["release_role"] for item in files}
    assert "tabular_dataset" in roles
    assert "sqlite_database" in roles
    assert "metadata_or_report" in roles or "json_metadata" in roles

    qc = json.loads((release_dir / "quality_control_report.json").read_text(encoding="utf-8"))
    assert qc["status"] == "pass"
    assert qc["checks"]["all_files_nonempty"] is True
    assert qc["checks"]["sha256_generated_for_all_files"] is True
    assert qc["checks"]["all_csv_have_row_counts"] is True
    assert qc["checks"]["all_sqlite_have_table_counts"] is True

    zenodo = json.loads((release_dir / "zenodo_metadata.json").read_text(encoding="utf-8"))
    assert zenodo["upload_type"] == "dataset"
    assert zenodo["license"] == "cc-by-4.0"
    assert zenodo["access_right"] == "open"
    assert zenodo["version"] == release.RELEASE_VERSION

    github_zenodo = json.loads((release.ROOT / ".zenodo.json").read_text(encoding="utf-8"))
    assert github_zenodo["upload_type"] == "software"
    assert github_zenodo["license"] == "bsd-3-clause"


def test_zenodo_release_package_checksums_match_first_manifest_file() -> None:
    release.build_release_package()

    manifest_path = release.RELEASE_DIR / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    first_file = manifest["files"][0]

    data_path = release.ROOT / Path(first_file["path"])
    digest = hashlib.sha256()
    with data_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    assert digest.hexdigest() == first_file["sha256"]

    checksums_text = (release.RELEASE_DIR / "checksums_sha256.txt").read_text(encoding="utf-8")
    assert f"{first_file['sha256']}  {first_file['path']}" in checksums_text
