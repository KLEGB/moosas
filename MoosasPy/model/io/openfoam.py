"""Export a MoosasGrid footprint as an extruded OpenFOAM volume mesh.

The complete UV footprint is meshed, including perimeter cells without valid
sampling points. This is an explicit constant-section extrusion, not a mesher
for arbitrary building solids. No OpenFOAM installation is needed to export.
"""

from __future__ import annotations

import json
from numbers import Integral
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import shapely
from shapely.geometry.polygon import orient
from shapely.ops import triangulate

from .result import SaveResult

if TYPE_CHECKING:
    from ...transform.geometry.grid import MoosasGrid


_PATCH_NAMES = ("bottom", "top", "walls")
_PATCH_TYPES = {"wall", "patch", "symmetry", "symmetryPlane"}


def export_openfoam(
    grid: MoosasGrid,
    case_dir: str | Path,
    *,
    height: float,
    layers: int = 1,
    base_offset: float = 0.0,
    patch_types: dict[str, str] | None = None,
) -> SaveResult:
    """Write ``constant/polyMesh`` and ``constant/moosasGrid.json``.

    ``height`` is a positive distance along the grid's projected local Z axis. ``layers``
    uniform layers start at ``base_offset`` relative to the source face,
    independently of the grid's sampling offset. Coordinates retain the input
    units (use metres for OpenFOAM).

    Columns follow the existing UV lattice, with squares clipped to UVFace.
    Concave/holed intersections are split into convex prisms; boundary columns
    are added where necessary to cover the entire footprint. Each cell's JSON
    entry records its layer, lattice index, grid index (null for added columns)
    and flattened valid-sample index (null when there is no valid sample).

    Boundary groups are ``bottom``, ``top`` and ``walls`` (all type ``wall`` by
    default). ``patch_types`` may change these to ``patch`` or symmetry types.
    Field boundary conditions and solver dictionaries are the caller's job.
    Existing mesh/mapping files are never overwritten; use a new case directory.
    Returns the mesh directory as primary_path and all six generated files.
    """
    height = _finite_number(height, "height")
    base_offset = _finite_number(base_offset, "base_offset")
    if height <= 0:
        raise ValueError("height must be positive")
    if isinstance(layers, (bool, np.bool_)) or not isinstance(layers, Integral) or layers < 1:
        raise ValueError("layers must be a positive integer")
    layers = int(layers)
    types = dict.fromkeys(_PATCH_NAMES, "wall")
    for name, value in (patch_types or {}).items():
        if name not in types or value not in _PATCH_TYPES:
            raise ValueError(f"Unsupported boundary patch/type: {name!r}: {value!r}")
        if name == "walls" and value == "symmetryPlane":
            raise ValueError("walls is not a single plane; use symmetry instead")
        types[name] = value

    size = _finite_number(grid.gridSize, "gridSize")
    if size <= 0:
        raise ValueError("gridSize must be positive")
    cells = np.asarray(grid.gridCell, dtype=object)
    if cells.ndim != 2 or not cells.size:
        raise ValueError("gridCell must be a nonempty rectangular grid")
    footprint = shapely.force_2d(grid.UVFace)
    if not isinstance(footprint, shapely.Polygon) or footprint.is_empty or not footprint.is_valid:
        raise ValueError("UVFace must be a nonempty valid Polygon")
    if not np.isfinite(shapely.get_coordinates(footprint)).all():
        raise ValueError("UVFace coordinates must be finite")
    # Export the represented grid only; MoosasGrid otherwise silently selects
    # the dominant source face when it is given fragmented geometry.
    if len(grid.geometry) != 1:
        raise ValueError("Export requires a grid built from one planar source face")
    # Use toWorld itself: the legacy projection has a left-handed basis and
    # an axis-aligned shortcut. Reconstructing a conventional frame would move
    # cells away from the existing grid's world coordinates.
    basis = shapely.get_coordinates(grid.proj.toWorld(shapely.LineString(
        [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
    )), include_z=True)
    origin = basis[0]
    rotation = (basis[1:] - origin).T
    if not (np.isfinite(rotation).all() and np.isfinite(origin).all()
            and np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-10)
            and np.isclose(abs(np.linalg.det(rotation)), 1.0)):
        raise ValueError("Grid projection must be a finite orthonormal frame")
    source = shapely.get_coordinates(grid.face, include_z=True)
    if not np.isfinite(source).all() or not np.allclose(
        (source - origin) @ rotation[:, 2], 0, atol=size * 1e-8, rtol=0
    ):
        raise ValueError("Source face must be planar in the grid projection")

    tolerance = size * 1e-9
    lattice_origin = np.asarray(cells[0, 0].origin.array[:2], dtype=float)
    for (row, column), cell in np.ndenumerate(cells):
        if not np.allclose(cell.origin.array[:2], lattice_origin + size * np.array([row, column]),
                           atol=tolerance, rtol=0):
            raise ValueError("gridCell positions must follow the MoosasGrid UV lattice")
    polygons, indices = _columns(footprint, lattice_origin, size, tolerance)
    uv_points, rings = _node_edges(polygons, tolerance)
    levels = base_offset + np.linspace(0.0, height, layers + 1)
    if not np.all(np.diff(levels) > 0):
        raise ValueError("Layer spacing is too small for the requested base_offset")
    local_points = np.array([(u, v, z) for z in levels for u, v in uv_points])
    points = local_points @ rotation.T + origin
    if not np.isfinite(points).all() or len(np.unique(points, axis=0)) != len(points):
        raise ValueError("World coordinates collapse mesh vertices; rescale the geometry")
    faces, owner, neighbour, patches = _extrude(rings, len(uv_points), layers)
    if np.linalg.det(rotation) < 0:
        faces = [list(reversed(face)) for face in faces]

    sample_indices = {}
    sample_points = []
    for index, cell in np.ndenumerate(cells):
        if cell.valid:
            sample_indices[index] = len(sample_points)
            sample_points.append(list(shapely.get_coordinates(
                grid.proj.toWorld(cell.origin.geometry), include_z=True
            )[0]))
    mapping = {
        "format_version": 1,
        "grid_shape": list(cells.shape),
        "grid_size": size,
        "grid_offset": _finite_number(grid.gridOffset, "gridOffset"),
        "layer_bounds": levels.tolist(),
        "sample_points": sample_points,
        "cells": [],
    }
    for layer in range(layers):
        for index in indices:
            row, column = index
            in_grid = 0 <= row < cells.shape[0] and 0 <= column < cells.shape[1]
            mapping["cells"].append({
                "cell": len(mapping["cells"]),
                "layer": layer,
                "lattice_index": list(index),
                "grid_index": list(index) if in_grid else None,
                "sample_index": sample_indices.get(index),
            })

    mesh_dir = Path(case_dir) / "constant" / "polyMesh"
    contents = {
        mesh_dir / "points": _foam_list("points", "vectorField", [
            "(" + " ".join(format(value, ".17g") for value in point) + ")" for point in points
        ]),
        mesh_dir / "faces": _foam_list("faces", "faceList", [
            f"{len(face)}(" + " ".join(map(str, face)) + ")" for face in faces
        ]),
        mesh_dir / "owner": _foam_list("owner", "labelList", list(map(str, owner))),
        mesh_dir / "neighbour": _foam_list("neighbour", "labelList", list(map(str, neighbour))),
        mesh_dir / "boundary": _foam_list("boundary", "polyBoundaryMesh", [
            f"{name}\n{{\n    type {types[name]};\n    nFaces {count};\n    startFace {start};\n}}"
            for name, start, count in patches
        ]),
        mesh_dir.parent / "moosasGrid.json": json.dumps(mapping, indent=2, allow_nan=False) + "\n",
    }
    # Refuse stale polyMesh sidecars (zones, compressed lists, addressing, etc.)
    # as well as the five core files, while allowing other case setup files.
    if mesh_dir.exists() and (not mesh_dir.is_dir() or any(mesh_dir.iterdir())):
        raise FileExistsError(f"Mesh directory is not empty: {mesh_dir}")
    for path in contents:
        if path.exists():
            raise FileExistsError(f"Export file already exists: {path}")
    mesh_dir.mkdir(parents=True, exist_ok=True)
    for path, content in contents.items():
        with path.open("x", encoding="ascii", newline="\n") as stream:
            stream.write(content)
    return SaveResult(primary_path=mesh_dir, generated_paths=tuple(contents))


