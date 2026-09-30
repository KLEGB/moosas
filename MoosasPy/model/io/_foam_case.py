"""OpenFOAM Foundation 12 isothermal RANS case generation for model.save."""

from __future__ import annotations

import json
from numbers import Integral
from collections import defaultdict, deque

import numpy as np
import shapely
from shapely.ops import triangulate
from scipy.spatial import cKDTree

from .result import SaveResult
from ...utils.constant import geom


def _number(value, name, positive=False):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not np.isfinite(result) or (positive and result <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return result


def _vector(value, name):
    vector = np.asarray(value, dtype=float)
    if vector.shape != (3,) or not np.isfinite(vector).all():
        raise ValueError(f"{name} must be a finite three-vector")
    return vector


def _foam_vector(value):
    return "(" + " ".join(f"{x:.12g}" for x in value) + ")"


def _dictionary(name, body, cls="dictionary"):
    return ("FoamFile\n{\n    version 2.0;\n    format ascii;\n"
            f"    class {cls};\n    object {name};\n}}\n\n{body}\n")


def _project_polygon(polygon, origin, axes):
    rings = [(shapely.get_coordinates(ring, include_z=True) - origin) @ axes
             for ring in shapely.get_rings(polygon)]
    return shapely.Polygon(rings[0], rings[1:])


def _surface_triangles(element, openings):
    """Triangulate each planar face, cutting selected openings in its own plane."""
    result = []
    covered = set()
    for polygon in np.asarray(element.face, dtype=object).reshape(-1):
        xyz = shapely.get_coordinates(shapely.get_exterior_ring(polygon), include_z=True)
        origin = xyz[0]
        normal = np.sum(np.cross(xyz[:-1] - origin, xyz[1:] - origin), axis=0)
        length = np.linalg.norm(normal)
        if length <= 1e-12 or not np.isfinite(xyz).all():
            raise ValueError(f"Invalid surface: {element.Uid}")
        normal /= length
        x_axis = xyz[1] - origin
        x_axis /= np.linalg.norm(x_axis)
        axes = np.column_stack((x_axis, np.cross(normal, x_axis)))
        if np.max(np.abs((xyz - origin) @ normal)) > 0.02:
            raise ValueError(f"Non-planar surface: {element.Uid}")
        footprint = _project_polygon(polygon, origin, axes)
        glazing = [_project_polygon(part, origin, axes)
                   for opening in element.glazingElement
                   for part in np.asarray(opening.face, dtype=object).reshape(-1)]
        if glazing:
            footprint = shapely.union(footprint, shapely.intersection(
                shapely.Polygon(footprint.exterior), shapely.union_all(glazing)))
        # Closed windows remain wall. Selected openings become separate patches.
        regions = {}
        opaque = footprint
        for name, opening in openings.items():
            parts = [_project_polygon(part, origin, axes)
                     for part in np.asarray(opening.face, dtype=object).reshape(-1)]
            aperture = shapely.intersection(footprint, shapely.union_all(parts))
            if aperture.area <= 1e-8:
                continue
            covered.add(name)
            regions[name] = aperture
            opaque = shapely.difference(opaque, aperture)
        regions["walls"] = opaque
        for name, region in regions.items():
            area = 0.0
            for candidate in triangulate(region):
                clipped = shapely.intersection(candidate, region)
                for part in shapely.get_parts(clipped):
                    if not isinstance(part, shapely.Polygon) or part.area <= 1e-12:
                        continue
                    for triangle in triangulate(part):
                        if part.covers(triangle):
                            uv = shapely.get_coordinates(triangle)[:3]
                            vertices = uv @ axes.T + origin
                            result.append((name, vertices))
                            area += triangle.area
            if not np.isclose(area, region.area, rtol=1e-8, atol=1e-8):
                raise ValueError(f"Unable to preserve complete surface {element.Uid}")
    if set(openings) != covered:
        raise ValueError("Selected opening does not intersect its parent face")
    return result


def _stl(triangles):
    lines = []
    for patch in sorted({name for name, _ in triangles}):
        lines.append(f"solid {patch}")
        for name, vertices in triangles:
            if name != patch:
                continue
            normal = np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])
            normal /= np.linalg.norm(normal)
            lines.append("facet normal " + " ".join(f"{x:.12g}" for x in normal))
            lines.append("outer loop")
            lines.extend("vertex " + " ".join(f"{x:.12g}" for x in vertex) for vertex in vertices)
            lines.extend(("endloop", "endfacet"))
        lines.append(f"endsolid {patch}")
    return "\n".join(lines) + "\n"


