"""Minimal building-core insertion for boundary preparation."""

import math

from ...utils import np, shapely
from .polygon import GeometryBasic


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
    """Return the face holes with one independent ring appended."""
    if not face_holes:
        return {0: np.asarray(hole_face, dtype=float)}
    if isinstance(face_holes, dict):
        rings = [face_holes[index] for index in sorted(face_holes)]
    else:
        rings = list(face_holes)
    rings.append(np.asarray(hole_face, dtype=float))
    return {index: ring for index, ring in enumerate(rings)}


def _face_polygon_xy(face, holes):
    """Build a 2-D polygon for strict core containment checks."""
    shell = np.asarray(face, dtype=float)[:, :2]
    if not holes:
        return shapely.polygons(shell)
    if isinstance(holes, dict):
        rings = [holes[index] for index in sorted(holes)]
    else:
        rings = list(holes)
    return shapely.polygons(shell, holes=[np.asarray(ring, dtype=float)[:, :2] for ring in rings])


def _shared_level_footprint(levels, faces, holes):
    """Return the area shared by one primary horizontal face on every level."""
    shared = None
    for level in levels:
        level_faces = [
            _face_polygon_xy(faces[index], holes[index]) for index in level["indices"]
        ]
        footprint = max(
            level_faces,
            key=shapely.area,
        )
        shared = footprint if shared is None else shapely.intersection(shared, footprint)
    parts = [part for part in shapely.get_parts(shared) if shapely.area(part) > 1e-6]
    if not parts:
        raise ValueError("Core insertion found no horizontal area shared by all selected levels.")
    return max(parts, key=shapely.area)


def _fit_core_rectangle(footprint, x_axis, y_axis, span_x, span_y):
    """Place and scale the oriented core rectangle strictly inside a footprint."""
    radius_line = shapely.maximum_inscribed_circle(footprint, tolerance=1e-4)
    center_xy = shapely.get_coordinates(radius_line)[0]

    def candidate(scale):
        return _build_rect_face(center_xy, x_axis, y_axis, span_x * scale, span_y * scale, 0.0)

    if shapely.contains_properly(footprint, shapely.polygons(candidate(1.0)[:, :2])):
        return center_xy, span_x, span_y

    lower = 0.0
    upper = 1.0
    for _ in range(50):
        scale = 0.5 * (lower + upper)
        rectangle = shapely.polygons(candidate(scale)[:, :2])
        if shapely.contains_properly(footprint, rectangle):
            lower = scale
        else:
            upper = scale
    if lower * lower * span_x * span_y <= 1e-6:
        raise ValueError("Core insertion could not fit a rectangular core inside the shared footprint.")
    strict_scale = lower * 0.999
    return center_xy, span_x * strict_scale, span_y * strict_scale


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
    """Cut a core opening from each slab and insert one closed core per story."""
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

    selected_levels = level_info[best_range[0] : best_range[1] + 1]
    shared_footprint = _shared_level_footprint(selected_levels, faces, holes)
    center_xy, rect_span_x, rect_span_y = _fit_core_rectangle(
        shared_footprint,
        x_axis,
        y_axis,
        rect_span_x,
        rect_span_y,
    )

    core_cat = list(cat)
    core_idd = list(idd)
    core_normal = [np.asarray(n, dtype=float) for n in normal]
    core_faces = [np.asarray(face, dtype=float) for face in faces]
    core_holes = list(holes)

    level_z = [level["z"] for level in selected_levels]

    for level_idx, level in enumerate(selected_levels):
        core_face = _build_rect_face(
            center_xy,
            x_axis,
            y_axis,
            rect_span_x,
            rect_span_y,
            level["z"],
        )
        core_polygon = shapely.polygons(core_face[:, :2])
        parent_indices = [
            face_idx
            for face_idx in level["indices"]
            if shapely.contains(
                _face_polygon_xy(core_faces[face_idx], core_holes[face_idx]),
                core_polygon,
            )
        ]
        if not parent_indices:
            raise ValueError(
                "Core plane must lie strictly inside a horizontal face at "
                f"z={level['z']:.6g}."
            )

        for parent_order, parent_idx in enumerate(parent_indices):
            core_holes[parent_idx] = _append_face_hole(core_holes[parent_idx], core_face)
            oriented_core_face = core_face
            if core_normal[parent_idx][2] < 0:
                oriented_core_face = core_face[::-1]
            core_cat.append(core_cat[parent_idx])
            core_idd.append(
                f"core_face_{best_range[0] + level_idx + 1}_{parent_order}"
            )
            core_normal.append(np.asarray(core_normal[parent_idx], dtype=float))
            core_faces.append(oriented_core_face)
            core_holes.append(None)

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
            core_cat.append("0")
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



