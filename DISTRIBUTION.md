# Distribution Guide

This document explains how to distribute `mnmd-anki-sync` to users.

## Prerequisites

1. **GitHub Account**: For hosting the source code
2. **PyPI Account**: For publishing to the Python Package Index
   - Create account at https://pypi.org/account/register/
   - Set up API token at https://pypi.org/manage/account/token/

## Quick Distribution Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Run all tests: `uv run pytest`
- [ ] Update CHANGELOG
- [ ] Sync documentation files:
  - `cp syntax-notes.md src/mnmd_anki_sync/`
  - `cp agents-syntax.md src/mnmd_anki_sync/`
- [ ] Commit all changes
- [ ] Build package: `uv build`
- [ ] Upload to PyPI: `uv publish` or `twine upload dist/*`
- [ ] Create GitHub release with tag
- [ ] Verify installation: `pipx install mnmd-anki-sync`
- [ ] Test syntax command: `mnmd syntax`

## Step-by-Step: Publishing to PyPI

### 1. Prepare the Release

Update version in `pyproject.toml`:
```toml
[project]
version = "0.2.0"  # Increment version
```

Run tests to ensure everything works:
```bash
uv run pytest
```

### 2. Build the Package

```bash
# Clean old builds
rm -rf dist/

# Build wheel and source distribution
uv build
```

This creates files in `dist/`:
- `mnmd_anki_sync-0.2.0-py3-none-any.whl` (wheel)
- `mnmd_anki_sync-0.2.0.tar.gz` (source distribution)

### 3. Test with TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI first
uv publish --index-url https://test.pypi.org/legacy/

# Test installation from TestPyPI
pipx install --index-url https://test.pypi.org/simple/ mnmd-anki-sync
mnmd --help

# Uninstall test version
pipx uninstall mnmd-anki-sync
```

### 4. Publish to PyPI

```bash
# Publish to real PyPI
uv publish

# Or use twine if you prefer
pip install twine
twine upload dist/*
```

You'll need to enter your PyPI API token when prompted.

### 5. Verify Installation

```bash
# Install from PyPI
pipx install mnmd-anki-sync

# Test it works
mnmd --help
mnmd version
```

## Step-by-Step: GitHub Release

### 1. Commit and Tag

```bash
# Commit all changes
git add .
git commit -m "Release v0.2.0"

# Create annotated tag
git tag -a v0.2.0 -m "Release version 0.2.0"

# Push commits and tags
git push origin main
git push origin v0.2.0
```

### 2. Create GitHub Release

1. Go to your repository on GitHub
2. Click "Releases" → "Create a new release"
3. Select the tag you just created (v0.2.0)
4. Title: "v0.2.0"
5. Description: Add release notes (features, bug fixes, breaking changes)
6. Attach the built files from `dist/` (optional)
7. Click "Publish release"

### 3. Installation from GitHub

Users can now install directly from GitHub:
```bash
pip install git+https://github.com/yourusername/mnmd-anki-sync.git
```

Or from a specific version:
```bash
pip install git+https://github.com/yourusername/mnmd-anki-sync.git@v0.2.0
```

## Versioning Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0 → 2.0.0): Breaking changes
- **Minor** (0.1.0 → 0.2.0): New features, backwards compatible
- **Patch** (0.1.0 → 0.1.1): Bug fixes, backwards compatible

## Automation with GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install uv
        run: pip install uv

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish --token $PYPI_TOKEN
```

Add your PyPI token to GitHub Secrets:
1. Go to repository Settings → Secrets → Actions
2. Add secret named `PYPI_TOKEN`
3. Paste your PyPI API token

Now creating a GitHub release automatically publishes to PyPI!

## Distribution Checklist for v0.1.0 (First Release)

Since this is the first release, here's what you should do:

1. **Review the code**:
   - [x] All 103 tests passing
   - [x] Documentation up to date
   - [ ] Add LICENSE file if missing
   - [ ] Add CHANGELOG.md

2. **Prepare PyPI account**:
   - [ ] Create PyPI account
   - [ ] Create API token
   - [ ] Store token securely

3. **Publish**:
   - [ ] Update README with your GitHub username
   - [ ] Build: `uv build`
   - [ ] Publish: `uv publish`
   - [ ] Create GitHub repo
   - [ ] Push code: `git push origin main`
   - [ ] Create release v0.1.0 on GitHub

4. **Share with users**:
   - [ ] Share installation instructions: `pipx install mnmd-anki-sync`
   - [ ] Link to documentation

## Troubleshooting

### "Package already exists" error
- You're trying to upload a version that's already on PyPI
- Increment the version number in `pyproject.toml`

### Authentication issues
- Make sure you're using an API token, not your password
- Token format: `pypi-...` (starts with "pypi-")

### Build fails
- Run `uv run pytest` to check tests
- Check `pyproject.toml` for syntax errors
- Make sure all files are committed

## Quick Commands Reference

```bash
# Build
uv build

# Publish to PyPI
uv publish

# Install locally for testing
uv pip install -e .

# Create tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0

# Clean build artifacts
rm -rf dist/ build/ *.egg-info
```
