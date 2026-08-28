"""Typed weather-domain data."""

from __future__ import annotations

from dataclasses import dataclass, fields

import numpy as np


@dataclass(frozen=True, slots=True)
class Location:
    """Geographic and atmospheric metadata for a weather station."""

    station_id: str
    city: str
    state: str
    latitude: float
    longitude: float
    altitude: float
    pressure: float

    def __post_init__(self):
        object.__setattr__(self, "station_id", str(self.station_id))
        object.__setattr__(self, "city", str(self.city))
        object.__setattr__(self, "state", str(self.state))
        for name in ("latitude", "longitude", "altitude", "pressure"):
            object.__setattr__(self, name, round(float(getattr(self, name)), 2))

    @classmethod
    def from_csv_row(cls, row: list[str]) -> "Location":
        if len(row) != 7:
            raise ValueError(f"Station row must contain 7 fields, got {len(row)}")
        return cls(*row)

    def to_csv_row(self) -> list[str]:
        return [
            self.station_id,
            self.city,
            self.state,
            str(self.latitude),
            str(self.longitude),
            str(self.altitude),
            str(self.pressure),
        ]


@dataclass(frozen=True, slots=True)
class WeatherData:
    """One year of numeric hourly weather data and its source metadata."""

    location: Location
    weather_file: str
    hour_of_year: np.ndarray
    temperature: np.ndarray
    humidity_ratio: np.ndarray
    global_radiation: np.ndarray
    diffuse_radiation: np.ndarray
    ground_temperature: np.ndarray
    sky_temperature: np.ndarray
    wind_speed: np.ndarray
    wind_direction: np.ndarray
    pressure: np.ndarray

    HOURS_PER_YEAR = 8760

    def __post_init__(self):
        object.__setattr__(self, "weather_file", str(self.weather_file))
        for field in fields(self)[2:]:
            values = np.array(getattr(self, field.name), dtype=float, copy=True)
            if values.shape != (self.HOURS_PER_YEAR,):
                raise ValueError(
                    f"{field.name} must contain {self.HOURS_PER_YEAR} hourly values, got {values.shape}"
                )
            values.setflags(write=False)
            object.__setattr__(self, field.name, values)
