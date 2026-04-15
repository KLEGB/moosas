"""
EPW Weather Data Download Tool

Features:
  - Find the best matching weather station by station_id
  - Find the nearest weather station by lat/lon coordinates
  - Download the corresponding ZIP file and extract the EPW file
  - Save the EPW file to the specified path

URL construction logic (from ladybug.tools/epwmap JS file):
  - onebuilding source: https://climate.onebuilding.org + site path
  - doe source: https://energyplus-weather.s3.amazonaws.com + site path
"""

import os
import math
import zipfile
import tempfile
import requests
import csv
from typing import Optional, Union
from pathlib import Path


# ── Constants ─────────────────────────────────────────────────────────────

# Download request timeout (seconds)
DOWNLOAD_TIMEOUT_SECONDS = 120

# HTTP request headers, simulate browser access
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Data Loading ──────────────────────────────────────────────────────────

_stations_cache = None


def load_stations_list(csv_path: str = STATIONS_CSV_PATH) -> list[dict]:
    """
    Load weather station data table (with cache to avoid repeated reads). Returns a list of dicts.
    """
    global _stations_cache
    if _stations_cache is None:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            stations = []
            for row in reader:
                # Type conversion
                row["lat"] = float(row["lat"]) if row["lat"] else None
                row["lon"] = float(row["lon"]) if row["lon"] else None
                row["stationId"] = str(row["stationId"])
                stations.append(row)
            _stations_cache = stations
    return _stations_cache


# ── Distance Calculation ─────────────────────────────────────────────────

