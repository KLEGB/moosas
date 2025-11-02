import numpy as np
from collections import defaultdict


def create_quadrilaterals(divide_lines):
    """
    Create quadrilateral faces and their corresponding normals from grouped 3D lines.
    
    Parameters
    ----------
    divide_lines : list of numpy.ndarray
        A list of line segments, where each line is a 2x3 numpy array representing 
        two 3D points (shape: [2, 3]). Each line segment is used to generate quadrilaterals 
        when paired with overlapping lines at different heights.
    
    Returns
    -------
    quad_faces : list of numpy.ndarray
        A list of quadrilateral faces, each represented as a 4x3 numpy array containing 
        the four corner points in 3D space.
    quad_normals : list of numpy.ndarray
        A list of unit normal vectors (3D) corresponding to each quadrilateral face, 
        normalized to unit length.
    """
    line_groups = defaultdict(list)
    quad_faces = []
    quad_normals = []

    # Get the projection coordinates and midpoint heights
    projected_lines = [line[:, :2] for line in divide_lines]
    z_lines = [(line[0, 2] + line[1, 2]) / 2 for line in divide_lines]

    # Group overlapping lines
    for i in range(len(projected_lines)):
        found_group = False
        for j in range(i):
            if (np.array_equal(projected_lines[i], projected_lines[j]) or 
                np.array_equal(projected_lines[i], projected_lines[j][::-1])):
                line_groups[j].append((divide_lines[i], z_lines[i]))
                found_group = True
                break
        if not found_group:
            line_groups[i].append((divide_lines[i], z_lines[i]))

    # Process each group to form quadrilaterals
    for group in line_groups.values():
        if len(group) < 2:
            continue  # Skip groups with fewer than 2 lines

        # Sort lines in the group by midpoint height
        group.sort(key=lambda x: x[1])  # Sort by z value

        # Create quadrilaterals
        for k in range(len(group) - 1):
            line1, _ = group[k]
            line2, _ = group[k + 1]

            # Skip if the two lines are geometrically identical (same endpoints)
            if (np.allclose(line1, line2) or np.allclose(line1, line2[::-1])):
                continue

            quad_face = np.array([line1[0], line1[1], line2[1], line2[0]])
            normal_vector = np.cross(line1[0] - line1[1], line1[0] - line2[0])
            quad_normal = normal_vector / np.linalg.norm(normal_vector)

            quad_faces.append(quad_face)
            quad_normals.append(quad_normal)

    return quad_faces, quad_normals