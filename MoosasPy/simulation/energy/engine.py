from __future__ import annotations

import csv
from dataclasses import dataclass, field
import math
from pathlib import Path

import numpy as np


AIR_DENSITY = 1.29
AIR_CAPACITY = 1.40
AIR_CAPACITY_RESIDENTIAL = 0.717
SOLAR_CONSTANT = 1367.0
MONTH_START_DAYS = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365)
RESIDENTIAL_LIGHTING_SCHEDULE = np.array(
    [0, 0, 0, 0, 0, 0.65, 0.65, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.1, 0.4, 0.4, 0.6, 0.4, 0, 0],
    dtype=float,
)
RESIDENTIAL_EQUIPMENT_SCHEDULE = np.array(
    [0, 0, 0, 0, 0, 0, 0.65, 0.75, 0.35, 0.2, 0.2, 0.4, 0.35, 0.2, 0.2, 0.2, 0.2, 0.4, 0.35, 0.35, 0.6, 0.4, 0, 0],
    dtype=float,
)


@dataclass(frozen=True)
class SchedulableValue:
    fixed: float | None = None
    hourly: np.ndarray | None = None

    def at(self, hour: int) -> float:
        return float(self.hourly[hour]) if self.hourly is not None else float(self.fixed)

    def daily_sum(self, day: int) -> float:
        if self.hourly is None:
            return 0.0
        start = day * 24
        return float(sum(self.hourly[start:start + 24]))


@dataclass(frozen=True)
class Space:
    story_height: float
    floor_area: float
    perimeter_zone_area: float
    exterior_wall_area: float
    exterior_window_area: float
    roof_area: float
    skylight_area: float
    ground_floor_area: float
    summer_solar_gain: SchedulableValue
    winter_solar_gain: SchedulableValue
    wall_u_value: float
    window_u_value: float
    window_shgc: float
    cooling_setpoint_temp: SchedulableValue
    cooling_setpoint_humidity: SchedulableValue
    heating_setpoint_temp: SchedulableValue
    cooling_eer: float
    heating_eer: float
    occupancy_start_hour: int
    occupancy_end_hour: int
    occupant_density: SchedulableValue
    fresh_air_per_person: SchedulableValue
    occupant_heat_gain: SchedulableValue
    equipment_heat_gain: SchedulableValue
    lighting_heat_gain: SchedulableValue
    infiltration_ach: float
    night_ventilation_ach: float


@dataclass(frozen=True)
class Climate:
    cooling_start: int
    cooling_end: int
    heating_start: int
    heating_end: int
    correction_alpha_t: float = -1.83
    correction_alpha_s: float = 2.16


@dataclass
class EnergyOutput:
    total: np.ndarray
    spaces: np.ndarray
    months: np.ndarray
    days: np.ndarray | None = None
    hours: np.ndarray | None = None
    zone_months: np.ndarray | None = None
    zone_days: np.ndarray | None = None
    zone_hours: np.ndarray | None = None


@dataclass(frozen=True)
class EngineConfig:
    weather_path: str
    building_type: int = 0
    latitude: float = 0.0
    altitude: float = 0.0
    shape_factor: float = 0.78
    schedule_path: str | None = None
    export_daily: bool = False
    export_hourly: bool = False
    export_by_zone: bool = False


def config_from_arguments(arguments: list[str]) -> EngineConfig:
    values: dict[str, str] = {}
    aliases = {
        "-w": "weather_path", "-weather": "weather_path",
        "-t": "building_type", "-type": "building_type",
        "-l": "latitude", "-lat": "latitude",
        "-a": "altitude", "-alt": "altitude",
        "-s": "shape_factor", "-shape": "shape_factor",
        "-sch": "schedule_path", "-schedule": "schedule_path",
        "-d": "export_daily", "-daily": "export_daily",
        "-r": "export_hourly", "-hourly": "export_hourly",
        "-z": "export_by_zone", "-zone": "export_by_zone",
    }
    index = 0
    while index < len(arguments):
        key = aliases.get(arguments[index])
        if key is not None:
            values[key] = arguments[index + 1]
            index += 2
        else:
            index += 1
    if "weather_path" not in values:
        raise ValueError("Energy simulation requires a weather file")
    return EngineConfig(
        weather_path=values["weather_path"],
        building_type=int(values.get("building_type", 0)),
        latitude=float(values.get("latitude", 0.0)),
        altitude=float(values.get("altitude", 0.0)),
        shape_factor=float(values.get("shape_factor", 0.78)),
        schedule_path=values.get("schedule_path"),
        export_daily=values.get("export_daily", "0") == "1",
        export_hourly=values.get("export_hourly", "0") == "1",
        export_by_zone=values.get("export_by_zone", "0") == "1",
    )


