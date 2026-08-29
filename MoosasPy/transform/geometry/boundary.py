'''Pure geometry helpers for boundary simplification and core insertion.'''
from __future__ import annotations

from ...utils import np, shapely
from .geos import Vector
from .polygon import GeometryBasic, calculate_wwr, create_obb, obb_to_face_vertices


def geometry_arrays(geometries):
    categories, face_ids, normals, faces, holes = [], [], [], [], []
    for geometry in geometries:
        rings = shapely.get_rings(geometry.face)
        categories.append(geometry.category)
        face_ids.append(geometry.faceId)
        normals.append(Vector(geometry.normal).array)
        faces.append(shapely.get_coordinates(rings[0], include_z=True)[:-1])
        face_holes = {
            index: shapely.get_coordinates(ring, include_z=True)[:-1]
            for index, ring in enumerate(rings[1:])
        }
        holes.append(face_holes or None)
    return categories, face_ids, normals, faces, holes


def _create_window_on_wall(face, normal, wwr, margin_ratio=0.1):
    if wwr <= 0 or abs(normal[2]) > 0.7:
        return None, None
    center = np.mean(face, axis=0)
    horizontal = face[1] - face[0]
    vertical = face[3] - face[0]
    horizontal_unit = horizontal / (np.linalg.norm(horizontal) + 1e-10)
    vertical_unit = vertical / (np.linalg.norm(vertical) + 1e-10)
    scale = np.sqrt(wwr) * (1 - 2 * margin_ratio)
    half_width = np.linalg.norm(horizontal) * scale / 2
    half_height = np.linalg.norm(vertical) * scale / 2
    window = np.array([
        center - half_width * horizontal_unit - half_height * vertical_unit,
        center + half_width * horizontal_unit - half_height * vertical_unit,
        center + half_width * horizontal_unit + half_height * vertical_unit,
        center - half_width * horizontal_unit + half_height * vertical_unit,
    ])
    return {0: window}, window


def simplify_to_layered_obb(categories, normals, faces):
    if not faces:
        raise ValueError('Boundary simplification requires non-empty geometry.')
    min_area = 1e-5
    horizontal_faces = [
        np.asarray(face, dtype=float)
        for face, normal in zip(faces, normals)
        if abs(normal[2]) > 0.7
        and len(face) >= 3
        and GeometryBasic.polygon_area_3d(face) > min_area
    ]
    if len(horizontal_faces) < 2:
        raise ValueError('Boundary simplification requires at least two horizontal levels.')

    z_centers = [float(np.mean(face[:, 2])) for face in horizontal_faces]
    z_tolerance = max(0.05, (max(z_centers) - min(z_centers)) * 0.01)
    level_groups = []
    for z_center, face in sorted(zip(z_centers, horizontal_faces), key=lambda item: item[0]):
        if not level_groups or abs(z_center - np.mean(level_groups[-1]['z_values'])) > z_tolerance:
            level_groups.append({'z_values': [z_center], 'faces': [face]})
        else:
            level_groups[-1]['z_values'].append(z_center)
            level_groups[-1]['faces'].append(face)
    levels = [float(np.mean(group['z_values'])) for group in level_groups]
    if len(levels) < 2:
        raise ValueError('Boundary simplification requires two distinct horizontal levels.')

    wall_faces = [
        np.asarray(face, dtype=float)
        for face, normal in zip(faces, normals)
        if abs(normal[2]) <= 0.7
        and len(face) >= 3
        and GeometryBasic.polygon_area_3d(face) > min_area
    ]
    if not wall_faces:
        raise ValueError('Boundary simplification requires vertical boundary faces.')

    wwr = calculate_wwr(categories, faces, normals)
    out_categories, out_ids, out_normals, out_faces, out_holes = [], [], [], [], []
    for layer_index, (bottom_z, top_z) in enumerate(zip(levels[:-1], levels[1:]), start=1):
        layer_height = top_z - bottom_z
        if layer_height <= 1e-3:
            raise ValueError(f'Boundary simplification found a degenerate layer {layer_index}.')
        layer_tolerance = max(1e-4, layer_height * 0.02)
        layer_walls = [
            wall for wall in wall_faces
            if float(np.min(wall[:, 2])) <= top_z + layer_tolerance
            and float(np.max(wall[:, 2])) >= bottom_z - layer_tolerance
        ]
        if not layer_walls:
            raise ValueError(f'Boundary simplification found no walls for layer {layer_index}.')

        vertices = np.vstack(layer_walls)
        if np.ptp(vertices[:, 0]) <= 1e-4 or np.ptp(vertices[:, 1]) <= 1e-4:
            raise ValueError(f'Boundary simplification found a degenerate layer {layer_index}.')

        obb = create_obb(vertices, (0, 0, 1))
        obb['scale'][2] = layer_height
        obb['center'][2] = bottom_z + layer_height / 2
        obb_faces, obb_normals = obb_to_face_vertices(obb)
        for face_index, (face, normal) in enumerate(zip(obb_faces, obb_normals)):
            if GeometryBasic.polygon_area_3d(face) <= min_area:
                raise ValueError(
                    f'Boundary simplification generated a degenerate layer {layer_index}.'
                )
            hole, window = _create_window_on_wall(face, normal, wwr)
            out_categories.append(0)
            out_ids.append(f'layer{layer_index}_obb_face_{face_index}')
            out_normals.append(normal)
            out_faces.append(face)
            out_holes.append(hole)
            if window is not None:
                out_categories.append(1)
                out_ids.append(f'layer{layer_index}_obb_window_{face_index}')
                out_normals.append(normal)
                out_faces.append(window)
                out_holes.append(None)

    return np.asarray(out_categories), out_ids, np.asarray(out_normals), out_faces, out_holes
