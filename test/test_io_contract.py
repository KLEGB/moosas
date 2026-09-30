from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

from eppy.modeleditor import IDF
import pytest

from MoosasPy.model import MoosasModel
from MoosasPy.model.io.idf import exportIDF
from MoosasPy.model.io.idf.adapter import IDFtoXml, _idf_build_artifacts
from MoosasPy.model.io.idf.input import encodeFace
from MoosasPy.model.io.idf.model import FaceDefault, MoosasSettings
from MoosasPy.model.io.idf.version import bundled_template_idf_path, configure_idd
from MoosasPy.model.resources import configure_model_resources, rebuild_schedule_index
from MoosasPy.transform import transform
from MoosasPy.transform.geometry.element import MoosasElement, MoosasGeometry
from MoosasPy.transform.geometry.geos import Vector
from MoosasPy.utils import shapely


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_FIXTURE = PROJECT_ROOT / "test" / "caseFile" / "test3_geomove.geo"


@pytest.fixture(scope="module")
def semantic_model() -> MoosasModel:
    return transform(str(GEOMETRY_FIXTURE), input_type="geo", stdout=StringIO())


def test_model_initialization_does_not_load_external_resources():
    model = MoosasModel()

    assert model.buildingTemplate == {}
    assert model.schedule == {}
    assert not hasattr(model, "weather")
    assert not hasattr(model, "cumSky")
    assert not hasattr(model, "idfZoneTemplate")
    assert not hasattr(model, "loadSchedule")
    assert not hasattr(model, "loadWeatherData")


def test_resource_service_configures_a_domain_model():
    model = configure_model_resources(MoosasModel())

    assert model.buildingTemplate
    assert model.schedule
    assert model.scheduleByType


def test_schedule_index_uses_weekly_roots_regardless_of_insertion_order():
    schedules = {
        "OFF_EquipHeat_Weekend": {"type": "Daily", "value": [0.0] * 24},
        "OFF_EquipHeat_Weekly": {"type": "Weekly", "value": ["daily"] * 7},
        "OFF_EquipHeat_Weekday": {"type": "Daily", "value": [1.0] * 24},
    }
    model = MoosasModel()
    model.schedule = dict(reversed(list(schedules.items())))

    rebuild_schedule_index(model)

    assert model.scheduleByType["OFFICE"]["zone_equipment"] == "OFF_EquipHeat_Weekly"


def test_schedule_index_rejects_duplicate_weekly_roots():
    model = MoosasModel()
    model.schedule = {
        "OFF_EquipHeat_Weekly": {"type": "Weekly", "value": ["daily"] * 7},
        "OFF_EquipmentHeatGain_Weekly": {"type": "Weekly", "value": ["daily"] * 7},
    }

    with pytest.raises(ValueError, match="Multiple weekly schedules"):
        rebuild_schedule_index(model)


@pytest.mark.parametrize("suffix", (".geo", ".obj", ".stl"))
def test_load_rejects_raw_geometry_sources(suffix: str):
    with pytest.raises(ValueError, match="Unsupported model load format"):
        MoosasModel.load(f"raw-geometry{suffix}")


@pytest.mark.parametrize("suffix", (".geo", ".obj", ".stl"))
def test_save_rejects_raw_geometry_targets(suffix: str):
    model = MoosasModel()
    with pytest.raises(ValueError, match="Unsupported model save format"):
        model.save(f"raw-geometry{suffix}")


@pytest.mark.parametrize("suffix", (".graph.json", ".gbxml"))
def test_load_rejects_save_only_model_formats(suffix: str):
    with pytest.raises(ValueError, match="Unsupported model load format"):
        MoosasModel.load(f"model{suffix}")


@pytest.mark.parametrize("suffix", (".rdf", ".xml", ".json"))
def test_semantic_model_formats_round_trip(semantic_model: MoosasModel, suffix: str):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / f"model{suffix}"
        save_result = semantic_model.save(file_path)
        restored = MoosasModel.load(file_path)

    assert save_result.primary_path == file_path
    assert isinstance(restored, MoosasModel)
    assert len(restored.geometryList) == len(semantic_model.geometryList)
    assert len(restored.spaceList) == len(semantic_model.spaceList)
    assert len(restored.wallList) == len(semantic_model.wallList)


def test_json_round_trip_preserves_empty_shading(semantic_model: MoosasModel):
    original_shading = semantic_model.shadingList
    semantic_model.shadingList = []
    try:
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "model.json"
            semantic_model.save(file_path)
            document = json.loads(file_path.read_text(encoding="utf-8"))
            document["shading"] = None
            file_path.write_text(json.dumps(document), encoding="utf-8")
            restored = MoosasModel.load(file_path)
    finally:
        semantic_model.shadingList = original_shading

    assert restored.shadingList == []


