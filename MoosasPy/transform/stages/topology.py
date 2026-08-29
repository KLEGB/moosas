"""Second-level space and face topology construction."""
from __future__ import annotations

from ...model import MoosasModel
from ...utils import mixItemListToList, np, shapely
from ...utils.constant import geom
from ...utils.tools import searchBy
from ..geometry.element import MoosasFace, MoosasFloor, MoosasGlazing, MoosasSkylight, MoosasSpace
from ..geometry.geos import GeometryError, Vector, overlapArea
from .glazing import match_face_glazing


def build_space_topology(
    model: MoosasModel,
    break_wall_vertical: bool,
) -> MoosasModel:
    """Regenerate space IDs and record space-to-space adjacency."""
    model.faceList = list(model.faceList)
    if break_wall_vertical:
        print("\r2LSB: Checking void connection", end="")
        for index, void in enumerate(model.voidList):
            print(f"\r2LSB: Checking void connection {index}/{len(model.voidList)}", end="")
            if void.floor is None or overlapArea(void.floor.force_2d(), void.edge.force_2d()) <= void.area - geom.AREA_PRECISION:
                continue
            meta_voids = [void]
            while meta_voids[-1] is not None:
                meta_voids.append(find_void_above(meta_voids[-1]))
            meta_voids.pop()
            if not meta_voids or meta_voids[-1].ceiling is None:
                continue
            meta_voids = [MoosasSpace(item.floor, item.edge, item.ceiling) for item in meta_voids]
            for space_bottom, space_top in zip(meta_voids[:-1], meta_voids[1:]):
                space_bottom.ceiling, space_top.floor = find_co_ceiling(space_bottom, space_top)
                model.ceilingList.append(space_bottom.ceiling)
                model.floorList.append(space_top.floor)
            model.spaceList = list(np.append(model.spaceList, meta_voids))
            model.voidList = list(set(model.voidList) - set(meta_voids))
        print()

    print("\r2LSB: Recording Boundary topology", end="")
    for space in model.spaceList:
        space.regenerateId()

    for index, space in enumerate(model.spaceList):
        print(f"\r2LSB: Recording Boundary topology {index}/{len(model.spaceList)}", end="")
        elements = space.getAllFaces(to_dict=True)
        for element in elements["MoosasWall"]:
            if len(element.space) > 1:
                element.isOuter = False
                neighbor_id = element.space[1] if element.space[0] == space.id else element.space[0]
                space.add_neighbor(neighbor_id, element)
        for element in elements["MoosasFloor"]:
            if len(element.space) > 1:
                element.isOuter = False
                neighbor_id = element.space[1] if element.space[0] == space.id else element.space[0]
                space.add_neighbor(neighbor_id, element)
                model.spaceIdDict[neighbor_id].add_neighbor(space.id, element)
    print()
    return model


def build_face_topology(model: MoosasModel) -> MoosasModel:
    """Record face-to-face adjacency through shared geometric edges."""
    edges = {}
    faces = model.getAllFaces(dumpUseless=True)
    faces = list(faces["MoosasWall"]) + list(faces["MoosasFace"])
    for index, face in enumerate(faces):
        print(f"\r2LSB: Extracting Faces topology {index}/{len(faces)}", end="")
        if not isinstance(face, MoosasGlazing) or isinstance(face, MoosasSkylight):
            for edge in face.getEdgeStr():
                edges.setdefault(edge, []).append(face)

    print()
    for index, edge in enumerate(edges):
        print(f"\r2LSB: Extracting Faces topology {index}/{len(edges)}", end="")
        edge_faces = edges[edge]
        for first_index, first_face in enumerate(edge_faces[:-1]):
            first_face.neighbor[edge] = []
            for second_face in edge_faces[first_index + 1:]:
                first_face.neighbor[edge].append(second_face.Uid)
                second_face.neighbor.setdefault(edge, []).append(first_face.Uid)
    print()
    return model