def calculate_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points using the Haversine formula (km).
    """
    earth_radius_km = 6371.0
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)

    haversine_a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    central_angle = 2 * math.atan2(math.sqrt(haversine_a), math.sqrt(1 - haversine_a))
    return earth_radius_km * central_angle


# ── Weather Station Lookup ───────────────────────────────────────────────

def find_station_by_id(
    station_id: Union[str, int],
    prefer_source: str = "onebuilding",
    prefer_file_type: str = "TMYx",
) -> Optional[dict]:
    """
    Find weather station record by station_id.
    When multiple records exist for the same station_id, prefer:
    1. The specified data source (prefer_source)
    2. The specified file type (prefer_file_type)
    3. The latest file (descending by site path)
    """
    stations = load_stations_list()
    matches = [row for row in stations if row["stationId"] == str(station_id)]
    if not matches:
        return None
    # Prefer data source
    source_filtered = [row for row in matches if row["sources"].lower() == prefer_source.lower()]
    if source_filtered:
        matches = source_filtered
    # Prefer file type
    type_filtered = [row for row in matches if prefer_file_type.lower() in (row["fileType"] or "").lower()]
    if type_filtered:
        matches = type_filtered
    # Sort by site path descending
    matches.sort(key=lambda x: x["site"], reverse=True)
    return matches[0]


def find_nearest_station_by_coordinates(
    latitude: float,
    longitude: float,
    prefer_source: str = "onebuilding",
    prefer_file_type: str = "TMYx",
) -> Optional[dict]:
    """
    Find the nearest weather station by coordinates.
    """
    stations = load_stations_list()
    filtered = stations
    source_filtered = [row for row in filtered if row["sources"].lower() == prefer_source.lower()]
    if source_filtered:
        filtered = source_filtered
    type_filtered = [row for row in filtered if prefer_file_type.lower() in (row["fileType"] or "").lower()]
    if type_filtered:
        filtered = type_filtered
    if not filtered:
        return None
    # Calculate distance
    def dist(row):
        return calculate_haversine_distance(latitude, longitude, row["lat"], row["lon"])
    nearest = min(filtered, key=dist)
    nearest = nearest.copy() if hasattr(nearest, 'copy') else dict(nearest)
    nearest["distance_km"] = dist(nearest)
    return nearest


# ── File Download and Extraction ─────────────────────────────────────────

def download_and_extract_epw(
    download_url: str,
    output_epw_path: str,
    verbose: bool = True,
) -> str:
    """
    Download ZIP file and extract EPW file, save to specified path.
    """
    output_path = Path(output_epw_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        print(f"  Downloading: {download_url}")

    # Download ZIP file to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_filename = os.path.basename(download_url)
        temp_zip_path = os.path.join(temp_dir, zip_filename)

        response = requests.get(
            download_url,
            headers=REQUEST_HEADERS,
            timeout=DOWNLOAD_TIMEOUT_SECONDS,
            stream=True,
        )
        response.raise_for_status()

        # Streamed write, avoid large files consuming too much memory
        total_bytes = 0
        with open(temp_zip_path, "wb") as zip_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    zip_file.write(chunk)
                    total_bytes += len(chunk)

        if verbose:
            print(f"  Download complete, file size: {total_bytes / 1024:.1f} KB")

        # Extract ZIP file, find EPW file
        with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
            all_files_in_zip = zip_ref.namelist()
            epw_files_in_zip = [
                f for f in all_files_in_zip if f.lower().endswith(".epw")
            ]

            if not epw_files_in_zip:
                raise FileNotFoundError(
                    f"ZIP file contains no EPW files. Contents: {all_files_in_zip}"
                )

            # If multiple EPW files, take the first
            epw_file_in_zip = epw_files_in_zip[0]
            if verbose and len(epw_files_in_zip) > 1:
                print(
                    f"  ZIP contains {len(epw_files_in_zip)} EPW files, "
                    f"using: {epw_file_in_zip}"
                )

            # Extract EPW file to temporary directory
            zip_ref.extract(epw_file_in_zip, temp_dir)
            extracted_epw_path = os.path.join(temp_dir, epw_file_in_zip)

            # Copy EPW file to target path
            import shutil
            shutil.copy2(extracted_epw_path, str(output_path))

    if verbose:
        print(f"  EPW file saved to: {output_path}")

    return str(output_path)


# ── Main Interface Functions ─────────────────────────────────────────────

def download_epw_by_station_id(
    station_id: Union[str, int],
    output_epw_path: str,
    prefer_source: str = "onebuilding",
    prefer_file_type: str = "TMYx",
    verbose: bool = True,
) -> str:
    """
    Download EPW weather data file by station_id.
    """
    if verbose:
        print(f"\n[station_id={station_id}] Starting to find weather station...")

    station = find_station_by_id(station_id, prefer_source, prefer_file_type)
    if station is None:
        raise ValueError(f"Station_id={station_id} not found")

    if verbose:
        print(f"  Found weather station: {station['name']}")
        print(f"  Data source: {station['sources']}  File type: {station['fileType']}")
        print(f"  Coordinates: lat={station['lat']}, lon={station['lon']}")

    return download_and_extract_epw(
        download_url=station["download_url"],
        output_epw_path=output_epw_path,
        verbose=verbose,
    )


def download_epw_by_coordinates(
    latitude: float,
    longitude: float,
    output_epw_path: str,
    prefer_source: str = "onebuilding",
    prefer_file_type: str = "TMYx",
    verbose: bool = True,
) -> str:
    """
    Find the nearest weather station by coordinates and download EPW weather data file.
    """
    if verbose:
        print(f"\n[lat={latitude}, lon={longitude}] Starting to find nearest weather station...")

    station = find_nearest_station_by_coordinates(
        latitude, longitude, prefer_source, prefer_file_type
    )
    if station is None:
        raise ValueError("No weather station records found")

    if verbose:
        print(f"  Nearest weather station: {station['name']}")
        print(f"  station_id: {station['stationId']}")
        print(f"  Data source: {station['sources']}  File type: {station['fileType']}")
        print(f"  Coordinates: lat={station['lat']}, lon={station['lon']}")
        if "distance_km" in station:
            print(f"  Distance to target point: {station['distance_km']:.2f} km")

    return download_and_extract_epw(
        download_url=station["download_url"],
        output_epw_path=output_epw_path,
        verbose=verbose,
    )


# ── Command Line Entry ───────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="EPW Weather Data Download Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download by station_id
  python epw_downloader.py --station-id 661040 --output /tmp/cabinda.epw

  # Download by coordinates
  python epw_downloader.py --lat 39.9 --lon 116.4 --output /tmp/beijing.epw
        """,
    )
    parser.add_argument("--station-id", type=str, help="Weather station ID")
    parser.add_argument("--lat", type=float, help="Target latitude")
    parser.add_argument("--lon", type=float, help="Target longitude")
    parser.add_argument("--output", type=str, required=True, help="EPW output file path")
    parser.add_argument(
        "--source", type=str, default="onebuilding", help="Preferred data source (default: onebuilding)"
    )
    parser.add_argument(
        "--file-type", type=str, default="TMYx", help="Preferred file type (default: TMYx)"
    )

    args = parser.parse_args()

    if args.station_id:
        download_epw_by_station_id(
            station_id=args.station_id,
            output_epw_path=args.output,
            prefer_source=args.source,
            prefer_file_type=args.file_type,
        )
    elif args.lat is not None and args.lon is not None:
        download_epw_by_coordinates(
            latitude=args.lat,
            longitude=args.lon,
            output_epw_path=args.output,
            prefer_source=args.source,
            prefer_file_type=args.file_type,
        )
    else:
        parser.error("You must specify --station-id or both --lat and --lon")
