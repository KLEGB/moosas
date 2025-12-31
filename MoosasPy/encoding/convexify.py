from typing import Union, List, Tuple
from ..utils import pygeos,np
from ..geometry.geos import Projection,simplify
class BasicOptions:
    @staticmethod
    def left_on(p1, p2, p3):
        """Determine if point p3 is to the left of the line formed by points p1 and p2 in 2D space.
        
            Parameters
            ----------
            p1 : array-like, shape (N,) or (2,)
                First point in N-dimensional space; only the first two coordinates are used.
            p2 : array-like, shape (N,) or (2,)
                Second point in N-dimensional space; only the first two coordinates are used.
            p3 : array-like, shape (N,) or (2,)
                Third point in N-dimensional space; only the first two coordinates are used.
        
            Returns
            -------
            bool
                True if p3 is strictly to the left of the directed line from p1 to p2,
                False otherwise (including collinear or right-side cases).
        """

        p1_2d = p1[:2]
        p2_2d = p2[:2]
        p3_2d = p3[:2]
        cross = np.cross(p2_2d - p1_2d, p3_2d - p2_2d)
        if cross > 0 and np.abs(cross) < 1e-6 * np.linalg.norm(p2_2d - p1_2d) * np.linalg.norm(p3_2d - p2_2d):
            return False
        return cross > 0
    
    @staticmethod
    def angle(p1, p2, p3):
        """
        Calculate the signed angle in degrees between three points in 2D or 3D space.
        
        Parameters
        ----------
        p1 : array_like
            First point (tail of the first vector).
        p2 : array_like
            Second point (vertex of the angle, shared by both vectors).
        p3 : array_like
            Third point (tip of the second vector).
        
        Returns
        -------
        float
            The signed angle in degrees between the vectors (p2 - p1) and (p3 - p2). 
            Positive if the rotation from v1 to v2 is counterclockwise (right-hand rule), 
            negative if clockwise. Returns 0 if the vectors are colinear or nearly so.
        """
        v1 = p2 - p1
        v2 = p3 - p2
        if len(v1) == 2: v1 = np.append(v1, 0)
        if len(v2) == 2: v2 = np.append(v2, 0)
        cross = np.cross(v1, v2)
        dot = np.dot(v1, v2)
        
        if np.linalg.norm(cross) < 1e-3 * np.linalg.norm(v1) * np.linalg.norm(v2):
            return 0  
        
        angle_rad = np.arccos(np.clip(dot/(np.linalg.norm(v1) * np.linalg.norm(v2)), -1.0, 1.0))
        angle_deg = np.degrees(angle_rad)
        
        if np.isscalar(cross):
            return angle_deg if cross > 0 else -angle_deg
        else:
            return angle_deg if cross[2] > 0 else -angle_deg

    @staticmethod
    def get_angle_tan(p1, p2, verts_all):
        """
        Calculate the angle of the vector between two points using arctangent.
        
        Parameters
        ----------
        p1 : int
            Index of the first point in verts_all.
        p2 : int
            Index of the second point in verts_all.
        verts_all : numpy.ndarray
            Array of vertex coordinates, where each vertex is a row with at least 2D coordinates.
        
        Returns
        -------
        float
            The angle in radians between the vector from p1 to p2 and the positive x-axis.
        """
        vec = verts_all[p2] - verts_all[p1]
        return np.arctan2(vec[1], vec[0])
    
    @staticmethod
    def is_obtuse(v1, v2, v3):
        """Check if the angle formed by three points is obtuse.
        
        Parameters
        ----------
        v1 : array-like
            First point in space.
        v2 : array-like
            Second point (vertex of the angle).
        v3 : array-like
            Third point in space.
        
        Returns
        -------
        bool
            True if the angle at v2 formed by v1, v2, and v3 is greater than 90 degrees, False otherwise.
        """
        return BasicOptions.angle(v1, v2, v3) > 90

    @staticmethod
    def collinear(p1, p2, p3):
        """
        Check if three points are approximately collinear.
        
        Parameters
        ----------
        p1 : numpy.ndarray
            First point in 2D or 3D space.
        p2 : numpy.ndarray
            Second point in 2D or 3D space.
        p3 : numpy.ndarray
            Third point in 2D or 3D space.
        
        Returns
        -------
        bool
            True if the points are approximately collinear, False otherwise.
        """
        area = np.cross(p2 - p1, p3 - p2)
        dist = area / (np.dot(p1, p2 - p1) + 1e-6)
        return np.abs(dist) < 1e-3

    @staticmethod
    def between(p1, p2, p3):
        """
        Check if point p3 lies between points p1 and p2 along one axis in 2D space.
        
        Parameters
        ----------
        p1 : array-like
            First 2D point, represented as a sequence of at least two coordinates (x, y).
        p2 : array-like
            Second 2D point, represented as a sequence of at least two coordinates (x, y).
        p3 : array-like
            Query 2D point, represented as a sequence of at least two coordinates (x, y).
        
        Returns
        -------
        bool
            True if p3 lies between p1 and p2 along the x-axis (if x differs) or y-axis (if x is same), False otherwise.
        """

        p1_2d = p1[:2]
        p2_2d = p2[:2]
        p3_2d = p3[:2]
        if p1_2d[0] != p2_2d[0]:
            return (p1_2d[0] <= p3_2d[0] <= p2_2d[0]) or (p1_2d[0] >= p3_2d[0] >= p2_2d[0])
        else:
            return (p1_2d[1] <= p3_2d[1] <= p2_2d[1]) or (p1_2d[1] >= p3_2d[1] >= p2_2d[1])

    @staticmethod
    def intersect(a, b, c, d):
        """
        Determine if two line segments intersect in 2D space.
        
        Parameters
        ----------
        a : array-like
            The first endpoint of the first line segment, as a 2D point (x, y).
        b : array-like
            The second endpoint of the first line segment, as a 2D point (x, y).
        c : array-like
            The first endpoint of the second line segment, as a 2D point (x, y).
        d : array-like
            The second endpoint of the second line segment, as a 2D point (x, y).
        
        Returns
        -------
        bool
            True if the two line segments intersect, False otherwise.
        """

        a_2d = a[:2]
        b_2d = b[:2]
        c_2d = c[:2]
        d_2d = d[:2]
        if BasicOptions.collinear(a_2d, b_2d, c_2d):
            return BasicOptions.between(a_2d, b_2d, c_2d)
        if BasicOptions.collinear(a_2d, b_2d, d_2d):
            return BasicOptions.between(a_2d, b_2d, d_2d)
        if BasicOptions.collinear(c_2d, d_2d, a_2d):
            return BasicOptions.between(c_2d, d_2d, a_2d)
        if BasicOptions.collinear(c_2d, d_2d, b_2d):
            return BasicOptions.between(c_2d, d_2d, b_2d)
        cd_cross = np.logical_xor(BasicOptions.left_on(a_2d, b_2d, c_2d), BasicOptions.left_on(a_2d, b_2d, d_2d))
        ab_cross = np.logical_xor(BasicOptions.left_on(c_2d, d_2d, a_2d), BasicOptions.left_on(c_2d, d_2d, b_2d))
        return ab_cross and cd_cross
        
    @staticmethod
    def diagonal(verts: np.ndarray, indices: np.ndarray, ia: int, ib: int) -> bool:
        """
        Check if the line segment between two vertices is a valid diagonal in a polygon.
        
        Parameters
        ----------
        verts : numpy.ndarray
            Array of vertex coordinates, where each row represents a point in 2D space.
        indices : numpy.ndarray
            Array of indices defining the order of vertices in the polygon.
        ia : int
            Index of the first vertex in the diagonal.
        ib : int
            Index of the second vertex in the diagonal.
        
        Returns
        -------
        bool
            True if the segment between verts[ia] and verts[ib] is a valid diagonal; False otherwise.
        """
        def in_cone(verts: np.ndarray, indices: np.ndarray, ia: int, ib: int) -> bool:
            """
            Check whether a given edge is inside the cone formed by a vertex and its neighbors.
            
            Parameters
            ----------
            verts : numpy.ndarray
                Array of vertex coordinates, where each vertex is represented by its coordinates.
            indices : numpy.ndarray
                Array of indices referencing vertices in `verts`, representing a polygon or cycle.
            ia : int
                Index into `indices` for the central vertex of the cone.
            ib : int
                Index into `indices` for the vertex to check if it lies within the cone.
            
            Returns
            -------
            bool
                True if the vertex `ib` lies within the cone defined by `ia` and its adjacent vertices; False otherwise.
            """
            # Check whether (ia, ib) is in cone of (ia-, ia, ia+)
            n = len(indices)
            ia_prev = ia - 1 if ia - 1 >= 0 else n - 1
            ia_next = ia + 1 if ia + 1 < n else 0

            # turn index of `indices` to index of `verts`
            ia, ib = indices[ia], indices[ib]
            ia_prev, ia_next = indices[ia_prev], indices[ia_next]

            # Convex
            if BasicOptions.left_on(verts[ia_prev], verts[ia], verts[ia_next]):
                return BasicOptions.left_on(verts[ia], verts[ib], verts[ia_prev]) and \
                    BasicOptions.left_on(verts[ib], verts[ia], verts[ia_next])
            # Concave
            return not (BasicOptions.left_on(verts[ia], verts[ib], verts[ia_next]) and \
                        BasicOptions.left_on(verts[ib], verts[ia], verts[ia_prev]))

            
        def diagonalie(verts: np.ndarray, indices: np.ndarray, ia: int, ib: int) -> bool:
            """Check if a diagonal between two vertices lies strictly inside a polygon.
            
                Parameters
                ----------
                verts : np.ndarray
                    Array of shape (N, 2) representing the coordinates of the polygon's vertices.
                indices : np.ndarray
                    Array of integers representing the indices of vertices forming the polygon boundary.
                ia : int
                    Index into `verts` array for the first endpoint of the diagonal.
                ib : int
                    Index into `verts` array for the second endpoint of the diagonal.
            
                Returns
                -------
                bool
                    True if the diagonal between vertices `ia` and `ib` does not intersect any edge of the polygon 
                    (except at endpoints) and lies entirely within the polygon; False otherwise.
            """
            n = len(indices)
            for now_i in range(n):
                # exclude edges contains point a and point b
                if indices[now_i] == indices[ia] or indices[now_i] == indices[ib]:
                    continue
                next_i = (now_i + 1) % n
                if indices[next_i] == indices[ia] or indices[next_i] == indices[ib]:
                    continue

                if BasicOptions.intersect(
                        verts[indices[ia]], verts[indices[ib]],
                        verts[indices[now_i]], verts[indices[next_i]]
                ):
                    return False
            return True
    
        return  in_cone(verts, indices, ia, ib) and \
                in_cone(verts, indices, ib, ia) and \
                diagonalie(verts, indices, ia, ib)

