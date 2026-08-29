"""
Convexification utilities aligned with the current cuger implementation.
"""

import math

from .geos import Projection, simplify
from ...utils import np, shapely
from .polygon import GeometryBasic, GeometryOperator, GeometryValidator


def _group_horizontal_face_levels(faces, normal, min_face_area=1e-5):
    horizontal = []
    for idx, face_normal in enumerate(normal):
        if np.abs(face_normal[2]) <= 0.7:
            continue

        face = np.asarray(faces[idx], dtype=float)
        if len(face) < 3:
            continue
        if GeometryBasic.polygon_area_3d(face) <= min_face_area:
            continue

        horizontal.append((float(np.mean(face[:, 2])), idx))

    if not horizontal:
        return []

    z_values = [item[0] for item in horizontal]
    z_range = max(z_values) - min(z_values)
    z_tol = max(0.05, z_range * 0.01)

    groups = []
    for z_center, idx in sorted(horizontal, key=lambda item: item[0]):
        if not groups:
            groups.append({"z_values": [z_center], "indices": [idx]})
            continue

        current_mean = float(np.mean(groups[-1]["z_values"]))
        if abs(z_center - current_mean) <= z_tol:
            groups[-1]["z_values"].append(z_center)
            groups[-1]["indices"].append(idx)
        else:
            groups.append({"z_values": [z_center], "indices": [idx]})

    return groups


def _compute_dominant_xy_axes(faces, edge_tol=1e-6):
    orient_x = 0.0
    orient_y = 0.0

    for face in faces:
        verts = np.asarray(face, dtype=float)
        if len(verts) < 2:
            continue

        for idx in range(len(verts)):
            edge = verts[(idx + 1) % len(verts), :2] - verts[idx, :2]
            length = float(np.linalg.norm(edge))
            if length <= edge_tol:
                continue

            theta = math.atan2(edge[1], edge[0])
            orient_x += length * math.cos(4.0 * theta)
            orient_y += length * math.sin(4.0 * theta)

    if abs(orient_x) <= edge_tol and abs(orient_y) <= edge_tol:
        angle = 0.0
    else:
        angle = 0.25 * math.atan2(orient_y, orient_x)

    x_axis = np.array([math.cos(angle), math.sin(angle)], dtype=float)
    y_axis = np.array([-math.sin(angle), math.cos(angle)], dtype=float)
    return x_axis, y_axis


def _project_xy_bounds(face, x_axis, y_axis):
    verts = np.asarray(face, dtype=float)
    proj_x = verts[:, :2] @ x_axis
    proj_y = verts[:, :2] @ y_axis
    return (
        float(np.min(proj_x)),
        float(np.max(proj_x)),
        float(np.min(proj_y)),
        float(np.max(proj_y)),
    )


def _build_rect_face(center_xy, x_axis, y_axis, span_x, span_y, z_value):
    half_x = 0.5 * span_x
    half_y = 0.5 * span_y
    xy = np.array(
        [
            center_xy - half_x * x_axis - half_y * y_axis,
            center_xy + half_x * x_axis - half_y * y_axis,
            center_xy + half_x * x_axis + half_y * y_axis,
            center_xy - half_x * x_axis + half_y * y_axis,
        ],
        dtype=float,
    )

    z_column = np.full((4, 1), float(z_value), dtype=float)
    return np.hstack((xy, z_column))


def _intersect_projected_bounds(bounds):
    return (
        max(bound[0] for bound in bounds),
        min(bound[1] for bound in bounds),
        max(bound[2] for bound in bounds),
        min(bound[3] for bound in bounds),
    )


def _append_face_hole(face_holes, hole_face):
    hole_face = np.asarray(hole_face, dtype=float)
    if face_holes is None:
        return {0: hole_face}

    ordered_holes = [np.asarray(face_holes[key], dtype=float) for key in sorted(face_holes)]
    ordered_holes.append(hole_face)
    return {idx: hole for idx, hole in enumerate(ordered_holes)}


