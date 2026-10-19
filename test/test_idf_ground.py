from io import StringIO

import pytest
import shapely
from eppy.modeleditor import IDF

from MoosasPy.model.io.idf import configure_idd
from MoosasPy.model.io.idf.ground import apply_ground_templates, capture_ground_templates
from MoosasPy.model.io.idf.materials import prune_unused_constructions_and_materials
from MoosasPy.utils.constant import geom


def empty_idf():
    configure_idd()
    return IDF(StringIO("Version,26.1;"))


def floor(idf, name, zone, construction, boundary, coordinates):
    surface = idf.newidfobject(
        "BuildingSurface:Detailed", Name=name, Zone_Name=zone,
        Surface_Type="Floor", Construction_Name=construction,
        Outside_Boundary_Condition=boundary, Sun_Exposure="NoSun",
        Wind_Exposure="NoWind",
    )
    surface.Number_of_Vertices = len(coordinates)
    for index, point in enumerate(coordinates, start=1):
        for axis, coordinate in zip("XYZ", point):
            surface[f"Vertex_{index}_{axis}coordinate"] = coordinate
    return surface


def rectangle(x0, y0, x1, y1):
    return [(x0, y0, 0), (x0, y1, 0), (x1, y1, 0), (x1, y0, 0)]


def f_factor_template():
    idf = empty_idf()
    idf.newidfobject(
        "Construction:FfactorGroundFloor", Name="template foundation",
        FFactor=1.26, Area=1000, PerimeterExposed=300,
    )
    idf.newidfobject(
        "Site:GroundTemperature:FCfactorMethod",
        **{f"{month}_Ground_Temperature": value for month, value in zip(
            ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"],
            range(10, 22),
        )},
    )
    floor(idf, "template floor", "template room", "template foundation",
          "GroundFCfactorMethod", rectangle(0, 0, 10, 10))
    return idf