class Geometry_Option:
    @staticmethod
    def reorder_vertices(face, is_upward):
        """
        Re-order vertices of a face to make the normal face upward or downward.
        
        Parameters
        ----------
        face : numpy.ndarray
            Array of shape (n, 3) representing the sequence of vertices of a face.
        is_upward : bool
            If True, reorders vertices so that the face normal points upward;
            if False, reorders for downward normal.
        
        Returns
        -------
        reordered_face : numpy.ndarray
            Array of shape (n, 3) with vertices reordered according to the specified normal direction.
        """
        """Re-order vertices of a face to make the normal face upward or downward.
        
        Args:
            face: numpy array, shape=(n, 3), sequence of vertices of a face
            is_upward: bool，True for upward, False for downward
        
        Returns:
            reordered_face: numpy array, shape=(n, 3)
        """
        # calculate the sum of x, y, z of each vertex
        sum_xyz = np.sum(face, axis=1)
        min_index = np.argmin(sum_xyz)
        
        # reorder the vertices based on the minimum index
        if is_upward:
            face = np.roll(face, -min_index, axis=0)
        else:
            face = np.roll(face, -min_index + face.shape[0] - 1, axis=0)[::-1]
            
        return face

    @staticmethod
    def is_same_polygon(polygon1, polygon2, projection=False):
        """
        Check if two polygons are the same, with support for 2D projection or 3D coordinates.
        
        Parameters
        ----------
        polygon1 : numpy.ndarray
            A numpy array of shape (n, 2) or (n, 3) representing the first polygon.
        polygon2 : numpy.ndarray
            A numpy array of the same shape as polygon1 representing the second polygon.
        projection : bool
            If True, only the first two columns (x, y) are compared (projection on xoy plane).
        
        Returns
        -------
        bool
            True if the polygons are the same, considering point order and reverse order (with fixed first point), otherwise False.
        """
        """
        Determine if two polygons are the same, supporting 2D projection or 3D coordinates.
        Allows different vertex orders, but the first point is fixed and other points can be in reverse order.

        Args:
            polygon1: numpy array, shape (n, 2) or (n, 3)
            polygon2: numpy array, shape must be consistent with polygon1
            projection: bool, if True only compare the first two columns (xoy projection)

        Returns:
            bool: whether the polygons are the same
        """
        # Ensure polygon vertex counts are the same
        if polygon1.shape != polygon2.shape:
            return False

        # Extract coordinates to compare
        if projection:
            # Ensure at least two coordinates
            if polygon1.shape[1] < 2 or polygon2.shape[1] < 2:
                return False
            poly1 = polygon1[:, :2]
            poly2 = polygon2[:, :2]
        else:
            poly1 = polygon1
            poly2 = polygon2

        # Directly identical
        if np.array_equal(poly1, poly2):
            return True

        # First point is the same, other points in reverse order
        if np.array_equal(poly1[0], poly2[0]) and np.array_equal(poly1[1:], poly2[1:][::-1]):
            return True

        return False
    
    def is_valid_face(vertices, area_eps=1e-8):
        """
        Check whether a 3D polygon face is geometrically valid.

        Parameters
        ----------
        vertices : list or np.ndarray, shape (N, 3)
            Vertices of the polygon.
        area_eps : float
            Area threshold below which the face is considered degenerate.

        Returns
        -------
        bool
            True if face is valid, False otherwise.
        """

        # 1. Vertex count
        if vertices is None or len(vertices) < 3:
            return False

        v = np.asarray(vertices, dtype=float)

        # 2. Finite check
        if not np.isfinite(v).all():
            return False

        # 3. Area check (fan triangulation)
        p0 = v[0]
        area = 0.0

        for i in range(1, len(v) - 1):
            e1 = v[i]     - p0
            e2 = v[i + 1] - p0
            area += 0.5 * np.linalg.norm(np.cross(e1, e2))

        if area <= area_eps:
            return False

        return True

    
    @staticmethod
    def process_hole(hole, faces, check_projection=True):
        """
        Process a hole to determine if it should be skipped based on geometric conditions.
        
        Parameters
        ----------
        hole : numpy.ndarray
            A 2D array of shape (n, 3) representing the 3D coordinates of the hole polygon.
        faces : list of numpy.ndarray
            A list of 2D arrays, each representing a 3D face polygon with shape (m, 3).
        check_projection : bool, optional
            If True, checks whether the projection of the hole overlaps with projections of other faces.
            Default is True.
        
        Returns
        -------
        bool
            True if the hole should be skipped (i.e., it fully coincides with a face and meets projection criteria),
            False otherwise.
        """
        """
        Logic to process a hole and determine if it should be skipped.

        Conditions:
        1. Hole completely coincides with a face in 3D
        2. If check_projection is True, additionally check if projection does not overlap with other faces

        Args:
            hole: numpy array, shape (n, 3)
            faces: list[numpy array], all face data
            check_projection: whether to check projection overlap

        Returns:
            bool: whether to skip this hole
        """
        for other_face in faces:
            # 1. Check for complete 3D coincidence
            if Geometry_Option.is_same_polygon(hole, other_face):
                if not check_projection:
                    return True  # Skip directly
                
                # 2. Check if projection overlaps with other faces (excluding itself)
                has_projection_overlap = False
                for face in faces:
                    if Geometry_Option.is_same_polygon(hole, face):
                        continue  # Skip itself
                    
                    # Check if projections are the same (allowing reverse order)
                    if Geometry_Option.is_same_polygon(hole, face, projection=True):
                        has_projection_overlap = True
                        break
                
                # If no other face projection overlaps, skip this hole
                if not has_projection_overlap:
                    return True
        
        return False
    
    @staticmethod
    def merge_holes(verts_poly: np.ndarray, verts_holes: dict[int, np.ndarray]) -> np.ndarray:
        """
        Merge holes into a polygon by finding the shortest valid connection lines.
        
        Parameters
        ----------
        verts_poly : np.ndarray
            Array of vertices representing the outer polygon boundary.
        verts_holes : dict[int, np.ndarray]
            Dictionary mapping hole indices to their respective vertex arrays; each key is an integer 
            identifying a hole, and the corresponding value is a NumPy array of its vertices.
        
        Returns
        -------
        tuple[np.ndarray, list[np.ndarray]]
            A tuple containing:
            - indices_all: Array of merged vertices including both polygon and hole vertices in traversal order.
            - diagonals: List of connection line segments represented as arrays of two points, 
              each connecting a polygon vertex to a hole vertex.
        """
        """
        Find the shortest valid connection line for each hole.
        
        Args:
            verts_poly: outer polygon vertex coordinates
            verts_holes: dictionary of hole vertex coordinates, key is hole index
        
        Returns:
            tuple: (indices_all, diagonals)
                - indices_all: list of all vertex indices
                - diagonals: list of connection lines, each element is (hole_vertex_idx, poly_vertex_idx)
        """
        if verts_holes is None or len(verts_holes) == 0:
            return verts_poly, []
        
        n_poly = len(verts_poly)  # Number of outer polygon vertices
        indices_poly = list(range(n_poly))
        indices_holes = {}
        verts_all = verts_poly.copy()
        indices_all = indices_poly.copy()

        # Calculate vertex indices for all holes
        offset = n_poly
        for hole_id, verts_hole in verts_holes.items():
            n_hole = len(verts_hole)
            indices_holes[hole_id] = list(range(offset, offset + n_hole))
            verts_all = np.concatenate((verts_all, verts_hole))
            indices_all.extend(range(offset, offset + n_hole))
            offset += n_hole

        best_diagonals = {}  # Store the best connection for each hole

        # Iterate through each hole
        for hole_id, indices_hole in indices_holes.items():
            verts_hole = verts_holes[hole_id]
            n_hole = len(indices_hole)
            min_diagonal_length = float('inf')
            min_diagonal = None

            # Iterate through all vertices of current hole
            for hole_idx, hole_vert_idx in enumerate(indices_hole):
                hole_vertex = verts_hole[hole_idx]  # Use hole_idx instead of hole_vert_idx
                # Check connection with outer polygon vertices
                for poly_idx, poly_vertex_idx in enumerate(indices_poly):
                    poly_vertex = verts_poly[poly_idx]
                    okay = True
                    
                    # Check intersection with outer polygon edges
                    for poly_edge in range(n_poly):
                        poly_a = verts_poly[poly_edge]
                        poly_b = verts_poly[(poly_edge + 1) % n_poly]
                        if poly_idx in (poly_edge, (poly_edge + 1) % n_poly):
                            continue
                        if BasicOptions.intersect(poly_vertex, hole_vertex, poly_a, poly_b):
                            okay = False
                            break
                    
                    if not okay:
                        continue
                        
                    # Check intersection with current hole edges
                    for hole_edge in range(n_hole):
                        hole_a = verts_hole[hole_edge]
                        hole_b = verts_hole[(hole_edge + 1) % n_hole]
                        if hole_idx in (hole_edge, (hole_edge + 1) % n_hole):
                            continue
                        if BasicOptions.intersect(poly_vertex, hole_vertex, hole_a, hole_b):
                            okay = False
                            break
                    
                    if not okay:
                        continue
                        
                    # Check intersection with other holes
                    for other_id, other_indices in indices_holes.items():
                        if other_id == hole_id:
                            continue
                        other_verts = verts_holes[other_id]
                        for edge in range(len(other_verts)):
                            a = other_verts[edge]
                            b = other_verts[(edge + 1) % len(other_verts)]
                            if BasicOptions.intersect(poly_vertex, hole_vertex, a, b):
                                okay = False
                                break
                        if not okay:
                            break
                    
                    if okay:
                        # Calculate diagonal length
                        diagonal_length = np.linalg.norm(poly_vertex - hole_vertex)
                        if diagonal_length < min_diagonal_length:
                            min_diagonal_length = diagonal_length
                            min_diagonal = (poly_vertex_idx, hole_vert_idx)
            
            if min_diagonal is not None:
                best_diagonals[hole_id] = min_diagonal

        # Build connection line list
        diagonals = []
        
        for hole_id, (p_idx, h_idx) in best_diagonals.items():
            diagonals.append((p_idx, h_idx))
        diagonals = sorted(diagonals, key=lambda x: (x[0], -BasicOptions.get_angle_tan(x[0], x[1], verts_all)))

        # Build new vertex list
        verts = []
        for idx in indices_poly:
            verts.append(verts_all[idx])
            
            # Check if there are connection lines starting from current vertex
            for diagonal in diagonals:
                if diagonal[0] == idx:
                    hole_vertex = diagonal[1]
                    # Find which hole this hole vertex belongs to
                    target_hole_id = None
                    target_hole_indices = None
                    for hole_id, hole_indices in indices_holes.items():
                        if hole_vertex in hole_indices:
                            target_hole_id = hole_id
                            target_hole_indices = hole_indices
                            break
                    
                    if target_hole_indices:
                        # Traverse hole vertices starting from connection endpoint
                        start_idx = target_hole_indices.index(hole_vertex)
                        n_hole = len(target_hole_indices)
                        # Add hole vertices in order
                        for i in range(n_hole + 1):  # +1 is to return to the starting point
                            current_idx = target_hole_indices[(start_idx + i) % n_hole]
                            verts.append(verts_all[current_idx])
                        # Add current outer vertex again to close
                        verts.append(verts_all[idx])
        
        mergelines = [np.array([verts_all[pair[0]], verts_all[pair[1]]]) for pair in diagonals]

        return np.array(verts), mergelines
    
    @staticmethod
    def split_poly(verts: np.ndarray, indices: np.ndarray) -> Union[List[np.ndarray], List[Tuple[int, int]]]:
        """
        Split a simple polygon into convex polygons using a divide-and-conquer approach.
        
        Parameters
        ----------
        verts : np.ndarray
            Array of shape (#verts, 2) containing the 2D coordinates of vertices.
        indices : np.ndarray
            Array of shape (#verts,) containing the indices of vertices forming the polygon, 
            referencing rows in `verts`.
        
        Returns
        -------
        list of np.ndarray, list of tuple of int
            A tuple containing two elements:
            - A list of arrays, each array containing indices of `verts` that form a convex polygon.
            - A list of tuples, each tuple representing a diagonal (split edge) by vertex indices 
              used to partition the original polygon.
        """
        """
        Turn a simple polygon into a list of convex polygons that shares the same area.
        This divide-and-conquer methods base on Arkin, Ronald C.'s report (1987).
        "Path planning for a vision-based autonomous robot"

        :param verts:       np.ndarray (#verts, 2)  a list of 2D-vertices position
        :param indices:     np.ndarray (#vert, )    a list of polygon vertex index (to array `verts`)
        :return:  ([np.ndarray], [(int, int)])
            a list of indices of `verts` that constructs convex areas
            e.g: [np.array(p1_i1, p1_i2, p1_i3, ..), np.array(p2_i1, ...), ..]

            list of diagonals that splits the input polygon.
            e.g: [(diag1_a_index, diag1_b_index), ...]
        """

        # find concave vertex
        n = len(indices)
        i_concave = -1

        for ia in range(n):
            ia_prev, ia_next = (ia - 1) % n, (ia + 1) % n
            angle = BasicOptions.angle(verts[indices[ia_prev]], verts[indices[ia]], verts[indices[ia_next]])
            
            if angle < 0:
                i_concave = ia
                break

        # if there is no concave vertex, which means current polygon is convex. Return itself directly
        if i_concave == -1:
            return [indices], []

        # Find vertex i_break that `<i_concave, i_break>` is an internal edge
        i_break = -1
        min_diagonal_length = float('inf')  # initialize with infinity
        for i in range(n):
            if i != i_concave and i != (i_concave+1) % n and i != (i_concave-1) % n:
                if BasicOptions.diagonal(verts, indices, i_concave, i):
                    # Calculate the length of the diagonal
                    diagonal_length = np.linalg.norm(verts[indices[i_concave]] - verts[indices[i]])

                    # Update i_break if the current diagonal is shorter
                    if diagonal_length < min_diagonal_length:
                        i_break = i
                        min_diagonal_length = diagonal_length

        # Not find (should not happen!)
        if i_break == -1:
            # Just keep that weird region for now
            # TBD: raise a warning
            return [indices], []

        # Split the simple polygon by <i_concave, i_break>
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

        # keep convexifying new-ly generated two areas in a recursive manner
        i1, diag1 = Geometry_Option.split_poly(verts, indices1)
        i2, diag2 = Geometry_Option.split_poly(verts, indices2)

        # merge results from recursively convexify
        ret_diag = [[i_concave, i_break]]
        for diag in diag1:
            ret_diag.append(((diag[0] + i_concave) % n, (diag[1] + i_concave) % n))
        for diag in diag2:
            ret_diag.append(((diag[0] + i_break) % n, (diag[1] + i_break) % n))

        result_indices = i1 + i2
        """
        for new_indices in [indices1, indices2]:
            count = 0
            for ia in range(len(new_indices)):
                ia_prev, ia_next = (ia - 1) % n, (ia + 1) % n
                angle = BasicOptions.angle(verts[indices[ia_prev]], verts[indices[ia]], verts[indices[ia_next]])
                if angle > 0:
                    count += 1
            
            if count > 4:    
                return Geometry_Option.split_poly(verts, new_indices)
        """

        return result_indices, ret_diag

    @staticmethod
    def split_quad(verts: np.ndarray, indices: np.ndarray) -> Union[List[np.ndarray], List[Tuple[int, int]]]:
        """
        Split a convex polygon into triangles or convex quadrilaterals without obtuse angles.
        
        Parameters
        ----------
        verts : np.ndarray, shape (N, 2)
            Array of 2D vertex positions, where N is the number of vertices.
        indices : np.ndarray, shape (M,)
            Array of indices referring to vertices in `verts` that form the convex polygon.
        
        Returns
        -------
        list of np.ndarray or list of tuple of int
            List of sub-polygons, each represented as an array (or tuple) of vertex indices;
            each sub-polygon is either a triangle or a convex quadrilateral.
        """
        """
        Split a convex polygon into triangles or convex quadrilaterals without obtuse angles.
        
        :param verts: np.ndarray (#verts, 2) - a list of 2D vertices positions
        :param indices: np.ndarray (#verts,) - a list of polygon vertex indices (referring to the array `verts`)
        :return: List of np.ndarray - each sub-array corresponds to the indices of a triangle or quadrilateral
        """
        n = len(indices)
        if n <= 4:
            return [indices]  # Already a triangle or quadrilateral
        
        # Try to form triangles and quadrilaterals
        polygons = []
        
        # Iterate over vertices to create triangles and quadrilaterals
        for i in range(n):
            if i < n - 2:
                # Form a triangle
                triangle_indices = [indices[i], indices[i + 1], indices[i + 2]]
                polygons.append(triangle_indices)
            
            if i < n - 3:
                # Form a quadrilateral if possible
                quad_indices = [indices[i], indices[i + 1], indices[i + 2], indices[i + 3]]
                polygons.append(quad_indices)
        
        return polygons