@pytest.mark.parametrize("suffix", (".rdf", ".xml", ".json"))
def test_semantic_formats_preserve_shading_and_void_area(
    semantic_model: MoosasModel,
    suffix: str,
):
    source_geometry = semantic_model.geometryList[0]
    shading_geometry = MoosasGeometry(
        source_geometry.face,
        "roundtrip-shading-geometry",
        source_geometry.normal,
        -1,
    )
    original_shading = semantic_model.shadingList
    semantic_model.geometryList.append(shading_geometry)
    semantic_model.geoId.append(shading_geometry.faceId)
    shading = MoosasElement(semantic_model, shading_geometry, uid="roundtrip-shading")
    semantic_model.shadingList = [shading]
    try:
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / f"model{suffix}"
            semantic_model.save(file_path)
            restored = MoosasModel.load(file_path)
    finally:
        semantic_model.shadingList = original_shading
        semantic_model.geometryList.pop()
        semantic_model.geoId.pop()

    assert [(item.Uid, list(item.faceId)) for item in restored.shadingList] == [
        (shading.Uid, list(shading.faceId))
    ]
    assert sum(space.area for space in restored.spaceList) == pytest.approx(
        sum(space.area for space in semantic_model.spaceList)
    )


def test_rdf_round_trip_loads_spaces_in_stable_uri_order(semantic_model: MoosasModel):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / "model.rdf"
        semantic_model.save(file_path)
        restored = MoosasModel.load(file_path)

    restored_ids = [space.id for space in restored.spaceList]
    assert restored_ids == sorted(restored_ids, key=lambda value: f"Space_{value}")


def test_rdf_round_trip_preserves_air_boundaries_as_walls(semantic_model: MoosasModel):
    source_air_walls = [wall for wall in semantic_model.wallList if wall.is_air_boundary]
    assert source_air_walls

    with TemporaryDirectory() as directory:
        file_path = Path(directory) / "air-boundaries.rdf"
        semantic_model.save(file_path)
        restored = MoosasModel.load(file_path)

    restored_air_walls = [wall for wall in restored.wallList if wall.is_air_boundary]
    assert len(restored_air_walls) == len(source_air_walls)
    assert all(glazing.category != 2 for glazing in restored.glazingList)


def test_idf_air_boundaries_use_native_simple_mixing(semantic_model: MoosasModel):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / "air-boundaries.idf"
        semantic_model.save(file_path)
        configure_idd()
        idf = IDF(str(file_path))

    air_boundaries = list(idf.idfobjects["CONSTRUCTION:AIRBOUNDARY"])
    air_boundary = air_boundaries[0]
    air_surfaces = [
        surface
        for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
        if surface.Construction_Name == "Moosas Air Boundary"
    ]

    assert len(air_boundaries) == 1
    assert air_boundary.Name == "Moosas Air Boundary"
    assert air_boundary.Air_Exchange_Method == "SimpleMixing"
    assert air_boundary.Simple_Mixing_Air_Changes_per_Hour == pytest.approx(0.5)
    assert air_boundary.Simple_Mixing_Schedule_Name == ""
    assert air_surfaces
    assert len(idf.idfobjects["ZONEMIXING"]) == 0


def test_idf_face_encoding_removes_unused_vertex_fields():
    settings = MoosasSettings(FaceDefault)
    triangle = shapely.polygons(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))

    encodeFace(settings, triangle, Vector(0.0, 0.0, 1.0))

    assert settings.params["Number_of_Vertices"] == 3
    assert "Vertex_4_Xcoordinate" not in settings.params
    assert "Vertex_4_Ycoordinate" not in settings.params
    assert "Vertex_4_Zcoordinate" not in settings.params


