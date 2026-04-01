"""
Geometry utilities for convexification and simplification in Moosas.
"""

from collections import defaultdict
from typing import List, Tuple, Union

from scipy.spatial.transform import Rotation as R

from ..utils import np, pygeos


class GeometryBasic:
    """Basic geometry utility methods."""

    @staticmethod
    def angle(p1, p2, p3):
        """Calculate the signed angle at ``p2`` formed by ``p1-p2-p3``."""
        v1 = p2 - p1
        v2 = p3 - p2
        cross = np.cross(v1, v2)
        dot = np.dot(v1, v2)

        if np.linalg.norm(cross) < 1e-3 * np.linalg.norm(v1) * np.linalg.norm(v2):
            return 0

        angle_rad = np.arccos(np.clip(dot / (np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        return angle_deg if cross[2] > 0 else -angle_deg

    @staticmethod
    def get_angle_tan(p1, p2, verts_all):
        vec = verts_all[p2] - verts_all[p1]
        return np.arctan2(vec[1], vec[0])

    @staticmethod
    def polygon_area_2d(vertices):
        """Calculate 2D polygon area by the shoelace formula."""
        if len(vertices) < 3:
            return 0.0

        area = 0.0
        n = len(vertices)
        for i in range(n):
            x1, y1 = vertices[i][:2]
            x2, y2 = vertices[(i + 1) % n][:2]
            area += x1 * y2 - x2 * y1

        return abs(area) / 2.0

    @staticmethod
    def polygon_area_3d(vertices):
        """Calculate 3D polygon area using Newell's method."""
        if len(vertices) < 3:
            return 0.0

        v = np.asarray(vertices, dtype=float)
        normal = np.zeros(3)
        for i in range(len(v)):
            current = v[i]
            next_vertex = v[(i + 1) % len(v)]
            normal[0] += (current[1] - next_vertex[1]) * (current[2] + next_vertex[2])
            normal[1] += (current[2] - next_vertex[2]) * (current[0] + next_vertex[0])
            normal[2] += (current[0] - next_vertex[0]) * (current[1] + next_vertex[1])

        return np.linalg.norm(normal) / 2.0


class GeometryValidator:
    """Geometry validation helpers."""

    @staticmethod
    def _is_left_on(p1, p2, p3):
        p1_2d = p1[:2]
        p2_2d = p2[:2]
        p3_2d = p3[:2]
        cross = np.cross(p2_2d - p1_2d, p3_2d - p2_2d)
        if cross > 0 and np.abs(cross) < 1e-6 * np.linalg.norm(p2_2d - p1_2d) * np.linalg.norm(p3_2d - p2_2d):
            return False
        return cross > 0

    @staticmethod
    def _is_collinear(p1, p2, p3):
        area = np.cross(p2 - p1, p3 - p2)
        dist = area / (np.dot(p1, p2 - p1) + 1e-6)
        return np.abs(dist) < 1e-3

    @staticmethod
    def _is_between(p1, p2, p3):
        p1_2d = p1[:2]
        p2_2d = p2[:2]
        p3_2d = p3[:2]
        if p1_2d[0] != p2_2d[0]:
            return (p1_2d[0] <= p3_2d[0] <= p2_2d[0]) or (p1_2d[0] >= p3_2d[0] >= p2_2d[0])
        return (p1_2d[1] <= p3_2d[1] <= p2_2d[1]) or (p1_2d[1] >= p3_2d[1] >= p2_2d[1])

    @staticmethod
    def _is_intersect(a, b, c, d):
        a_2d = a[:2]
        b_2d = b[:2]
        c_2d = c[:2]
        d_2d = d[:2]
        if GeometryValidator._is_collinear(a_2d, b_2d, c_2d):
            return GeometryValidator._is_between(a_2d, b_2d, c_2d)
        if GeometryValidator._is_collinear(a_2d, b_2d, d_2d):
            return GeometryValidator._is_between(a_2d, b_2d, d_2d)
        if GeometryValidator._is_collinear(c_2d, d_2d, a_2d):
            return GeometryValidator._is_between(c_2d, d_2d, a_2d)
        if GeometryValidator._is_collinear(c_2d, d_2d, b_2d):
            return GeometryValidator._is_between(c_2d, d_2d, b_2d)
        cd_cross = np.logical_xor(
            GeometryValidator._is_left_on(a_2d, b_2d, c_2d),
            GeometryValidator._is_left_on(a_2d, b_2d, d_2d),
        )
        ab_cross = np.logical_xor(
            GeometryValidator._is_left_on(c_2d, d_2d, a_2d),
            GeometryValidator._is_left_on(c_2d, d_2d, b_2d),
        )
        return ab_cross and cd_cross

    @staticmethod
    def _is_obtuse(v1, v2, v3):
        return GeometryBasic.angle(v1, v2, v3) > 90

    @staticmethod
    def _is_valid_face(vertices, area_eps=1e-8):
        if vertices is None or len(vertices) < 3:
            return False

        v = np.asarray(vertices, dtype=float)
        if not np.isfinite(v).all():
            return False

        p0 = v[0]
        area = 0.0
        for i in range(1, len(v) - 1):
            e1 = v[i] - p0
            e2 = v[i + 1] - p0
            area += 0.5 * np.linalg.norm(np.cross(e1, e2))

        return area > area_eps

    @staticmethod
    def _is_same_polygon(polygon1, polygon2, projection=False):
        if polygon1.shape != polygon2.shape:
            return False

        if projection:
            if polygon1.shape[1] < 2 or polygon2.shape[1] < 2:
                return False
            poly1 = polygon1[:, :2]
            poly2 = polygon2[:, :2]
        else:
            poly1 = polygon1
            poly2 = polygon2

        if np.array_equal(poly1, poly2):
            return True

        if np.array_equal(poly1[0], poly2[0]) and np.array_equal(poly1[1:], poly2[1:][::-1]):
            return True

        return False

    @staticmethod
    def _is_diagonal(verts: np.ndarray, indices: np.ndarray, ia: int, ib: int) -> bool:
        def in_cone(local_verts: np.ndarray, local_indices: np.ndarray, idx_a: int, idx_b: int) -> bool:
            n = len(local_indices)
            ia_prev = idx_a - 1 if idx_a - 1 >= 0 else n - 1
            ia_next = idx_a + 1 if idx_a + 1 < n else 0

            idx_a, idx_b = local_indices[idx_a], local_indices[idx_b]
            ia_prev, ia_next = local_indices[ia_prev], local_indices[ia_next]

            if GeometryValidator._is_left_on(local_verts[ia_prev], local_verts[idx_a], local_verts[ia_next]):
                return GeometryValidator._is_left_on(local_verts[idx_a], local_verts[idx_b], local_verts[ia_prev]) and \
                    GeometryValidator._is_left_on(local_verts[idx_b], local_verts[idx_a], local_verts[ia_next])
            return not (
                GeometryValidator._is_left_on(local_verts[idx_a], local_verts[idx_b], local_verts[ia_next]) and
                GeometryValidator._is_left_on(local_verts[idx_b], local_verts[idx_a], local_verts[ia_prev])
            )

        def diagonalie(local_verts: np.ndarray, local_indices: np.ndarray, idx_a: int, idx_b: int) -> bool:
            n = len(local_indices)
            for now_i in range(n):
                if local_indices[now_i] == local_indices[idx_a] or local_indices[now_i] == local_indices[idx_b]:
                    continue
                next_i = (now_i + 1) % n
                if local_indices[next_i] == local_indices[idx_a] or local_indices[next_i] == local_indices[idx_b]:
                    continue

                if GeometryValidator._is_intersect(
                    local_verts[local_indices[idx_a]],
                    local_verts[local_indices[idx_b]],
                    local_verts[local_indices[now_i]],
                    local_verts[local_indices[next_i]],
                ):
                    return False
            return True

        return in_cone(verts, indices, ia, ib) and in_cone(verts, indices, ib, ia) and diagonalie(verts, indices, ia, ib)


class GeometryOperator:
    """Geometry transformation and polygon decomposition helpers."""

    @staticmethod
    def reorder_vertices(face, is_upward):
        face = np.asarray(face, dtype=float)
        if len(face) <= 1:
            return face

        min_index = np.argmin(np.sum(face, axis=1))
        face = np.roll(face, -min_index, axis=0)

        x = face[:, 0]
        y = face[:, 1]
        signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
        is_ccw = signed_area > 0

        if (is_upward and not is_ccw) or ((not is_upward) and is_ccw):
            face = face[::-1]

        min_index = np.argmin(np.sum(face, axis=1))
        face = np.roll(face, -min_index, axis=0)
        return face

    @staticmethod
    def compute_max_inscribed_quadrilateral(vertices):
        if len(vertices) <= 4:
            return vertices

        max_area = 0.0
        best_quad_indices = None
        for i in range(len(vertices)):
            for j in range(i + 1, len(vertices)):
                for k in range(j + 1, len(vertices)):
                    for l in range(k + 1, len(vertices)):
                        quad_vertices = [vertices[i], vertices[j], vertices[k], vertices[l]]
                        area = GeometryBasic.polygon_area_2d(quad_vertices)
                        if area > max_area:
                            max_area = area
                            best_quad_indices = [i, j, k, l]

        if best_quad_indices is not None:
            return [vertices[idx] for idx in best_quad_indices]
        return vertices

    @staticmethod
    def process_hole(hole, faces, check_projection=True):
        for other_face in faces:
            if GeometryValidator._is_same_polygon(hole, other_face):
                if not check_projection:
                    return True

                has_projection_overlap = False
                for face in faces:
                    if GeometryValidator._is_same_polygon(hole, face):
                        continue
                    if GeometryValidator._is_same_polygon(hole, face, projection=True):
                        has_projection_overlap = True
                        break

                if not has_projection_overlap:
                    return True

        return False

    @staticmethod
    def merge_holes(verts_poly: np.ndarray, verts_holes: dict[int, np.ndarray]) -> np.ndarray:
        if verts_holes is None or len(verts_holes) == 0:
            return verts_poly, []

        n_poly = len(verts_poly)
        indices_poly = list(range(n_poly))
        indices_holes = {}
        verts_all = verts_poly.copy()

        offset = n_poly
        for hole_id, verts_hole in verts_holes.items():
            n_hole = len(verts_hole)
            indices_holes[hole_id] = list(range(offset, offset + n_hole))
            verts_all = np.concatenate((verts_all, verts_hole))
            offset += n_hole

        best_diagonals = {}

        for hole_id, indices_hole in indices_holes.items():
            verts_hole = verts_holes[hole_id]
            n_hole = len(indices_hole)
            min_diagonal_length = float("inf")
            min_diagonal = None

            for hole_idx, hole_vert_idx in enumerate(indices_hole):
                hole_vertex = verts_hole[hole_idx]
                for poly_idx, poly_vertex_idx in enumerate(indices_poly):
                    poly_vertex = verts_poly[poly_idx]
                    okay = True

                    for poly_edge in range(n_poly):
                        poly_a = verts_poly[poly_edge]
                        poly_b = verts_poly[(poly_edge + 1) % n_poly]
                        if poly_idx in (poly_edge, (poly_edge + 1) % n_poly):
                            continue
                        if GeometryValidator._is_intersect(poly_vertex, hole_vertex, poly_a, poly_b):
                            okay = False
                            break

                    if not okay:
                        continue

                    for hole_edge in range(n_hole):
                        hole_a = verts_hole[hole_edge]
                        hole_b = verts_hole[(hole_edge + 1) % n_hole]
                        if hole_idx in (hole_edge, (hole_edge + 1) % n_hole):
                            continue
                        if GeometryValidator._is_intersect(poly_vertex, hole_vertex, hole_a, hole_b):
                            okay = False
                            break

                    if not okay:
                        continue

                    for other_id, other_indices in indices_holes.items():
                        if other_id == hole_id:
                            continue
                        other_verts = verts_holes[other_id]
                        for edge in range(len(other_verts)):
                            a = other_verts[edge]
                            b = other_verts[(edge + 1) % len(other_verts)]
                            if GeometryValidator._is_intersect(poly_vertex, hole_vertex, a, b):
                                okay = False
                                break
                        if not okay:
                            break

                    if okay:
                        diagonal_length = np.linalg.norm(poly_vertex - hole_vertex)
                        if diagonal_length < min_diagonal_length:
                            min_diagonal_length = diagonal_length
                            min_diagonal = (poly_vertex_idx, hole_vert_idx)

            if min_diagonal is not None:
                best_diagonals[hole_id] = min_diagonal

        diagonals = list(best_diagonals.values())
        diagonals = sorted(diagonals, key=lambda x: (x[0], -GeometryBasic.get_angle_tan(x[0], x[1], verts_all)))

        verts = []
        for idx in indices_poly:
            verts.append(verts_all[idx])

            for diagonal in diagonals:
                if diagonal[0] != idx:
                    continue

                hole_vertex = diagonal[1]
                target_hole_indices = None
                for hole_id, hole_indices in indices_holes.items():
                    if hole_vertex in hole_indices:
                        target_hole_indices = hole_indices
                        break

                if target_hole_indices:
                    start_idx = target_hole_indices.index(hole_vertex)
                    n_hole = len(target_hole_indices)
                    for i in range(n_hole + 1):
                        current_idx = target_hole_indices[(start_idx + i) % n_hole]
                        verts.append(verts_all[current_idx])
                    verts.append(verts_all[idx])

        mergelines = [np.array([verts_all[pair[0]], verts_all[pair[1]]]) for pair in diagonals]
        return np.array(verts), mergelines

    @staticmethod
    def split_poly(verts: np.ndarray, indices: np.ndarray) -> Union[List[np.ndarray], List[Tuple[int, int]]]:
        n = len(indices)
        i_concave = -1

        for ia in range(n):
            ia_prev, ia_next = (ia - 1) % n, (ia + 1) % n
            angle = GeometryBasic.angle(verts[indices[ia_prev]], verts[indices[ia]], verts[indices[ia_next]])
            if angle < 0:
                i_concave = ia
                break

        if i_concave == -1:
            return [indices], []

        i_break = -1
        min_diagonal_length = float("inf")
        for i in range(n):
            if i != i_concave and i != (i_concave + 1) % n and i != (i_concave - 1) % n:
                if GeometryValidator._is_diagonal(verts, indices, i_concave, i):
                    diagonal_length = np.linalg.norm(verts[indices[i_concave]] - verts[indices[i]])
                    if diagonal_length < min_diagonal_length:
                        i_break = i
                        min_diagonal_length = diagonal_length

        if i_break == -1:
            return [indices], []

        indices1 = []
        indices2 = []
        i_now = i_concave

        while i_now != i_break:
            indices1.append(indices[i_now])
            i_now = (i_now + 1) % n
        indices1.append(indices[i_break])

        while i_now != i_concave:
            indices2.append(indices[i_now])
            i_now = (i_now + 1) % n
        indices2.append(indices[i_concave])

        i1, diag1 = GeometryOperator.split_poly(verts, indices1)
        i2, diag2 = GeometryOperator.split_poly(verts, indices2)

        ret_diag = [[i_concave, i_break]]
        for diag in diag1:
            ret_diag.append(((diag[0] + i_concave) % n, (diag[1] + i_concave) % n))
        for diag in diag2:
            ret_diag.append(((diag[0] + i_break) % n, (diag[1] + i_break) % n))

        return i1 + i2, ret_diag

    @staticmethod
    def create_airwalls(divide_lines):
        line_groups = defaultdict(list)
        quad_faces = []
        quad_normals = []

        projected_lines = [line[:, :2] for line in divide_lines]
        z_lines = [(line[0, 2] + line[1, 2]) / 2 for line in divide_lines]

        for i in range(len(projected_lines)):
            found_group = False
            for j in range(i):
                if np.array_equal(projected_lines[i], projected_lines[j]) or np.array_equal(
                    projected_lines[i], projected_lines[j][::-1]
                ):
                    line_groups[j].append((divide_lines[i], z_lines[i]))
                    found_group = True
                    break
            if not found_group:
                line_groups[i].append((divide_lines[i], z_lines[i]))

        for group in line_groups.values():
            if len(group) < 2:
                continue

            group.sort(key=lambda x: x[1])
            for k in range(len(group) - 1):
                line1, _ = group[k]
                line2, _ = group[k + 1]

                quad = np.array([line1[0], line1[1], line2[1], line2[0]])
                quad_faces.append(quad)

                v1 = quad[1] - quad[0]
                v2 = quad[3] - quad[0]
                normal = np.cross(v1, v2)
                norm = np.linalg.norm(normal)
                if norm > 0:
                    normal = normal / norm
                quad_normals.append(normal)

        return quad_faces, quad_normals


def create_obb(points, normal, min_scale=0.1):
    """Create an oriented bounding box (OBB) for a set of points."""
    geometry = pygeos.multipoints(points)
    z_axis = np.array([0, 0, 1])
    z_r = normal

    if np.abs(z_r[0]) <= 1e-3 and np.abs(z_r[1]) <= 1e-3:
        z_r = z_axis
        min_rotated_rectangle = pygeos.minimum_rotated_rectangle(geometry)
        obb_coords = np.array(pygeos.get_coordinates(min_rotated_rectangle, include_z=True))[:-1]
        obb_coords = np.nan_to_num(obb_coords, nan=points[0, 2])
        obb_coords[:, 2] = (np.min(points[:, 2]) + np.max(points[:, 2])) / 2

        if len(obb_coords) <= 2:
            centroid = np.mean(points, axis=0)
            x_r, y_r = np.array([1, 0, 0]), np.array([0, 1, 0])
            rotation = np.array([x_r, y_r, z_r])
            rotation_matrix = R.from_matrix(rotation).as_matrix()
            l = max(np.ptp(points[:, 0]), min_scale)
            w = max(np.ptp(points[:, 1]), min_scale)
            h = max(np.ptp(points[:, 2]), min_scale)
            original_obb_centroid = centroid
        else:
            x_vec = obb_coords[1] - obb_coords[0]
            y_vec = obb_coords[3] - obb_coords[0]

            x_norm = np.linalg.norm(x_vec)
            y_norm = np.linalg.norm(y_vec)

            x_r = x_vec / x_norm if x_norm > 1e-6 else np.array([1, 0, 0])
            y_r = y_vec / y_norm if y_norm > 1e-6 else np.array([0, 1, 0])

            rotation = np.array([x_r, y_r, z_r])
            rotation_matrix = R.from_matrix(rotation).as_matrix()

            l = np.linalg.norm(obb_coords[1] - obb_coords[0])
            w = np.linalg.norm(obb_coords[3] - obb_coords[0])
            h = max(np.max(points[:, 2]) - np.min(points[:, 2]), min_scale)
            original_obb_centroid = np.mean(obb_coords, axis=0)
    else:
        x_r = np.cross(z_r, z_axis)
        y_r = np.cross(z_r, x_r)

        rotation = np.array([x_r, y_r, z_r])
        rotation_matrix = R.from_matrix(rotation).as_matrix()

        rotated_points = points.dot(rotation_matrix.T)
        l = max(np.ptp(rotated_points[:, 0]), min_scale)
        w = max(np.ptp(rotated_points[:, 1]), min_scale)
        h = max(np.ptp(rotated_points[:, 2]), min_scale)

        centroid = np.mean(
            [
                [np.min(rotated_points[:, 0]), np.min(rotated_points[:, 1]), np.min(rotated_points[:, 2])],
                [np.max(rotated_points[:, 0]), np.max(rotated_points[:, 1]), np.max(rotated_points[:, 2])],
            ],
            axis=0,
        )
        original_obb_centroid = np.dot(centroid, rotation_matrix)

    return {
        "center": original_obb_centroid,
        "scale": np.array([l, w, h]),
        "rotation": rotation_matrix,
    }


def obb_to_face_vertices(obb_params):
    """Convert OBB parameters to face vertices and normals."""
    center = obb_params["center"]
    l, w, h = obb_params["scale"]
    rotation_matrix = obb_params["rotation"]

    offsets = np.array(
        [
            [-l / 2, -w / 2, -h / 2],
            [l / 2, -w / 2, -h / 2],
            [l / 2, w / 2, -h / 2],
            [-l / 2, w / 2, -h / 2],
            [-l / 2, -w / 2, h / 2],
            [l / 2, -w / 2, h / 2],
            [l / 2, w / 2, h / 2],
            [-l / 2, w / 2, h / 2],
        ]
    )

    corners = offsets.dot(rotation_matrix) + center
    faces = [
        [corners[0], corners[1], corners[2], corners[3]],
        [corners[4], corners[7], corners[6], corners[5]],
        [corners[0], corners[4], corners[5], corners[1]],
        [corners[2], corners[6], corners[7], corners[3]],
        [corners[0], corners[3], corners[7], corners[4]],
        [corners[1], corners[5], corners[6], corners[2]],
    ]

    faces = [np.array(face) for face in faces]
    normals = []
    for face in faces:
        v1 = face[1] - face[0]
        v2 = face[3] - face[0]
        normal = np.cross(v1, v2)
        normal = np.round(normal / (np.linalg.norm(normal) + 1e-6), 3)
        normals.append(normal)

    return faces, normals


def calculate_wwr(cats, faces, normals):
    """Calculate the window-to-wall ratio."""
    total_wall_area = 0.0
    total_window_area = 0.0

    for cat, face, normal in zip(cats, faces, normals):
        area = GeometryBasic.polygon_area_3d(face)
        if area < 1e-6:
            continue

        if abs(normal[2]) < 1e-3:
            if int(cat) == 1:
                total_window_area += area
            else:
                total_wall_area += area

    if total_wall_area + total_window_area == 0:
        return 0.0

    return total_window_area / (total_wall_area + total_window_area)
