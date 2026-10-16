"""Wall openings must form patches without leaving holes in the CFD shell."""

from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

from MoosasPy.model.io._foam_case import _conformal_surface, _contains_point, _surface_triangles
from MoosasPy.model.io.foam import exportFoam
from MoosasPy.transform import transform


def face(uid, polygons, glazing=()):
    return SimpleNamespace(Uid=uid, face=np.asarray(polygons, dtype=object), glazingElement=list(glazing))


def front_polygon(points):
    return shapely.Polygon([(x, 0, z) for x, z in points])


def room_sides():
    return [
        [(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)],
        [(0, 0, 3), (4, 0, 3), (4, 4, 3), (0, 4, 3)],
        [(0, 4, 0), (4, 4, 0), (4, 4, 3), (0, 4, 3)],
        [(0, 0, 0), (0, 4, 0), (0, 4, 3), (0, 0, 3)],
        [(4, 0, 0), (4, 4, 0), (4, 4, 3), (4, 0, 3)],
    ]


@pytest.mark.parametrize("kind", ["interior_hole", "floor_cutout", "side_cutout", "multipart"])
def test_opening_preserves_area_and_closes_room(kind):
    outline = [(0, 0), (4, 0), (4, 3), (0, 3)]
    aperture = [(1, 1), (3, 1), (3, 2), (1, 2)]
    if kind == "floor_cutout":
        outline = [(0, 0), (1, 0), (1, 2), (2, 2), (2, 0), (4, 0), (4, 3), (0, 3)]
        aperture = [(1, 0), (2, 0), (2, 2), (1, 2)]
    elif kind == "side_cutout":
        outline = [(0, 0), (4, 0), (4, 3), (0, 3), (0, 2), (2, 2), (2, 1), (0, 1)]
        aperture = [(0, 1), (2, 1), (2, 2), (0, 2)]
    polygons = [front_polygon(outline)]
    if kind == "interior_hole":
        polygons = [shapely.Polygon(polygons[0].exterior, [front_polygon(aperture).exterior])]
    elif kind == "multipart":
        polygons = [front_polygon([(0, 0), (2, 0), (2, 3), (0, 3)]),
                    front_polygon([(2, 0), (4, 0), (4, 3), (2, 3)])]
    opening = face("gls_door", [front_polygon(aperture)])
    wall = face("wall_front", polygons, [opening])
    triangles = _surface_triangles(wall, {"inlet": opening})
    areas = {"inlet": 0.0, "walls": 0.0}
    for patch, vertices in triangles:
        areas[patch] += np.linalg.norm(np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])) / 2
    assert areas == pytest.approx({"inlet": 2.0, "walls": 10.0})
    for index, points in enumerate(room_sides()):
        triangles.extend(_surface_triangles(face(f"side_{index}", [shapely.Polygon(points)]), {}))
    closed = _conformal_surface(triangles)
    assert _contains_point(closed, [2, 2, 1.5])
    assert not _contains_point(closed, [2, -1, 1.5])


def test_unselected_boundary_opening_is_closed_as_wall():
    opening = face("gls_door", [front_polygon([(1, 0), (2, 0), (2, 2), (1, 2)])])
    wall = face("wall_front", [front_polygon([
        (0, 0), (1, 0), (1, 2), (2, 2), (2, 0), (4, 0), (4, 3), (0, 3),
    ])], [opening])
    triangles = _surface_triangles(wall, {})
    assert all(patch == "walls" for patch, _ in triangles)
    area = sum(np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0])) / 2 for _, v in triangles)
    assert area == pytest.approx(12)


@pytest.mark.parametrize("offset", [0.3, -0.3])
def test_opening_on_different_plane_is_not_silently_projected(offset):
    opening = face("gls_offset", [shapely.Polygon([
        (1, offset, 1), (3, offset, 1), (3, offset, 2), (1, offset, 2),
    ])])
    wall = face("wall_front", [front_polygon([(0, 0), (4, 0), (4, 3), (0, 3)])], [opening])
    with pytest.raises(ValueError, match="gls_offset.*wall_front"):
        _surface_triangles(wall, {"inlet": opening})


def test_unassociated_hole_still_fails_closure():
    wall = face("wall_front", [front_polygon([
        (0, 0), (1, 0), (1, 2), (2, 2), (2, 0), (4, 0), (4, 3), (0, 3),
    ])])
    triangles = _surface_triangles(wall, {})
    for index, points in enumerate(room_sides()):
        triangles.extend(_surface_triangles(face(f"side_{index}", [shapely.Polygon(points)]), {}))
    with pytest.raises(ValueError, match="not closed"):
        _conformal_surface(triangles)


@pytest.mark.parametrize("inlet,outlet,velocity", [
    ("gls_glazing_0", "gls_glazing_2", [0, 0.2, 0]),
    ("gls_glazing_2", "gls_glazing_3", [0, -0.2, 0]),
])
def test_real_room_boundary_openings_export_without_rebuilding_walls(tmp_path, inlet, outlet, velocity):
    model = transform(str(Path(__file__).parent / "caseFile/room_boundary_openings.geo"),
                      input_type="geo", stdout=StringIO())
    result = exportFoam(
        model, tmp_path / "case.foam", scenario="indoor", space_index=0,
        conditions=dict(viscosity=1.5e-5, turbulence_intensity=0.05,
                        turbulence_length=1.0, iterations=1000,
                        inlet=dict(opening=inlet, velocity=velocity),
                        outlet=dict(opening=outlet, pressure=0)),
    )
    assert result.primary_path.is_file()
    surface = (tmp_path / "constant/geometry/model.stl").read_text()
    assert "solid inlet\n" in surface and "solid outlet\n" in surface


def test_overlapping_selected_openings_are_rejected():
    first = face("gls_a", [front_polygon([(1, 1), (3, 1), (3, 2), (1, 2)])])
    second = face("gls_b", [front_polygon([(2, 1), (4, 1), (4, 2), (2, 2)])])
    wall = face("wall_front", [front_polygon([(0, 0), (4, 0), (4, 3), (0, 3)])], [first, second])
    with pytest.raises(ValueError, match="overlap.*wall_front"):
        _surface_triangles(wall, {"inlet": first, "outlet": second})


def test_closure_error_identifies_source_surface():
    triangles = _surface_triangles(face("wall_front", [front_polygon([
        (0, 0), (4, 0), (4, 3), (0, 3),
    ])]), {})
    owners = ["wall_front"] * len(triangles)
    with pytest.raises(ValueError, match="not closed.*wall_front"):
        _conformal_surface(triangles, source_uids=owners)
