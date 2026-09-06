import math
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import MoosasPy
from MoosasPy.simulation import CommandResult, SimulationResult, WorkspaceReport
from MoosasPy.simulation.energy.runner import (
    EnergyResult,
    EnergyRunner,
    build_energy_input,
)
from MoosasPy.simulation.energy.engine import EnergyOutput
from MoosasPy.simulation.coupling import (
    EnergyAirflowCoupler,
    PVResult,
    run_facade_pv,
    run_roof_pv,
)
from MoosasPy.simulation.coupling.pv import _pv_output_to_data
from MoosasPy.simulation.radiation.runner import RadianceDaylightResult
from MoosasPy.utils.constant import buildingType
from MoosasPy.simulation.airflow.runner import (
    AirflowResult,
    AirflowRunner,
    AirflowZoneResult,
    VentPaths,
    _calculate_temperature,
)


class SimulationContractTests(unittest.TestCase):
    def test_root_api_contains_only_model_transform_and_simulation(self):
        self.assertEqual(
            set(MoosasPy.__all__),
            {"__version__", "MoosasModel", "TransformOptions", "simulation", "transform"},
        )
        self.assertEqual(MoosasPy.transform.__name__, "MoosasPy.transform")
        self.assertTrue(callable(MoosasPy.transform.transform))
        self.assertTrue(callable(MoosasPy.MoosasModel.load))
        self.assertTrue(callable(MoosasPy.MoosasModel().save))
        self.assertFalse(hasattr(MoosasPy, "load"))
        self.assertFalse(hasattr(MoosasPy, "save"))
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

    def test_airflow_exposes_only_model_driven_simulation_api(self):
        airflow = MoosasPy.simulation.airflow

        self.assertEqual(
            set(airflow.__all__),
            {"AirflowResult", "AirflowRunner", "AirflowZoneResult", "create_openfoam_workspace"},
        )
        for legacy_name in ("iterateFile", "iterateProjects", "contam_iteration", "runFile"):
            self.assertFalse(hasattr(airflow, legacy_name))

    def test_weather_exports_unprefixed_sky_types(self):
        weather = MoosasPy.simulation.weather

        self.assertEqual(weather.DirectSky.__name__, "DirectSky")
        self.assertEqual(weather.CumulativeSky.__name__, "CumulativeSky")
        self.assertEqual(weather.WeatherData.__name__, "WeatherData")
        self.assertFalse(hasattr(weather, "MoosasDirectSky"))
        self.assertFalse(hasattr(weather, "MoosasCumSky"))
        self.assertFalse(hasattr(weather, "MoosasWeather"))
        self.assertFalse(hasattr(weather, "includeEpw"))
        self.assertFalse(hasattr(weather, "loadCumSky"))

    def test_energy_exposes_only_formal_runner_and_snake_case_helpers(self):
        energy = MoosasPy.simulation.energy

        self.assertEqual(
            set(energy.__all__),
            {"EnergyResult", "EnergyRunner", "build_energy_input", "calculate_pv_generation"},
        )
        for legacy_name in ("energyAnalysis", "getEnergyInput", "parseEnergyOutput"):
            self.assertFalse(hasattr(energy, legacy_name))

    def test_radiation_exposes_only_formal_runner_and_snake_case_helpers(self):
        radiation = MoosasPy.simulation.radiation

        self.assertEqual(
            set(radiation.__all__),
            {
                "DaylightFloorResult",
                "RadianceCommandError",
                "RadianceCommandResult",
                "RadianceDaylightResult",
                "RadianceRunner",
                "RadianceSky",
                "RadianceTimeoutError",
                "calculate_face_radiation",
                "calculate_model_radiation",
                "calculate_position_radiation",
                "calculate_position_sun_hours",
                "calculate_space_radiation",
                "estimate_space_daylight_factor",
                "ray_test",
                "write_radiation_geometry",
            },
        )
        for legacy_name in (
            "faceRadiation",
            "modelRadiation",
            "positionRadiation",
            "positionSunHour",
            "simModel",
            "spaceRadiation",
        ):
            self.assertFalse(hasattr(radiation, legacy_name))

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
        self.assertEqual(result.data, {"total": {"cooling": 10.0}})

    def test_pv_result_implements_shared_contract(self):
        result = PVResult(data={"total": 10.0})

        self.assertIsInstance(result, SimulationResult)
        self.assertEqual(result.data, {"total": 10.0})

    def test_pv_output_uses_requested_temporal_scale(self):
        hourly = np.ones(8760)

        hourly_data = _pv_output_to_data(hourly, "hourly")
        daily_data = _pv_output_to_data(hourly, "daily")
        monthly_data = _pv_output_to_data(hourly, "monthly")

        self.assertEqual(len(hourly_data["hours"]), 8760)
        self.assertEqual(daily_data["days"], [24.0] * 365)
        self.assertEqual(monthly_data["months"]["Feb"], 28 * 24)
        self.assertEqual(sum(monthly_data["months"].values()), 8760.0)
        self.assertEqual(hourly_data["total"], daily_data["total"])
        self.assertEqual(daily_data["total"], monthly_data["total"])

    def test_pv_output_rejects_unknown_temporal_scale(self):
        with self.assertRaisesRegex(ValueError, "temporal_scale"):
            _pv_output_to_data(np.ones(8760), "annual")

    def test_pv_entry_points_accept_energy_options(self):
        model = SimpleNamespace(
            getAllFaces=lambda _: {"MoosasFace": [], "MoosasWall": []},
            levelList=[],
        )
        sky = np.zeros((145, 8760))

        with patch(
            "MoosasPy.simulation.coupling.pv.write_radiation_geometry",
            return_value="model.rad",
        ):
            roof = run_roof_pv(model, sky, core=buildingType.OFFICE)
            facade = run_facade_pv(
                model,
                sky,
                temporal_scale="daily",
                spatial_scale="zone",
            )

        self.assertEqual(len(roof.data["months"]), 12)
        self.assertEqual(len(facade.data["days"]), 365)

    def test_energy_runner_returns_python_engine_data(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        energy_input = {"zones": [zone], "args": ["-w", "weather.csv"]}
        output = EnergyOutput(
            total=np.zeros(4), spaces=np.zeros((1, 4)), months=np.zeros((12, 4))
        )

        with patch("MoosasPy.simulation.energy.runner.simulate_energy", return_value=output):
            result = EnergyRunner(energy_input=energy_input).run()

        self.assertEqual(result.data["total"]["total"], 0.0)
        self.assertEqual(result.commands, ())

    def test_energy_runner_does_not_mutate_reused_input(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        energy_input = {"zones": [zone], "args": ["-w", "weather.csv"]}
        output = EnergyOutput(
            total=np.zeros(4), spaces=np.zeros((1, 4)), months=np.zeros((12, 4)),
            hours=np.zeros((8760, 4)), zone_months=np.zeros((1, 12, 4)),
            zone_hours=np.zeros((1, 8760, 4)),
        )

        with patch("MoosasPy.simulation.energy.runner.simulate_energy", return_value=output):
            runner = EnergyRunner(
                energy_input=energy_input,
                temporal_scale="hourly",
                spatial_scale="zone",
            )
            runner.run()
            runner.run()

        self.assertEqual(energy_input["args"], ["-w", "weather.csv"])

    def test_energy_scales_map_to_one_temporal_flag_and_one_spatial_flag(self):
        space = SimpleNamespace(
            id="zone-1",
            settings={},
            area=10.0,
            height=3.0,
            edge=SimpleNamespace(wall=[]),
            ceiling=SimpleNamespace(face=[]),
            floor=SimpleNamespace(face=[]),
        )
        model = SimpleNamespace(spaceList=[space], schedule=None)
        weather = SimpleNamespace(
            weather_file="weather.csv",
            location=SimpleNamespace(latitude=37.8, altitude=0.0),
        )

        monthly = build_energy_input(model, weather, temporal_scale="monthly")
        daily = build_energy_input(model, weather, temporal_scale="daily")
        hourly_zone = build_energy_input(
            model,
            weather,
            temporal_scale="hourly",
            spatial_scale="zone",
        )

        self.assertNotIn("-d", monthly["args"])
        self.assertNotIn("-r", monthly["args"])
        self.assertAlmostEqual(
            float(monthly["args"][monthly["args"].index("-l") + 1]),
            math.radians(37.8),
        )
        self.assertEqual(daily["args"][-2:], ["-d", "1"])
        self.assertEqual(hourly_zone["args"][-4:], ["-r", "1", "-z", "1"])

    def test_energy_scales_reject_unknown_values(self):
        zone = SimpleNamespace(paramToString=lambda: "zone", paramTags=lambda: "header")
        with self.assertRaisesRegex(ValueError, "temporal_scale"):
            EnergyRunner(energy_input={"zones": [zone], "args": []}, temporal_scale="annual")
        with self.assertRaisesRegex(ValueError, "spatial_scale"):
            EnergyRunner(energy_input={"zones": [zone], "args": []}, spatial_scale="space")

    def test_energy_building_types_map_to_engine_codes(self):
        space = SimpleNamespace(
            id="zone-1",
            settings={},
            area=10.0,
            height=3.0,
            edge=SimpleNamespace(wall=[]),
            ceiling=SimpleNamespace(face=[]),
            floor=SimpleNamespace(face=[]),
        )
        model = SimpleNamespace(spaceList=[space], schedule=None)
        weather = SimpleNamespace(
            weather_file="weather.csv",
            location=SimpleNamespace(latitude=37.8, altitude=0.0),
        )
        expected_codes = {
            buildingType.RESIDENTIAL: "0",
            buildingType.OFFICE: "1",
            buildingType.HOTEL: "2",
            buildingType.SCHOOL: "3",
            buildingType.COMMERCIAL: "4",
        }

        for core, expected_code in expected_codes.items():
            energy_input = build_energy_input(model, weather, core=core)
            type_index = energy_input["args"].index("-t")
            self.assertEqual(energy_input["args"][type_index + 1], expected_code)

        with self.assertRaisesRegex(ValueError, "core must be one of"):
            build_energy_input(model, weather, core=buildingType.HOSPITAL)

    def test_airflow_runner_builds_project_from_model_in_its_workspace(self):
        command_result = CommandResult(("contamx", "model.prj"), 0, "", "")
        matrix = [[0.0, 1.0], [1.0, 0.0]]
        model = SimpleNamespace()
        zone = SimpleNamespace(
            userName="zone-1", prjName="z001", heatLoad=100.0, volume=30.0
        )
        airflow_paths = [SimpleNamespace()]

        with TemporaryDirectory() as work_dir:
            root = Path(work_dir)
            response_path = root / "response.txt"
            response_path.write_text("response", encoding="utf-8")
            paths = VentPaths.from_workspace(root / "workspace")
            with patch(
                "MoosasPy.simulation.airflow.runner.AirflowRunner.run_command",
                return_value=command_result,
            ) as run_command, patch(
                "MoosasPy.simulation.airflow.runner.build_matrix", return_value=matrix
            ), patch(
                "MoosasPy.simulation.airflow.runner.buildNetworkFile"
            ) as build_network_file, patch(
                "MoosasPy.simulation.airflow.runner.getZoneAndPath",
                return_value=([zone], airflow_paths),
            ), patch(
                "MoosasPy.simulation.airflow.runner._solve_sensible_heat",
                return_value=[[298.15]],
            ), patch(
                "MoosasPy.simulation.airflow.runner._write_project_temperatures"
            ):
                result = AirflowRunner(
                    model=model,
                    response_file=str(response_path),
                    paths=paths,
                    max_iterations=2,
                ).run()

        self.assertIsInstance(result, AirflowResult)
        self.assertEqual(result.airflow_matrix.tolist(), matrix)
        self.assertTrue(result.converged)
        self.assertEqual(result.iteration_count, 2)
        self.assertEqual(result.residual, 0.0)
        self.assertEqual(result.zones[0].user_name, "zone-1")
        self.assertEqual(len(result.commands), 5)
        self.assertEqual(run_command.call_count, 5)
        build_network_file.assert_called_once_with(
            model=model,
            pathList=airflow_paths,
            zoneList=[zone],
            networkFilePath=str(Path(paths.project_dir) / "model.json"),
        )
        self.assertEqual(
            run_command.call_args_list[1].args[0],
            (paths.contamx, str(Path(paths.project_dir) / "model.prj")),
        )

    def test_airflow_temperature_solver_uses_ndarrays(self):
        airflow_matrix = np.array([[0.0, 2.0], [3.0, 0.0]])
        conversion = 1.2 / 3600 * 1005

        temperature = _calculate_temperature(airflow_matrix, [100.0], 25.0)

        expected = 273.15 + (100.0 + 3.0 * 25.0 * conversion) / (3.0 * conversion)
        self.assertIsInstance(temperature, np.ndarray)
        self.assertEqual(temperature.shape, (1,))
        np.testing.assert_allclose(temperature, [expected])

    def test_airflow_temperature_solver_is_deterministic(self):
        airflow_matrix = np.array([
            [0.0, 2.0, 1.0],
            [3.0, 0.0, 1.0],
            [2.0, 4.0, 0.0],
        ])

        first = _calculate_temperature(airflow_matrix, [100.0, 120.0], 25.0)
        second = _calculate_temperature(airflow_matrix, [100.0, 120.0], 25.0)

        np.testing.assert_array_equal(first, second)

    def test_energy_airflow_coupler_is_exposed_by_coupling_package(self):
        self.assertEqual(EnergyAirflowCoupler.__module__, "MoosasPy.simulation.coupling.energy_airflow")

    def test_energy_airflow_coupler_delegates_iteration_to_airflow_runner(self):
        coupler = object.__new__(EnergyAirflowCoupler)
        coupler.model = SimpleNamespace()
        coupler.networkDict = {
            "zones": {"zone-1": {"userName": "zone-1", "heatLoad": 120.0}}
        }
        coupler.runtime = {
            "outdoor_temperature": 21.0,
            "vent_paths": SimpleNamespace(),
        }
        zone_result = AirflowZoneResult(
            user_name="zone-1",
            project_name="z001",
            heat_load=120.0,
            volume=30.0,
            temperatures=(24.0,),
            ach_values=(1.5,),
        )
        airflow_result = AirflowResult(
            zones=(zone_result,),
            workspace=WorkspaceReport("workspace", True),
        )

        with patch.object(
            EnergyAirflowCoupler, "_ensure_runtime_workspace"
        ), patch.object(
            EnergyAirflowCoupler, "updateHeatLoad"
        ), patch(
            "MoosasPy.simulation.coupling.energy_airflow.AirflowRunner"
        ) as runner_type:
            runner_type.return_value.run.return_value = airflow_result
            zones = coupler.ventilationTask(10, iteration=3, inf_p=0.2)

        self.assertEqual(zones, (zone_result,))
        runner_type.assert_called_once_with(
            model=coupler.model,
            outdoor_temperature=21.0,
            heat_loads={"zone-1": 120.0},
            max_iterations=3,
            flow_multiplier=1.2,
            paths=coupler.runtime["vent_paths"],
        )

    def test_energy_airflow_coupler_aggregates_hourly_energy_into_days(self):
        coupler = object.__new__(EnergyAirflowCoupler)
        zone = SimpleNamespace(params={"zone_name": "zone-1", "zone_area": 20.0})
        hourly = [
            {"heating": "1", "cooling": "2", "lighting": "3"}
            for _ in range(24)
        ]

        result = coupler._format_energy_result(
            {"zones": [zone]},
            {"zone_hours": [hourly]},
        )

        self.assertEqual(result["zone-1"]["heating"][0], 24.0)
        self.assertEqual(result["zone-1"]["cooling"][0], 48.0)
        self.assertEqual(result["zone-1"]["Lighting"][0], 72.0)


if __name__ == "__main__":
    unittest.main()
