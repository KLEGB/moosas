"""Single EnergyPlus version contract for MOOSAS IDF I/O."""

from __future__ import annotations

import re
from pathlib import Path

from eppy.modeleditor import IDF

from ....utils import path


ENERGYPLUS_VERSION = "26.1"

_IDF_VERSION_PATTERN = re.compile(
    r"^\s*Version\s*,\s*([^;,\s]+)\s*;",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)
_IDD_VERSION_PATTERN = re.compile(r"^!IDD_Version\s+([^\s]+)", re.IGNORECASE | re.MULTILINE)


def bundled_idd_path() -> Path:
    return Path(path.dataBaseDir) / "Energy+.idd"


def bundled_template_idf_path() -> Path:
    return Path(path.dataBaseDir) / "in.idf"


def _without_comments(contents: str) -> str:
    return "\n".join(line.split("!", 1)[0] for line in contents.splitlines())


def idf_version(idf_path: str | Path) -> str:
    source = Path(idf_path)
    match = _IDF_VERSION_PATTERN.search(_without_comments(source.read_text(encoding="utf-8-sig")))
    if match is None:
        raise ValueError(f"IDF has no Version object: {source}")
    return match.group(1)


def idd_version(idd_path: str | Path) -> str:
    source = Path(idd_path)
    match = _IDD_VERSION_PATTERN.search(source.read_text(encoding="utf-8-sig"))
    if match is None:
        raise ValueError(f"IDD has no !IDD_Version header: {source}")
    return match.group(1).removesuffix(".0")


def require_idf_version(idf_path: str | Path) -> Path:
    source = Path(idf_path)
    actual = idf_version(source)
    if actual != ENERGYPLUS_VERSION:
        raise ValueError(
            f"MOOSAS requires EnergyPlus {ENERGYPLUS_VERSION} IDF input; "
            f"got {actual} from {source}. Run the official EnergyPlus Transition chain first."
        )
    return source


def configure_idd() -> Path:
    source = bundled_idd_path()
    actual = idd_version(source)
    if actual != ENERGYPLUS_VERSION:
        raise ValueError(
            f"MOOSAS requires EnergyPlus {ENERGYPLUS_VERSION} IDD input; got {actual} from {source}."
        )
    IDF.setiddname(str(source))
    return source