class FaceValidationUtils:
    """Utility class for face validation and processing logic."""
    
    @staticmethod
    def validate_face(face, is_valid_face=True, is_quad_clean=False, expected_quad_vertices=None):
        """
        Validate a single face based on validation flags.
        
        Parameters
        ----------
        face : list or numpy.ndarray
            Face vertices to validate.
        is_valid_face : bool, optional
            If True, validate face using Geometry_Option.is_valid_face().
            Default is True.
        is_quad_clean : bool, optional
            If True, apply additional quadrilateral validation.
            Default is False.
        expected_quad_vertices : int, optional
            Expected number of vertices for quadrilateral validation.
            Default is None (no check).
        
        Returns
        -------
        bool
            True if face passes all validation checks, False otherwise.
        """
        # Basic validity check
        if is_valid_face:
            if not Geometry_Option.is_valid_face(face):
                return False
        
        # Quadrilateral-specific validation
        if is_quad_clean and expected_quad_vertices is not None:
            if len(face) != expected_quad_vertices:
                return False
        
        return True
    
    @staticmethod
    def add_face_to_output(face, cat_value, idd_value, normal_value, 
                          convex_cat, convex_idd, convex_normal, convex_faces):
        """
        Add a validated face to output lists.
        
        Parameters
        ----------
        face : list or numpy.ndarray
            Face vertices.
        cat_value : str
            Category value.
        idd_value : str
            ID value.
        normal_value : array-like
            Normal vector.
        convex_cat : list
            Output category list.
        convex_idd : list
            Output ID list.
        convex_normal : list
            Output normal list.
        convex_faces : list
            Output face list.
        """
        convex_cat.append(cat_value)
        convex_idd.append(idd_value)
        convex_normal.append(normal_value)
        convex_faces.append(face)
    
    @staticmethod
    def process_filtered_faces(filtered_faces, cat_idx, idd_base, normal_idx,
                              cat, idd, normal, convex_cat, convex_idd, 
                              convex_normal, convex_faces, is_valid_face=True, 
                              is_quad_clean=False, use_indexed_idd=False):
        """
        Process a list of filtered faces and add them to output.
        
        Parameters
        ----------
        filtered_faces : list
            List of filtered face vertices.
        cat_idx : int
            Index in cat list.
        idd_base : str
            Base ID string.
        normal_idx : int
            Index in normal list.
        cat : list
            Input category list.
        idd : list
            Input ID list.
        normal : list
            Input normal list.
        convex_cat : list
            Output category list.
        convex_idd : list
            Output ID list.
        convex_normal : list
            Output normal list.
        convex_faces : list
            Output face list.
        is_valid_face : bool, optional
            Enable face validity validation. Default is True.
        is_quad_clean : bool, optional
            Enable quadrilateral validation. Default is False.
        use_indexed_idd : bool, optional
            If True, append index to ID (e.g., "id_0", "id_1").
            Default is False.
        
        Returns
        -------
        int
            Number of faces successfully added.
        """
        count = 0
        for i, face in enumerate(filtered_faces):
            # Validate face
            if not FaceValidationUtils.validate_face(face, is_valid_face, is_quad_clean):
                continue
            
            # Prepare ID
            if use_indexed_idd:
                face_idd = f"#{idd[idd_base]}_{i}"
            else:
                face_idd = idd[idd_base]
            
            # Add to output
            FaceValidationUtils.add_face_to_output(
                face, cat[cat_idx], face_idd, normal[normal_idx],
                convex_cat, convex_idd, convex_normal, convex_faces
            )
            count += 1
        
        return count



    @staticmethod
    def process_convex_decomposition_faces(polys, verts, idx, cat, idd, normal,
                                          convex_cat, convex_idd, convex_normal, 
                                          convex_faces, is_valid_face=True, 
                                          is_quad_clean=False):
        """
        Process faces resulting from convex decomposition.
        
        Parameters
        ----------
        polys : list
            List of polygon indices from decomposition.
        verts : numpy.ndarray
            Vertex array.
        idx : int
            Current face index.
        cat : list
            Input category list.
        idd : list
            Input ID list.
        normal : list
            Input normal list.
        convex_cat : list
            Output category list.
        convex_idd : list
            Output ID list.
        convex_normal : list
            Output normal list.
        convex_faces : list
            Output face list.
        is_valid_face : bool, optional
            Enable face validity validation. Default is True.
        is_quad_clean : bool, optional
            Enable quadrilateral validation. Default is False.
        
        Returns
        -------
        int
            Number of faces successfully added.
        """
        # Extract subfaces from polygon indices
        subfaces = [verts[poly] for poly in polys]
        
        # Apply face node filtering
        filtered_subfaces = FaceFilterAndQuadrilateral.filter_and_process_faces(subfaces)
        
        # Process filtered faces
        use_indexed = len(filtered_subfaces) > 1
        return FaceValidationUtils.process_filtered_faces(
            filtered_subfaces, idx, idx, idx,
            cat, idd, normal, convex_cat, convex_idd, convex_normal, convex_faces,
            is_valid_face=is_valid_face, is_quad_clean=is_quad_clean,
            use_indexed_idd=use_indexed
        )
    
    @staticmethod
    def process_quadrilateral_faces(quad_faces, quad_normals, convex_cat, convex_idd,
                                   convex_normal, convex_faces, is_valid_face=True,
                                   is_quad_clean=True):
        """
        Process quadrilateral air-wall faces with validation.
        
        Parameters
        ----------
        quad_faces : list
            List of quadrilateral face vertices.
        quad_normals : list
            List of quadrilateral normals.
        convex_cat : list
            Output category list.
        convex_idd : list
            Output ID list.
        convex_normal : list
            Output normal list.
        convex_faces : list
            Output face list.
        is_valid_face : bool, optional
            Enable face validity validation. Default is True.
        is_quad_clean : bool, optional
            Enable quadrilateral validation. Default is True.
        
        Returns
        -------
        int
            Number of quadrilateral faces successfully added.
        """
        count = 0
        for i, face in enumerate(quad_faces):
            # Apply quadrilateral-specific validation
            if not FaceValidationUtils.validate_face(
                face, is_valid_face=is_valid_face, 
                is_quad_clean=is_quad_clean, expected_quad_vertices=4
            ):
                continue
            
            # Add to output
            FaceValidationUtils.add_face_to_output(
                face, "2", f"a_{i}", quad_normals[i],
                convex_cat, convex_idd, convex_normal, convex_faces
            )
            count += 1
        
        return count