def _contains_point(triangles, point):
    """Odd/even ray intersections against a closed triangle surface."""
    vertices = np.asarray([v for _, v in triangles])
    edge1 = vertices[:, 1] - vertices[:, 0]
    edge2 = vertices[:, 2] - vertices[:, 0]
    direction = np.array([1.0, 0.371390676, 0.694746591])
    h = np.cross(direction, edge2)
    determinant = np.einsum("ij,ij->i", edge1, h)
    nonparallel = np.abs(determinant) > 1e-12
    inverse = np.zeros_like(determinant)
    inverse[nonparallel] = 1 / determinant[nonparallel]
    delta = np.asarray(point) - vertices[:, 0]
    u = inverse * np.einsum("ij,ij->i", delta, h)
    q = np.cross(delta, edge1)
    v = inverse * (q @ direction)
    distance = inverse * np.einsum("ij,ij->i", edge2, q)
    hits = nonparallel & (u >= -1e-10) & (v >= -1e-10) & (u + v <= 1 + 1e-10) & (distance > 1e-9)
    return len(np.unique(np.round(distance[hits], 8))) % 2 == 1


def _conformal_surface(triangles):
    """Use model precision once, then node shared edges and orient the shell."""
    vertices = np.round(np.vstack([v for _, v in triangles]) / geom.POINT_PRECISION) * geom.POINT_PRECISION
    points, inverse = np.unique(vertices, axis=0, return_inverse=True)
    tree = cKDTree(points)
    faces = []
    seen = {}
    for (patch, _), ring in zip(triangles, inverse.reshape(-1, 3)):
        key = tuple(sorted(ring))
        if len(set(ring)) < 3:
            raise ValueError("Geometry contains features smaller than model precision")
        if key in seen:
            if seen[key] != patch:
                raise ValueError("Opening overlaps another surface patch")
            continue
        seen[key] = patch
        boundary = []
        for a, b in zip(ring, np.roll(ring, -1)):
            edge = points[b] - points[a]
            length = np.linalg.norm(edge)
            nearby = tree.query_ball_point((points[a] + points[b]) / 2, length / 2 + 1e-7)
            split = []
            for index in nearby:
                fraction = np.dot(points[index] - points[a], edge) / length ** 2
                distance = np.linalg.norm(points[index] - points[a] - fraction * edge)
                if (index not in (a, b) and 1e-9 < fraction < 1 - 1e-9
                        and distance <= geom.POINT_PRECISION):
                    split.append((fraction, index))
            boundary.append(int(a))
            boundary.extend(index for _, index in sorted(split))
        if len(boundary) == 3:
            faces.append([patch, boundary])
        else:
            center = len(points)
            points = np.vstack((points, np.mean(points[ring], axis=0)))
            faces.extend([patch, [a, b, center]] for a, b in zip(boundary, boundary[1:] + boundary[:1]))
    edges = defaultdict(list)
    for i, (_, face) in enumerate(faces):
        for a, b in zip(face, face[1:] + face[:1]):
            edges[tuple(sorted((a, b)))].append((i, a < b))
    bad = [edge for edge, users in edges.items() if len(users) != 2]
    if bad:
        sample = [(points[a].tolist(), points[b].tolist(), len(edges[(a, b)])) for a, b in bad[:3]]
        raise ValueError(f"Model surface is not closed at {len(bad)} edges: {sample}")
    adjacency = defaultdict(list)
    for users in edges.values():
        (a, direction_a), (b, direction_b) = users
        adjacency[a].append((b, direction_a == direction_b))
        adjacency[b].append((a, direction_a == direction_b))
    flip = {}
    for seed in range(len(faces)):
        if seed in flip:
            continue
        flip[seed] = False
        queue = deque([seed])
        while queue:
            a = queue.popleft()
            for b, reverse in adjacency[a]:
                desired = flip[a] ^ reverse
                if b in flip and flip[b] != desired:
                    raise ValueError("Model surface has inconsistent orientation")
                if b not in flip:
                    flip[b] = desired
                    queue.append(b)
    return [(patch, points[face[::-1] if flip[i] else face]) for i, (patch, face) in enumerate(faces)]


