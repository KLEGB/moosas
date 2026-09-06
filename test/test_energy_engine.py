from pathlib import Path

import numpy as np
import pytest

from MoosasPy.simulation.energy.engine import _lighting, parse_spaces, simulate_energy_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENERGY_FIXTURES = PROJECT_ROOT / "test" / "caseFile" / "energy"
WEATHER_FILE = PROJECT_ROOT / "MoosasPy" / "db" / "weather" / "545110.csv"


def test_space_perimeter_area_is_limited_to_floor_area():
    row = "3,100,120,20,10,0,0,0,0,0,0.5,2,0.5,26,0.5,18,2,2,8,18,0,0,0,0,0,0.5,1"

    space = parse_spaces([row])[0]

    assert space.perimeter_zone_area == 100.0


def test_public_lighting_uses_solar_altitude_in_degrees():
    lighting = _lighting(
        latitude=np.radians(39.93),
        altitude=55.0,
        day=172,
        hour=12,
        glazing_ratio=0.3,
        interior_area=70.0,
        perimeter_area=30.0,
        heat_gain=100.0,
    )

    assert lighting == pytest.approx(9626.0501308)


@pytest.mark.parametrize(
    ("building_type", "expected_total"),
    (
        (0, [15.14748801, 23.97725302, 21.402, 53.799]),
        (1, [13.67118254, 55.36738866, 19.47530843, 52.339]),
    ),
)
def test_schedule_driven_energy_matches_migrated_engine_baseline(building_type, expected_total):
    arguments = [
        "-w", str(WEATHER_FILE),
        "-t", str(building_type),
        "-l", "0.69691",
        "-a", "55",
        "-s", "0.78",
        "-d", "1",
        "-r", "1",
        "-z", "1",
        "-sch", str(ENERGY_FIXTURES / "test_schedule_v2.csv"),
    ]

    result = simulate_energy_file(ENERGY_FIXTURES / "Energy_sch_v2.i", arguments)

    np.testing.assert_allclose(result.total, expected_total, rtol=1e-8, atol=1e-8)
    assert result.spaces.shape == (11, 4)
    assert result.months.shape == (12, 4)
    assert result.days.shape == (365, 4)
    assert result.hours.shape == (8760, 4)
    assert result.zone_months.shape == (11, 12, 4)
    assert result.zone_days.shape == (11, 365, 4)
    assert result.zone_hours.shape == (11, 8760, 4)
    assert np.all(result.zone_hours >= 0)
