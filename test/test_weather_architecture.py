from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from MoosasPy.simulation.weather import (
    CumulativeSky,
    DirectSky,
    WeatherData,
    build_cumulative_skies,
    find_nearest_station,
    find_station_by_id,
    load_download_catalog,
    load_station_weather,
)
from MoosasPy.utils.date import DateTime


class WeatherArchitectureTests(unittest.TestCase):
    def test_packaged_station_loads_as_typed_immutable_weather(self):
        weather = load_station_weather("545110")

        self.assertIsInstance(weather, WeatherData)
        self.assertEqual(weather.location.station_id, "545110")
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

    def test_download_catalog_lookup_is_explicit(self):
        catalog = (
            "stationId,name,lat,lon,sources,fileType,site,download_url\n"
            "A,Alpha,0,0,other,TMY,2020,https://example.com/a.zip\n"
            "A,Alpha,1,1,onebuilding,TMYx,2024,https://example.com/a-new.zip\n"
            "B,Beta,10,10,onebuilding,TMYx,2024,https://example.com/b.zip\n"
        )
        with TemporaryDirectory() as temporary_dir:
            catalog_path = Path(temporary_dir) / "stations.csv"
            catalog_path.write_text(catalog, encoding="utf-8")
            stations = load_download_catalog(str(catalog_path))

        self.assertEqual(find_station_by_id(stations, "A").download_url, "https://example.com/a-new.zip")
        self.assertEqual(find_nearest_station(stations, 0, 0).station_id, "A")

    def test_legacy_weather_modules_are_removed(self):
        weather_directory = Path(__file__).parents[1] / "MoosasPy" / "simulation" / "weather"

        self.assertFalse((weather_directory / "directsky.py").exists())
        self.assertFalse((weather_directory / "cumsky.py").exists())


if __name__ == "__main__":
    unittest.main()
