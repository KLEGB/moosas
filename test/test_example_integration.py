from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import unittest

from MoosasPy.model_resources import load_weather
from MoosasPy.simulation.energy.runner import EnergyRunner
from MoosasPy.transform import transform


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_FIXTURE = PROJECT_ROOT / "test" / "caseFile" / "test8_topology.geo"
ENERGY_ENGINE = PROJECT_ROOT / "MoosasPy" / "libs" / "energy" / "MoosasEnergy.exe"
BEIJING_WEATHER = PROJECT_ROOT / "MoosasPy" / "db" / "weather" / "545110.csv"


class ExampleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = transform(
            str(GEOMETRY_FIXTURE),
            input_type="geo",
            stdout=StringIO(),
        )

    def test_geometry_fixture_transforms_to_expected_topology(self):
        self.assertGreaterEqual(len(self.model.geometryList), 450)
        self.assertEqual(len(self.model.spaceList), 70)
        self.assertEqual(len(self.model.voidList), 0)
        self.assertEqual(len(self.model.wallList), 249)
        self.assertEqual(len(self.model.faceList), 153)
        self.assertEqual(len(self.model.glazingList), 91)
        self.assertEqual(len(self.model.skylightList), 0)
        self.assertEqual(
            tuple(self.model.levelList),
            (0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0),
        )
        self.assertTrue(all(space.area > 0 for space in self.model.spaceList))
        self.assertAlmostEqual(sum(space.area for space in self.model.spaceList), 28199.6484, places=4)

        neighbor_pairs = {
            tuple(sorted((str(space.id), str(neighbor_id))))
            for space in self.model.spaceList
            for neighbor_id in space.neighbor
            if str(neighbor_id) != str(space.id)
        }
        self.assertEqual(len(neighbor_pairs), 122)
        self.assertTrue(all(space.neighbor for space in self.model.spaceList))

    @unittest.skipUnless(
        ENERGY_ENGINE.is_file() and BEIJING_WEATHER.is_file(),
        "requires the bundled MoosasEnergy engine and Beijing 545110 weather data",
    )
    def test_energy_engine_returns_real_results_for_geometry_fixture(self):
        load_weather(self.model, "545110")

        with TemporaryDirectory() as work_dir:
            result = EnergyRunner(
                model=self.model,
                work_dir=work_dir,
                timeout_seconds=60,
            ).run()

        self.assertEqual(result.commands[0].returncode, 0)
        self.assertEqual(len(result.data["spaces"]), 70)
        self.assertEqual(len(result.data["months"]), 12)

        total = result.data["total"]
        component_total = 0.0
        for key in ("cooling", "heating", "lighting"):
            value = float(total[key])
            self.assertTrue(math.isfinite(value))
            self.assertGreaterEqual(value, 0.0)
            component_total += value
        self.assertGreater(component_total, 0.0)
        self.assertAlmostEqual(float(total["cooling"]), 3.54, places=2)
        self.assertAlmostEqual(float(total["heating"]), 11.59, places=2)
        self.assertAlmostEqual(float(total["lighting"]), 2.63, places=2)
        self.assertAlmostEqual(float(total["total"]), 17.76, places=2)
        self.assertAlmostEqual(float(total["total"]), component_total, places=6)


if __name__ == "__main__":
    unittest.main()