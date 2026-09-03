from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from MoosasPy.simulation.energy.runner import EnergyRunner
from MoosasPy.simulation.radiation.calculation import write_radiation_geometry
from MoosasPy.simulation.airflow.parser import read_file, read_topology
from MoosasPy.simulation.airflow.runner import AirflowResult, AirflowRunner, VentPaths, _contam_platform
from MoosasPy.simulation.weather.epw import convert_epw_to_wea


class SimulationWorkspaceTests(unittest.TestCase):
    def test_contam_platform_selects_supported_x86_64_binaries(self):
        self.assertEqual(_contam_platform("win32", "AMD64"), ("windows-x86_64", ".exe"))
        self.assertEqual(_contam_platform("linux", "x86_64"), ("linux-x86_64", ""))

    def test_contam_platform_rejects_unsupported_hosts(self):
        with self.assertRaisesRegex(OSError, "architecture"):
            _contam_platform("linux", "aarch64")
        with self.assertRaisesRegex(OSError, "platform"):
            _contam_platform("darwin", "x86_64")

    def test_energy_defaults_are_removed_after_parsing(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        energy_input = {"zones": [zone], "args": []}
        recorded_paths = []

        def run_command(command, **_kwargs):
            output_path = Path(command[command.index("-o") + 1])
            output_path.write_text("output", encoding="utf-8")
            recorded_paths.append(output_path)

        with patch("MoosasPy.simulation.energy.runner.Runner.run_command", side_effect=run_command), patch(
            "MoosasPy.simulation.energy.runner.parse_energy_output", return_value={"total": {}}
        ):
            result = EnergyRunner(energy_input=energy_input).run()

        self.assertEqual(result.data, {"total": {}})
        self.assertEqual(len(recorded_paths), 1)
        self.assertFalse(recorded_paths[0].parent.exists())

    def test_weather_conversion_uses_explicit_output_path(self):
        def run_command(command, **_kwargs):
            Path(command[-1]).write_text("wea", encoding="utf-8")

        with TemporaryDirectory() as work_dir, patch(
            "MoosasPy.simulation.weather.epw.Runner.run_command", side_effect=run_command
        ):
            output_path = Path(work_dir) / "station.wea"
            wea_path = Path(convert_epw_to_wea("input.epw", str(output_path)))

            self.assertEqual(wea_path, output_path)
            self.assertTrue(wea_path.exists())

    def test_airflow_default_workspace_is_owned_by_run(self):
        observed_paths = []

        def run_in_workspace(runner, report):
            observed_paths.append(Path(report.path))
            self.assertTrue(observed_paths[-1].is_dir())
            return AirflowResult(workspace=report)

        with TemporaryDirectory() as work_dir, patch.object(
            VentPaths,
            "from_workspace",
            side_effect=lambda root: SimpleNamespace(workspace=str(root)),
        ) as from_workspace, patch.object(
            AirflowRunner,
            "_run",
            autospec=True,
            side_effect=run_in_workspace,
        ):
            runner = AirflowRunner(model=SimpleNamespace(), work_dir=work_dir)
            self.assertIsNone(runner.paths)
            result = runner.run()

        self.assertFalse(result.workspace.retained)
        self.assertFalse(observed_paths[0].exists())
        from_workspace.assert_called_once()

    def test_contam_parsers_reject_sections_without_terminator(self):
        with TemporaryDirectory() as work_dir:
            project_path = Path(work_dir) / "broken.prj"
            project_path.write_text("zones\nheader\nzone row\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing -999 terminator"):
                read_file(project_path)

            project_path.write_text("flow paths\nheader\npath row\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing -999 terminator"):
                read_topology(project_path)

    def test_radiation_and_vent_defaults_use_unique_workspaces(self):
        with TemporaryDirectory() as work_dir, patch(
            "MoosasPy.simulation.radiation.calculation.writeGeo"
        ) as write_geo:
            geo_path = Path(write_radiation_geometry(SimpleNamespace(), work_dir=work_dir))
            write_geo.assert_called_once_with(str(geo_path), unittest.mock.ANY)
            self.assertEqual(geo_path.name, "model.geo")
            self.assertEqual(geo_path.parent.parent, Path(work_dir))

            vent_paths = VentPaths.create(work_dir=work_dir)
            self.assertEqual(Path(vent_paths.workspace).parent, Path(work_dir))
            self.assertTrue(Path(vent_paths.project_dir).is_dir())
            self.assertTrue(Path(vent_paths.result_dir).is_dir())
            self.assertTrue(Path(vent_paths.contamx).is_file())
            self.assertTrue(Path(vent_paths.simread).is_file())
            self.assertEqual(Path(vent_paths.contamx).parent, Path(vent_paths.workspace) / "contam")
            self.assertEqual(Path(vent_paths.response).name, "response.txt")


if __name__ == "__main__":
    unittest.main()
