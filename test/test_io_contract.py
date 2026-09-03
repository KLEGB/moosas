from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from eppy.modeleditor import IDF
import pytest

from MoosasPy.model import MoosasModel
from MoosasPy.model.io.idf.version import configure_idd
from MoosasPy.model.resources import configure_model_resources
from MoosasPy.transform import transform


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
    assert air_boundary.Simple_Mixing_Schedule_Name == "Always On"
    assert air_surfaces
    assert len(idf.idfobjects["ZONEMIXING"]) == 0


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