def _load_schedules(file_path: str | None) -> dict[str, np.ndarray]:
    if not file_path:
        return {}
    with open(file_path, newline="", encoding="utf-8") as schedule_file:
        rows = list(csv.reader(schedule_file))
    schedules: dict[str, np.ndarray] = {}
    for row in rows:
        if len(row) < 2 or row[1].strip() not in {"Daily", "Hourly"}:
            continue
        name, schedule_type = row[0].strip(), row[1].strip()
        count = 24 if schedule_type == "Daily" else 8760
        factors = np.array([float(value.strip()) for value in row[2:2 + count]], dtype=float)
        if len(factors) != count:
            raise ValueError(f"{schedule_type} schedule {name!r} requires {count} values")
        schedules[name] = np.tile(factors, 365) if schedule_type == "Daily" else factors
    for row in rows:
        if len(row) < 2 or row[1].strip() != "Weekly":
            continue
        name = row[0].strip()
        daily_names = [value.strip() for value in row[2:9]]
        if len(daily_names) != 7:
            raise ValueError(f"Weekly schedule {name!r} requires 7 Daily schedule names")
        schedules[name] = np.concatenate([schedules[daily_names[day % 7]][:24] for day in range(365)])
    return schedules


def _schedulable(value: str, schedules: dict[str, np.ndarray]) -> SchedulableValue:
    value = value.strip()
    try:
        return SchedulableValue(fixed=float(value))
    except ValueError:
        try:
            return SchedulableValue(hourly=schedules[value])
        except KeyError as exc:
            raise ValueError(f"Unknown schedule {value!r}") from exc


def parse_spaces(rows: list[str], schedule_path: str | None = None) -> list[Space]:
    schedules = _load_schedules(schedule_path)
    spaces = []
    for row in rows:
        row = row.strip()
        if not row or row.startswith("!"):
            continue
        fields = row.split(",")
        if len(fields) < 27:
            continue
        floor_area = float(fields[1])
        perimeter_zone_area = min(float(fields[2]), floor_area)
        spaces.append(Space(
            story_height=float(fields[0]), floor_area=floor_area,
            perimeter_zone_area=perimeter_zone_area, exterior_wall_area=float(fields[3]),
            exterior_window_area=float(fields[4]), roof_area=float(fields[5]),
            skylight_area=float(fields[6]), ground_floor_area=float(fields[7]),
            summer_solar_gain=_schedulable(fields[8], schedules),
            winter_solar_gain=_schedulable(fields[9], schedules),
            wall_u_value=float(fields[10]), window_u_value=float(fields[11]),
            window_shgc=float(fields[12]), cooling_setpoint_temp=_schedulable(fields[13], schedules),
            cooling_setpoint_humidity=_schedulable(fields[14], schedules),
            heating_setpoint_temp=_schedulable(fields[15], schedules),
            cooling_eer=float(fields[16]), heating_eer=float(fields[17]),
            occupancy_start_hour=int(fields[18]), occupancy_end_hour=int(fields[19]),
            occupant_density=_schedulable(fields[20], schedules),
            fresh_air_per_person=_schedulable(fields[21], schedules),
            occupant_heat_gain=_schedulable(fields[22], schedules),
            equipment_heat_gain=_schedulable(fields[23], schedules),
            lighting_heat_gain=_schedulable(fields[24], schedules),
            infiltration_ach=float(fields[25]), night_ventilation_ach=float(fields[26].strip()),
        ))
    return spaces