def _build_core_wall_faces(bottom_face, top_face, core_center_xy):
    wall_faces = []
    wall_normals = []

    for idx in range(len(bottom_face)):
        face = np.array(
            [
                bottom_face[idx],
                top_face[idx],
                top_face[(idx + 1) % len(top_face)],
                bottom_face[(idx + 1) % len(bottom_face)],
            ],
            dtype=float,
        )

        v1 = face[1] - face[0]
        v2 = face[3] - face[0]
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm <= 1e-8:
            continue
        normal = normal / norm

        face_center_xy = np.mean(face[:, :2], axis=0)
        outward_xy = face_center_xy - core_center_xy
        if np.dot(normal[:2], outward_xy) < 0:
            face = face[::-1]
            v1 = face[1] - face[0]
            v2 = face[3] - face[0]
            normal = np.cross(v1, v2)
            normal = normal / (np.linalg.norm(normal) + 1e-12)

        wall_faces.append(face)
        wall_normals.append(normal)

    return wall_faces, wall_normals


def inject_minimal_core(cat, idd, normal, faces, holes, core_area_ratio=0.2):
    """Inject a simple rectangular core shaft for simplified low/medium LOD inputs."""
    level_groups = _group_horizontal_face_levels(faces, normal)
    if len(level_groups) < 2:
        print("--Minimal core skipped: insufficient horizontal levels--")
        return cat, idd, normal, faces, holes

    x_axis, y_axis = _compute_dominant_xy_axes(faces)

    reference_area = 0.0
    level_info = []
    for group in level_groups:
        group_bounds = [_project_xy_bounds(faces[idx], x_axis, y_axis) for idx in group["indices"]]
        common_bounds = _intersect_projected_bounds(group_bounds)
        level_area = max(GeometryBasic.polygon_area_3d(faces[idx]) for idx in group["indices"])
        reference_area = max(reference_area, level_area)
        level_info.append(
            {
                "z": float(np.mean(group["z_values"])),
                "indices": list(group["indices"]),
                "bounds": common_bounds,
            }
        )

    if reference_area <= 1e-6:
        print("--Minimal core skipped: invalid horizontal reference area--")
        return cat, idd, normal, faces, holes

    target_area = reference_area * float(core_area_ratio)
    best_range = None
    best_bounds = None
    best_available_area = -1.0
    best_story_count = -1

    for start in range(len(level_info) - 1):
        for end in range(start + 1, len(level_info)):
            candidate_bounds = _intersect_projected_bounds(
                [level["bounds"] for level in level_info[start : end + 1]]
            )
            span_x = candidate_bounds[1] - candidate_bounds[0]
            span_y = candidate_bounds[3] - candidate_bounds[2]
            if span_x <= 1e-6 or span_y <= 1e-6:
                continue

            available_area = span_x * span_y * 0.81
            story_count = end - start
            if story_count > best_story_count or (
                story_count == best_story_count and available_area > best_available_area
            ):
                best_range = (start, end)
                best_bounds = candidate_bounds
                best_available_area = available_area
                best_story_count = story_count

    if best_range is None or best_bounds is None or best_available_area <= 1e-6:
        print("--Minimal core skipped: no shared footprint for any story stack--")
        return cat, idd, normal, faces, holes

    rect_area = min(target_area, best_available_area)
    if rect_area <= 1e-6:
        print("--Minimal core skipped: target core area too small--")
        return cat, idd, normal, faces, holes

    common_min_x, common_max_x, common_min_y, common_max_y = best_bounds
    common_span_x = common_max_x - common_min_x
    common_span_y = common_max_y - common_min_y

    aspect_ratio = max(common_span_x / max(common_span_y, 1e-8), 1e-8)
    rect_span_x = math.sqrt(rect_area * aspect_ratio)
    rect_span_y = rect_area / max(rect_span_x, 1e-8)

    scale = min(
        1.0,
        (common_span_x * 0.9) / max(rect_span_x, 1e-8),
        (common_span_y * 0.9) / max(rect_span_y, 1e-8),
    )
    rect_span_x *= scale
    rect_span_y *= scale

    center_xy = np.array(
        [
            0.5 * (common_min_x + common_max_x),
            0.5 * (common_min_y + common_max_y),
        ],
        dtype=float,
    )

    core_cat = list(cat)
    core_idd = list(idd)
    core_normal = [np.asarray(n, dtype=float) for n in normal]
    core_faces = [np.asarray(face, dtype=float) for face in faces]
    core_holes = list(holes)

    selected_levels = level_info[best_range[0] : best_range[1] + 1]
    selected_indices = [idx for level in selected_levels for idx in level["indices"]]

    for idx in selected_indices:
        z_value = float(np.mean(core_faces[idx][:, 2]))
        hole_face = _build_rect_face(center_xy, x_axis, y_axis, rect_span_x, rect_span_y, z_value)
        core_holes[idx] = _append_face_hole(core_holes[idx], hole_face)

    level_z = [level["z"] for level in selected_levels]
    for story_idx in range(len(level_z) - 1):
        bottom_z = level_z[story_idx]
        top_z = level_z[story_idx + 1]
        if top_z - bottom_z <= 1e-6:
            continue

        bottom_face = _build_rect_face(center_xy, x_axis, y_axis, rect_span_x, rect_span_y, bottom_z)
        top_face = _build_rect_face(center_xy, x_axis, y_axis, rect_span_x, rect_span_y, top_z)
        wall_faces, wall_normals = _build_core_wall_faces(bottom_face, top_face, center_xy)
        story_label = best_range[0] + story_idx + 1

        for wall_idx, wall_face in enumerate(wall_faces):
            core_cat.append("2")
            core_idd.append(f"core_wall_{story_label}_{wall_idx}")
            core_normal.append(np.asarray(wall_normals[wall_idx], dtype=float))
            core_faces.append(wall_face)
            core_holes.append(None)

    print(
        f"--Minimal core inserted across {max(len(level_z) - 1, 0)} layers "
        f"(levels {best_range[0] + 1}-{best_range[1] + 1})--"
    )
    return (
        np.asarray(core_cat),
        core_idd,
        np.asarray(core_normal),
        core_faces,
        core_holes,
    )