class FaceFilterAndQuadrilateral:
    """Utility class for filtering faces by node count and computing maximum inscribed quadrilaterals."""
    
    @staticmethod
    def polygon_area_2d(vertices):
        """
        Calculate the area of a 2D polygon using the shoelace formula.
        
        Parameters
        ----------
        vertices : list or numpy.ndarray
            List of 2D vertices (x, y) forming a polygon.
        
        Returns
        -------
        float
            The area of the polygon.
        """
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
    def compute_max_inscribed_quadrilateral(vertices):
        """
        Compute the maximum area inscribed quadrilateral from a convex polygon.
        
        The inscribed quadrilateral has all four vertices selected from the polygon's vertices.
        This function uses a brute-force approach to find the quadrilateral with maximum area.
        
        Parameters
        ----------
        vertices : list or numpy.ndarray
            List of vertices of a convex polygon, ordered counter-clockwise.
        
        Returns
        -------
        list
            List of four vertices forming the maximum area inscribed quadrilateral,
            or the original vertices if fewer than 4 vertices exist.
        """
        n = len(vertices)
        
        # If polygon has 4 or fewer vertices, return as is
        if n <= 4:
            return vertices
        
        max_area = 0.0
        best_quad_indices = None
        
        # Brute-force search through all combinations of 4 vertices
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    for l in range(k + 1, n):
                        # Create quadrilateral from selected vertex indices
                        quad_vertices = [vertices[i], vertices[j], vertices[k], vertices[l]]
                        
                        # Calculate area of this quadrilateral
                        area = FaceFilterAndQuadrilateral.polygon_area_2d(quad_vertices)
                        
                        # Update best quadrilateral if this one has larger area
                        if area > max_area:
                            max_area = area
                            best_quad_indices = [i, j, k, l]
        
        # Return the best inscribed quadrilateral found
        if best_quad_indices is not None:
            return [vertices[idx] for idx in best_quad_indices]
        else:
            return vertices
    
    @staticmethod
    def filter_and_process_faces(faces):
        """
        Filter faces by node count and process them according to the following rules:
        - Discard faces with fewer than 3 vertices
        - Keep faces with 3 or 4 vertices as-is
        - For faces with more than 4 vertices, compute the maximum inscribed quadrilateral
        
        Parameters
        ----------
        faces : list[list[array-like]]
            List of face vertex lists.
        
        Returns
        -------
        list[list[array-like]]
            Processed faces meeting the filtering criteria.
        """
        processed_faces = []
        
        for face in faces:
            num_vertices = len(face)
            
            # Discard faces with fewer than 3 vertices
            if num_vertices < 3:
                continue
            
            # Keep faces with 3 or 4 vertices as-is
            elif num_vertices <= 4:
                processed_faces.append(face)
            
            # For faces with more than 4 vertices, compute maximum inscribed quadrilateral
            else:
                max_quad = FaceFilterAndQuadrilateral.compute_max_inscribed_quadrilateral(face)
                processed_faces.append(max_quad)
        
        return processed_faces



