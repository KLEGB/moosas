from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from MoosasPy.model import MoosasModel
from MoosasPy.transform import transform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_FIXTURE = PROJECT_ROOT / "test" / "caseFile" / "test8_topology.geo"


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


@pytest.mark.parametrize("suffix", (".graph.json", ".gbxml"))
def test_save_only_model_projections(semantic_model: MoosasModel, suffix: str):
    with TemporaryDirectory() as directory:
        file_path = Path(directory) / f"model{suffix}"
        result = semantic_model.save(file_path)

        assert result.generated_paths == (file_path,)
        assert file_path.is_file()
