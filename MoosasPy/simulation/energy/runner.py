"""
Quick energy analysis module.

This energy analysis is based on a simplified physical model,
which only takes 0.01s for a space and gets acceptable accuracy.
The analysis result has been validated by ASHRAE 140.
More information can be found in this article:
https://doi.org/10.1016/j.buildenv.2021.107929.

The residential and public energy models run directly in Python.
"""
from __future__ import annotations

from copy import copy
import math
from ...utils.support import os
from dataclasses import dataclass
import re
from ...utils.constant import buildingType, dateSetting
from ..contracts import SimulationResult
from .engine import EnergyOutput, simulate_energy

from ...model.io.idf.model import ThermalSettings

from ...model.resources import get_schedule_name, load_schedule
from ...model import MoosasModel
from ...utils import np, shapely

# A quick radiation estimation based on measured data (Beijing cumSky)
SUMMER_RADIATION = [280100, 175200, 213200, 116300, 280100]
WINTER_RADIATION = [150800, 355200, 123600, 51500, 150800]

# Legacy season boundaries copied from the historic MoosasModel defaults.
SUMMER_SOLAR_SEASON_DAYS = 123
WINTER_SOLAR_SEASON_DAYS = 120
SOLAR_ACTIVE_HOURS = tuple(range(8, 18))

# Month names for output parsing (12 months)
MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


TEMPORAL_SCALES = frozenset({"monthly", "daily", "hourly"})
SPATIAL_SCALES = frozenset({"building", "zone"})


def _validate_scales(temporal_scale: str, spatial_scale: str) -> tuple[str, str]:
    temporal_scale = str(temporal_scale).strip().lower()
    spatial_scale = str(spatial_scale).strip().lower()
    if temporal_scale not in TEMPORAL_SCALES:
        raise ValueError(f"temporal_scale must be one of {sorted(TEMPORAL_SCALES)}")
    if spatial_scale not in SPATIAL_SCALES:
        raise ValueError(f"spatial_scale must be one of {sorted(SPATIAL_SCALES)}")
    return temporal_scale, spatial_scale


def _scale_arguments(temporal_scale: str, spatial_scale: str) -> list[str]:
    arguments = []
    if temporal_scale == "daily":
        arguments += ["-d", "1"]
    elif temporal_scale == "hourly":
        arguments += ["-r", "1"]
    if spatial_scale == "zone":
        arguments += ["-z", "1"]
    return arguments


def _space_template_type(space):
    template = str(space.settings.get("zone_template", "")).strip()
    if not template:
        return ""
    return template.split("_")[-1].upper()


def _resolve_schedule_ref(model: MoosasModel, template_type: str, field_name: str, current_value):
    if isinstance(current_value, str):
        text = current_value.strip()
        try:
            return float(text)
        except Exception:
            return text
    if template_type:
        schedule_name = get_schedule_name(model, template_type, field_name)
        if schedule_name:
            return schedule_name
    return current_value


def _normalize_radiation_mode(require_radiation) -> int:
    if isinstance(require_radiation, bool):
        return 1 if require_radiation else 0
    if require_radiation is None:
        return 0
    if isinstance(require_radiation, str):
        text = require_radiation.strip().lower()
        if text in {"true", "yes", "on"}:
            return 1
        if text in {"false", "no", "off", ""}:
            return 0
        try:
            require_radiation = int(text)
        except Exception as exc:
            raise ValueError(f"Invalid requireRadiation value: {require_radiation!r}") from exc
    try:
        mode = int(require_radiation)
    except Exception as exc:
        raise ValueError(f"Invalid requireRadiation value: {require_radiation!r}") from exc
    if mode not in (0, 1, 2):
        raise ValueError(f"requireRadiation must be 0, 1, or 2; got {require_radiation!r}")
    return mode


def _num_or_zero(value):
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text or text.lower() == "none":
        return 0.0
    try:
        return float(text)
    except Exception:
        return 0.0


def _solar_season_day_count(season: str) -> int:
    season = str(season).strip().lower()
    if season == "summer":
        return SUMMER_SOLAR_SEASON_DAYS
    if season == "winter":
        return WINTER_SOLAR_SEASON_DAYS
    raise ValueError(f"Unsupported solar season: {season!r}")