def test_idf_export_clones_simple_baseboard_hvac_per_zone(semantic_model: MoosasModel):
    configure_idd()
    with TemporaryDirectory() as directory:
        directory = Path(directory)
        template_path = directory / "baseboard-template.idf"
        output_path = directory / "baseboard-export.idf"
        template = IDF(str(bundled_template_idf_path()))
        connection = template.idfobjects["ZONEHVAC:EQUIPMENTCONNECTIONS"][0]
        zone_name = str(connection.Zone_Name)
        equipment_list = next(
            item for item in template.idfobjects["ZONEHVAC:EQUIPMENTLIST"]
            if str(item.Name) == str(connection.Zone_Conditioning_Equipment_List_Name)
        )
        equipment_list.Zone_Equipment_1_Object_Type = "ZoneHVAC:Baseboard:Convective:Electric"
        equipment_list.Zone_Equipment_1_Name = "template electric baseboard"
        template.newidfobject(
            "ZONEHVAC:BASEBOARD:CONVECTIVE:ELECTRIC",
            Name="template electric baseboard",
            Availability_Schedule_Name="Always On",
            Heating_Design_Capacity_Method="HeatingDesignCapacity",
            Heating_Design_Capacity=1000.0,
            Efficiency=1.0,
        )
        template.saveas(str(template_path))

        exportIDF(
            semantic_model,
            str(output_path),
            idfTemplatePath=str(template_path),
            zoneNameToSpaceDict={zone_name: [str(space.id) for space in semantic_model.spaceList]},
            hvac_mode="simple",
        )
        exported = IDF(str(output_path))

    equipment_lists = exported.idfobjects["ZONEHVAC:EQUIPMENTLIST"]
    baseboards = exported.idfobjects["ZONEHVAC:BASEBOARD:CONVECTIVE:ELECTRIC"]
    baseboards_by_name = {str(baseboard.Name): baseboard for baseboard in baseboards}

    assert len(equipment_lists) == len(semantic_model.spaceList)
    assert len(baseboards_by_name) == len(semantic_model.spaceList)
    assert not exported.idfobjects["SURFACEPROPERTY:INCIDENTSOLARMULTIPLIER"]
    assert all(
        equipment_list.Zone_Equipment_1_Object_Type == "ZoneHVAC:Baseboard:Convective:Electric"
        and str(equipment_list.Zone_Equipment_1_Name) in baseboards_by_name
        for equipment_list in equipment_lists
    )


def test_idf_export_uses_ideal_loads_for_complex_office_template(semantic_model: MoosasModel):
    template_path = PROJECT_ROOT / "temp" / "90032007981091.idf"
    if not template_path.is_file():
        pytest.skip("office template attachment is not present")

    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "office-ideal-loads.idf"
        exportIDF(
            semantic_model,
            str(output_path),
            idfTemplatePath=str(template_path),
            zoneNameToSpaceDict={"Space 0 ZN": [str(space.id) for space in semantic_model.spaceList]},
        )
        configure_idd()
        exported = IDF(str(output_path))

    assert not exported.idfobjects["AIRLOOPHVAC"]
    assert not exported.idfobjects["PLANTLOOP"]
    assert not exported.idfobjects["ZONEHVAC:AIRDISTRIBUTIONUNIT"]
    ideal_loads = {
        str(equipment.Name): equipment
        for equipment in exported.idfobjects["ZONEHVAC:IDEALLOADSAIRSYSTEM"]
    }
    assert len(ideal_loads) == len(semantic_model.spaceList)
    assert all(
        equipment_list.Zone_Equipment_1_Object_Type == "ZoneHVAC:IdealLoadsAirSystem"
        and str(equipment_list.Zone_Equipment_1_Name) in ideal_loads
        for equipment_list in exported.idfobjects["ZONEHVAC:EQUIPMENTLIST"]
    )


def test_idf_export_preserves_shading_geometry(semantic_model: MoosasModel):
    source_geometry = semantic_model.geometryList[0]
    shading_geometry = MoosasGeometry(
        source_geometry.face,
        "idf-shading-geometry",
        source_geometry.normal,
        -1,
    )
    shading = MoosasElement(semantic_model, shading_geometry, uid="idf-shading")
    original_shading = semantic_model.shadingList
    semantic_model.geometryList.append(shading_geometry)
    semantic_model.geoId.append(shading_geometry.faceId)
    semantic_model.shadingList = [shading]
    try:
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "shading.idf"
            semantic_model.save(file_path)
            configure_idd()
            idf = IDF(str(file_path))
    finally:
        semantic_model.shadingList = original_shading
        semantic_model.geometryList.pop()
        semantic_model.geoId.pop()

    exported = idf.idfobjects["SHADING:BUILDING:DETAILED"]
    expected_vertices = [
        tuple(point)
        for point in source_geometry.face.exterior.coords[:-1]
    ]
    actual_vertices = [
        (
            float(exported[0][f"Vertex_{index}_Xcoordinate"]),
            float(exported[0][f"Vertex_{index}_Ycoordinate"]),
            float(exported[0][f"Vertex_{index}_Zcoordinate"]),
        )
        for index in range(1, int(exported[0].Number_of_Vertices) + 1)
    ]

    assert [item.Name for item in exported] == ["idf-shading"]
    assert len(actual_vertices) == len(expected_vertices)
    for actual, expected in zip(actual_vertices, expected_vertices):
        assert actual == pytest.approx(expected)


