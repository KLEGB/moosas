from functools import lru_cache
from io import StringIO
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import pytest

from MoosasPy.simulation.energy.runner import EnergyRunner
from MoosasPy.simulation.weather import Location
from MoosasPy.simulation.weather.epw import read_weather_csv
from MoosasPy.transform import TransformOptions, transform
from MoosasPy.transform.geometry.element import MoosasSpace
from MoosasPy.utils import shapely
from MoosasPy.utils.constant import geom


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_DIRECTORY = PROJECT_ROOT / "test" / "caseFile"
BEIJING_WEATHER = PROJECT_ROOT / "MoosasPy" / "db" / "weather" / "545110.csv"


@lru_cache(maxsize=None)
def _transform_divided_case(case_name):
    return transform(
        str(CASE_DIRECTORY / case_name),
        input_type="geo",
        stdout=StringIO(),
        options=TransformOptions(divided_zones=True),
    )


def test_attic_is_preserved_without_divided_zones():
    model = transform(
        str(CASE_DIRECTORY / "test90_restockwithattic.geo"),
        input_type="geo",
        stdout=StringIO(),
        options=TransformOptions(divided_zones=False),
    )

    assert sum(space.space_type == "attic" for space in model.spaceList) == 1


def test_roof_classification_accepts_a_30_degree_slope():
    target_roof_normal_z = math.cos(math.radians(30.21))

    assert target_roof_normal_z >= geom.HORIZONTAL_ANGLE_THRESHOLD


def test_attic_is_not_rejected_by_standard_room_height():
    space = object.__new__(MoosasSpace)
    space.floor = SimpleNamespace(level=2.43, offset=0.0)
    space.ceiling = SimpleNamespace(level=3.2076, offset=0.0)
    space.space_type = "room"

    assert space.is_void()

    space.space_type = "attic"

    assert not space.is_void()


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

    assert len(model.spaceList) == 53
    assert len(air_walls) == 18
    assert all(len({str(space_id) for space_id in wall.space}) == 2 for wall in air_walls)


def test_divided_zones_preserve_explicit_shading_geometry():
    source = (CASE_DIRECTORY / "test0_6spacesIntersection.geo").read_text(encoding="utf-8")
    shading = """\
f,-1,preserved_shading
fn,0.447,0.000,-0.894
fv,0.000,-2.000,20.000
fv,4.000,-2.000,22.000
fv,4.000,-4.000,22.000
fv,0.000,-4.000,20.000
fh,0,1.000,-2.500,20.500
fh,0,3.000,-2.500,21.500
fh,0,3.000,-3.500,21.500
fh,0,1.000,-3.500,20.500
;
"""
    with TemporaryDirectory() as directory:
        source_path = Path(directory) / "divided-with-shading.geo"
        source_path.write_text(f"{source.rstrip()}\n{shading}", encoding="utf-8")
        model = transform(
            str(source_path),
            input_type="geo",
            stdout=StringIO(),
            options=TransformOptions(divided_zones=True, attach_shading=True),
        )

    preserved = next(item for item in model.shadingList if item.firstFaceId == "preserved_shading")
    geometry = preserved.geometry[0]
    rings = shapely.get_rings(geometry.face)
    outer = shapely.get_coordinates(rings[0], include_z=True)[:-1]
    hole = shapely.get_coordinates(rings[1], include_z=True)[:-1]

    assert geometry.category == -1
    assert np.ptp(outer[:, 2]) == pytest.approx(2.0)
    assert np.ptp(hole[:, 2]) == pytest.approx(1.0)


@pytest.mark.skipif(
    not BEIJING_WEATHER.is_file(),
    reason="requires Beijing 545110 weather data",
)
def test_divided_zone_model_runs_energy_simulation():
    model = _transform_divided_case("test0_6spacesIntersection.geo")

    result = EnergyRunner(
        model=model,
        weather=read_weather_csv(
            BEIJING_WEATHER,
            Location("545110", "BEIJING/PEKING", "-", 39.93, 116.28, 55.0, 100962.17),
        ),
    ).run()

    assert result.commands == ()
    assert len(result.data["spaces"]) == len(model.spaceList)
    assert len(result.data["months"]) == 12
    totals = {key: float(result.data["total"][key]) for key in ("cooling", "heating", "lighting", "equipment", "total")}
    assert all(math.isfinite(value) and value >= 0 for value in totals.values())
    assert totals["cooling"] == pytest.approx(13.93, abs=0.01)
    assert totals["heating"] == pytest.approx(20.05, abs=0.01)
    assert totals["lighting"] == pytest.approx(9.47, abs=0.01)
    assert totals["equipment"] == pytest.approx(14.08, abs=0.01)
    assert totals["total"] == pytest.approx(sum(totals[key] for key in ("cooling", "heating", "lighting", "equipment")), abs=0.01)
