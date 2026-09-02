from pathlib import Path
from tempfile import TemporaryDirectory
import importlib
import unittest

import numpy as np

from MoosasPy.simulation.weather import (
    CumulativeSky,
    DirectSky,
    WeatherData,
    build_cumulative_skies,
    load_epw,
)
from MoosasPy.utils.date import DateTime


class WeatherArchitectureTests(unittest.TestCase):
    def test_epw_loads_as_typed_immutable_weather(self):
        with TemporaryDirectory() as temporary_dir:
            epw_path = Path(temporary_dir) / "weather.epw"
            self._write_epw_fixture(epw_path)
            weather = load_epw(epw_path, Path(temporary_dir) / "prepared")

        self.assertIsInstance(weather, WeatherData)
        self.assertEqual(weather.location.station_id, "12345")
        self.assertEqual(Path(weather.weather_file).name, "weather.csv")
        self.assertEqual(weather.temperature.shape, (8760,))
        self.assertTrue(np.issubdtype(weather.temperature.dtype, np.floating))
        self.assertFalse(weather.temperature.flags.writeable)
        with self.assertRaises(ValueError):
            weather.temperature[0] = 0

    def test_cumulative_sky_builds_annual_and_seasonal_views(self):
        matrix = np.ones((145, CumulativeSky.HOURS_PER_YEAR))

        skies = build_cumulative_skies(matrix)

        self.assertEqual(set(skies), {"annual", "summer", "winter"})
        np.testing.assert_allclose(skies["annual"].values, 8.76)
        np.testing.assert_allclose(skies["summer"].values, 2.208)
        np.testing.assert_allclose(skies["winter"].values, 2.16)

    def test_direct_sky_uses_degree_based_location_coordinates(self):
        sun = DirectSky(0, 0, time_zone=0).sun_at_datetime(DateTime(3, 20, 12))

        self.assertGreater(sun.z, 0.99)

    def test_station_matching_modules_are_removed(self):
        for module_name in (
            "MoosasPy.simulation.weather.station",
            "MoosasPy.simulation.weather.downloader",
        ):
            with self.assertRaises(ModuleNotFoundError):
                importlib.import_module(module_name)

    def test_legacy_weather_modules_are_removed(self):
        weather_directory = Path(__file__).parents[1] / "MoosasPy" / "simulation" / "weather"

        self.assertFalse((weather_directory / "directsky.py").exists())
        self.assertFalse((weather_directory / "cumsky.py").exists())

    @staticmethod
    def _write_epw_fixture(epw_path: Path) -> None:
        ground_temperatures = ["GROUND", "0", "0", "0", "0", "0"] + ["10"] * 12
        hourly_record = ["0"] * 22
        hourly_record[6] = "20.125"
        hourly_record[7] = "10"
        hourly_record[9] = "101325"
        hourly_record[12] = "300"
        hourly_record[13] = "100"
        hourly_record[15] = "50"
        hourly_record[20] = "0"
        hourly_record[21] = "1"
        lines = [
            "LOCATION,City,State,Country,Source,12345;,1,2,3,4",
            "header",
            "header",
            ",".join(ground_temperatures),
            "header",
            "header",
            "header",
            "header",
        ] + [",".join(hourly_record)] * 8760
        epw_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