def convexify_faces(cat, idd, normal, faces, holes, valid_face=True, clean_quad=False):
    """Convexify polygonal faces and generate quadrilateral air-wall patches."""
    convex_cat = []
    convex_idd = []
    convex_normal = []
    convex_faces = []
    divide_lines = []

    for idx in range(len(faces)):
        if np.abs(normal[idx][2]) > 1e-3:
            faces[idx] = GeometryOperator.reorder_vertices(faces[idx], is_upward=True)
            if holes[idx]:
                for i in range(len(holes[idx])):
                    holes[idx][i] = GeometryOperator.reorder_vertices(holes[idx][i], is_upward=False)

    print("--Faces reordering done--")

    for idx, face in enumerate(faces):
        if valid_face and not GeometryValidator._is_valid_face(face):
            print(f"    Skipping invalid face {idd[idx]}")
            continue

        if np.abs(normal[idx][2]) > 1e-3:
            poly_ex = face

            poly_in = {}
            if holes[idx]:
                for i in range(len(holes[idx])):
                    hole = holes[idx][i]
                    should_skip = GeometryOperator.process_hole(hole, faces, check_projection=True)
                    if should_skip:
                        continue
                    poly_in[i] = hole

                verts, mergelines = GeometryOperator.merge_holes(poly_ex, poly_in)
                if mergelines:
                    divide_lines.extend(mergelines)
            else:
                verts = poly_ex

            indices = list(range(len(verts)))
            polys, diags = GeometryOperator.split_poly(verts, indices)

            subfaces = []
            for poly in polys:
                candidate_face = verts[poly]

                if valid_face and not GeometryValidator._is_valid_face(candidate_face):
                    print(f"    Skipping invalid sub-face in face {idd[idx]}")
                    continue

                if clean_quad and len(poly) > 4:
                    quad_poly = GeometryOperator.compute_max_inscribed_quadrilateral(candidate_face)
                    if valid_face and not GeometryValidator._is_valid_face(quad_poly):
                        print(f"    Skipping invalid quadrilateral sub-face in face {idd[idx]}")
                        continue
                    candidate_face = np.array(quad_poly)

                subfaces.append(candidate_face)

            if len(subfaces) == 1:
                for subface in subfaces:
                    convex_cat.append(cat[idx])
                    convex_idd.append(idd[idx])
                    convex_normal.append(normal[idx])
                    convex_faces.append(subface)
            else:
                for i, subface in enumerate(subfaces):
                    convex_cat.append(cat[idx])
                    convex_idd.append(f"#{idd[idx]}_{i}")
                    convex_normal.append(normal[idx])
                    convex_faces.append(subface)

                if diags:
                    sublines = [np.array([verts[pair[0]], verts[pair[1]]]) for pair in diags]
                    divide_lines.extend(sublines)
        else:
            convex_cat.append(cat[idx])
            convex_idd.append(idd[idx])
            convex_normal.append(normal[idx])
            convex_faces.append(face)

    print("--Faces splitting done--")

    quad_faces, quad_normals = GeometryOperator.create_airwalls(divide_lines)
    for i, face in enumerate(quad_faces):
        convex_cat.append("2")
        convex_idd.append(f"a_{i}")
        convex_normal.append(quad_normals[i])
        convex_faces.append(face)

    return convex_cat, convex_idd, convex_normal, convex_faces, divide_lines


