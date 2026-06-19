# GitHub and Zenodo Release Guide

This guide prepares the UBY project for long-term archival, DOI assignment, and
global reuse.

## 1. Repository preparation

1. Ensure the repository contains:
   - `src/uby_time/`
   - `examples/`
   - `tests/`
   - `schemas/`
   - `docs/`
   - `specs/`
   - `README.md`
   - `LICENSE`
   - `.zenodo.json`
   - `data_release/uby-time-dataset-v0.1.0/`

2. Do not commit very large raw API batch files unless Git LFS is explicitly
   configured.  For GitHub, commit the code, schemas, documentation, and release
   metadata.  For Zenodo dataset deposition, upload the large processed data
   files directly.

## 2. Code archival through GitHub-Zenodo

1. Create or update the public GitHub repository.
2. Push all source code and release metadata.
3. Enable the repository in Zenodo GitHub integration.
4. Create a GitHub release tagged `v0.1.0`.
5. Zenodo will archive the GitHub release and mint a software DOI.
6. Add the software DOI to `CODE_AVAILABILITY.md`.

## 3. Dataset archival through Zenodo

Create a separate Zenodo upload with upload type `Dataset`.

Recommended files to upload:

- All files listed in `dataset_manifest.json`.
- `README_DATASET.md`
- `DATA_DICTIONARY.md`
- `DATA_AVAILABILITY.md`
- `CODE_AVAILABILITY.md`
- `LICENSE_DATA_CC_BY_4.0.md`
- `LICENSES_AND_ATTRIBUTION.md`
- `QUALITY_CONTROL.md`
- `quality_control_report.json`
- `dataset_manifest.json`
- `checksums_sha256.txt`
- `zenodo_metadata.json`

Use metadata from `zenodo_metadata.json`.

## 4. License

- Dataset: CC-BY-4.0.
- Code: BSD 3-Clause.

## 5. After DOI assignment

Update:

- `README_DATASET.md`
- `DATA_AVAILABILITY.md`
- project `README.md`
- manuscript or preprint citation
- GitHub release notes

with the final Zenodo dataset DOI and GitHub software DOI.
