# Code Availability

The full processing workflow is intended to be archived through GitHub and
linked to Zenodo.

Recommended GitHub repository contents:

- `src/uby_time/` — UBY Time Python package.
- `examples/` — complete data processing scripts.
- `tests/` — regression and integration tests.
- `schemas/` — JSON Schemas.
- `specs/` and `docs/` — specification and user documentation.
- `pyproject.toml` — reproducible Python package metadata.

Recommended release steps:

1. Commit all source code, scripts, schemas, and documentation.
2. Tag a release, for example `v0.1.0`.
3. Enable GitHub-Zenodo integration.
4. Archive the GitHub release on Zenodo.
5. Record the code DOI in the dataset Zenodo record.

The code license is BSD 3-Clause.
