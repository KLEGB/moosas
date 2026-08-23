from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from MoosasPy.simulation.energy.runner import energyAnalysis
from MoosasPy.simulation.radiation.calculation import writeRadGeo
from MoosasPy.simulation.airflow.runner import VentPaths
from MoosasPy.simulation.weather.epw import epw2wea


class SimulationWorkspaceTests(unittest.TestCase):
    def test_energy_defaults_are_removed_after_parsing(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        energy_input = {"zones": [zone], "args": []}
        recorded_paths = []

        def run_command(command, **_kwargs):
            output_path = Path(command[command.index("-o") + 1])
            output_path.write_text("output", encoding="utf-8")
            recorded_paths.append(output_path)

        with patch("MoosasPy.simulation.energy.runner.Runner.run_command", side_effect=run_command), patch(
            "MoosasPy.simulation.energy.runner.parseEnergyOutput", return_value={"total": {}}
        ):
            result = energyAnalysis(energyInput=energy_input)

        self.assertEqual(result, {"total": {}})
        self.assertEqual(len(recorded_paths), 1)
        self.assertFalse(recorded_paths[0].parent.exists())

    def test_weather_default_output_uses_temporary_directory(self):
        location = SimpleNamespace(stationId="station")

        def run_command(command, **_kwargs):
            Path(command[-1]).write_text("wea", encoding="utf-8")

        with patch("MoosasPy.simulation.weather.epw.Runner.run_command", side_effect=run_command):
            wea_path = Path(epw2wea(location, "input.epw"))

        self.assertTrue(wea_path.exists())
        self.assertNotIn("MoosasPy", str(wea_path))
        wea_path.unlink()
        wea_path.parent.rmdir()

    def test_radiation_and_vent_defaults_use_unique_workspaces(self):
        with TemporaryDirectory() as work_dir, patch(
            "MoosasPy.simulation.radiation.calculation.writeGeo"
        ) as write_geo:
            geo_path = Path(writeRadGeo(SimpleNamespace(), work_dir=work_dir))
            write_geo.assert_called_once_with(str(geo_path), unittest.mock.ANY)
            self.assertEqual(geo_path.name, "model.geo")
            self.assertEqual(geo_path.parent.parent, Path(work_dir))

            vent_paths = VentPaths.create(work_dir=work_dir)
            self.assertEqual(Path(vent_paths.workspace).parent, Path(work_dir))
            self.assertTrue(Path(vent_paths.project_dir).is_dir())
            self.assertTrue(Path(vent_paths.result_dir).is_dir())


if __name__ == "__main__":
    unittest.main()