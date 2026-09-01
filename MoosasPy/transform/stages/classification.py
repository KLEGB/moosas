"""Geometry classification stage for the transformation pipeline."""
from __future__ import annotations

import shapely

from ...model import MoosasModel
from ...utils import np
from ...utils.constant import geom
from ..geometry import triangulate2dFace
from ..geometry.cleanse import cleanseDuplicatedLevel
from ..geometry.element import MoosasElement, MoosasFace, MoosasGlazing, MoosasSkylight, MoosasWall
from ..geometry.geos import GeometryError, Projection, Vector
from .splitting import split_vertical_walls


def classify_model(
    model: MoosasModel,
    triangulate_faces: bool = True,
    break_wall_vertical: bool = True,
) -> MoosasModel | None:
    """Classify source geometry into building elements and establish levels."""
    print("\rLOADING: Predefining existing tag on faces...", end="")
    classified_ids = []
    for geometry in model.geometryList:
        if geometry.category == -1:
            geometry.setCategory()
            model.shadingList.append(MoosasElement(model, geometry))
            classified_ids.append(geometry.faceId)
        elif geometry.category == 4:
            classified_ids.append(geometry.faceId)
            geometry.setCategory()
            face = MoosasFace(model, geometry)
            model.faceList.append(face)
            if face.level not in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()
        elif geometry.category == 6:
            classified_ids.append(geometry.faceId)
            geometry.setCategory()
            face = MoosasSkylight(model, geometry)
            model.skylightList.append(face)
            if face.level not in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()

    for geometry in model.geometryList:
        if geometry.category == 3:
            classified_ids.append(geometry.faceId)
            geometry.setCategory()
            model.wallList.append(MoosasWall(model, geometry))
        elif geometry.category == 5:
            classified_ids.append(geometry.faceId)
            geometry.setCategory()
            model.glazingList.append(MoosasGlazing(model, geometry))

    print()
    if triangulate_faces:
        deleted_indices = []
        for index, geometry in enumerate(model.geometryList):
            if geometry.faceId in classified_ids:
                continue
            print(f"\rLOADING: triangulate horizontal faces {index + 1}/{len(model.geoId)}", end="")
            if np.abs(Vector.dot(geometry.normal, shapely.points([0, 0, 1]))) >= geom.HORIZONTAL_ANGLE_THRESHOLD:
                if len(geometry.holes) > 0:
                    projection = Projection.fromPolygon(geometry.face)
                    face_projection = projection.toUV(geometry.face)
                    hole_projections = [projection.toUV(hole) for hole in geometry.holes]
                    split_projections, _ = triangulate2dFace(face_projection, hole_projections)
                    for split_projection in split_projections:
                        try:
                            model.includeGeo(projection.toWorld(split_projection), cat=geometry.category)
                        except GeometryError as error:
                            print(f"******Warning: {error}")
                    deleted_indices.append(index)

        model.geoId = list(np.delete(model.geoId, deleted_indices))
        model.geometryList = list(np.delete(model.geometryList, deleted_indices))
        print(f"\t\tprocessing faces: {len(deleted_indices)}")

    for index, geometry in enumerate(model.geometryList):
        if geometry.faceId in classified_ids:
            continue
        print(f"\rLOADING: Filtering horizontal faces {index + 1}/{len(model.geoId)}", end="")
        if np.abs(Vector.dot(geometry.normal, shapely.points([0, 0, 1]))) >= 0.99:
            face = MoosasSkylight(model, geometry) if geometry.category != 0 else MoosasFace(model, geometry)
            (model.skylightList if geometry.category != 0 else model.faceList).append(face)
            if face.level not in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()
    print()

    for index, geometry in enumerate(model.geometryList):
        if geometry.faceId in classified_ids:
            continue
        print(f"\rLOADING: Filtering inclined faces {index + 1}/{len(model.geoId)}", end="")
        if 0.99 > np.abs(Vector.dot(geometry.normal, shapely.points([0, 0, 1]))) >= geom.HORIZONTAL_ANGLE_THRESHOLD:
            face = MoosasSkylight(model, geometry) if geometry.category != 0 else MoosasFace(model, geometry)
            (model.skylightList if geometry.category != 0 else model.faceList).append(face)
            if face.level not in model.levelList:
                model.levelList.append(face.level)
                model.levelList.sort()

    if not model.levelList:
        return None

    model = cleanseDuplicatedLevel(model)
    print(f"\t\ttotal horizontal faces: {len(model.faceList)} skylights: {len(model.skylightList)}")

    if break_wall_vertical:
        model = split_vertical_walls(model, classified_ids)

    for index, geometry in enumerate(model.geometryList):
        if geometry.faceId in classified_ids:
            continue
        print(f"\rLOADING: Filtering vertical faces {index + 1}/{len(model.geoId)}", end="")
        if np.abs(Vector.dot(geometry.normal, shapely.points([0, 0, 1]))) < geom.HORIZONTAL_ANGLE_THRESHOLD:
            if geometry.category in (0, 2):
                model.wallList.append(MoosasWall(model, geometry))
            else:
                model.glazingList.append(MoosasGlazing(model, geometry))

    print(f"\t\ttotal vertical faces: {len(model.wallList)} glazings: {len(model.glazingList)}")
    return model
