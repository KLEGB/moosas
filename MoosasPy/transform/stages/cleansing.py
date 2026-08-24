"""Geometry cleansing stage for the transformation pipeline."""
from __future__ import annotations

from collections.abc import Callable

from ...models import MoosasModel
from ...utils import np
from ...utils.tools import searchBy
from ..geometry.cleanse import (
    cleanseCoplannerLine,
    cleanseDuplicatedWall,
    cleanseInvalidFace,
    cleanseInvalidWall,
    cleanseOverlapFace,
    cleanseOverlapWall,
)


def cleanse_model(
    model: MoosasModel,
    *,
    solve_duplicated: bool,
    solve_redundant: bool,
    solve_overlap: bool,
    match_glazing: Callable[[MoosasModel], MoosasModel],
) -> tuple[MoosasModel, list[int]]:
    """Clean classified geometry and attach glazing before space generation."""
    if solve_redundant:
        model = cleanseCoplannerLine(model)

    model = cleanseInvalidWall(model)
    model = cleanseInvalidFace(model)
    model = match_glazing(model)

    wall_counts = [len(searchBy("level", level, model.wallList)) for level in model.levelList]
    if solve_redundant:
        model = cleanseCoplannerLine(model)
    if solve_duplicated:
        model = cleanseDuplicatedWall(model)

    model = cleanseInvalidWall(model)
    model = cleanseInvalidFace(model)

    if solve_overlap:
        model = cleanseOverlapWall(model)
        model = cleanseOverlapFace(model)
    return model, wall_counts