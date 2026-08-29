"""Air-boundary preparation stage for divided-zone transformations."""
from __future__ import annotations

from ...models import MoosasModel
from ...utils import np, shapely
from ...utils.tools import searchBy
from ..geometry.cleanse import cleanseOverlapWall
from ..geometry.contour import outerBoundary
from ..geometry.element import MoosasWall
from ..geometry.geos import contains, equals


def copy_air_boundaries(model: MoosasModel) -> MoosasModel:
    """Copy interior air boundaries across levels before space generation."""
    new_walls = []
    for level_index, level in enumerate(model.levelList[:-1]):
        outer_boundaries = outerBoundary(model, level)
        if outer_boundaries is None:
            continue
        level_walls = np.array(model.wallList)[searchBy("level", level, model.wallList)]
        for wall_index, wall in enumerate(model.wallList):
            print(f"\rTOPOLOGY: Copy air boundaries in level {level} {wall_index}/{len(model.wallList)}", end="")
            if wall.level == level:
                continue
            for boundary in outer_boundaries:
                if not shapely.contains(boundary, wall.force_2d()):
                    continue
                found = False
                for level_wall in level_walls:
                    if equals(level_wall.force_2d(), wall.force_2d()):
                        found = True
                    elif contains(level_wall.force_2d(), wall.force_2d()) or contains(
                        wall.force_2d(), level_wall.force_2d()
                    ):
                        new_walls.append(
                            MoosasWall.fromProjection(
                                wall.force_2d(),
                                bottom=level_wall.level + level_wall.offset,
                                top=level_wall.toplevel + level_wall.topoffset,
                                model=model,
                            )
                        )
                        found = True
                if not found:
                    new_walls.append(
                        MoosasWall.fromProjection(
                            wall.force_2d(),
                            bottom=level,
                            top=model.levelList[level_index + 1],
                            model=model,
                            airBoundary=True,
                        )
                    )
                break
    print()
    model.wallList = list(np.append(model.wallList, new_walls))
    return cleanseOverlapWall(model)
