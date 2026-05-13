from __future__ import annotations

import struct

from ..utils import np, shapely
from ..geometry.element import MoosasGeometry
from ._obj import _roundPolygons
from ..utils.constant import geom


def _readStl(file_path: str) -> list[MoosasGeometry]:
    """Read an STL file (ascii/binary) and return MoosasGeometry list."""
    triangles = _read_stl_ascii(file_path)
    if triangles is None:
        triangles = _read_stl_binary(file_path)

    cat, idd, normal, faces = [], [], [], []
    for i, tri in enumerate(triangles):
        pts = [np.array(v).astype(float) for v in tri["vertices"]]
        pts.append(pts[0])
        faces.append(shapely.polygons(pts))
        idd.append(i)
        normal.append(shapely.points(np.array(tri["normal"]).astype(float)))
        # STL has no material/transparency, all treated as opaque.
        cat.append(0)

    faces = _roundPolygons(faces, geom.POINT_PRECISION)
    return [MoosasGeometry(f, i, n, c) for f, i, n, c in zip(faces, idd, normal, cat)]


def _read_stl_ascii(file_path: str) -> list[dict] | None:
    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            lines = [ln.strip() for ln in f if ln.strip() != ""]
    except Exception:
        return None

    if len(lines) == 0 or not lines[0].lower().startswith("solid"):
        return None

    triangles = []
    i = 0
    while i < len(lines):
        li = lines[i].lower()
        if li.startswith("facet normal"):
            parts = lines[i].split()
            if len(parts) < 5:
                return None
            normal = [float(parts[-3]), float(parts[-2]), float(parts[-1])]
            i += 1
            if i >= len(lines) or lines[i].lower() != "outer loop":
                return None
            vertices = []
            for _ in range(3):
                i += 1
                if i >= len(lines) or not lines[i].lower().startswith("vertex"):
                    return None
                v = lines[i].split()
                if len(v) < 4:
                    return None
                vertices.append([float(v[-3]), float(v[-2]), float(v[-1])])
            i += 1
            if i >= len(lines) or lines[i].lower() != "endloop":
                return None
            i += 1
            if i >= len(lines) or lines[i].lower() != "endfacet":
                return None
            triangles.append({"normal": normal, "vertices": vertices})
        i += 1

    if len(triangles) == 0:
        return None
    return triangles


def _read_stl_binary(file_path: str) -> list[dict]:
    triangles = []
    with open(file_path, "rb") as f:
        data = f.read()

    if len(data) < 84:
        raise ValueError(f"Invalid STL file: {file_path}")

    tri_count = struct.unpack("<I", data[80:84])[0]
    expected = 84 + tri_count * 50
    if len(data) < expected:
        raise ValueError(f"Incomplete binary STL file: {file_path}")

    offset = 84
    for _ in range(tri_count):
        rec = data[offset: offset + 50]
        normal = struct.unpack("<3f", rec[0:12])
        v1 = struct.unpack("<3f", rec[12:24])
        v2 = struct.unpack("<3f", rec[24:36])
        v3 = struct.unpack("<3f", rec[36:48])
        triangles.append({"normal": normal, "vertices": [v1, v2, v3]})
        offset += 50
    return triangles

