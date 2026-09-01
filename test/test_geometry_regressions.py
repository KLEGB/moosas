from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from MoosasPy.simulation.energy.runner import _resolve_schedule_ref
from MoosasPy.transform.geometry.convexify import GeometryConvexifier
from MoosasPy.transform.geometry.element import MoosasSpace
from MoosasPy.transform.geometry.geos import simplify
from MoosasPy.utils import shapely


def test_simplify_keeps_a_narrow_valid_triangle_closed():
    """A shallow-angle triangle must not be collapsed into a two-point ring."""
    triangle = shapely.polygons(np.array([
        [-7.292645493490398, -0.1346168870321888, 0.0],
        [0.5721716279931042, 0.3190918803725927, 0.0],
        [14.013119358987678, -0.049858106308219, 0.0],
        [-7.292645493490398, -0.1346168870321888, 0.0],
    ]))

    result = simplify(triangle, include_z=True)
    coordinates = shapely.get_coordinates(result, include_z=True)

    assert len(coordinates) == 4
    assert np.allclose(coordinates[0], coordinates[-1])
    assert shapely.is_valid(result)
    assert shapely.area(result) > 1.0


def test_simplify_keeps_three_vertices_for_a_2d_triangle():
    triangle = shapely.polygons(np.array([
        [0.0, 0.0],
        [10.0, 0.1],
        [20.0, 0.0],
        [0.0, 0.0],
    ]))

    result = simplify(triangle)

    assert shapely.is_valid(result)
    assert len(shapely.get_coordinates(result)) == 4


def test_convexification_does_not_infer_vertical_air_walls():
    """Zone air walls are created from final contours, not stacked face diagonals."""
    footprint = np.array([
        [0.0, 0.0],
        [8.0, 0.0],
        [8.0, 3.0],
        [3.0, 3.0],
        [3.0, 8.0],
        [0.0, 8.0],
    ])
    faces = [
        np.column_stack((footprint, np.full(len(footprint), elevation)))
        for elevation in (0.0, 3.0)
    ]

    categories, _, _, _, divide_lines = GeometryConvexifier.convexify_faces(
        [0, 0],
        ["floor", "roof"],
        [np.array([0.0, 0.0, 1.0])] * 2,
        faces,
        [None, None],
    )

    assert divide_lines
    assert all(int(category) != 2 for category in categories)


def test_template_application_keeps_load_intensities_numeric():
    """A schedule reference must not replace the numeric IDF load value."""
    template = {
        "type": "RESIDENTIAL",
        "zone_ppsm": "0.031",
        "zone_equipment": "4.2",
        "zone_lighting": "6.5",
    }
    model = SimpleNamespace(
        buildingTemplate={"test-residential": template},
        scheduleByType={
            "RESIDENTIAL": {
                "zone_ppsm": "RES_OccDens_Weekly",
                "zone_equipment": "RES_Equip_Weekly",
                "zone_lighting": "RES_Light_Weekly",
            }
        },
    )
    space = object.__new__(MoosasSpace)
    space.edge = SimpleNamespace(parent=model)
    space.settings = {}

    space.applySettings(template)

    assert space.settings["zone_ppsm"] == 0.031
    assert space.settings["zone_equipment"] == 4.2
    assert space.settings["zone_lighting"] == 6.5
    assert _resolve_schedule_ref(model, "RESIDENTIAL", "zone_ppsm", space.settings["zone_ppsm"]) == "RES_OccDens_Weekly"

    invalid_template = {"type": "RESIDENTIAL", "zone_ppsm": "RES_OccDens_Weekly"}
    model.buildingTemplate = {"invalid-residential": invalid_template}
    with pytest.raises(ValueError, match="zone_ppsm.*must be numeric"):
        space.applySettings(invalid_template)