def _solar_typical_daily_profile(season_total: float, season: str) -> list[float]:
    season_total = float(season_total)
    season_days = _solar_season_day_count(season)
    daily_total = season_total / season_days if season_days > 0 else 0.0
    values = [0.0] * 24
    if daily_total == 0.0:
        return values
    weights = np.sin(np.linspace(0.0, np.pi, len(SOLAR_ACTIVE_HOURS)))
    weight_sum = float(np.sum(weights))
    if weight_sum <= 0:
        return values
    scaled = daily_total * weights / weight_sum
    for hour, value in zip(SOLAR_ACTIVE_HOURS, scaled.tolist()):
        values[hour] = float(value)
    active_sum = sum(values[hour] for hour in SOLAR_ACTIVE_HOURS)
    values[SOLAR_ACTIVE_HOURS[-1]] += daily_total - active_sum
    return values


def _solar_schedule_name(space_id, space_index: int, season: str, suffix: str) -> str:
    safe_space_id = re.sub(r"[^0-9A-Za-z_]+", "_", str(space_id))
    safe_season = str(season).strip().upper()
    safe_suffix = str(suffix).strip().upper()
    return f"RAD_{safe_space_id}_{space_index:03d}_{safe_season}_{safe_suffix}"


def _write_typical_solar_schedule(model: MoosasModel, space, space_index: int, season: str, season_total: float):
    daily_name = _solar_schedule_name(space.id, space_index, season, "DAILY")
    weekly_name = _solar_schedule_name(space.id, space_index, season, "WEEKLY")
    daily_values = _solar_typical_daily_profile(season_total, season)
    model.schedule[daily_name] = {"type": "Daily", "value": daily_values}
    model.schedule[weekly_name] = {"type": "Weekly", "value": [daily_name] * 7}
    return weekly_name


@dataclass(frozen=True)
class EnergyResult(SimulationResult):
    """Structured output from an energy simulation."""

    data: dict | None = None


class EnergyRunner:
    """Prepare inputs, run the Python energy model, and return its results."""

    def __init__(
        self,
        model: MoosasModel | None = None,
        weather: object | None = None,
        core=buildingType.RESIDENTIAL,
        require_radiation=False,
        temporal_scale="monthly",
        spatial_scale="building",
        schedule_path=None,
        energy_input=None,
    ):
        self.model = model
        self.weather = weather
        self.core = core
        self.require_radiation = require_radiation
        self.temporal_scale, self.spatial_scale = _validate_scales(
            temporal_scale,
            spatial_scale,
        )
        self.schedule_path = schedule_path
        self.energy_input = energy_input

    def run(self) -> EnergyResult:
        """Execute the energy model and return structured results."""
        energy_input = self.energy_input
        if not energy_input:
            energy_input = build_energy_input(
                self.model,
                weather=self.weather,
                core=self.core,
                require_radiation=self.require_radiation,
                temporal_scale=self.temporal_scale,
                spatial_scale=self.spatial_scale,
                schedule_path=self.schedule_path,
            )
        else:
            energy_input = copy(energy_input)
            energy_input["args"] = list(energy_input.get("args", []))
            energy_input["args"] += _scale_arguments(self.temporal_scale, self.spatial_scale)
            if energy_input.get("schedule_path") and "-sch" not in energy_input["args"]:
                energy_input["args"] += ["-sch", os.path.abspath(energy_input["schedule_path"])]

        rows = [zone.paramToString() for zone in energy_input["zones"]]
        output = simulate_energy(rows, energy_input["args"])
        data = _energy_output_to_data(
            output,
            energy_input["zones"],
            temporal_scale=self.temporal_scale,
            spatial_scale=self.spatial_scale,
        )
        return EnergyResult(data=data)


def _energy_row(values, precision):
    formatted = [f"{value:.{precision}f}" for value in values]
    return {
        "cooling": formatted[0],
        "heating": formatted[1],
        "lighting": formatted[2],
        "equipment": formatted[3],
        "total": sum(float(value) for value in formatted),
    }