def cap_floor(boundary: shapely.Geometry, level, model: MoosasModel, base_floor: MoosasFloor | None = None) -> MoosasFloor:
    """Split floor faces by a boundary and create any required aperture faces."""
    floor_faces = []
    remaining_faces = []
    aperture_faces = [] if base_floor is None else base_floor.glazingElement
    base_faces = [] if base_floor is None else base_floor.face
    for face in base_faces:
        geometry = shapely.multipolygons(mixItemListToList(face.face))
        useful = shapely.intersection(boundary, geometry, grid_size=geom.POINT_PRECISION)
        if shapely.is_empty(useful):
            continue
        for item in shapely.get_parts(useful):
            item = shapely.force_3d(item, z=level)
            if shapely.get_dimensions(item) != 2:
                continue
            geometry_id = model.includeGeo(item, Vector([0, 0, 1]).geometry, cat=0)
            model.faceList.append(MoosasFace(model=model, faceId=geometry_id))
            floor_faces.append(model.faceList[-1])
        remaining = shapely.difference(geometry, boundary, grid_size=geom.POINT_PRECISION)
        for item in shapely.get_parts(remaining):
            item = shapely.force_3d(item, z=level)
            if shapely.get_dimensions(item) != 2:
                continue
            geometry_id = model.includeGeo(item, Vector([0, 0, 1]).geometry, cat=0)
            model.faceList.append(MoosasFace(model, geometry_id))
            remaining_faces.append(model.faceList[-1])
    for face in floor_faces:
        boundary = shapely.difference(boundary, shapely.multipolygons(mixItemListToList(face.face)))
    for item in shapely.get_parts(boundary):
        try:
            item = shapely.force_3d(item, z=level)
            geometry_id = model.includeGeo(item, Vector([0, 0, 1]).geometry, cat=2)
            model.faceList.append(MoosasFace(model, geometry_id))
            model.skylightList.append(MoosasSkylight(model, geometry_id))
            model.faceList[-1].add_glazing(model.skylightList[-1])
            floor_faces.append(model.faceList[-1])
        except GeometryError:
            continue
    for glazing in aperture_faces:
        for face in floor_faces:
            if match_face_glazing(face, glazing):
                break
        else:
            for face in remaining_faces:
                if match_face_glazing(face, glazing):
                    break
    return MoosasFloor(floor_faces)


def find_void_above(void_with_floor: MoosasSpace) -> MoosasSpace | None:
    """Find the unbounded void directly above a bounded void."""
    model = void_with_floor.parent
    level_index = model.levelList.index(void_with_floor.level)
    if level_index == len(model.levelList) - 1:
        return None
    top_level = model.levelList[level_index + 1]
    top_voids = np.array(model.voidList)[searchBy("level", top_level, model.voidList)]
    for top_void in top_voids:
        if top_void.floor is None and (
            shapely.contains(void_with_floor.force_2d(top=True), top_void.force_2d())
            or shapely.contains(top_void.force_2d(), void_with_floor.force_2d(top=True))
        ):
            return top_void
    return None


def find_co_ceiling(space_bottom: MoosasSpace, space_top: MoosasSpace) -> tuple[MoosasFloor, MoosasFloor]:
    """Rebuild floor and ceiling portions around the overlap of stacked void spaces."""
    model = space_bottom.parent
    elevation = space_top.edge.elevation
    shared_faces = list(set(space_bottom.ceiling.face if space_bottom.ceiling else []) | set(space_top.floor.face if space_top.floor else []))
    intersection = shapely.intersection(space_bottom.force_2d(True), space_top.force_2d(), grid_size=geom.POINT_PRECISION)
    print(space_bottom.force_2d(True), space_top.force_2d(), intersection)
    ceiling_geometry = shapely.force_3d(shapely.difference(space_bottom.force_2d(True), intersection, grid_size=geom.POINT_PRECISION), z=elevation)
    floor_geometry = shapely.force_3d(shapely.difference(space_top.force_2d(), intersection, grid_size=geom.POINT_PRECISION), z=elevation)
    if shapely.is_empty(intersection):
        raise Exception("space disjoint")
    intersection_floor = cap_floor(space_top.force_2d(), space_top.level, model, MoosasFloor(shared_faces))
    floor_faces = _cap_remaining(floor_geometry, space_top, model, intersection_floor)
    ceiling_faces = _cap_remaining(ceiling_geometry, space_top, model, intersection_floor)
    return MoosasFloor(ceiling_faces), MoosasFloor(floor_faces)


def _cap_remaining(geometry, space_top: MoosasSpace, model: MoosasModel, intersection_floor: MoosasFloor):
    if shapely.is_empty(geometry):
        return intersection_floor.face
    included = []
    for face in mixItemListToList(shapely.get_parts(geometry)):
        try:
            geometry_id = model.includeGeo(face, Vector([0, 0, 1]).geometry)
            included.append(MoosasFace(model, geometry_id))
        except GeometryError:
            continue
    capped = cap_floor(space_top.force_2d(), space_top.level, model, MoosasFloor(included))
    return capped.face + intersection_floor.face
