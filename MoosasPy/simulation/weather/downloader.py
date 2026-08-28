"""Explicit EPW station lookup and download utilities."""

from __future__ import annotations

import csv
from dataclasses import dataclass
import math
from pathlib import Path
import shutil
import tempfile
from typing import Iterable
import zipfile

import requests


DOWNLOAD_TIMEOUT_SECONDS = 120
REQUEST_HEADERS = {"User-Agent": "MoosasPy weather downloader"}


@dataclass(frozen=True, slots=True)
class DownloadStation:
    station_id: str
    name: str
    latitude: float
    longitude: float
    source: str
    file_type: str
    site: str
    download_url: str


def load_download_catalog(catalog_path: str) -> tuple[DownloadStation, ...]:
    """Read an explicit download catalog; no implicit global catalog is used."""
    stations = []
    with open(catalog_path, newline="", encoding="utf-8") as catalog_file:
        for row in csv.DictReader(catalog_file):
            stations.append(DownloadStation(
                station_id=str(row["stationId"]),
                name=str(row["name"]),
                latitude=float(row["lat"]),
                longitude=float(row["lon"]),
                source=str(row["sources"]),
                file_type=str(row["fileType"]),
                site=str(row["site"]),
                download_url=str(row["download_url"]),
            ))
    return tuple(stations)


def calculate_haversine_distance(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    """Calculate great-circle distance in kilometres."""
    earth_radius_km = 6371.0
    delta_latitude = math.radians(latitude_b - latitude_a)
    delta_longitude = math.radians(longitude_b - longitude_a)
    latitude_a_radians = math.radians(latitude_a)
    latitude_b_radians = math.radians(latitude_b)
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_a_radians)
        * math.cos(latitude_b_radians)
        * math.sin(delta_longitude / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


def find_station_by_id(
    stations: Iterable[DownloadStation],
    station_id: str,
    *,
    preferred_source: str = "onebuilding",
    preferred_file_type: str = "TMYx",
) -> DownloadStation:
    """Select the preferred catalog record for a station ID."""
    matches = [station for station in stations if station.station_id == str(station_id)]
    if not matches:
        raise KeyError(f"Unknown download station: {station_id}")
    source_matches = [
        station for station in matches
        if station.source.lower() == preferred_source.lower()
    ]
    if source_matches:
        matches = source_matches
    type_matches = [
        station for station in matches
        if preferred_file_type.lower() in station.file_type.lower()
    ]
    if type_matches:
        matches = type_matches
    return sorted(matches, key=lambda station: station.site, reverse=True)[0]


def find_nearest_station(
    stations: Iterable[DownloadStation],
    latitude: float,
    longitude: float,
    *,
    preferred_source: str = "onebuilding",
    preferred_file_type: str = "TMYx",
) -> DownloadStation:
    """Find the nearest preferred station in an explicit catalog."""
    stations = tuple(stations)
    source_matches = [
        station for station in stations
        if station.source.lower() == preferred_source.lower()
    ]
    if source_matches:
        stations = tuple(source_matches)
    type_matches = [
        station for station in stations
        if preferred_file_type.lower() in station.file_type.lower()
    ]
    if type_matches:
        stations = tuple(type_matches)
    if not stations:
        raise ValueError("Download catalog contains no matching stations")
    return min(
        stations,
        key=lambda station: calculate_haversine_distance(
            latitude,
            longitude,
            station.latitude,
            station.longitude,
        ),
    )


def download_epw(station: DownloadStation, output_path: str) -> str:
    """Download a station ZIP and copy its first EPW member to ``output_path``."""
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="moosas-epw-download-") as temporary_dir:
        archive_path = Path(temporary_dir) / "weather.zip"
        response = requests.get(
            station.download_url,
            headers=REQUEST_HEADERS,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            stream=True,
        )
        response.raise_for_status()
        with archive_path.open("wb") as archive_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    archive_file.write(chunk)
        with zipfile.ZipFile(archive_path) as archive:
            epw_members = [name for name in archive.namelist() if name.lower().endswith(".epw")]
            if not epw_members:
                raise FileNotFoundError("Downloaded archive contains no EPW file")
            with archive.open(epw_members[0]) as source, output.open("wb") as destination:
                shutil.copyfileobj(source, destination)
    return str(output)