class MoosasConvexify:
    @staticmethod
    def convexify_faces(cat, idd, normal, faces, holes, is_valid_face=True, is_quad_clean=True):
        
        """
        Convexify polygonal faces and generate quadrilateral air-wall patches.

        This function processes a batch of polygonal faces (possibly with holes) 
        and performs geometric normalization, hole integration, convex decomposition, 
        and quadrilateral generation. The pipeline follows a divide-and-conquer method 
        inspired by Arkin (1987), *"Path Planning for a Vision-Based Autonomous Robot"*.

        Parameters
        ----------
        cat : list[str]
            Category ID of each face.
        idd : list[str]
            Identifier of each face.
        normal : list[array-like]
            Normal vectors of faces.
        faces : list[list[array-like]]
            Vertex sequences of each face (outer boundary).
        holes : list[list[list[array-like]]]
            Hole vertex sequences for each face (may be empty).
        is_valid_face : bool, optional
            If True, validates each output face using Geometry_Option.is_valid_face().
            Default is True.
        is_quad_clean : bool, optional
            If True, applies additional validation to quadrilateral faces (air walls).
            Default is True.

        Workflow
        --------
        1. **Vertex ordering**  
        Vertices of the outer boundary and hole boundaries are reordered 
        according to the face normal so that all polygons are in a consistent 
        counter-clockwise orientation.

        2. **Hole merging**  
        Valid hole polygons are merged into the outer boundary.  
        Any required merging lines are collected as divide-lines.

        3. **Convex decomposition**  
        Non-convex faces are split into convex sub-polygons using 
        a divide-and-conquer algorithm.  
        Each sub-face inherits its parent category and normal, 
        with the ID extended as `idd_i` for multi-piece splits.

        4. **Face node filtering**
        Faces are filtered and processed based on node count:
        - Faces with fewer than 3 nodes are discarded.
        - Faces with 3 or 4 nodes are kept as-is.
        - Faces with more than 4 nodes are replaced with the maximum inscribed quadrilateral.

        5. **Quadrilateral generation (air walls)**  
        All diagonal split lines from decomposition are connected into 
        quadrilateral patches. These are assigned:
        - category `"2"` (air-wall)
        - auto-generated IDs: `"a_i"`

        Returns
        -------
        convex_cat : list[str]
            Categories of all resulting faces (original + generated quads).
        convex_idd : list[str]
            IDs of resulting faces.
        convex_normal : list[array-like]
            Normals of resulting faces.
        convex_faces : list[list[array-like]]
            Vertex lists of resulting faces.
        divide_lines : list[array-like]
            All generated split/merge lines used in decomposition.

        Notes
        -----
        - Walls (faces with near-zero Z-normal) are not convexified.
        - The function guarantees consistent orientation and convexity of outputs.
        - The quadrilateral air-wall layer can be used for visualization or 
        topological reconstruction in graph-based pipelines.
        - Face node filtering ensures output faces have at most 4 vertices.
        """

        convex_cat = []
        convex_idd = []
        convex_normal = []
        convex_faces = []
        divide_lines = []
        
        
        # Face reordering by normal direction
        for idx in range(len(faces)):
            
            is_upward = normal[idx][2] > 0
            faces[idx] = Geometry_Option.reorder_vertices(faces[idx], is_upward=is_upward)
            
            if holes[idx]:
                for i in range(len(holes[idx])):
                    holes[idx][i] = Geometry_Option.reorder_vertices(holes[idx][i], is_upward=is_upward)
                    print (f"face[{idx}]:{faces[idx]}")
                    print (f"hole[{idx}][{i}]:{holes[idx][i]}")
        
        print ("--Faces reodering done--")

        for idx, face in enumerate(faces):
            if np.abs(normal[idx][2]) > 1e-3:  # Not wall determination
                poly_ex = face
                
                # Hole Merging
                poly_in = {}
                if holes[idx]:
                    for i in range(len(holes[idx])):
                        hole = holes[idx][i]
                        should_skip = Geometry_Option.process_hole(hole, faces, check_projection=True)
                        if should_skip:
                            continue  # Skip the hole
                        poly_in[i] = hole
   
                    verts, mergelines = Geometry_Option.merge_holes(poly_ex, poly_in)
                    
                    if mergelines:
                        divide_lines.extend(mergelines)
                        
                else:
                    verts = poly_ex

                # Convex decomposition and face processing
                indices = list(range(len(verts)))
                polys, diags = Geometry_Option.split_poly(verts, indices)
                
                # Process decomposed faces using utility method
                FaceValidationUtils.process_convex_decomposition_faces(
                    polys, verts, idx, cat, idd, normal,
                    convex_cat, convex_idd, convex_normal, convex_faces,
                    is_valid_face=is_valid_face, is_quad_clean=is_quad_clean
                )
                
                # Collect dividing lines
                if diags:
                    sublines = [np.array([verts[pair[0]], verts[pair[1]]]) for pair in diags]
                    divide_lines.extend(sublines)

            else:
                # For wall faces, apply node filtering and validation
                filtered_wall_faces = FaceFilterAndQuadrilateral.filter_and_process_faces([face])
                
                # Process wall faces using utility method
                FaceValidationUtils.process_filtered_faces(
                    filtered_wall_faces, idx, idx, idx,
                    cat, idd, normal, convex_cat, convex_idd, convex_normal, convex_faces,
                    is_valid_face=is_valid_face, is_quad_clean=is_quad_clean,
                    use_indexed_idd=False
                )
        
        print ("--Faces splitting done--")

        quad_faces, quad_normals = MoosasConvexify.create_quadrilaterals(divide_lines)
        
        # Process quadrilateral air-wall faces using utility method
        FaceValidationUtils.process_quadrilateral_faces(
            quad_faces, quad_normals, convex_cat, convex_idd,
            convex_normal, convex_faces, is_valid_face=is_valid_face,
            is_quad_clean=is_quad_clean
        )

        return convex_cat, convex_idd, convex_normal, convex_faces, divide_lines



    def convexify_faces_2d(faces, holes, is_valid_face=True, is_quad_clean=True):
        """
        Simplified 2D convexification:
        - reorder vertices
        - merge holes
        - split into convex polygons

        Parameters
        ----------
        faces : list[list[array-like]]
            Outer boundary vertices.
        holes : list[list[list[array-like]]]
            Hole vertices for each face.
        is_valid_face : bool, optional
            If True, validates each output face using Geometry_Option.is_valid_face().
            Default is True.
        is_quad_clean : bool, optional
            If True, applies additional validation to faces.
            Default is True.

        Returns
        -------
        convex_faces : list[list[array-like]]
            Convex sub-polygons.
        """

        convex_faces = []

        for idx, face in enumerate(faces):

            # 1. Vertex ordering (assume CCW in 2D)
            face = Geometry_Option.reorder_vertices(face, is_upward=True)

            hole_dict = {}

            if holes[idx]:
                for i, hole in enumerate(holes[idx]):
                    hole = Geometry_Option.reorder_vertices(hole, is_upward=True)

                    # Skip invalid holes
                    should_skip = Geometry_Option.process_hole(
                        hole, faces, check_projection=True
                    )
                    if should_skip:
                        continue

                    hole_dict[i] = hole

            # 2. Hole merging
            if hole_dict:
                verts, _ = Geometry_Option.merge_holes(face, hole_dict)
            else:
                verts = face

            # 3. Convex decomposition and face processing
            indices = list(range(len(verts)))
            polys, _ = Geometry_Option.split_poly(verts, indices)

            # Extract subfaces and apply node filtering
            subfaces = [verts[i] for i in polys]
            filtered_subfaces = FaceFilterAndQuadrilateral.filter_and_process_faces(subfaces)
            
            # Process filtered faces with validation
            for subface in filtered_subfaces:
                # Validate face
                if not FaceValidationUtils.validate_face(
                    subface, is_valid_face=is_valid_face, 
                    is_quad_clean=is_quad_clean
                ):
                    continue
                
                convex_faces.append(subface)

        return convex_faces