def _block_mesh(bounds, size, patches):
    lo, hi = bounds
    vertices = [(lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2]),
                (hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]),
                (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]),
                (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])]
    cells = np.maximum(1, np.ceil((hi - lo) / size).astype(int))
    faces = [(0, 4, 7, 3), (1, 2, 6, 5), (0, 1, 5, 4),
             (3, 7, 6, 2), (0, 3, 2, 1), (4, 5, 6, 7)]
    entries = [f"{name} {{ type {kind}; faces ({_foam_vector(face)}); }}"
               for (name, kind), face in zip(patches, faces)]
    return _dictionary("blockMeshDict", "convertToMeters 1;\nvertices\n(\n"
                       + "\n".join(_foam_vector(v) for v in vertices)
                       + "\n);\nblocks (hex (0 1 2 3 4 5 6 7) "
                       + _foam_vector(cells) + " simpleGrading (1 1 1));\n"
                       + "edges ();\nboundary\n(\n" + "\n".join(entries) + "\n);\n")


def _snappy(patches, inside):
    names = "\n".join(f"{p} {{ name {p}; }}" for p in patches)
    regions = "\n".join(f"{p} {{ level (1 1); patchInfo {{ type {t}; }} }}"
                        for p, t in patches.items())
    return _dictionary("snappyHexMeshDict", f'''
#includeEtc "caseDicts/mesh/generation/snappyHexMeshDict.cfg"
castellatedMesh true;
snap true;
addLayers false;
geometry {{ model {{ type triSurfaceMesh; file "model.stl"; regions {{ {names} }} }} }}
castellatedMeshControls
{{
    maxLocalCells 1000000;
    maxGlobalCells 2000000;
    minRefinementCells 0;
    refinementSurfaces {{ model {{ level (1 1); regions {{ {regions} }} }} }}
    refinementRegions {{}}
    insidePoint {_foam_vector(inside)};
}}
snapControls {{ implicitFeatureSnap true; multiRegionFeatureSnap true; }}
addLayersControls {{ layers {{}} }}
meshQualityControls {{}}
writeFlags ();
mergeTolerance 1e-6;
''')


def _fields(patches, velocity, pressure, intensity, length):
    speed = np.linalg.norm(velocity)
    kinetic = 1.5 * (speed * intensity) ** 2
    epsilon = 0.09 ** 0.75 * kinetic ** 1.5 / length
    initial = {"U": _foam_vector(velocity), "p": str(pressure), "k": str(kinetic),
               "epsilon": str(epsilon), "nut": str(0.09 * kinetic ** 2 / epsilon)}
    dimensions = {"U": "0 1 -1", "p": "0 2 -2", "k": "0 2 -2",
                  "epsilon": "0 2 -3", "nut": "0 2 -1"}
    files = {}
    for field in initial:
        boundary = []
        for name, kind in patches.items():
            if kind == "symmetry":
                body = "type symmetry;"
            elif kind == "wall":
                wall_type = {"U": "noSlip", "p": "zeroGradient", "k": "kqRWallFunction",
                             "epsilon": "epsilonWallFunction", "nut": "nutkWallFunction"}[field]
                body = f"type {wall_type};"
                if field in {"k", "epsilon", "nut"}:
                    body += f" value uniform {initial[field]};"
            elif kind == "inlet":
                if field == "p":
                    body = "type zeroGradient;"
                elif field == "nut":
                    body = f"type calculated; value uniform {initial[field]};"
                else:
                    body = f"type fixedValue; value uniform {initial[field]};"
            else:
                if field == "p":
                    body = f"type fixedValue; value uniform {pressure};"
                elif field == "U":
                    body = "type pressureInletOutletVelocity; value uniform (0 0 0);"
                elif field == "nut":
                    body = f"type calculated; value uniform {initial[field]};"
                else:
                    body = (f"type inletOutlet; inletValue uniform {initial[field]};"
                            f" value uniform {initial[field]};")
            boundary.append(f"{name}\n{{ {body} }}")
        cls = "volVectorField" if field == "U" else "volScalarField"
        files[f"0/{field}"] = _dictionary(field,
            f"dimensions [{dimensions[field]} 0 0 0 0];\ninternalField uniform {initial[field]};\n"
            + "boundaryField\n{\n" + "\n".join(boundary) + "\n}", cls)
    return files


