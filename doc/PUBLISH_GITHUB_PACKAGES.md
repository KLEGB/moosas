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

MoosasPy versions are driven by Git tags. The accepted tag format is:

```text
moosaspy-vX.Y.Z
```

This is configured in `pyproject.toml` through `setuptools_scm.tag_regex`.

Use the release helper from the repository root:

```powershell
.\scripts\release_moosaspy.ps1 1.2.0
```

or:

```powershell
.\scripts\release_moosaspy.ps1 moosaspy-v1.2.0
```

The script will:

- validate and normalize the version tag
- refuse to tag a dirty working tree unless `-AllowDirty` is passed
- fetch tags from `origin`
- delete an existing local tag with the same name
- delete an existing remote tag with the same name
- delete an existing GitHub Release with the same tag when `GH_TOKEN` or
  `GITHUB_TOKEN` is available
- create a new annotated tag at the current `HEAD`
- push the tag to GitHub

The workflow `.github/workflows/moosaspy-release.yml` will:

- build `dist/*.whl` and `dist/*.tar.gz`
- create a GitHub Release
- upload built files as release assets

### Re-publish the same version

To overwrite an existing version, run the same command again after moving `HEAD`
to the commit that should be released:

```powershell
$env:GH_TOKEN = "<github-token-with-contents-write>"
.\scripts\release_moosaspy.ps1 1.2.0
```

The token is only needed for deleting the existing GitHub Release before the
workflow uploads new assets. Without it, the script can still replace the Git
tag, but an old Release with assets of the same names may cause the GitHub
Actions upload step to fail.

For a preview without changing tags or releases:

```powershell
.\scripts\release_moosaspy.ps1 1.2.0 -DryRun
```

## 3. Install with pip

Public repo:

```bash
pip install "https://github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.1.0/moosaspy-1.1.0-py3-none-any.whl"
```

Private repo:

```bash
pip install "https://<USERNAME>:<TOKEN>@github.com/<OWNER>/<REPO>/releases/download/moosaspy-v1.1.0/moosaspy-1.1.0-py3-none-any.whl"
```

Use a PAT with repository read permission.

## Optional: publish to PyPI/TestPyPI

If you want native `pip install moosaspy` without URL installation, publish the
same `dist/*` artifacts to PyPI/TestPyPI with `twine`.
