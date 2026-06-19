# GitHub Repository Checklist for UBY Time v0.1.0

This checklist prepares the UBY Time repository for public GitHub release and
Zenodo software archival.

## Git availability

The local Windows environment used during preparation did not have `git`
available on `PATH`:

```text
git: The term 'git' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

Therefore the repository was cleaned and prepared at the file level, but the
actual `git add`, `git commit`, `git tag`, and `git push` commands must be run
after installing Git or from another environment where Git is available.

## Files and directories that should be committed

Commit the following source, documentation, schema, test, and release-metadata
files/directories:

```text
.gitignore
.zenodo.json
CHANGELOG.md
CONTRIBUTING.md
GITHUB_REPOSITORY_CHECKLIST.md
LICENSE
README.md
TESTPYPI_RELEASE_GUIDE.md
mkdocs.yml
pyproject.toml
docs/
examples/
schemas/
specs/
src/
tests/
data_release/
```

Important recently added release files include:

```text
examples/build_zenodo_release_package.py
tests/test_zenodo_release_package.py
data_release/uby-time-dataset-v0.1.0/README_DATASET.md
data_release/uby-time-dataset-v0.1.0/DATA_DICTIONARY.md
data_release/uby-time-dataset-v0.1.0/DATA_AVAILABILITY.md
data_release/uby-time-dataset-v0.1.0/CODE_AVAILABILITY.md
data_release/uby-time-dataset-v0.1.0/LICENSE_DATA_CC_BY_4.0.md
data_release/uby-time-dataset-v0.1.0/LICENSES_AND_ATTRIBUTION.md
data_release/uby-time-dataset-v0.1.0/QUALITY_CONTROL.md
data_release/uby-time-dataset-v0.1.0/quality_control_report.json
data_release/uby-time-dataset-v0.1.0/dataset_manifest.json
data_release/uby-time-dataset-v0.1.0/checksums_sha256.txt
data_release/uby-time-dataset-v0.1.0/zenodo_metadata.json
data_release/uby-time-dataset-v0.1.0/GITHUB_ZENODO_RELEASE_GUIDE.md
```

## Files and directories that should not be committed to normal Git

These are excluded by `.gitignore` and should be archived on Zenodo instead of
committed directly to GitHub:

```text
data/raw/
data/processed/
*.sqlite-wal
*.sqlite-shm
*.sqlite-journal
*_output.txt
*_run_output.txt
*_pytest_output.txt
__pycache__/
.pytest_cache/
dist/
build/
*.egg-info/
```

Rationale:

- `data/raw/` contains downloaded API batches and may be large.
- `data/processed/` contains the Zenodo dataset payload, currently about 5.85 GB.
- The large dataset files should be uploaded to Zenodo as a dataset record.
- GitHub should contain the reproducible workflow, release metadata, tests,
  schemas, and documentation.
- If large data must be hosted on GitHub, use Git LFS explicitly.

## Recommended Git commands after Git is installed

From the `uby-time/` directory:

```bash
git init
git add .gitignore .zenodo.json CHANGELOG.md CONTRIBUTING.md GITHUB_REPOSITORY_CHECKLIST.md LICENSE README.md TESTPYPI_RELEASE_GUIDE.md mkdocs.yml pyproject.toml docs examples schemas specs src tests data_release
git status
git commit -m "Prepare UBY Time v0.1.0 for GitHub and Zenodo release"
git tag v0.1.0
```

Then create the GitHub remote and push:

```bash
git remote add origin https://github.com/<OWNER>/<REPO>.git
git branch -M main
git push -u origin main
git push origin v0.1.0
```

## Zenodo integration

1. Enable GitHub integration in Zenodo.
2. Activate the GitHub repository.
3. Create a GitHub release from tag `v0.1.0`.
4. Zenodo will archive the code and mint a software DOI using `.zenodo.json`.
5. Create a separate Zenodo Dataset upload for the files listed in
   `data_release/uby-time-dataset-v0.1.0/dataset_manifest.json`.
6. Use `data_release/uby-time-dataset-v0.1.0/zenodo_metadata.json` as the dataset
   metadata source.
7. Select license: `Creative Commons Attribution 4.0 International`.
8. After publication, update:
   - `README.md`
   - `data_release/uby-time-dataset-v0.1.0/README_DATASET.md`
   - `data_release/uby-time-dataset-v0.1.0/DATA_AVAILABILITY.md`
   - any manuscript or preprint
   with the final dataset DOI and software DOI.

## Verification commands

Run before release:

```bash
python examples/build_zenodo_release_package.py
python -m pytest tests/test_zenodo_release_package.py -q
python -m pytest -q
```

The release-package test was verified locally:

```text
2 passed in 170.40s
```

## Current release-package summary

From `quality_control_report.json`:

```text
release_id: uby-time-dataset-v0.1.0
file_manifest_entries: 56
csv_file_count: 23
sqlite_file_count: 16
json_file_count: 17
total_size_bytes: 5,850,959,685
total_csv_rows: 3,143,604
total_sqlite_table_rows: 4,721,299
status: pass
```
