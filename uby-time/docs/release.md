# Release and TestPyPI

This page documents the release preparation workflow for `uby-time`.

## Pre-release checklist

Before publishing any package artifact:

1. Confirm the package version in `pyproject.toml`.
2. Confirm `UBY_SPEC_VERSION` and `IMPLEMENTATION_VERSION` in `src/uby_time/constants.py`.
3. Run the full test suite.
4. Build the source distribution and wheel.
5. Inspect distribution metadata.
6. Publish to TestPyPI first.
7. Install from TestPyPI in a clean environment.
8. Only then consider publishing to production PyPI.

## Local test and build

From the project root:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q --tb=short
python -m build
python -m twine check dist/*
```

On PowerShell during source-tree development:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q --tb=short
python -m build
python -m twine check dist/*
```

## GitHub Actions CI

The CI workflow is located at:

```text
.github/workflows/ci.yml
```

It runs tests on Python 3.10, 3.11, and 3.12, then builds both package artifacts.

## TestPyPI workflow

The TestPyPI publishing workflow is located at:

```text
.github/workflows/testpypi.yml
```

It is manually triggered with `workflow_dispatch`.

The workflow uses PyPI Trusted Publishing through GitHub OIDC. Configure a trusted publisher on TestPyPI for:

- Project name: `uby-time`
- Owner/repository: your GitHub organization and repository
- Workflow name: `testpypi.yml`
- Environment name: `testpypi`

Then run the `Publish to TestPyPI` workflow from the GitHub Actions UI.

## Manual TestPyPI fallback

If Trusted Publishing is not configured, use an API token locally:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

Do not commit tokens or credentials. Prefer `.pypirc`, environment variables, or interactive prompts.

## Verify TestPyPI installation

Use a clean environment:

```bash
python -m venv .venv-testpypi
. .venv-testpypi/bin/activate
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ uby-time
uby convert jd 2461041.5
python -c "import uby_time; print(uby_time.UBY_SPEC_VERSION)"
```

On Windows PowerShell:

```powershell
python -m venv .venv-testpypi
.\.venv-testpypi\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ uby-time
uby convert jd 2461041.5
python -c "import uby_time; print(uby_time.UBY_SPEC_VERSION)"
```

Expected basic CLI output includes:

```text
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
precision_level=Level 1
```

## Production PyPI

Production PyPI release should only be performed after TestPyPI validation succeeds.

Recommended policy for early versions:

- Publish Working Draft implementations as `0.x.y`.
- Keep API-breaking changes inside minor increments before `1.0.0`.
- Reserve `1.0.0` for a stable specification-aligned reference implementation.
