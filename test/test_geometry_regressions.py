from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from MoosasPy.simulation.energy.runner import _resolve_schedule_ref
from MoosasPy.transform.geometry.convexify import GeometryConvexifier
from MoosasPy.model import MoosasModel
from MoosasPy.transform.geometry.element import MoosasEdge, MoosasGeometry, MoosasSpace, MoosasWall
from MoosasPy.transform.geometry.geos import simplify
from MoosasPy.transform.geometry.planar_graph import TopoNetwork
from MoosasPy.transform.geometry.contour import _merge_tiny_partitions
from MoosasPy.transform.stages.convexification import convexify_model
from MoosasPy.utils import GeometryError, shapely


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


def test_convexified_model_preserves_the_next_geometry_id():
    model = MoosasModel()
    model.levelList = [0.0, 3.0]
    geometry = MoosasGeometry(
        np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 3.0],
            [5.0, 0.0, 3.0],
            [5.0, 0.0, 0.0],
        ]),
        "n40",
        np.array([0.0, -1.0, 0.0]),
        0,
    )
    model.geometryList = [geometry]
    model.geoId = [geometry.faceId]
    model.wallList = [MoosasWall(model, geometry)]
    model.newIndex = 41

    result = convexify_model(model)
    generated_id = result.includeGeo(
        shapely.polygons([
            [0.0, 1.0, 0.0],
            [0.0, 1.0, 3.0],
            [5.0, 1.0, 3.0],
            [5.0, 1.0, 0.0],
        ]),
        cat=2,
    )

    assert generated_id == "n41"
    assert len(result.geoId) == len(set(result.geoId))


def test_tiny_partition_is_merged_into_its_neighbor():
    tiny = shapely.box(0.0, 0.0, 0.01, 5.0)
    room = shapely.box(0.01, 0.0, 10.0, 5.0)

    result = _merge_tiny_partitions([tiny, room])

    assert len(result) == 1
    assert shapely.area(result[0]) == pytest.approx(50.0)


def test_negative_45_degree_wall_projects_to_a_line():
    model = MoosasModel()
    model.levelList = [0.0, 3.0]
    geometry = MoosasGeometry(
        np.array([
            [0.0, 5.0, 0.0],
            [0.0, 5.0, 3.0],
            [5.0, 0.0, 3.0],
            [5.0, 0.0, 0.0],
        ]),
        "negative_45_wall",
        np.array([1.0, 1.0, 0.0]),
        0,
    )
    model.geometryList = [geometry]
    model.geoId = [geometry.faceId]

    projection = MoosasWall(model, geometry).force_2d()

    assert shapely.get_type_id(projection) == shapely.GeometryType.LINESTRING
    assert shapely.length(projection) == pytest.approx(np.sqrt(50.0))


def test_rotated_rectangle_merges_half_grid_corner_rounding():
    model = MoosasModel()
    model.levelList = [0.0, 3.0]
    p0 = np.array([3.93, -8.98])
    p1 = np.array([9.0, -3.92])
    p2 = np.array([-3.87, 8.95])
    p3_from_first_wall = np.array([-8.934999999999999, 3.8850000000000007])
    p3_from_second_wall = np.array([-8.935000000000002, 3.8849999999999962])
    segments = (
        (p0, p1),
        (p1, p2),
        (p2, p3_from_first_wall),
        (p3_from_second_wall, p0),
    )

    walls = []
    for index, (start, end) in enumerate(segments):
        direction = end - start
        normal = np.array([direction[1], -direction[0], 0.0])
        normal /= np.linalg.norm(normal)
        geometry = MoosasGeometry(
            np.array([
                [start[0], start[1], 0.0],
                [start[0], start[1], 3.0],
                [end[0], end[1], 3.0],
                [end[0], end[1], 0.0],
            ]),
            f"rotated_wall_{index}",
            normal,
            0,
        )
        model.geometryList.append(geometry)
        model.geoId.append(geometry.faceId)
        walls.append(MoosasWall(model, geometry))
    model.wallList = np.array(walls)

    network = TopoNetwork.inLevel(0.0, model)

    assert len(network.edges) == 4
    assert len(network.nodes) == 4
    assert len(network.outerBoundary()) == 1


def test_select_wall_does_not_create_missing_air_boundaries():
    model = MoosasModel()
    model.levelList = [0.0, 3.0]
    geometry = MoosasGeometry(
        np.array([
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 3.0],
            [5.0, 0.0, 3.0],
            [5.0, 0.0, 0.0],
        ]),
        "only_existing_wall",
        np.array([0.0, -1.0, 0.0]),
        0,
    )
    model.geometryList = [geometry]
    model.geoId = [geometry.faceId]
    wall = MoosasWall(model, geometry)
    model.wallList = np.array([wall])
    wall_count = len(model.wallList)
    boundary = shapely.polygons([[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 0.0]])

    with pytest.raises(GeometryError, match="no existing wall matches boundary segment"):
        MoosasEdge.selectWall(boundary, model.wallList)

    assert len(model.wallList) == wall_count


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
