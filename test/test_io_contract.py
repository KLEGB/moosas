from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from eppy.modeleditor import IDF
import pytest

from MoosasPy.model import MoosasModel
from MoosasPy.model.io.idf.version import configure_idd
from MoosasPy.transform import transform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_FIXTURE = PROJECT_ROOT / "test" / "caseFile" / "test3_geomove.geo"


@pytest.fixture(scope="module")
def semantic_model() -> MoosasModel:
    return transform(str(GEOMETRY_FIXTURE), input_type="geo", stdout=StringIO())


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


@pytest.mark.parametrize("suffix", (".graph.json", ".gbxml"))
def test_save_only_model_projections(semantic_model: MoosasModel, suffix: str):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / f"model{suffix}"
        result = semantic_model.save(file_path)

        assert result.generated_paths == (file_path,)
        assert file_path.is_file()