def test_idf_import_serializes_detailed_shading_geometry(semantic_model: MoosasModel):
    base_vertices = (
        (0.0, 0.0),
        (2.0, 0.0),
        (2.0, 2.0),
        (0.0, 2.0),
    )
    expected_vertices = []
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / "shading-source.idf"
        semantic_model.save(file_path)
        configure_idd()
        idf = IDF(str(file_path))
        base_surface_name = idf.idfobjects["BUILDINGSURFACE:DETAILED"][0].Name
        for object_index, object_type in enumerate((
            "Shading:Site:Detailed",
            "Shading:Building:Detailed",
            "Shading:Zone:Detailed",
        )):
            vertices = tuple(
                (x, y, 5.0 + object_index)
                for x, y in base_vertices
            )
            expected_vertices.append(vertices)
            fields = {
                "Name": object_type,
                "Number_of_Vertices": len(vertices),
            }
            if object_type == "Shading:Zone:Detailed":
                fields["Base_Surface_Name"] = base_surface_name
            for index, (x, y, z) in enumerate(vertices, start=1):
                fields[f"Vertex_{index}_Xcoordinate"] = x
                fields[f"Vertex_{index}_Ycoordinate"] = y
                fields[f"Vertex_{index}_Zcoordinate"] = z
            idf.newidfobject(object_type, **fields)
        idf.save()

        records, faces, _, _ = _idf_build_artifacts(str(file_path))
        xml_path = Path(directory) / "shading-source.xml"
        IDFtoXml(str(file_path), str(xml_path))
        shading_nodes = ElementTree.parse(xml_path).getroot().findall("shading")

    shading_faces = [face for face in faces if face.cat == -1]
    assert len([record for record in records if record.family == "shading"]) == 3
    assert len(shading_faces) == 3
    assert {node.findtext("faceId") for node in shading_nodes} == {
        face.geo_id for face in shading_faces
    }
    assert {tuple(face.vertices) for face in shading_faces} == set(expected_vertices)


def test_unconditioned_space_exports_only_zone_and_surfaces(semantic_model: MoosasModel):
    core = semantic_model.spaceList[0]
    original_conditioned = core.conditioned
    core.conditioned = False
    prohibited = (
        "ZONEINFILTRATION:DESIGNFLOWRATE",
        "ZONEVENTILATION:DESIGNFLOWRATE",
        "ZONEVENTILATION:WINDANDSTACKOPENAREA",
        "OTHEREQUIPMENT",
        "ELECTRICEQUIPMENT",
        "PEOPLE",
        "LIGHTS",
        "SIZING:ZONE",
        "DESIGNSPECIFICATION:OUTDOORAIR",
        "DESIGNSPECIFICATION:ZONEAIRDISTRIBUTION",
        "ZONECONTROL:THERMOSTAT",
        "THERMOSTATSETPOINT:DUALSETPOINT",
        "ZONEHVAC:EQUIPMENTCONNECTIONS",
        "ZONEHVAC:EQUIPMENTLIST",
        "ZONEHVAC:IDEALLOADSAIRSYSTEM",
        "NODELIST",
    )
    try:
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "unconditioned-core.idf"
            semantic_model.save(file_path)
            configure_idd()
            idf = IDF(str(file_path))
    finally:
        core.conditioned = original_conditioned

    assert any(zone.Name == core.id for zone in idf.idfobjects["ZONE"])
    assert any(
        surface.Zone_Name == core.id
        for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]
    )
    zone_names = {zone.Name for zone in idf.idfobjects["ZONE"]}
    assert all(
        sizing.Zone_or_ZoneList_Name in zone_names
        for sizing in idf.idfobjects["SIZING:ZONE"]
    )
    for object_type in prohibited:
        assert all(core.id not in map(str, obj.fieldvalues) for obj in idf.idfobjects[object_type])


def test_all_unconditioned_spaces_remove_template_hvac(semantic_model: MoosasModel):
    original = [space.conditioned for space in semantic_model.spaceList]
    prohibited = (
        "SIZING:ZONE",
        "ZONECONTROL:THERMOSTAT",
        "ZONEHVAC:EQUIPMENTCONNECTIONS",
        "ZONEHVAC:EQUIPMENTLIST",
        "ZONEHVAC:IDEALLOADSAIRSYSTEM",
        "NODELIST",
    )
    try:
        for space in semantic_model.spaceList:
            space.conditioned = False
        with TemporaryDirectory() as directory:
            file_path = Path(directory) / "all-unconditioned.idf"
            semantic_model.save(file_path)
            configure_idd()
            idf = IDF(str(file_path))
    finally:
        for space, conditioned in zip(semantic_model.spaceList, original):
            space.conditioned = conditioned

    assert len(idf.idfobjects["ZONE"]) == len(semantic_model.spaceList)
    assert all(not idf.idfobjects[object_type] for object_type in prohibited)


@pytest.mark.parametrize("suffix", (".graph.json", ".gbxml"))
def test_save_only_model_projections(semantic_model: MoosasModel, suffix: str):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / f"model{suffix}"
        result = semantic_model.save(file_path)

        assert result.generated_paths == (file_path,)
        assert file_path.is_file()
