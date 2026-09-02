from functools import lru_cache
from io import StringIO
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from MoosasPy.simulation.energy.runner import EnergyRunner
from MoosasPy.simulation.weather import load_station_weather
from MoosasPy.transform import TransformOptions, transform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_DIRECTORY = PROJECT_ROOT / "test" / "caseFile"
ENERGY_ENGINE = PROJECT_ROOT / "MoosasPy" / "libs" / "energy" / "MoosasEnergy.exe"
BEIJING_WEATHER = PROJECT_ROOT / "MoosasPy" / "db" / "weather" / "545110.csv"


@lru_cache(maxsize=None)
def _transform_divided_case(case_name):
    return transform(
        str(CASE_DIRECTORY / case_name),
        input_type="geo",
        stdout=StringIO(),
        options=TransformOptions(divided_zones=True),
    )


@pytest.mark.parametrize(
    "case_name",
    (
        "test0_6spacesIntersection.geo",
        "test2_cortyard.geo",
        "test4_skylight.geo",
    ),
)
def test_divided_zone_cases_build_simulation_ready_topology(case_name):
    model = _transform_divided_case(case_name)

    space_ids = [str(space.id) for space in model.spaceList]
    assert space_ids
    assert len(space_ids) == len(set(space_ids))
    assert all(space.area > 0 for space in model.spaceList)
    assert all(
        len({str(space_id) for space_id in wall.space}) == 2
        for wall in model.wallList
        if wall.is_air_boundary
    )


def test_courtyard_case_generates_two_sided_air_boundaries():
    model = _transform_divided_case("test2_cortyard.geo")
    air_walls = [wall for wall in model.wallList if wall.is_air_boundary]

    assert len(model.spaceList) == 52
    assert len(air_walls) == 18
    assert all(len({str(space_id) for space_id in wall.space}) == 2 for wall in air_walls)


@pytest.mark.skipif(
    not ENERGY_ENGINE.is_file() or not BEIJING_WEATHER.is_file(),
    reason="requires the bundled MoosasEnergy engine and Beijing 545110 weather data",
)
def test_divided_zone_model_runs_energy_simulation():
    model = _transform_divided_case("test0_6spacesIntersection.geo")

    with TemporaryDirectory() as work_dir:
        result = EnergyRunner(
            model=model,
            weather=load_station_weather("545110"),
            work_dir=work_dir,
            timeout_seconds=60,
        ).run()

    assert result.commands[0].returncode == 0
    assert len(result.data["spaces"]) == len(model.spaceList)
    assert len(result.data["months"]) == 12
    totals = {key: float(result.data["total"][key]) for key in ("cooling", "heating", "lighting", "total")}
    assert all(math.isfinite(value) and value >= 0 for value in totals.values())
    assert totals["cooling"] == pytest.approx(10.19, abs=0.01)
    assert totals["heating"] == pytest.approx(32.43, abs=0.01)
    assert totals["lighting"] == pytest.approx(2.63, abs=0.01)
    assert totals["total"] == pytest.approx(45.25, abs=0.01)
