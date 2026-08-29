"""Glazing-to-parent element matching for transformed models."""
from __future__ import annotations

from ...model import MoosasModel
from ...utils import np, shapely
from ...utils.constant import geom
from ...utils.tools import searchBy
from ..geometry.element import MoosasFace, MoosasGlazing, MoosasSkylight, MoosasWall


def match_face_glazing(face: MoosasFace | MoosasWall, glazing: MoosasSkylight | MoosasGlazing) -> bool:
    """Attach glazing to a containing or coincident opaque parent face."""
    face_projection = face.force_2d(region=True)
    glazing_projection = glazing.force_2d(region=True)
    if shapely.get_dimensions(face_projection) == shapely.get_dimensions(glazing_projection) == 1:
        for point in shapely.points(shapely.get_coordinates(glazing_projection)):
            if shapely.distance(face_projection, point) > 2 * geom.POINT_PRECISION:
                return False
        face.add_glazing(glazing)
        return True
    if shapely.contains(face_projection, glazing_projection):
        face.add_glazing(glazing)
        return True
    return False


def attach_glazing_to_faces(model: MoosasModel) -> MoosasModel:
    """Attach glazing and skylights, creating curtain parents where necessary."""
    glazing_count = 0
    matched_glazing_count = 0
    for level in model.levelList:
        glazing = np.array(model.glazingList)[searchBy("level", level, model.glazingList)]
        walls = np.array(model.wallList)[searchBy("level", level, model.wallList)]
        wall_projections = [wall.force_2d() for wall in walls]
        for window in glazing:
            glazing_count += 1
            print(f"\rLOADING: Matching glazing {glazing_count}/{len(model.glazingList)}", end="")
            distances = np.argsort([shapely.distance(window.force_2d(), projection) for projection in wall_projections])
            for wall in walls[distances][:min(5, len(walls))]:
                if match_face_glazing(wall, window):
                    matched_glazing_count += 1
                    break
            else:
                curtain = MoosasWall(model, faceId=window.faceId)
                curtain.add_glazing(window)
                model.wallList = list(np.append(model.wallList, [curtain]))

    print("\tmatched glazings: ", matched_glazing_count)
    print("\rLOADING: Matching skylight", end="")
    matched_skylight_count = 0
    for index, skylight in enumerate(model.skylightList):
        print(f"\rLOADING: Matching skylight {index}/{len(model.skylightList)}", end="")
        floors = np.array(model.faceList)[searchBy("level", skylight.level, model.faceList)]
        for floor in floors:
            if match_face_glazing(floor, skylight):
                matched_skylight_count += 1
                break
        else:
            roof = MoosasFace(model=model, faceId=skylight.faceId)
            roof.add_glazing(skylight)
            model.faceList = list(np.append(model.faceList, [roof]))
    print("\t\t\tmatched skylight: ", matched_skylight_count)
    return model