def _energy_output_to_data(output: EnergyOutput, zone_list, temporal_scale, spatial_scale):
    total = _energy_row(output.total, 2)
    for zone, values in zip(zone_list, output.spaces):
        zone.load = _energy_row(values, 2)
    months = {
        month: _energy_row(values, 2)
        for month, values in zip(dateSetting.MONTH_NAME, output.months)
    }
    data = {"total": total, "spaces": zone_list}
    if temporal_scale == "monthly":
        data["months"] = months
    elif temporal_scale == "daily":
        data["days"] = [_energy_row(values, 4) for values in output.days]
    else:
        data["hours"] = [_energy_row(values, 5) for values in output.hours]

    if spatial_scale == "zone":
        if temporal_scale == "monthly":
            data["zone_months"] = [
                [_energy_row(values, 2) for values in zone]
                for zone in output.zone_months
            ]
        elif temporal_scale == "daily":
            data["zone_days"] = [
                [_energy_row(values, 4) for values in zone]
                for zone in output.zone_days
            ]
        else:
            data["zone_hours"] = [
                [_energy_row(values, 5) for values in zone]
                for zone in output.zone_hours
            ]
    return data


def build_energy_input(model: MoosasModel,
                   weather: object,
                   core=buildingType.RESIDENTIAL,
                   require_radiation=False,
                   temporal_scale="monthly",
                   spatial_scale="building",
                   schedule_path=None):
    """Get the energy input configuration for a given MoosasModel.

    This function computes geometry-derived parameters for each space,
    populates ThermalSettings objects, and builds the engine configuration.

    Args:
        model (MoosasModel): The model for which to generate the energy input.
        core: Building type selector. Use buildingType.RESIDENTIAL for
            residential buildings, or any other buildingType value for public
            buildings. (default: buildingType.RESIDENTIAL)
        require_radiation (bool | int): 0/False keeps the fast geometric
            estimate, 1/True consumes precomputed seasonal radiation totals,
            and 2 consumes those totals to write schedule-driven solar gains.
        temporal_scale (str): One of ``monthly``, ``daily``, or ``hourly``.
        spatial_scale (str): Either ``building`` or ``zone``.
        schedule_path (str or None): Path to the schedule CSV file. If
            provided, adds '-sch <path>' to command-line args. (default: None)

    Returns:
        dict: A dictionary containing the energy input configuration:
            - 'zones': list of ThermalSettings objects
            - 'args': list of command-line argument strings

    Examples:
        >>> energy_input = build_energy_input(model, core=buildingType.OFFICE)
        >>> for z in energy_input['zones']:
        ...     print(z)

        >>> # Hourly output by zone
        >>> energy_input = build_energy_input(
        ...     model,
        ...     temporal_scale='hourly',
        ...     spatial_scale='zone',
        ...     schedule_path='office_schedule.csv',
        ... )
    """
    temporal_scale, spatial_scale = _validate_scales(temporal_scale, spatial_scale)
    def calculate_orientation(n):
        """Calculate the orientation angle in degrees from a 2D normal vector.

        Args:
            n: A 2-element array representing a 2D vector [n[0], n[1]].

        Returns:
            int: Orientation angle in degrees (0~360), measured clockwise
                from the positive y-axis. W:0, S:90, E:180, N:270.
        """
        o = int((np.arccos((-1) * n[0] / np.sqrt(n[0] ** 2 + n[1] ** 2))
                 * 180 / np.pi).round())
        if n[1] > 0:
            o = 360 - o
        if o == 360:
            o = 0
        return o

    def non(x):
        """Return x if positive, otherwise 0."""
        return x if x > 0 else 0

    if schedule_path is not None:
        load_schedule(model, schedule_path)

    radiation_mode = _normalize_radiation_mode(require_radiation)

    if radiation_mode in (1, 2):
        missing_space_ids = [
            s.id
            for s in model.spaceList
            if s.settings.get('zone_summerrad') is None
            or s.settings.get('zone_winterrad') is None
        ]
        if missing_space_ids:
            raise ValueError(
                "Precomputed zone_summerrad and zone_winterrad are required "
                f"for spaces: {', '.join(map(str, missing_space_ids))}"
            )

    total_outside_area, total_volume = 0, 0
    zones = []

    for i, s in enumerate(model.spaceList):
        outside_area, facade_area, window_area = 0, 0, 0
        roof_area, skylight_area, floor_area = 0, 0, 0
        summer_solar, winter_solar = 0.0, 0.0
        theZone = ThermalSettings(**(s.settings))
        theZone.id = s.id

        template_type = _space_template_type(s)
        for field_name in ("zone_ppsm", "zone_equipment", "zone_lighting"):
            resolved = _resolve_schedule_ref(model, template_type, field_name, theZone.params.get(field_name))
            if resolved is not None:
                theZone.updateParams(**{field_name: resolved})

        total_volume += s.area * s.height

        for b in s.edge.wall:
            if b.isOuter:
                total_outside_area += b.area
                outside_area += non(shapely.length(b.force_2d()) - 5.0) * 5.0
                facade_area += b.area * (1 - b.wwr)
                window_area += b.area * b.wwr
                o = calculate_orientation(b.normal)
                summer_solar += (
                    SUMMER_RADIATION[o // 90]
                    + ((o % 90) / 90.0)
                    * (SUMMER_RADIATION[o // 90 + 1]
                       - SUMMER_RADIATION[o // 90])
                ) * b.area * b.wwr
                winter_solar += (
                    WINTER_RADIATION[o // 90]
                    + ((o % 90) / 90.0)
                    * (WINTER_RADIATION[o // 90 + 1]
                       - WINTER_RADIATION[o // 90])
                ) * b.area * b.wwr

        if radiation_mode == 1:
            summer_solar = _num_or_zero(s.settings.get('zone_summerrad')) * 60
            winter_solar = _num_or_zero(s.settings.get('zone_winterrad')) * 60
        elif radiation_mode == 2:
            summer_total = _num_or_zero(s.settings.get('zone_summerrad'))
            winter_total = _num_or_zero(s.settings.get('zone_winterrad'))
            summer_schedule = _write_typical_solar_schedule(model, s, i, "summer", summer_total * 60)
            winter_schedule = _write_typical_solar_schedule(model, s, i, "winter", winter_total * 60)
            s.settings['summer_solar'] = summer_schedule
            s.settings['winter_solar'] = winter_schedule
            theZone.updateParams(**{
                'summer_solar': summer_schedule,
                'winter_solar': winter_schedule,
            })

        for c in s.ceiling.face:
            if c.isOuter:
                total_outside_area += c.area
                roof_area += c.area
            elif len(c.glazingId) > 0:
                skylight_area += c.area * c.wwr

        for fl in s.floor.face:
            if fl.isOuter:
                floor_area += fl.area

        addSettings = {
            'space_height': round(s.height, 2),
            'zone_area': round(s.area, 2),
            'outside_area': round(outside_area, 2),
            'facade_area': round(facade_area, 2),
            'window_area': round(window_area, 2),
            'roof_area': round(roof_area, 2),
            'skylight_area': round(skylight_area, 2),
            'floor_area': round(floor_area, 2),
        }

        if radiation_mode == 2:
            addSettings['summer_solar'] = s.settings['summer_solar']
            addSettings['winter_solar'] = s.settings['winter_solar']
        else:
            addSettings['summer_solar'] = round(summer_solar, 2)
            addSettings['winter_solar'] = round(winter_solar, 2)

        theZone.updateParams(**addSettings)
        zones.append(theZone)

    # ── Build command-line arguments ──────────────────────
    # Determine the building type integer for the -t parameter.
    # buildingType.RESIDENTIAL maps to 0; all others map to their
    # integer value (1=OFFICE, 2=HOTEL, 3=SCHOOL, etc.)
    building_type_int = 0 if core == buildingType.RESIDENTIAL else 1

    args = [
        '-w', weather.weather_file,
        '-t', str(building_type_int),
        '-l', str(math.radians(float(weather.location.latitude))),
        '-a', str(round(float(weather.location.altitude), 2)),
        '-s', str(round(total_outside_area / total_volume, 2)),
    ]

    args += _scale_arguments(temporal_scale, spatial_scale)

    schedule_out_path = None
    if getattr(model, "schedule", None):
        from ...model.resources import write_schedule

        schedule_out_path = write_schedule(model)
        args += ['-sch', schedule_out_path]

    return {'zones': zones, 'args': args, 'schedule_path': schedule_out_path}
