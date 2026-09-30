"""Real GEO to runnable OpenFOAM 12 cases."""

from io import StringIO
from pathlib import Path
import json
import shutil

import numpy as np
import pytest
import shapely

from MoosasPy.transform import transform


@pytest.fixture(scope="module")
def building():
    return transform(str(Path(__file__).parent / "caseFile/test0_6spacesIntersection.geo"),
                     input_type="geo", stdout=StringIO())


@pytest.fixture(scope="module")
def indoor_model():
    return transform(str(Path(__file__).parent / "caseFile/test6_twoVolumes.geo"),
                     input_type="geo", stdout=StringIO())


def physical_conditions():
    return dict(viscosity=1.5e-5, turbulence_intensity=0.05,
                turbulence_length=1.0, iterations=1000)


def test_opening_in_one_part_of_a_multipart_wall():
    from MoosasPy.model import MoosasModel
    from MoosasPy.model.io._foam_case import _surface_triangles
    from MoosasPy.transform.geometry.element import MoosasElement

    model = MoosasModel()
    left = model.includeGeo(shapely.Polygon([(0, 0, 0), (2, 0, 0), (2, 0, 3), (0, 0, 3)]))
    right = model.includeGeo(shapely.Polygon([(2, 0, 0), (4, 0, 0), (4, 0, 3), (2, 0, 3)]))
    aperture = model.includeGeo(shapely.Polygon([(0.5, 0, 1), (1.5, 0, 1), (1.5, 0, 2), (0.5, 0, 2)]))
    opening = MoosasElement(model, aperture)
    wall = MoosasElement(model, [left, right], glazingElement=[opening])
    triangles = _surface_triangles(wall, {"inlet": opening})
    areas = {"inlet": 0.0, "walls": 0.0}
    for name, v in triangles:
        areas[name] += np.linalg.norm(np.cross(v[1] - v[0], v[2] - v[0])) / 2
    assert areas["inlet"] == pytest.approx(1.0)
    assert areas["walls"] == pytest.approx(11.0)


def indoor_conditions():
    return dict(**physical_conditions(),
                inlet={"opening": "gls_g_80", "velocity": [0.409451, 0.286966, 0]},
                outlet={"opening": "gls_g_79", "pressure": 0.0})


def outdoor_conditions():
    return dict(**physical_conditions(), velocity=[2.0, 0.0, 0.0],
                domain=[[-100, 120, 0], [0, 240, 45]],
                inside_point=[-90, 130, 5])


@pytest.mark.parametrize("scenario", ["indoor", "outdoor"])
def test_real_geo_saves_complete_case(building, indoor_model, tmp_path, scenario):
    model = indoor_model if scenario == "indoor" else building
    options = dict(space_index=37) if scenario == "indoor" else {}
    conditions = indoor_conditions() if scenario == "indoor" else outdoor_conditions()
    result = model.save(tmp_path / "case.foam", scenario=scenario, grid_size=2,
                        conditions=conditions, **options)
    assert result.primary_path == tmp_path / "case.foam"
    for name in ("system/blockMeshDict", "system/snappyHexMeshDict", "system/controlDict",
                 "system/fvSchemes", "system/fvSolution", "constant/physicalProperties",
                 "constant/momentumTransport", "0/U", "0/p", "0/k", "0/epsilon", "0/nut"):
        assert (tmp_path / name).is_file()
        assert tmp_path / name in result.generated_paths
    manifest = json.loads((tmp_path / "constant/moosasCase.json").read_text())
    assert manifest["scenario"] == scenario
    assert manifest["conditions"] == conditions
    assert manifest["openfoam_version"] == 12


def test_indoor_rejects_unknown_openings_before_writing(indoor_model, tmp_path):
    conditions = indoor_conditions()
    conditions["inlet"]["opening"] = "missing"
    with pytest.raises(ValueError, match="opening"):
        indoor_model.save(tmp_path / "case.foam", scenario="indoor", space_index=37,
                          conditions=conditions)
    assert not list(tmp_path.iterdir())


def test_outdoor_requires_explicit_physical_conditions(building, tmp_path):
    with pytest.raises(ValueError, match="conditions"):
        building.save(tmp_path / "case.foam", scenario="outdoor")
    assert not list(tmp_path.iterdir())


def test_outdoor_rejects_point_inside_building(building, tmp_path):
    conditions = outdoor_conditions()
    conditions["inside_point"] = [-56, 180, 2]
    with pytest.raises(ValueError, match="inside_point"):
        building.save(tmp_path / "case.foam", scenario="outdoor", conditions=conditions)
    assert not list(tmp_path.iterdir())


def test_indoor_rejects_outward_inlet_velocity(indoor_model, tmp_path):
    conditions = indoor_conditions()
    conditions["inlet"]["velocity"] = [-0.409451, -0.286966, 0]
    with pytest.raises(ValueError, match="into the room"):
        indoor_model.save(tmp_path / "case.foam", scenario="indoor", space_index=37,
                          conditions=conditions)
    assert not list(tmp_path.iterdir())


def test_case_does_not_overwrite_existing_files(building, tmp_path):
    existing = tmp_path / "notes.txt"
    existing.write_text("keep")
    with pytest.raises(FileExistsError):
        building.save(tmp_path / "case.foam", scenario="outdoor", conditions=outdoor_conditions())
    assert existing.read_text() == "keep"
    assert not (tmp_path / "constant").exists()


@pytest.mark.skipif(shutil.which("foamRun") is None, reason="OpenFOAM 12 is not on PATH")
@pytest.mark.parametrize("iterations", [1, 26])
def test_iteration_limit_is_not_reported_as_success(indoor_model, tmp_path, iterations):
    from MoosasPy.simulation.airflow import OpenFoamRunner

    conditions = indoor_conditions()
    conditions["iterations"] = iterations
    indoor_model.save(tmp_path / "case.foam", scenario="indoor", space_index=37,
                      grid_size=2, conditions=conditions)
    result = OpenFoamRunner(tmp_path).run()
    assert not result.converged
    assert not result.successful
    assert result.warnings
    assert result.time_directory.name == str(iterations)
    assert (tmp_path / "log.foamRun").is_file()


@pytest.mark.skipif(shutil.which("foamRun") is None, reason="OpenFOAM 12 is not on PATH")
@pytest.mark.parametrize("scenario", ["indoor", "outdoor"])
def test_real_geo_solves_and_conserves_flow(building, indoor_model, tmp_path, scenario):
    from MoosasPy.simulation.airflow.openfoam import OpenFoamRunner

    model = indoor_model if scenario == "indoor" else building
    conditions = indoor_conditions() if scenario == "indoor" else outdoor_conditions()
    options = dict(space_index=37) if scenario == "indoor" else {}
    model.save(tmp_path / "case.foam", scenario=scenario, grid_size=2 if scenario == "indoor" else 4,
               conditions=conditions, **options)
    result = OpenFoamRunner(tmp_path, timeout_seconds=180).run()
    assert result.successful
    assert result.converged
    assert result.relative_flow_imbalance < 0.01
    assert np.isfinite(list(result.patch_flows.values())).all()
    assert any(value < 0 for value in result.patch_flows.values())
    assert any(value > 0 for value in result.patch_flows.values())
    assert (result.time_directory / "U").is_file()
    assert (result.time_directory / "p").is_file()
