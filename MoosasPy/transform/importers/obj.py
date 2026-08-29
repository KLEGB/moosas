from __future__ import annotations

import os

# This module is a transform-only geometry source reader.

from ..geometry.element import MoosasGeometry
from ...utils import np, shapely, path, GeometryError
from ...utils.constant import geom


def _roundPolygons(polygons: np.ndarray[shapely.Geometry], precision: float) -> np.ndarray:
    """
    Round polygon coordinates according to precision and rebuild polygons.
    """
    coordinates, coorLengthIndex = [], [0]
    for p in polygons:
        coor = shapely.get_coordinates(p, include_z=True)
        coordinates += list(coor)
        coorLengthIndex += [coorLengthIndex[-1] + len(coor)]
    coordinates = np.array(coordinates)
    for dim in range(3):
        xIndex = np.argsort(coordinates[:, dim].flatten())
        xReindex = np.argsort(xIndex)
        coordinates = coordinates[xIndex]
        for i in range(1, len(xIndex) - 1):
            if np.abs(coordinates[i][dim] - coordinates[i + 1][dim]) < precision:
                coordinates[i + 1][dim] = coordinates[i][dim]
        coordinates = coordinates[xReindex]
    coordinates = geom.round(coordinates, precision)
    coordinates = [coordinates[idxS:idxE] for idxS, idxE in zip(coorLengthIndex[:-1], coorLengthIndex[1:])]
    return np.array([shapely.polygons(coors) for coors in coordinates])


def _readObj(file_path) -> list[MoosasGeometry]:
    """
    Read a Wavefront OBJ file into a list of MoosasGeometry objects.

    The reader accepts OBJ files with or without MTL references. When no
    material library exists, all faces default to opaque (category 0).
    """
    vertices: list[np.ndarray] = []
    normals: list[np.ndarray] = []
    obj_faces = []
    material_lab = {}
    current_material = ""

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if not parts:
                continue
            tag = parts[0].lower()
            if tag == "mtllib" and len(parts) > 1:
                mtl_path = os.path.join(os.path.dirname(file_path), parts[1])
                if os.path.isfile(mtl_path):
                    with open(mtl_path, "r", encoding="utf-8", errors="ignore") as mtl:
                        material_name = None
                        material_block = {}
                        for mline in mtl:
                            mline = mline.strip()
                            if not mline or mline.startswith("#"):
                                continue
                            mparts = mline.split()
                            if not mparts:
                                continue
                            if mparts[0].lower() == "newmtl" and len(mparts) > 1:
                                if material_name is not None:
                                    material_lab[material_name] = material_block
                                material_name = mparts[1]
                                material_block = {}
                            else:
                                material_block[mparts[0]] = mparts[1:]
                        if material_name is not None:
                            material_lab[material_name] = material_block
            elif tag == "usemtl" and len(parts) > 1:
                current_material = parts[1]
            elif tag == "v" and len(parts) >= 4:
                vertices.append(np.array(parts[1:4], dtype=float))
            elif tag == "vn" and len(parts) >= 4:
                normals.append(np.array(parts[1:4], dtype=float))
            elif tag == "f" and len(parts) >= 4:
                face_vertices = []
                face_normals = []
                for node in parts[1:]:
                    if not node:
                        continue
                    node_parts = node.split("/")
                    v_idx = int(node_parts[0])
                    if v_idx < 0:
                        v_idx = len(vertices) + v_idx + 1
                    face_vertices.append(vertices[v_idx - 1])
                    if len(node_parts) >= 3 and node_parts[2] != "":
                        n_idx = int(node_parts[2])
                        if n_idx < 0:
                            n_idx = len(normals) + n_idx + 1
                        if 0 <= n_idx - 1 < len(normals):
                            face_normals.append(normals[n_idx - 1])

                if len(face_vertices) < 3:
                    continue
                if face_normals:
                    normal = np.array([np.round(np.mean(nor_d), 3) for nor_d in np.array(face_normals).T]).astype(float)
                else:
                    normal = np.array([0.0, 0.0, 1.0], dtype=float)
                material_info = material_lab.get(current_material, {})
                cat = 0
                if "d" in material_info and len(material_info["d"]) > 0:
                    try:
                        if float(material_info["d"][0]) < 1.0:
                            cat = 1
                    except Exception:
                        pass
                obj_faces.append({
                    "vertices": face_vertices,
                    "normal": normal,
                    "category": cat,
                })

    faces = [shapely.polygons(vertices) for vertices in [item["vertices"] for item in obj_faces]]
    return [
        MoosasGeometry(f, i, shapely.points(item["normal"]), item["category"])
        for i, (f, item) in enumerate(zip(faces, obj_faces))
    ]


def _iter_obj_polygons(geo: MoosasGeometry):
    rings = shapely.get_rings(geo.face)
    if len(rings) == 0:
        return
    coords = shapely.get_coordinates(rings[0], include_z=True)
    if len(coords) >= 4:
        yield coords[:-1]


def writeObj(file_path, model=None, geoList=None, mask=None) -> str:
    """
    Write a Moosas geometry model to a Wavefront OBJ file without MTL.
    """
    path.checkBuildDir(file_path)
    if geoList is None:
        geoList = []
    if mask and model:
        geoList = model.findFace(mask)
    elif model:
        geoList = list(model.geometryList)

    vertices = []
    faces = []
    vertex_index = {}

    def _vertex_key(point):
        point = np.asarray(point, dtype=float)
        return tuple(np.round(point, 6))

    def _get_vertex_id(point):
        key = _vertex_key(point)
        if key not in vertex_index:
            vertex_index[key] = len(vertices) + 1
            vertices.append(np.asarray(point, dtype=float))
        return vertex_index[key]

    for geo in geoList:
        for polygon in _iter_obj_polygons(geo):
            face_ids = [_get_vertex_id(poi) for poi in polygon]
            if len(face_ids) >= 3:
                faces.append((geo, face_ids))

    lines = ["# Moosas OBJ export"]
    for v in vertices:
        lines.append(f"v {v[0]} {v[1]} {v[2]}")

    normal_offset = 0
    for idx, (geo, face_ids) in enumerate(faces):
        normal_coords = shapely.get_coordinates(geo.normal, include_z=True)
        normal = np.asarray(normal_coords[0], dtype=float) if len(normal_coords) > 0 else np.array([0.0, 0.0, 1.0], dtype=float)
        normal_index = normal_offset + 1
        lines.append(f"vn {normal[0]} {normal[1]} {normal[2]}")
        lines.append(f"o face_{idx}_{geo.faceId}")
        lines.append("s off")
        lines.append("usemtl default")
        lines.append("f " + " ".join([f"{vid}//{normal_index}" for vid in face_ids]))
        normal_offset += 1

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)