def _climate(latitude: float) -> Climate:
    if latitude > 0.74:
        return Climate(151, 242, 293, 99, -2.34, 1.96)
    if latitude > 0.62:
        return Climate(140, 262, 319, 73, -1.83, 2.16)
    if latitude > 0.47:
        return Climate(135, 272, 334, 58, -2.39, 2.39)
    return Climate(90, 303, 334, 58, -2.06, 2.57)


def _weather(path: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with open(path, newline="") as weather_file:
        rows = list(csv.reader(weather_file))
    dry_bulb = np.array([float(row[3]) for row in rows], dtype=float)
    dew_point = np.array([float(row[4]) for row in rows], dtype=float)
    ground = np.array([float(row[7]) for row in rows], dtype=float)
    if len(dry_bulb) < 8760:
        raise ValueError(f"Weather file must contain 8760 rows: {path}")
    return dry_bulb, dew_point, ground


def _envelope(space: Space, temp_diff: float, ground_diff: float) -> float:
    return ((space.exterior_wall_area + space.roof_area) * space.wall_u_value * temp_diff
            + (space.exterior_window_area + space.skylight_area) * space.window_u_value * temp_diff
            + space.ground_floor_area * space.wall_u_value * ground_diff)


def _lighting(latitude: float, altitude: float, day: int, hour: int, glazing_ratio: float,
              interior_area: float, perimeter_area: float, heat_gain: float) -> float:
    if glazing_ratio == 0:
        return heat_gain * (interior_area + perimeter_area)
    declination = 23.45 * math.sin(2 * math.pi * (284 + day) / 365)
    daylight_hours = 2 / 15 * math.acos(-math.tan(latitude) * math.tan(math.radians(declination))) * 180 / math.pi
    sunrise, sunset = int(12 - daylight_hours / 2) + 1, int(12 + daylight_hours / 2)
    if hour < sunrise or hour > sunset:
        return heat_gain * (interior_area + perimeter_area)
    altitude_km = min(altitude / 1000, 2.49)
    day_angle = 2 * math.pi * day / 365
    extraterrestrial = SOLAR_CONSTANT * (1.00011 + 0.034221 * math.cos(day_angle) + 0.00128 * math.sin(day_angle)
                                           + 0.000719 * math.cos(2 * day_angle) + 0.000077 * math.sin(2 * day_angle))
    coeff_a1 = 0.97 * (0.4237 - 0.00821 * math.sqrt(6 - altitude_km))
    coeff_a2 = 0.99 * (0.5055 + 0.00595 * math.sqrt(6.5 - altitude_km))
    coeff_a3 = 1.02 * (0.2711 + 0.01858 * math.sqrt(2.5 - altitude_km))
    hour_angle = math.radians(15 * (12 - hour))
    solar_altitude = math.asin(math.cos(latitude) * math.cos(math.radians(declination)) * math.cos(hour_angle)
                               + math.sin(latitude) * math.sin(math.radians(declination)))
    solar_zenith_degrees = 90 - math.degrees(solar_altitude)
    direct = coeff_a1 + coeff_a2 * math.exp(-coeff_a3 / math.cos(math.radians(solar_zenith_degrees)))
    horizontal_irradiance = extraterrestrial * (direct + 0.271 - 0.294 * direct) / 2
    daylight_illuminance = glazing_ratio * horizontal_irradiance * 0.5
    if daylight_illuminance < heat_gain:
        return (heat_gain * interior_area * (1.6 - glazing_ratio)
                + (heat_gain - daylight_illuminance) * perimeter_area * (1.2 - glazing_ratio))
    return heat_gain * interior_area * (1.6 - glazing_ratio)


def _night_correction(envelope_k: float, shape: float, night_temp: float, setpoint: float,
                      occupancy_hours: int, night_ach: float) -> float:
    non_occupancy_hours = 24 - occupancy_hours
    difference = abs(setpoint - night_temp)
    decay = -math.inf if difference == 0 else math.log(difference)
    decay -= (2.985 * envelope_k * shape + night_ach) * non_occupancy_hours
    sign = -1.0 if setpoint < night_temp else (1.0 if setpoint > night_temp else 0.0)
    temp_at_start = sign * math.exp(decay) + night_temp
    drift = 0.335 * (setpoint - temp_at_start) / ((envelope_k * shape + 0.335 * night_ach) * non_occupancy_hours)
    return (1 + 0.335 * night_ach / envelope_k * shape) * non_occupancy_hours / occupancy_hours * drift


def _indoor_enthalpy(temp: float, humidity: float) -> float:
    pressure = 0.07394 * temp ** 3 - 0.02 * temp ** 2 + 62.49 * temp + 581.9
    return 1.01 * temp + (2500 + 1.84 * temp) * 622 * (humidity * pressure / (101325 - humidity * pressure)) / 1000


def _simulate_space(space: Space, config: EngineConfig, climate: Climate, dry_bulb: np.ndarray,
                    dew_point: np.ndarray, ground: np.ndarray, envelope_k: float,
                    weekend_correction: float) -> tuple[np.ndarray, np.ndarray]:
    daily = np.zeros((365, 4), dtype=float)
    hourly = np.zeros((365, 24, 4), dtype=float)
    cooling_days = climate.cooling_end - climate.cooling_start + 1
    heating_days = 365 - climate.heating_start + climate.heating_end + 1
    summer_daily = 0.0 if space.summer_solar_gain.hourly is not None else space.summer_solar_gain.fixed * 0.5936 / cooling_days
    winter_daily = 0.0 if space.winter_solar_gain.hourly is not None else space.winter_solar_gain.fixed * 0.6234 / heating_days
    occupied_hours = range(max(space.occupancy_start_hour - 1, 0), space.occupancy_end_hour - 1)
    glazing_area = space.exterior_wall_area + space.exterior_window_area + space.roof_area + space.skylight_area
    glazing_ratio = ((space.exterior_window_area + space.skylight_area) / glazing_area) if glazing_area else 0.0

    for day in range(365):
        hours = range(24) if config.building_type == 0 else occupied_hours
        night_temp = 0.0
        if config.building_type != 0:
            night_sum = sum(dry_bulb[day * 24 + hour] for hour in range(24)
                            if hour <= space.occupancy_start_hour - 2 or hour >= space.occupancy_end_hour - 1)
            night_temp = night_sum / (24 - (space.occupancy_end_hour - space.occupancy_start_hour))
        for hour in hours:
            absolute_hour = day * 24 + hour
            cooling_temp = space.cooling_setpoint_temp.at(absolute_hour)
            heating_temp = space.heating_setpoint_temp.at(absolute_hour)
            density = space.occupant_density.at(absolute_hour)
            people_gain = space.occupant_heat_gain.at(absolute_hour)
            equipment_gain = space.equipment_heat_gain.at(absolute_hour)
            lighting_gain = space.lighting_heat_gain.at(absolute_hour)
            if config.building_type == 0:
                lighting_factor = 1.0 if space.lighting_heat_gain.hourly is not None else RESIDENTIAL_LIGHTING_SCHEDULE[hour]
                equipment_factor = 1.0 if space.equipment_heat_gain.hourly is not None else RESIDENTIAL_EQUIPMENT_SCHEDULE[hour]
                lighting = lighting_gain * lighting_factor * space.floor_area
                equipment = equipment_gain * equipment_factor * space.floor_area
            else:
                lighting = _lighting(config.latitude, config.altitude, day + 1, hour + 1, glazing_ratio,
                                     space.floor_area - space.perimeter_zone_area,
                                     space.perimeter_zone_area, lighting_gain)
                equipment = equipment_gain * space.floor_area
            daily[day, 2] += lighting
            daily[day, 3] += equipment
            hourly[day, hour, 2:] = lighting, equipment
            internal_gain = density * people_gain * space.floor_area + equipment + lighting * (0.5 if config.building_type else 1.0)

            if climate.cooling_start <= day <= climate.cooling_end:
                if config.building_type == 0:
                    temp_diff = dry_bulb[absolute_hour] - cooling_temp
                    envelope = _envelope(space, temp_diff + 3.0, ground[absolute_hour] - cooling_temp)
                    fresh_air = 0.0
                    infiltration_delta = temp_diff
                    air_capacity = AIR_CAPACITY_RESIDENTIAL
                else:
                    correction = _night_correction(envelope_k, config.shape_factor, night_temp, cooling_temp,
                                                   space.occupancy_end_hour - space.occupancy_start_hour,
                                                   space.night_ventilation_ach)
                    temp_diff = dry_bulb[absolute_hour] - cooling_temp + correction
                    envelope = _envelope(space, temp_diff, ground[absolute_hour] - cooling_temp) * weekend_correction
                    outdoor_enthalpy = 1.01 * dry_bulb[absolute_hour] + (1.84 * dry_bulb[absolute_hour] + 2500) * dew_point[absolute_hour] / 1000
                    enthalpy_diff = outdoor_enthalpy - _indoor_enthalpy(cooling_temp, space.cooling_setpoint_humidity.at(absolute_hour))
                    fresh_air = density * space.fresh_air_per_person.at(absolute_hour) * max(enthalpy_diff, 0.0) * space.floor_area / 3.6
                    infiltration_delta = max(temp_diff, 0.0)
                    air_capacity = AIR_CAPACITY
                infiltration = 0.0
                if space.perimeter_zone_area > 0:
                    infiltration = AIR_DENSITY * air_capacity * infiltration_delta * space.floor_area * space.story_height * space.infiltration_ach / 3.6
                cooling_load = max(envelope + fresh_air + internal_gain + infiltration, 0.0)
                daily[day, 0] += cooling_load
                hourly[day, hour, 0] = cooling_load
            elif day >= climate.heating_start or day <= climate.heating_end:
                if config.building_type == 0:
                    temp_diff = heating_temp - dry_bulb[absolute_hour]
                    envelope = _envelope(space, temp_diff - 3.0, heating_temp - ground[absolute_hour])
                    fresh_air = 0.0
                    infiltration_delta = temp_diff
                    air_capacity = AIR_CAPACITY_RESIDENTIAL
                else:
                    correction = _night_correction(envelope_k, config.shape_factor, night_temp, heating_temp,
                                                   space.occupancy_end_hour - space.occupancy_start_hour,
                                                   space.night_ventilation_ach)
                    temp_diff = heating_temp - dry_bulb[absolute_hour] - correction
                    envelope = _envelope(space, temp_diff, heating_temp - ground[absolute_hour]) * weekend_correction
                    fresh_air = density * space.fresh_air_per_person.at(absolute_hour) * AIR_DENSITY * AIR_CAPACITY * max(temp_diff, 0.0) / 3.6 * space.floor_area
                    infiltration_delta = max(temp_diff, 0.0)
                    air_capacity = AIR_CAPACITY
                infiltration = 0.0
                if space.perimeter_zone_area > 0:
                    infiltration = AIR_DENSITY * air_capacity * infiltration_delta * space.floor_area * space.story_height * space.infiltration_ach / 3.6
                heating_load = max(envelope + fresh_air - internal_gain + infiltration, 0.0)
                daily[day, 1] += heating_load
                hourly[day, hour, 1] = heating_load

        solar_hours = range(24) if config.building_type == 0 else occupied_hours
        if climate.cooling_start <= day <= climate.cooling_end:
            daily_solar = space.summer_solar_gain.daily_sum(day) if space.summer_solar_gain.hourly is not None else summer_daily
            daily[day, 0] = max(daily[day, 0] + daily_solar * space.window_shgc, 0.0) / space.cooling_eer
            if space.summer_solar_gain.hourly is not None:
                for hour in solar_hours:
                    hourly[day, hour, 0] = max(hourly[day, hour, 0] + space.summer_solar_gain.at(day * 24 + hour) * space.window_shgc, 0.0) / space.cooling_eer
            else:
                per_hour = daily_solar * space.window_shgc / max(len(solar_hours), 1)
                for hour in solar_hours:
                    hourly[day, hour, 0] = max(hourly[day, hour, 0] + per_hour, 0.0) / space.cooling_eer
        elif day >= climate.heating_start or day <= climate.heating_end:
            daily_solar = space.winter_solar_gain.daily_sum(day) if space.winter_solar_gain.hourly is not None else winter_daily
            daily[day, 1] = max(daily[day, 1] - daily_solar * space.window_shgc, 0.0) / space.heating_eer
            if space.winter_solar_gain.hourly is not None:
                for hour in solar_hours:
                    hourly[day, hour, 1] = max(hourly[day, hour, 1] - space.winter_solar_gain.at(day * 24 + hour) * space.window_shgc, 0.0) / space.heating_eer
            else:
                per_hour = daily_solar * space.window_shgc / max(len(solar_hours), 1)
                for hour in solar_hours:
                    hourly[day, hour, 1] = max(hourly[day, hour, 1] - per_hour, 0.0) / space.heating_eer
    return daily, hourly


def simulate_energy(rows: list[str], arguments: list[str]) -> EnergyOutput:
    config = config_from_arguments(arguments)
    spaces = parse_spaces(rows, config.schedule_path)
    climate = _climate(config.latitude)
    dry_bulb, dew_point, ground = _weather(config.weather_path)
    envelope_area = sum(space.exterior_wall_area + space.exterior_window_area + space.roof_area + space.skylight_area for space in spaces)
    envelope_times_k = sum((space.exterior_wall_area + space.roof_area) * space.wall_u_value
                           + (space.exterior_window_area + space.skylight_area) * space.window_u_value for space in spaces)
    envelope_k = envelope_times_k / envelope_area if envelope_area > 0 else 0.35
    weekend_correction = 1 + climate.correction_alpha_t * envelope_k * config.shape_factor + climate.correction_alpha_s * config.shape_factor
    simulated_spaces = [
        _simulate_space(space, config, climate, dry_bulb, dew_point, ground, envelope_k, weekend_correction)
        for space in spaces
    ]
    daily_loads = np.array([result[0] for result in simulated_spaces])
    zone_hours = np.array([result[1] for result in simulated_spaces])
    zone_days = zone_hours.sum(axis=2)
    zone_months = np.stack([
        daily_loads[:, MONTH_START_DAYS[month]:MONTH_START_DAYS[month + 1]].sum(axis=1)
        for month in range(12)
    ], axis=1)
    total_area = sum(space.floor_area for space in spaces)
    space_areas = np.array([space.floor_area for space in spaces])[:, None]
    normalized_zone_hours = zone_hours.reshape(len(spaces), 8760, 4) / space_areas[:, None, :] / 1000
    normalized_zone_days = zone_days / space_areas[:, None, :] / 1000
    normalized_zone_months = zone_months / space_areas[:, None, :] / 1000
    return EnergyOutput(
        total=daily_loads.sum(axis=(0, 1)) / total_area / 1000,
        spaces=daily_loads.sum(axis=1) / space_areas / 1000,
        months=zone_months.sum(axis=0) / total_area / 1000,
        days=zone_days.sum(axis=0) / total_area / 1000 if config.export_daily else None,
        hours=zone_hours.sum(axis=0).reshape(8760, 4) / total_area / 1000 if config.export_hourly else None,
        zone_months=normalized_zone_months if config.export_by_zone else None,
        zone_days=normalized_zone_days if config.export_by_zone and config.export_daily else None,
        zone_hours=normalized_zone_hours if config.export_by_zone and config.export_hourly else None,
    )


def simulate_energy_file(input_path: str | Path, arguments: list[str]) -> EnergyOutput:
    return simulate_energy(Path(input_path).read_text().splitlines(), arguments)