def _finite_number(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite number")
    try:
        value = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a finite number") from error
    if not np.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    return value


def _polygon_parts(geometry):
    if isinstance(geometry, shapely.Polygon):
        if not geometry.is_empty and geometry.area > 0:
            yield geometry
    elif hasattr(geometry, "geoms"):
        for part in geometry.geoms:
            yield from _polygon_parts(part)


def _columns(footprint, origin, size, tolerance):
    """Cover the footprint using the grid's lattice, not its sampling mask."""
    snapped = shapely.set_precision(footprint, tolerance)
    bounds = np.asarray(footprint.bounds).reshape(2, 2)
    first = np.floor((bounds[0] - origin) / size - 0.5).astype(int)
    last = np.ceil((bounds[1] - origin) / size + 0.5).astype(int)
    polygons, indices = [], []
    for row in range(first[0], last[0] + 1):
        for column in range(first[1], last[1] + 1):
            center = origin + size * np.array([row, column])
            square = shapely.box(*(center - size / 2), *(center + size / 2))
            clipped = shapely.intersection(snapped, square, grid_size=tolerance)
            for polygon in _polygon_parts(clipped):
                if not polygon.interiors and polygon.convex_hull.area - polygon.area <= tolerance**2:
                    parts = [polygon]
                else:
                    # Clip the full Delaunay tessellation, rather than filtering
                    # triangles by centroid (which can lose concavities/holes).
                    parts = [part for triangle in triangulate(polygon)
                             for part in _polygon_parts(shapely.intersection(
                                 triangle, polygon, grid_size=tolerance))]
                for part in parts:
                    if part.interiors or part.convex_hull.area - part.area > tolerance * size:
                        raise ValueError("Unable to form convex columns for this footprint")
                    polygons.append(orient(part, sign=1.0))
                    indices.append((row, column))
    if not polygons or abs(sum(p.area for p in polygons) - footprint.area) > tolerance * footprint.length:
        raise ValueError("Grid precision cannot preserve the complete footprint")
    return polygons, indices


def _node_edges(polygons, tolerance):
    """Insert shared edge vertices so split/clipped columns have no T-junctions."""
    coordinates = list(dict.fromkeys(tuple(point) for polygon in polygons
                                    for point in polygon.exterior.coords[:-1]))
    vertices = np.asarray(coordinates)
    lookup = {point: index for index, point in enumerate(coordinates)}
    tree = shapely.STRtree(shapely.points(vertices))
    rings = []
    for polygon in polygons:
        ring = []
        for start, end in zip(polygon.exterior.coords[:-1], polygon.exterior.coords[1:]):
            a, b = np.asarray(start), np.asarray(end)
            edge = b - a
            length_squared = np.dot(edge, edge)
            candidates = tree.query(shapely.box(*(np.minimum(a, b) - tolerance),
                                                 *(np.maximum(a, b) + tolerance)))
            along = (vertices[candidates] - a) @ edge / length_squared
            distance = np.linalg.norm(vertices[candidates] - a - along[:, None] * edge, axis=1)
            endpoints = {lookup[tuple(start)], lookup[tuple(end)]}
            selected = [(fraction, int(index)) for index, fraction, error
                        in zip(candidates, along, distance)
                        if index not in endpoints and 0 < fraction < 1 and error < tolerance * 0.1]
            ring.append(lookup[tuple(start)])
            ring.extend(index for _, index in sorted(selected))
        if len(set(ring)) != len(ring):
            raise ValueError("Degenerate grid column after edge matching")
        rings.append(ring)
    return vertices, rings


def _extrude(rings, point_count, layers):
    """Deduplicate faces and place internal faces before contiguous patches."""
    records, lookup = [], {}

    def add(face, cell, patch):
        key = tuple(sorted(face))
        if key not in lookup:
            lookup[key] = len(records)
            records.append([face, cell, None, patch])
        else:
            record = records[lookup[key]]
            if record[2] is not None:
                raise ValueError("Non-manifold mesh: a face belongs to more than two cells")
            # Adjacent outward faces must use opposite cyclic order.
            reverse = list(reversed(record[0]))
            offset = reverse.index(face[0])
            if reverse[offset:] + reverse[:offset] != face:
                raise ValueError("Inconsistent face orientation between adjacent cells")
            record[2] = cell

    for layer in range(layers):
        for column, ring in enumerate(rings):
            cell = layer * len(rings) + column
            bottom = [point + layer * point_count for point in ring]
            top = [point + (layer + 1) * point_count for point in ring]
            add(list(reversed(bottom)), cell, "bottom")
            add(top, cell, "top")
            for j in range(len(ring)):
                k = (j + 1) % len(ring)
                add([bottom[j], bottom[k], top[k], top[j]], cell, "walls")
    internal = sorted((record for record in records if record[2] is not None),
                      key=lambda record: (record[1], record[2]))
    ordered = list(internal)
    patches = []
    for name in _PATCH_NAMES:
        boundary = [record for record in records if record[2] is None and record[3] == name]
        patches.append((name, len(ordered), len(boundary)))
        ordered.extend(boundary)
    return ([record[0] for record in ordered], [record[1] for record in ordered],
            [record[2] for record in internal], patches)


def _foam_list(name, class_name, entries):
    header = ("FoamFile\n{\n    version 2.0;\n    format ascii;\n"
              f"    class {class_name};\n    location \"constant/polyMesh\";\n"
              f"    object {name};\n}}\n\n")
    return header + str(len(entries)) + "\n(\n" + "\n".join(entries) + "\n)\n"
