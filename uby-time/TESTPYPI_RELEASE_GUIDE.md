# TestPyPI Release Guide

This guide provides step-by-step instructions for publishing `uby-time 0.1.0` to TestPyPI using GitHub Actions with Trusted Publishing.

## Prerequisites

1. GitHub repository with the `uby-time` project
2. TestPyPI account
3. Repository admin access to configure GitHub Actions environments

## Step 1: Configure TestPyPI Trusted Publisher

### 1.1 Create TestPyPI Project

1. Go to [test.pypi.org](https://test.pypi.org)
2. Log in to your TestPyPI account
3. Navigate to "Your projects" → "Publishing"
4. Click "Add a new pending publisher"

### 1.2 Configure Trusted Publisher Settings

Fill in the following details:

| Field | Value |
|-------|-------|
| **PyPI project name** | `uby-time` |
| **Owner** | `[your-github-username-or-org]` |
| **Repository name** | `UBY-Specification` |
| **Workflow filename** | `testpypi.yml` |
| **Environment name** | `testpypi` |

Example configuration:
```
Owner: uby-spec
Repository name: UBY-Specification
Workflow filename: testpypi.yml
Environment name: testpypi
```

### 1.3 Save Trusted Publisher

Click "Add" to create the trusted publisher configuration.

## Step 2: Configure GitHub Repository

### 2.1 Create GitHub Repository

1. Create a new GitHub repository named `UBY-Specification`
2. Push the current project contents:

```bash
cd /path/to/UBY-Specification
git init
git add .
git commit -m "Initial commit: UBY Cross-scale Time Labeling Specification WD 0.1.0"
git branch -M main
git remote add origin https://github.com/[username]/UBY-Specification.git
git push -u origin main
```

### 2.2 Create GitHub Environment

1. Go to your GitHub repository
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Name: `testpypi`
5. Click **Configure environment**
6. **Environment protection rules**: (optional, can leave default)
7. **Environment secrets**: (none needed for Trusted Publishing)
8. Click **Save protection rules**

## Step 3: Verify Workflow Configuration

The repository already contains the TestPyPI workflow at:

```
.github/workflows/testpypi.yml
```

Key workflow settings:
- **Trigger**: Manual (`workflow_dispatch`)
- **Environment**: `testpypi`
- **Permissions**: `id-token: write` (for OIDC)
- **Repository URL**: `https://test.pypi.org/legacy/`

## Step 4: Pre-Release Validation

Before triggering the release, verify the package is ready:

### 4.1 Local Quality Checks

```bash
cd uby-time
python -m pytest -q --tb=short
python -m build
python -m twine check dist/*
```

Expected output:
```
42 passed in 0.32s
Successfully built uby_time-0.1.0.tar.gz and uby_time-0.1.0-py3-none-any.whl
Checking dist\uby_time-0.1.0-py3-none-any.whl: PASSED
Checking dist\uby_time-0.1.0.tar.gz: PASSED
```

### 4.2 Specification Lint Check

```bash
uby lint spec "../UBY-TLS-WD-0.1.0.md"
```

Should show only warnings (no errors).

### 4.3 Package Metadata Verification

Verify `pyproject.toml` contains:
- Correct version: `0.1.0`
- Valid classifiers
- Project URLs
- `py.typed` is included in wheel

## Step 5: Execute TestPyPI Release

### 5.1 Trigger GitHub Actions Workflow

1. Go to your GitHub repository
2. Navigate to **Actions** tab
3. Select **Publish to TestPyPI** workflow
4. Click **Run workflow**
5. Select branch: `main`
6. Click **Run workflow**

### 5.2 Monitor Workflow Execution

The workflow will:
1. Check out the repository
2. Set up Python 3.12
3. Install build dependencies
4. Run tests (`pytest -q --tb=short`)
5. Build source distribution and wheel
6. Publish to TestPyPI using Trusted Publishing

Expected workflow duration: ~2-3 minutes

### 5.3 Verify Publication Success

Check the workflow logs for:
```
Successfully uploaded distributions to https://test.pypi.org/
```

## Step 6: Verify TestPyPI Installation

### 6.1 Install from TestPyPI

Create a clean environment and install:

```bash
python -m venv .venv-testpypi-verify
# On Windows:
.venv-testpypi-verify\Scripts\activate
# On Unix:
source .venv-testpypi-verify/bin/activate

pip install --upgrade pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ uby-time
```

### 6.2 Smoke Test Installation

```bash
# Test CLI
uby convert jd 2461041.5

# Test import
python -c "import uby_time; print(uby_time.UBY_SPEC_VERSION)"
```

Expected output:
```
UBY 13787002026.0 [model=LCDM-Planck2018] [spec=0.1.0]
precision_level=Level 1
0.1.0
```

### 6.3 Test Package Features

```python
from uby_time import iso_to_uby, format_full, lint_uby_expressions

# Test conversion
uby = iso_to_uby("2026-01-01T00:00:00Z")
print(format_full(uby))

# Test new lint feature
issues = lint_uby_expressions("Example: UBY 380K [spec=0.1.0]")
print(f"Lint issues: {len(issues)}")
```

## Step 7: Post-Release Verification

### 7.1 Check TestPyPI Project Page

Visit: https://test.pypi.org/project/uby-time/

Verify:
- Version `0.1.0` is listed
- Package description renders correctly
- Download files include both `.tar.gz` and `.whl`
- Project URLs are functional
- Classifiers are displayed

### 7.2 Cleanup Test Environment

```bash
deactivate
rm -rf .venv-testpypi-verify
```

## Troubleshooting

### Common Issues

1. **Trusted Publisher Not Found**
   - Verify repository name matches exactly
   - Check workflow filename is `testpypi.yml`
   - Ensure environment name is `testpypi`

2. **Workflow Permission Denied**
   - Verify `id-token: write` permission in workflow
   - Check GitHub environment is configured
   - Ensure repository has Actions enabled

3. **Package Already Exists**
   - TestPyPI doesn't allow re-uploading same version
   - Increment version in `pyproject.toml` if needed
   - Or delete existing TestPyPI project and recreate

4. **Build Failures**
   - Check test failures in workflow logs
   - Verify all dependencies are available
   - Ensure `pyproject.toml` is valid

### Support Resources

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python Packaging User Guide](https://packaging.python.org/)

## Next Steps

After successful TestPyPI release:

1. **Production PyPI**: Configure similar Trusted Publisher for production PyPI
2. **Version Management**: Plan version increment strategy for future releases
3. **CI/CD**: Consider automating releases on git tags
4. **Documentation**: Update project documentation with installation instructions

---

**Package**: `uby-time 0.1.0`  
**Specification**: UBY Cross-scale Time Labeling Specification Working Draft 0.1.0  
**Release Target**: TestPyPI (test.pypi.org)  
**Release Method**: GitHub Actions + PyPI Trusted Publishing