def triangulate2dFace(boundary: pygeos.Geometry, holes: np.ndarray[pygeos.Geometry] = None) -> np.ndarray[pygeos.Geometry]:
    """
    Triangulate a 2D face defined by a boundary and optional holes into convex faces and dividing lines.
    
    Parameters
    ----------
    boundary : pygeos.Geometry
        The outer boundary of the 2D face, represented as a PyGEOS geometry object.
        Must be a linear ring or polygon; will be converted to 3D with z=0 if necessary.
    holes : numpy.ndarray of pygeos.Geometry, optional
        Array of PyGEOS geometry objects representing holes within the boundary.
        Each hole is expected to be a linear ring or polygon.
        If None, no holes are assumed (default is None).
    
    Returns
    -------
    tuple of numpy.ndarray
        A tuple containing two arrays:
        - convexFaces: numpy.ndarray of pygeos.Geometry
          Convex polygonal faces resulting from the decomposition.
        - dividedLines: numpy.ndarray of pygeos.Geometry
          Linestrings representing the internal edges introduced during decomposition.
    """
    boundary = pygeos.polygons(pygeos.get_coordinates(pygeos.force_3d(boundary, z=0),include_z=True))
    proj = Projection.fromPolygon(boundary)
    boundary = proj.toUV(boundary)
    boundary = simplify(boundary,include_z=True)
    boundary = pygeos.get_coordinates(pygeos.force_3d(boundary, z=0),include_z=True)[:-1]
    if holes is None:
        holes = []
    else:
        holes = [proj.toUV(hole) for hole in holes]
        holes = [pygeos.get_coordinates(pygeos.force_3d(hole, z=0))[:-1] for hole in holes]
    convexFaces = MoosasConvexify.convexify_faces_2d([boundary],[holes])
    convexFaces = [pygeos.polygons(convexFace) for convexFace in convexFaces]
    convexFaces = [proj.toWorld(convexFace) for convexFace in convexFaces]
    return convexFaces