class GeometryConvexifier:
    """Convexification operations for polygonal building geometry."""

    @staticmethod
    def convexify_faces(cat, idd, normal, faces, holes, is_valid_face=True, is_quad_clean=False):
        return convexify_faces(
            cat,
            idd,
            normal,
            faces,
            holes,
            valid_face=is_valid_face,
            clean_quad=is_quad_clean,
        )

    @staticmethod
    def convexify_faces_2d(faces, holes, is_valid_face=True, is_quad_clean=False):
        convex_faces = []
        divide_lines = []

        for idx, face in enumerate(faces):
            face = GeometryOperator.reorder_vertices(face, is_upward=True)
            hole_dict = {}

            if holes[idx]:
                for i, hole in enumerate(holes[idx]):
                    hole = GeometryOperator.reorder_vertices(hole, is_upward=False)
                    should_skip = GeometryOperator.process_hole(hole, faces, check_projection=True)
                    if should_skip:
                        continue
                    hole_dict[i] = hole

            if hole_dict:
                verts, mergelines = GeometryOperator.merge_holes(face, hole_dict)
                if mergelines:
                    divide_lines.extend(mergelines)
            else:
                verts = face

            indices = list(range(len(verts)))
            polys, diags = GeometryOperator.split_poly(verts, indices)

            for poly in polys:
                candidate_face = verts[poly]
                if is_valid_face and not GeometryValidator._is_valid_face(candidate_face):
                    continue

                if is_quad_clean and len(poly) > 4:
                    quad_poly = GeometryOperator.compute_max_inscribed_quadrilateral(candidate_face)
                    if is_valid_face and not GeometryValidator._is_valid_face(quad_poly):
                        continue
                    candidate_face = np.array(quad_poly)

                convex_faces.append(candidate_face)

            if diags:
                divide_lines.extend([np.array([verts[pair[0]], verts[pair[1]]]) for pair in diags])

        return convex_faces, divide_lines


def triangulate2dFace(boundary: shapely.Geometry, holes: np.ndarray[shapely.Geometry] = None):
    """Triangulate a 2D face with optional holes into convex faces and divide lines."""
    boundary = shapely.polygons(shapely.get_coordinates(shapely.force_3d(boundary, z=0), include_z=True))
    proj = Projection.fromPolygon(boundary)
    boundary = proj.toUV(boundary)
    boundary = simplify(boundary, include_z=True)
    boundary = shapely.get_coordinates(shapely.force_3d(boundary, z=0), include_z=True)[:-1]

    if holes is None:
        holes = []
    else:
        holes = [proj.toUV(hole) for hole in holes]
        holes = [shapely.get_coordinates(shapely.force_3d(hole, z=0), include_z=True)[:-1] for hole in holes]

    convex_faces, divided_lines = GeometryConvexifier.convexify_faces_2d(
        [boundary],
        [holes],
        is_quad_clean=False,
    )
    convex_faces = [shapely.polygons(convex_face) for convex_face in convex_faces]
    convex_faces = [proj.toWorld(convex_face) for convex_face in convex_faces]
    divided_lines = [proj.toWorld(shapely.linestrings(line)) for line in divided_lines]
    return convex_faces, divided_lines
