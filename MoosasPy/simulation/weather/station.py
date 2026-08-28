"""Packaged weather-station catalog and data readers."""

from __future__ import annotations

import csv
import os

import numpy as np

from ...utils.tools import path
from .data import Location, WeatherData


DEFAULT_STATION_CATALOG = os.path.join(path.dataBaseDir, "dest_station.csv")
DEFAULT_WEATHER_DIRECTORY = os.path.join(path.dataBaseDir, "weather")


def load_station_catalog(catalog_path: str = DEFAULT_STATION_CATALOG) -> dict[str, Location]:
    """Read a seven-column station catalog keyed by station ID."""
    stations = {}
    with open(catalog_path, newline="", encoding="utf-8") as catalog_file:
        for row in csv.reader(catalog_file):
            if not row:
                continue
            location = Location.from_csv_row(row)
            stations[location.station_id] = location
    return stations


def read_weather_csv(weather_file: str, location: Location) -> WeatherData:
    """Read the MOOSAS/DeST 8760-row weather CSV format."""
    weather_file = os.path.abspath(weather_file)
    values = np.loadtxt(weather_file, delimiter=",", dtype=float)
    if values.shape != (WeatherData.HOURS_PER_YEAR, 13):
        raise ValueError(
            "Weather CSV must contain 8760 rows and 13 columns, "
            f"got {values.shape}"
        )
    return WeatherData(
        location=location,
        weather_file=weather_file,
        hour_of_year=values[:, 2],
        temperature=values[:, 3],
        humidity_ratio=values[:, 4],
        global_radiation=values[:, 5],
        diffuse_radiation=values[:, 6],
        ground_temperature=values[:, 7],
        sky_temperature=values[:, 8],
        wind_speed=values[:, 9],
        wind_direction=values[:, 10],
        pressure=values[:, 11],
    )


def load_station_weather(
    station_id: str,
    *,
    catalog_path: str = DEFAULT_STATION_CATALOG,
    weather_directory: str = DEFAULT_WEATHER_DIRECTORY,
) -> WeatherData:
    """Load one packaged station and its hourly weather series."""
    station_id = str(station_id)
    stations = load_station_catalog(catalog_path)
    if station_id not in stations:
        raise KeyError(f"Unknown weather station: {station_id}")
    weather_file = os.path.join(weather_directory, f"{station_id}.csv")
    if not os.path.isfile(weather_file):
        raise FileNotFoundError(f"Weather file not found: {weather_file}")
    return read_weather_csv(weather_file, stations[station_id])
