# MOOSAS

MOOSAS is a building performance analysis and optimization toolkit for the early design stage.

This repository contains:

- `MoosasPy`: Python package for geometry transformation, model I/O, and building-performance simulation workflows.

## Version

Current Python package release target: `MoosasPy v1.2.2`.

## Quick Start

Install the package and development tools:

```bash
python -m pip install -e ".[dev]"
```

Run a basic import check:

```bash
python -c "import MoosasPy; print(MoosasPy.__version__)"
```

## MoosasPy Packaging and Release

Packaging metadata is managed from repository root via `pyproject.toml`.

Read the [package documentation](doc/document.md) for the current module
layout and public API examples.

Current release workflow:

1. Validate distributions (`python -m build`, `python -m twine check dist/*`).
2. Push tag `moosaspy-v*` (for example `moosaspy-v1.1.0`).
3. GitHub Actions workflow `.github/workflows/moosaspy-release.yml` uploads
   wheel/sdist to GitHub Release assets.

## Documentation

- Transformation and module docs: [doc/document.md](doc/document.md)

## Contact

Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.  
**For colaboration, Please contact:**  
linbr@tsinghua.edu.cn  
**If you have any technical problems, Please reach to:**  
junx026@gmail.com
liyihui23@mails.tsinghua.edu.cn