def test_ground_export_preserves_f_factor_method_and_recalculates_geometry():
    idf = f_factor_template()
    temperatures = list(idf.idfobjects["SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"][0].obj)
    policies = capture_ground_templates(idf, {"template room": ["left", "right"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    first = floor(idf, "left floor", "left", "ordinary", "Ground", rectangle(0, 0, 4, 4))
    second = floor(idf, "right floor", "right", "ordinary", "Ground", rectangle(4, 0, 8, 4))

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    for surface in (first, second):
        assert surface.Outside_Boundary_Condition == "GroundFCfactorMethod"
        construction = constructions[surface.Construction_Name]
        assert construction.FFactor == pytest.approx(1.26)
        assert construction.Area == pytest.approx(16)
        assert construction.PerimeterExposed == pytest.approx(12)
    assert first.Construction_Name != second.Construction_Name
    assert list(idf.idfobjects["SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"][0].obj) == temperatures
    assert not idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]


def test_partitioned_floor_uses_surface_areas_and_excludes_internal_edges():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    left = floor(idf, "left part", "room", "ordinary", "Ground", rectangle(0, 0, 2, 4))
    right = floor(idf, "right part", "room", "ordinary", "Ground", rectangle(2, 0, 4, 4))

    apply_ground_templates(idf, policies)

    assert left.Construction_Name == right.Construction_Name
    construction = next(c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]
                        if c.Name == left.Construction_Name)
    assert construction.Area == pytest.approx(8)
    assert construction.PerimeterExposed == pytest.approx(8)
    assert len(left.coords) == len(right.coords) == 4


@pytest.mark.parametrize("seam_offset", [0, 0.0008, 0.001])
def test_precision_scale_seams_preserve_face_areas_and_whole_slab_conductance(seam_offset):
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["left", "right"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    surfaces = [
        floor(idf, "left floor", "left", "ordinary", "Ground", rectangle(0, 0, 4, 4)),
        floor(idf, "right floor", "right", "ordinary", "Ground",
              rectangle(4 - seam_offset, 0, 8, 4)),
    ]
    coordinates = [list(surface.coords) for surface in surfaces]
    footprints = [
        shapely.set_precision(shapely.Polygon([(x, y) for x, y, _ in points]), geom.POINT_PRECISION)
        for points in coordinates
    ]
    perimeter = shapely.union_all(footprints, grid_size=geom.POINT_PRECISION).length
    area = sum(polygon.area for polygon in footprints)

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assigned = [constructions[s.Construction_Name] for s in surfaces]
    assert [list(surface.coords) for surface in surfaces] == coordinates
    assert [c.Area for c in assigned] == pytest.approx([p.area for p in footprints])
    assert sum(c.FFactor * c.PerimeterExposed for c in assigned) == pytest.approx(1.26 * perimeter)
    assert all(c.Area / (c.FFactor * c.PerimeterExposed) == pytest.approx(area / (1.26 * perimeter))
               for c in assigned)


def test_sloped_t_junction_union_rounding_is_not_reported_as_overlap():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["lower", "upper"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    lower = [(0, 0, 0), (10, 0, 0), (10, 5.003, 0), (0, 5, 0)]
    upper = [(0, 5, 0), (4, 5.0012, 0), (4, 10, 0), (0, 10, 0)]
    surfaces = [
        floor(idf, "lower floor", "lower", "ordinary", "Ground", lower),
        floor(idf, "upper floor", "upper", "ordinary", "Ground", upper),
    ]
    raw = [shapely.Polygon([(x, y) for x, y, _ in points]) for points in (lower, upper)]
    assert raw[0].intersection(raw[1]).area == pytest.approx(0)
    footprints = [shapely.set_precision(polygon, geom.POINT_PRECISION) for polygon in raw]
    slab = shapely.union_all(footprints, grid_size=geom.POINT_PRECISION)
    area = sum(polygon.area for polygon in footprints)
    assert abs(area - slab.area) > geom.POINT_PRECISION ** 2

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assigned = [constructions[s.Construction_Name] for s in surfaces]
    assert sum(c.Area for c in assigned) == pytest.approx(area)
    assert sum(c.FFactor * c.PerimeterExposed for c in assigned) == pytest.approx(1.26 * slab.length)


@pytest.mark.parametrize("coordinates", [
    rectangle(0, 0, 4, 4),
    rectangle(1, 1, 3, 3),
    rectangle(2, 0, 6, 4),
    rectangle(3.9989, 0, 8, 4),
])
def test_ground_overlap_beyond_precision_reports_surfaces_and_zones(coordinates):
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["first zone", "second zone"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    floor(idf, "first floor", "first zone", "ordinary", "Ground", rectangle(0, 0, 4, 4))
    floor(idf, "second floor", "second zone", "ordinary", "Ground", coordinates)

    with pytest.raises(ValueError, match="Overlapping ground floors") as error:
        apply_ground_templates(idf, policies)

    assert all(name in str(error.value)
               for name in ("first floor", "second floor", "first zone", "second zone"))


def test_interior_zone_receives_area_weighted_equivalent_perimeter():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["center", "outside"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    center = floor(idf, "center", "center", "ordinary", "Ground", rectangle(1, 1, 3, 3))
    for name, coordinates in [
        ("bottom", rectangle(0, 0, 4, 1)), ("top", rectangle(0, 3, 4, 4)),
        ("left", rectangle(0, 1, 1, 3)), ("right", rectangle(3, 1, 4, 3)),
    ]:
        floor(idf, name, "outside", "ordinary", "Ground", coordinates)

    apply_ground_templates(idf, policies)

    construction = next(c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]
                        if c.Name == center.Construction_Name)
    assert construction.PerimeterExposed == 4
    assert construction.Area == 4


def test_ground_export_preserves_ordinary_ground_temperature_and_construction():
    idf = empty_idf()
    idf.newidfobject("Construction", Name="template slab", Outside_Layer="soil layer")
    temperature = idf.newidfobject("Site:GroundTemperature:BuildingSurface",
                                  January_Ground_Temperature=14)
    floor(idf, "source", "source", "template slab", "Ground", rectangle(0, 0, 2, 2))
    policies = capture_ground_templates(idf, {"source": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    target = floor(idf, "target", "room", "generated slab", "Ground", rectangle(0, 0, 4, 4))

    apply_ground_templates(idf, policies)

    assert target.Outside_Boundary_Condition == "Ground"
    assert target.Construction_Name == "template slab"
    assert temperature.January_Ground_Temperature == 14
    assert not idf.idfobjects["SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"]


def test_upper_template_zone_inherits_only_an_unambiguous_ground_policy():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"upper room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    target = floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    apply_ground_templates(idf, policies)

    assert target.Outside_Boundary_Condition == "GroundFCfactorMethod"


@pytest.mark.parametrize("boundary", ["Foundation", "GroundSlabPreprocessorAverage"])
def test_unsupported_template_ground_method_is_not_silently_downgraded(boundary):
    idf = empty_idf()
    floor(idf, "source", "source", "slab", boundary, rectangle(0, 0, 4, 4))
    policies = capture_ground_templates(idf, {"source": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    with pytest.raises(ValueError, match="ground|Ground"):
        apply_ground_templates(idf, policies)


def test_ground_method_requires_matching_foundation_construction():
    idf = f_factor_template()
    idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"] = []
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))
    with pytest.raises(ValueError, match="construction|Construction"):
        apply_ground_templates(idf, policies)


def test_conflicting_template_ground_methods_require_explicit_zone_mapping():
    idf = f_factor_template()
    idf.newidfobject("Construction", Name="other slab", Outside_Layer="soil")
    floor(idf, "other floor", "other room", "other slab", "Ground", rectangle(0, 0, 4, 4))
    policies = capture_ground_templates(idf, {"upper room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    with pytest.raises(ValueError, match="Ambiguous template ground"):
        apply_ground_templates(idf, policies)


def test_mapped_ground_zone_is_not_affected_by_other_zones_different_method():
    idf = f_factor_template()
    idf.newidfobject("Construction", Name="other slab", Outside_Layer="soil")
    floor(idf, "other floor", "other room", "other slab", "Ground", rectangle(0, 0, 4, 4))
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    target = floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    apply_ground_templates(idf, policies)

    assert target.Outside_Boundary_Condition == "GroundFCfactorMethod"


def test_missing_ground_temperatures_warns_without_inventing_an_object():
    idf = f_factor_template()
    idf.idfobjects["SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"] = []
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    target = floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    with pytest.warns(UserWarning, match="no SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"):
        apply_ground_templates(idf, policies)

    assert target.Outside_Boundary_Condition == "GroundFCfactorMethod"
    assert not idf.idfobjects["SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"]
    assert not idf.idfobjects["SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"]


def test_courtyard_edges_contribute_to_exposed_perimeter():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    for name, coordinates in [
        ("bottom", rectangle(0, 0, 4, 1)), ("top", rectangle(0, 3, 4, 4)),
        ("left", rectangle(0, 1, 1, 3)), ("right", rectangle(3, 1, 4, 3)),
    ]:
        floor(idf, name, "room", "ordinary", "Ground", coordinates)

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assigned = [constructions[s.Construction_Name] for s in idf.idfobjects["BUILDINGSURFACE:DETAILED"]]
    assert sum(c.Area for c in assigned) == pytest.approx(12)
    assert sum(c.PerimeterExposed for c in assigned) == pytest.approx(24)
    assert all(c.FFactor == 1.26 for c in assigned)


def test_tiny_triangle_preserves_whole_slab_conductance_without_negative_resistance():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["triangle", "rest"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    small = floor(idf, "small", "triangle", "ordinary", "Ground",
                  [(0, 0, 0), (0.478, 0, 0), (0, 7.546, 0)])
    large = floor(idf, "large", "rest", "ordinary", "Ground",
                  [(0.478, 0, 0), (8, 0, 0), (8, 8, 0), (0, 8, 0), (0, 7.546, 0)])

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assigned = [constructions[s.Construction_Name] for s in (small, large)]
    assert assigned[0].Area == pytest.approx(1.803494)
    assert sum(c.Area for c in assigned) == pytest.approx(64)
    assert sum(c.FFactor * c.PerimeterExposed for c in assigned) == pytest.approx(1.26 * 32)
    assert all(c.Area / (c.FFactor * c.PerimeterExposed) == pytest.approx(64 / (1.26 * 32))
               for c in assigned)


def test_disconnected_slabs_are_equivalenced_separately():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["small", "large"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    small = floor(idf, "small", "small", "ordinary", "Ground", rectangle(0, 0, 4, 4))
    large = floor(idf, "large", "large", "ordinary", "Ground", rectangle(10, 0, 18, 8))

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assert constructions[small.Construction_Name].PerimeterExposed == pytest.approx(16)
    assert constructions[large.Construction_Name].PerimeterExposed == pytest.approx(32)


def test_equivalent_perimeter_respects_face_bound_without_changing_conductance():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["main", "wing"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    main = floor(idf, "main", "main", "ordinary", "Ground", rectangle(0, 0, 10, 10))
    wing = floor(idf, "wing", "wing", "ordinary", "Ground", rectangle(10, 0, 30, 1))

    apply_ground_templates(idf, policies)

    constructions = {c.Name: c for c in idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]}
    assigned = [constructions[s.Construction_Name] for s in (main, wing)]
    assert assigned[0].PerimeterExposed == pytest.approx(40)
    assert assigned[0].FFactor == pytest.approx(2.1)
    assert assigned[1].PerimeterExposed <= 42
    assert sum(c.FFactor * c.PerimeterExposed for c in assigned) == pytest.approx(1.26 * 80)
    assert all(c.Area / (c.FFactor * c.PerimeterExposed) == pytest.approx(120 / (1.26 * 80))
               for c in assigned)


def test_existing_generated_ground_construction_is_reused_without_duplicate_names():
    idf = f_factor_template()
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    target = floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))
    apply_ground_templates(idf, policies)
    expected_name = target.Construction_Name
    target.Outside_Boundary_Condition = "Ground"
    target.Construction_Name = "ordinary"

    apply_ground_templates(idf, policies)

    assert target.Construction_Name == expected_name
    assert len(idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]) == 2


@pytest.mark.parametrize("factor", [0, -1, float("nan"), float("inf")])
def test_invalid_template_f_factor_fails_explicitly(factor):
    idf = f_factor_template()
    idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"][0].FFactor = factor
    policies = capture_ground_templates(idf, {"template room": ["room"]})
    idf.idfobjects["BUILDINGSURFACE:DETAILED"] = []
    floor(idf, "target", "room", "ordinary", "Ground", rectangle(0, 0, 4, 4))

    with pytest.raises(ValueError, match="invalid F-factor"):
        apply_ground_templates(idf, policies)


def test_pruning_follows_idd_references_and_preserves_non_surface_consumers():
    idf = empty_idf()
    for name in ("slab", "unused slab", "mass", "switchable"):
        idf.newidfobject("Material", Name=name, Roughness="Rough", Thickness=0.1,
                        Conductivity=1, Density=1000, Specific_Heat=1000)
        idf.newidfobject("Construction", Name=name, Outside_Layer=name)
    floor(idf, "floor", "room", "slab", "Ground", rectangle(0, 0, 4, 4))
    idf.newidfobject("InternalMass", Name="mass", Construction_Name="mass",
                    Zone_or_ZoneList_Name="room", Surface_Area=1)
    idf.newidfobject("EnergyManagementSystem:ConstructionIndexVariable",
                    Name="construction index", Construction_Object_Name="switchable")
    idf.newidfobject("Construction:FfactorGroundFloor", Name="unused foundation",
                    FFactor=1.26, Area=100, PerimeterExposed=40)
    idf.newidfobject("Construction:AirBoundary", Name="unused air")

    prune_unused_constructions_and_materials(idf)

    expected = {"slab", "mass", "switchable"}
    assert {c.Name for c in idf.idfobjects["CONSTRUCTION"]} == expected
    assert {m.Name for m in idf.idfobjects["MATERIAL"]} == expected
    assert not idf.idfobjects["CONSTRUCTION:FFACTORGROUNDFLOOR"]
    assert not idf.idfobjects["CONSTRUCTION:AIRBOUNDARY"]


def test_pruning_preserves_materials_referenced_by_window_shading():
    idf = empty_idf()
    idf.newidfobject("WindowMaterial:Shade", Name="active shade")
    idf.newidfobject("WindowMaterial:Shade", Name="unused shade")
    idf.newidfobject("WindowShadingControl", Name="control",
                    Shading_Device_Material_Name="active shade")

    prune_unused_constructions_and_materials(idf)

    assert [m.Name for m in idf.idfobjects["WINDOWMATERIAL:SHADE"]] == ["active shade"]


def test_pruning_does_not_treat_material_properties_as_unused_material_definitions():
    idf = empty_idf()
    idf.newidfobject("Material", Name="phase material")
    idf.newidfobject("Construction", Name="slab", Outside_Layer="phase material")
    properties = idf.newidfobject("MaterialProperty:PhaseChange", Name="phase material",
                                 Temperature_Coefficient_for_Thermal_Conductivity=0)
    floor(idf, "floor", "room", "slab", "Ground", rectangle(0, 0, 4, 4))

    prune_unused_constructions_and_materials(idf)

    assert list(idf.idfobjects["MATERIALPROPERTY:PHASECHANGE"]) == [properties]
    assert [m.Name for m in idf.idfobjects["MATERIAL"]] == ["phase material"]