def write_case(model, target, scenario, space_index, grid_size, conditions):
    if not isinstance(conditions, dict):
        raise ValueError("Explicit physical conditions are required")
    required = {"viscosity", "turbulence_intensity", "turbulence_length", "iterations"}
    required |= {"inlet", "outlet"} if scenario == "indoor" else {"velocity", "domain", "inside_point"}
    if set(conditions) != required:
        raise ValueError(f"conditions must contain exactly: {', '.join(sorted(required))}")
    size = _number(grid_size, "grid_size", positive=True)
    nu = _number(conditions["viscosity"], "viscosity", positive=True)
    intensity = _number(conditions["turbulence_intensity"], "turbulence_intensity", positive=True)
    length = _number(conditions["turbulence_length"], "turbulence_length", positive=True)
    iterations = conditions["iterations"]
    if isinstance(iterations, bool) or not isinstance(iterations, Integral) or iterations < 1:
        raise ValueError("iterations must be a positive integer")
    triangles = []
    pressure = 0.0
    if scenario == "indoor":
        if (isinstance(space_index, bool) or not isinstance(space_index, Integral)
                or not 0 <= space_index < len(model.spaceList)):
            raise ValueError("space_index must identify an existing model space")
        space = model.spaceList[space_index]
        if space.internalMass:
            raise ValueError("Indoor CFD requires explicit closed obstacle geometry; internalMass is unsupported")
        faces = space.getAllFaces(to_dict=True)
        openings = {g.Uid: g for g in faces["MoosasGlazing"] + faces["MoosasSkylight"]}
        selected = {}
        for name in ("inlet", "outlet"):
            expected = {"opening", "velocity" if name == "inlet" else "pressure"}
            if not isinstance(conditions[name], dict) or set(conditions[name]) != expected:
                raise ValueError(f"{name} must contain {expected}")
            uid = conditions[name]["opening"]
            if uid not in openings:
                raise ValueError(f"Unknown opening in selected room: {uid}")
            selected[name] = openings[uid]
        if selected["inlet"] is selected["outlet"]:
            raise ValueError("Inlet and outlet must be distinct openings")
        velocity = _vector(conditions["inlet"]["velocity"], "inlet velocity")
        pressure = _number(conditions["outlet"]["pressure"], "outlet pressure")
        for element in faces["MoosasFloor"] + faces["MoosasCeiling"] + faces["MoosasWall"]:
            cut = {name: g for name, g in selected.items() if g in element.glazingElement}
            triangles.extend(_surface_triangles(element, cut))
        if not {"inlet", "outlet"}.issubset({name for name, _ in triangles}):
            raise ValueError("Selected openings must belong to room boundary faces")
        coords = np.vstack([v for _, v in triangles])
        bounds = np.array([coords.min(axis=0) - size, coords.max(axis=0) + size])
        footprint = shapely.union_all([shapely.force_2d(p) for f in faces["MoosasFloor"]
                                      for p in np.asarray(f.face, dtype=object).reshape(-1)])
        point = footprint.representative_point()
        inside = np.array([point.x, point.y, (coords[:, 2].min() + coords[:, 2].max()) / 2])
        block_patches = [(f"background{i}", "patch") for i in range(6)]
        patches = {"walls": "wall", "inlet": "inlet", "outlet": "outlet"}
    else:
        if space_index is not None:
            raise ValueError("Outdoor cases use the whole model; omit space_index")
        velocity = _vector(conditions["velocity"], "velocity")
        if abs(velocity[2]) > 1e-12:
            raise ValueError("Outdoor inlet velocity must be horizontal")
        bounds = np.asarray(conditions["domain"], dtype=float)
        if bounds.shape != (2, 3) or not np.isfinite(bounds).all() or not np.all(bounds[1] > bounds[0]):
            raise ValueError("domain must contain finite minimum and maximum XYZ corners")
        inside = _vector(conditions["inside_point"], "inside_point")
        if not np.all((inside > bounds[0]) & (inside < bounds[1])):
            raise ValueError("inside_point must be strictly inside the domain and outside buildings")
        faces = model.getAllFaces(dumpUseless=True)
        for element in list(faces["MoosasFace"]) + list(faces["MoosasWall"]):
            if element.isOuter:
                triangles.extend(_surface_triangles(element, {}))
        if not triangles:
            raise ValueError("Model has no exterior building surfaces")
        coords = np.vstack([v for _, v in triangles])
        if np.any(coords < bounds[0] - 0.02) or np.any(coords > bounds[1] + 0.02):
            raise ValueError("domain must contain the complete building geometry")
        patches = {"walls": "wall"}
        block_patches = []
        for name, axis, sign in (("west", 0, -1), ("east", 0, 1),
                                 ("south", 1, -1), ("north", 1, 1)):
            flow = sign * velocity[axis]
            kind = "symmetry" if abs(flow) < 1e-12 else ("inlet" if flow < 0 else "outlet")
            patches[name] = kind
            block_patches.append((name, "symmetry" if kind == "symmetry" else "patch"))
        patches.update(ground="wall", top="symmetry")
        block_patches.extend((("ground", "wall"), ("top", "symmetry")))
    if np.linalg.norm(velocity) <= 0:
        raise ValueError("Inlet velocity must be nonzero")
    triangles = _conformal_surface(triangles)
    if _contains_point(triangles, inside) != (scenario == "indoor"):
        raise ValueError("inside_point must be in the selected fluid region")
    if scenario == "indoor":
        inlet = [v for name, v in triangles if name == "inlet"]
        sample = max(inlet, key=lambda v: np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0]))).mean(axis=0)
        step = velocity / np.linalg.norm(velocity) * geom.POINT_PRECISION * 2
        if not _contains_point(triangles, sample + step) or _contains_point(triangles, sample - step):
            raise ValueError("Inlet velocity must point into the room")
    surface_patches = {name: ("wall" if name == "walls" else "patch")
                       for name in sorted({name for name, _ in triangles})}
    files = {"constant/geometry/model.stl": _stl(triangles),
             "system/blockMeshDict": _block_mesh(bounds, size, block_patches),
             "system/snappyHexMeshDict": _snappy(surface_patches, inside),
             "system/meshQualityDict": _dictionary("meshQualityDict",
                 '#includeEtc "caseDicts/mesh/generation/meshQualityDict"\nmaxBoundarySkewness 4;'),
             "constant/physicalProperties": _dictionary("physicalProperties", f"viscosityModel constant;\nnu {nu};"),
             "constant/momentumTransport": _dictionary("momentumTransport",
                 "simulationType RAS;\nRAS { model kEpsilon; turbulence on; printCoeffs on; }")}
    files.update(_fields(patches, velocity, pressure, intensity, length))
    functions = "\n".join(f'''flow_{name}
{{
    type surfaceFieldValue;
    libs ("libfieldFunctionObjects.so");
    writeControl timeStep; writeInterval 1;
    regionType patch; name {name};
    operation sum; fields (phi); writeFields false;
}}''' for name, kind in patches.items() if kind in {"inlet", "outlet"})
    files["system/controlDict"] = _dictionary("controlDict", f'''
application foamRun;
solver incompressibleFluid;
startFrom startTime; startTime 0;
stopAt endTime; endTime {iterations}; deltaT 1;
writeControl timeStep; writeInterval 1;
purgeWrite 1; writeFormat ascii; writePrecision 12; writeCompression off;
timeFormat general; timePrecision 8; runTimeModifiable false;
functions {{ {functions} }}
''')
    files["system/fvSchemes"] = _dictionary("fvSchemes", '''
ddtSchemes { default steadyState; }
gradSchemes { default cellLimited Gauss linear 1; }
divSchemes
{
    default none;
    div(phi,U) bounded Gauss upwind;
    div(phi,k) bounded Gauss upwind;
    div(phi,epsilon) bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear limited 0.5; }
interpolationSchemes { default linear; }
snGradSchemes { default limited 0.5; }
wallDist { method meshWave; }
''')
    files["system/fvSolution"] = _dictionary("fvSolution", '''
solvers
{
    p { solver GAMG; tolerance 1e-10; relTol 0; smoother GaussSeidel; }
    "(U|k|epsilon)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-10; relTol 0; }
}
SIMPLE
{
    nNonOrthogonalCorrectors 2;
    consistent yes;
    residualControl { p 1e-4; U 1e-4; k 1e-4; epsilon 1e-4; }
}
relaxationFactors { fields { p 0.2; } equations { U 0.3; k 0.5; epsilon 0.5; } }
''')
    files["constant/moosasCase.json"] = json.dumps({
        "openfoam_version": 12, "scenario": scenario, "space_index": space_index,
        "grid_size": size, "conditions": conditions,
        "flow_patches": [name for name, kind in patches.items() if kind in {"inlet", "outlet"}],
    }, indent=2, allow_nan=False) + "\n"
    if target.parent.exists() and any(target.parent.iterdir()):
        raise FileExistsError(f"OpenFOAM case directory must be empty: {target.parent}")
    for name, content in files.items():
        path = target.parent / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="ascii", newline="\n")
    target.touch(exist_ok=False)
    return SaveResult(target, (*tuple(target.parent / name for name in files), target))
