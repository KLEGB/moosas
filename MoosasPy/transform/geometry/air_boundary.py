"""Air-boundary geometry preparation for divided-zone transformations."""
from __future__ import annotations

from .cleanse import cleanseOverlapWall
from .contour import outerBoundary
from .element import MoosasWall
from .geos import contains, equals
from ...utils import np, shapely
from ...utils.tools import searchBy


def copy_air_boundaries(model):
    """Copy interior air boundaries across levels before divided-zone generation."""
    new_walls = []
    for level_index, level in enumerate(model.levelList[:-1]):
        outer_boundaries = outerBoundary(model, level)
        if outer_boundaries is not None:
            level_walls = np.array(model.wallList)[searchBy("level", level, model.wallList)]
            for wall_index, wall in enumerate(model.wallList):
                print(f"\rTOPOLOGY: Copy air boundaries in level {level} {wall_index}/{len(model.wallList)}", end="")
                if wall.level != level:
                    for boundary in outer_boundaries:
                        if shapely.contains(boundary, wall.force_2d()):
                            found = False
                            for level_wall in level_walls:
                                if equals(level_wall.force_2d(), wall.force_2d()):
                                    found = True
                                elif contains(level_wall.force_2d(), wall.force_2d()) or contains(wall.force_2d(), level_wall.force_2d()):
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