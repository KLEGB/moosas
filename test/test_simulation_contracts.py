import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import MoosasPy
from MoosasPy.simulation import CommandResult, SimulationResult
from MoosasPy.simulation.energy.runner import EnergyResult, EnergyRunner
from MoosasPy.simulation.coupling import EnergyAirflowCoupler
from MoosasPy.simulation.radiation.runner import RadianceDaylightResult
from MoosasPy.simulation.airflow.runner import AirflowResult, AirflowRunner, VentPaths


class SimulationContractTests(unittest.TestCase):
    def test_root_api_contains_only_transform_io_and_simulation(self):
        self.assertEqual(
            set(MoosasPy.__all__),
            {"__version__", "load", "save", "simulation", "transform"},
        )
        self.assertEqual(MoosasPy.transform.__name__, "MoosasPy.transform")
        self.assertTrue(callable(MoosasPy.transform.transform))
        self.assertTrue(callable(MoosasPy.load))
        self.assertTrue(callable(MoosasPy.save))
        self.assertFalse(hasattr(MoosasPy, "energyAnalysis"))
        self.assertFalse(hasattr(MoosasPy, "includeEpw"))
        self.assertFalse(hasattr(MoosasPy, "positionRadiation"))
        self.assertFalse(hasattr(MoosasPy, "positionSunHour"))

    def test_simulation_aggregates_domain_modules(self):
        self.assertEqual(MoosasPy.simulation.energy.__name__, "MoosasPy.simulation.energy")
        self.assertEqual(MoosasPy.simulation.radiation.__name__, "MoosasPy.simulation.radiation")
        self.assertEqual(MoosasPy.simulation.airflow.__name__, "MoosasPy.simulation.airflow")
        self.assertEqual(MoosasPy.simulation.weather.__name__, "MoosasPy.simulation.weather")
        self.assertEqual(MoosasPy.simulation.coupling.__name__, "MoosasPy.simulation.coupling")

    def test_base_result_defaults_to_empty_diagnostics(self):
        result = SimulationResult()

        self.assertEqual(result.commands, ())
        self.assertEqual(result.warnings, ())

    def test_radiance_result_implements_shared_contract(self):
        command = CommandResult(("oconv", "model.rad"), 0, "", "")
        result = RadianceDaylightResult(commands=(command,), warnings=("coarse grid",))

        self.assertIsInstance(result, SimulationResult)
        self.assertEqual(result.floors, ())
        self.assertEqual(result.commands, (command,))
        self.assertEqual(result.warnings, ("coarse grid",))

    def test_energy_result_implements_shared_contract(self):
        result = EnergyResult(data={"total": {"cooling": 10.0}})

        self.assertIsInstance(result, SimulationResult)
        self.assertEqual(result.as_legacy(), {"total": {"cooling": 10.0}})

    def test_energy_runner_returns_parsed_data_and_command_diagnostics(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        energy_input = {"zones": [zone], "args": []}
        command_result = CommandResult(("MoosasEnergy",), 0, "", "")

        with TemporaryDirectory() as work_dir, patch(
            "MoosasPy.simulation.energy.runner.Runner.run_command", return_value=command_result
        ), patch(
            "MoosasPy.simulation.energy.runner.parseEnergyOutput", return_value={"total": {}}
        ):
            result = EnergyRunner(energy_input=energy_input, work_dir=work_dir).run()

        self.assertEqual(result.as_legacy(), {"total": {}})
        self.assertEqual(result.commands, (command_result,))

    def test_airflow_runner_returns_matrix_and_command_diagnostics(self):
        command_result = CommandResult(("contamx", "model.prj"), 0, "", "")
        matrix = [[0.0, 1.0], [1.0, 0.0]]

        with TemporaryDirectory() as work_dir:
            root = Path(work_dir)
            project_path = root / "model.prj"
            response_path = root / "response.txt"
            project_path.write_text("project", encoding="utf-8")
            response_path.write_text("response", encoding="utf-8")
            paths = VentPaths.from_workspace(root / "workspace")
            with patch(
                "MoosasPy.simulation.airflow.runner.AirflowRunner.run_command",
                return_value=command_result,
            ) as run_command, patch(
                "MoosasPy.simulation.airflow.runner.build_matrix", return_value=matrix
            ):
                result = AirflowRunner(
                    prj_file=str(project_path),
                    response_file=str(response_path),
                    paths=paths,
                ).run()

        self.assertIsInstance(result, AirflowResult)
        self.assertEqual(result.airflow_matrix, matrix)
        self.assertEqual(result.commands, (command_result, command_result))
        self.assertEqual(run_command.call_count, 2)

    def test_energy_airflow_coupler_is_exposed_by_coupling_package(self):
        self.assertEqual(EnergyAirflowCoupler.__module__, "MoosasPy.simulation.coupling.energy_airflow")


if __name__ == "__main__":
    unittest.main()