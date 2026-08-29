"""Independent state produced by IDF conversion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...model import MoosasModel
    from .parser import ZoneTemplate


@dataclass(frozen=True)
class IDFConversionResult:
    """IDF-specific state kept outside the semantic building model."""

    model: MoosasModel
    zone_to_space_ids: dict[str, list[str]]
    templates_by_space_id: dict[str, ZoneTemplate]
    graph: object | None
    graph_source: str | None
    uri_map: dict[str, str]
