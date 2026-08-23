"""Validate local documentation links and documented package boundaries."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = (ROOT / "README.md", ROOT / "doc" / "document.md")
PACKAGE_PATHS = (
    "MoosasPy/transformation/",
    "MoosasPy/transformation/alignment/",
    "MoosasPy/transformation/geometry/",
    "MoosasPy/transformation/io/",
    "MoosasPy/simulation/airflow/",
    "MoosasPy/simulation/coupling/",
    "MoosasPy/simulation/energy/",
    "MoosasPy/simulation/radiation/",
    "MoosasPy/simulation/weather/",
    "MoosasPy/utils/",
    "MoosasPy/data/",
    "MoosasPy/db/",
    "MoosasPy/libs/",
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]*]\(([^)]+)\)")


def local_link_errors(document: Path) -> list[str]:
    errors = []
    for target in MARKDOWN_LINK.findall(document.read_text(encoding="utf-8")):
        target = target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("mailto:"):
            continue
        if not (document.parent / target).exists():
            errors.append(f"{document.relative_to(ROOT)}: missing linked path {target}")
    return errors


def main() -> int:
    errors = []
    for document in DOCUMENTS:
        if not document.exists():
            errors.append(f"Missing documentation file: {document.relative_to(ROOT)}")
            continue
        errors.extend(local_link_errors(document))

    package_document = ROOT / "doc" / "document.md"
    if package_document.exists():
        content = package_document.read_text(encoding="utf-8")
        for package_path in PACKAGE_PATHS:
            if package_path not in content:
                errors.append(
                    f"{package_document.relative_to(ROOT)}: missing documented package path {package_path}"
                )

    if errors:
        print("Documentation validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1

    print("Documentation validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
