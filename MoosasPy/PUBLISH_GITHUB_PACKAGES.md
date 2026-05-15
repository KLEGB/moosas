# MoosasPy Publishing Guide (GitHub-hosted)

This repository is now ready for Python packaging with `pyproject.toml`.

Runtime requirement: Python `>=3.10`.

## Important: GitHub Packages and pip

As of May 15, 2026, GitHub Packages does not provide a first-class PyPI
registry for `pip` package publishing/installation.

That means:

- you can build standard Python distributions (`sdist`, `wheel`)
- but you should publish them via GitHub Releases (or PyPI/TestPyPI)
  for `pip` consumption

## 1. Build distributions locally

From repository root:

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

## 2. Publish to GitHub Releases

Create a tag and push:

```bash
git tag moosaspy-v1.0.0
git push origin moosaspy-v1.0.0
```

The workflow `.github/workflows/moosaspy-release.yml` will:

- build `dist/*.whl` and `dist/*.tar.gz`
- create a GitHub Release
- upload built files as release assets

## 3. Install with pip

Public repo:

```bash
pip install "https://github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.0.0/moosaspy-1.0.0-py3-none-any.whl"
```

Private repo:

```bash
pip install "https://<USERNAME>:<TOKEN>@github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.0.0/moosaspy-1.0.0-py3-none-any.whl"
```

Use a PAT with repository read permission.

## Optional: publish to PyPI/TestPyPI

If you want native `pip install moosaspy` without URL installation, publish the
same `dist/*` artifacts to PyPI/TestPyPI with `twine`.
