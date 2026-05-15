"""
Quick energy analysis module.

This energy analysis is based on a simplified physical model,
which only takes 0.01s for a space and gets acceptable accuracy.
The analysis result has been validated by ASHRAE 140.
More information can be found in this article:
https://doi.org/10.1016/j.buildenv.2021.107929.

This module serves as the Python-side interface for the unified
MoosasEnergy Go executable, which supports both residential and
public building types via the -t parameter.
"""
from ..utils.support import os
from datetime import datetime
from ..utils import path, callCmd, parseFile, FileError
from ..utils.constant import buildingType, dateSetting
from ..rad import modelRadiation

from ..thermal.settings import ThermalSettings

from ..models import *

# A quick radiation estimation based on measured data (Beijing cumSky)
SUMMER_RADIATION = [280100, 175200, 213200, 116300, 280100]
WINTER_RADIATION = [150800, 355200, 123600, 51500, 150800]

# Directory paths for the energy module
energyScriptDir = os.path.join(path.libDir, "energy")
energyDataDir = os.path.join(path.dataDir, "energy")
energyExeSuffix = ".exe" if os.name == "nt" else ""

# Month names for output parsing (12 months)
MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


def _read_weather_temperature_from_file(weather_file):
    with open(weather_file, "r") as f:
        data = np.array([line.strip('\n').split(',') for line in f.readlines()]).T
    return np.array(data[3]).astype(float).tolist()


def _interpolate_daily_to_hourly(daily_rows, t_out_hourly, zone_h_temp, zone_c_temp):
    """Temporary interpolation path for hourly loads from daily totals."""
    t_out = np.array(t_out_hourly, dtype=float)
    if t_out.size < 8760:
        raise ValueError("weather temperature series must have at least 8760 points.")
    zone_h_temp = float(zone_h_temp)
    zone_c_temp = float(zone_c_temp)
    rows = []
    for day in range(365):
        day_vals = daily_rows[day]
        day_t = t_out[day * 24:(day + 1) * 24]
        h_weight = np.maximum(zone_h_temp - day_t, 0.0)
        c_weight = np.maximum(day_t - zone_c_temp, 0.0)
        h_sum = float(np.sum(h_weight))
        c_sum = float(np.sum(c_weight))
        h_day = float(day_vals["heating"])
        c_day = float(day_vals["cooling"])
        l_day = float(day_vals["lighting"])
        h_hour = h_day * (h_weight / h_sum) if h_sum > 0 else np.zeros(24, dtype=float)
        c_hour = c_day * (c_weight / c_sum) if c_sum > 0 else np.zeros(24, dtype=float)
        l_hour = np.full(24, l_day / 24.0, dtype=float)
        for i in range(24):
            rows.append({
                "cooling": float(c_hour[i]),
                "heating": float(h_hour[i]),
                "lighting": float(l_hour[i]),
                "total": float(c_hour[i] + h_hour[i] + l_hour[i]),
            })
    return rows


def energyAnalysis(model: MoosasModel = None,
                   core=buildingType.RESIDENTIAL,
                   requireRadiation=False,
                   exportDaily=False,
                   exportHourly=False,
                   exportByZone=False,
                   schedulePath=None,
                   energyInput=None,
                   inputPath=os.path.join(energyDataDir, "Energy.i"),
                   resultPath=os.path.join(energyDataDir, "Energy.o")) -> dict:
    """Quick energy analysis function.

    This function prepares the input file, invokes the unified MoosasEnergy
    executable, and parses the output. It supports both residential and public
    building types, and can export results at multiple granularities.

    Args:
        model (MoosasModel): The model to analyze.
        core: Building type selector. Use buildingType.RESIDENTIAL for
            residential buildings (type=0), or any other buildingType value
            for public buildings (type=1~6). (default: buildingType.RESIDENTIAL)
        requireRadiation (bool): True to perform accurate radiation calculation
            using MoosasRad. If False, solar heat is estimated based on
            Beijing's cumSky. (default: False)
        exportDaily (bool): If True, include daily (365-row) results in output.
            (default: False)
        exportHourly (bool): If True, include hourly (8760-row) results in
            output. (default: False)
        exportByZone (bool): If True, include per-zone results in output.
            (default: False)
        schedulePath (str or None): Path to the schedule CSV file. If None,
            schedule functionality is disabled. (default: None)
        energyInput (dict or None): Pre-built energy input dict. If provided,
            skips getEnergyInput(). Must contain 'zones' and 'args' keys.
            (default: None)
        inputPath (str): Path to save the input .i file.
            (default: data/energy/Energy.i)
        resultPath (str): Path to save the output .o file.
            (default: data/energy/Energy.o)

    Returns:
        dict: A dictionary containing the parsed energy results:
            - 'total': dict with 'cooling', 'heating', 'lighting', 'total'
            - 'spaces': list of ThermalSettings with load attributes set
            - 'months': dict mapping month names to energy demand dicts
            - 'days': list of dicts (365 items), only if exportDaily=True
            - 'hours': list of dicts (8760 items), only if exportHourly=True
            - 'zone_months': list of list of dicts, only if exportByZone=True
            - 'zone_days': list of list of dicts, only if exportByZone=True
                and exportDaily=True
            - 'zone_hours': list of list of dicts, only if exportByZone=True
                and exportHourly=True

    Raises:
        ShellError: Error occurred in MoosasEnergy executable.

    Examples:
        >>> e_data = energyAnalysis(model, requireRadiation=True)
        >>> print(e_data['total'])

        >>> # With daily and hourly output
        >>> e_data = energyAnalysis(model, exportDaily=True, exportHourly=True)
        >>> print(len(e_data['days']))   # 365
        >>> print(len(e_data['hours']))  # 8760

        >>> # With schedule file
        >>> e_data = energyAnalysis(model, schedulePath='office_schedule.csv')

    References:
        https://doi.org/10.1016/j.buildenv.2021.107929.
    """
    if not energyInput:
        energyInput = getEnergyInput(
            model,
            core=core,
            requireRadiation=requireRadiation,
            exportDaily=exportDaily,
            exportHourly=exportHourly,
            exportByZone=exportByZone,
            schedulePath=schedulePath,
        )

    inputPath = os.path.abspath(inputPath)
    resultPath = os.path.abspath(resultPath)

    # Write the input .i file
    with open(inputPath, "w") as file:
        lines = [zone.paramToString() for zone in energyInput['zones']]
        file.write('!' + energyInput['zones'][0].paramTags() + '\n')
        file.write('\n'.join(lines))

    # Append output path and input path to the command-line arguments
    energyInput['args'] += ['-o', f'"{resultPath}"'] + [f'"{inputPath}"']

    # Use the unified MoosasEnergy executable
    exe_command = os.path.abspath(
        os.path.join(energyScriptDir, f"MoosasEnergy{energyExeSuffix}")
    )
    exe_command = f'"{exe_command}"'
    exe_command = [exe_command] + energyInput['args']
    callCmd(exe_command, cwd=os.path.abspath(energyScriptDir))

    weather_temperature = None
    if model is not None:
        if model.weather is None:
            model.loadWeatherData()
        weather_temperature = np.array(model.weather.weatherData.get("temperature")).astype(float).tolist()
    else:
        # fallback from -w argument when only energyInput is provided.
        args = energyInput.get("args", []) if isinstance(energyInput, dict) else []
        w_path = None
        for i, a in enumerate(args):
            if a == "-w" and i + 1 < len(args):
                w_path = args[i + 1].strip('"')
                break
        if w_path and os.path.isfile(w_path):
            weather_temperature = _read_weather_temperature_from_file(w_path)

    return parseEnergyOutput(
        resultPath,
        energyInput['zones'],
        exportDaily=exportDaily,
        exportHourly=exportHourly,
        exportByZone=exportByZone,
        weather_temperature=weather_temperature,
    )


def parseEnergyOutput(resultPath,
                      zoneList: list[ThermalSettings] = None,
                      exportDaily=False,
                      exportHourly=False,
                      exportByZone=False,
                      weather_temperature=None):
    """Parse the output file from MoosasEnergy executable.

    The output file contains multiple sections separated by ';', each
    starting with a '!' header line. This function parses all sections
    and returns a structured dictionary.

    Args:
        resultPath (str): Path to the result .o file to parse.
        zoneList (list[ThermalSettings], optional): List of ThermalSettings
            objects to record per-space results. If None, results are returned
            as plain dictionaries. (default: None)
        exportDaily (bool): Whether daily results are expected in the output.
            (default: False)
        exportHourly (bool): Whether hourly results are expected in the output.
            (default: False)
        exportByZone (bool): Whether per-zone results are expected in the
            output. (default: False)

    Returns:
        dict: A dictionary containing the parsed energy results with keys:
            - 'total': dict with 'cooling', 'heating', 'lighting', 'total'
            - 'spaces': list of ThermalSettings or list of dicts
            - 'months': dict mapping month names to energy demand dicts
            - 'days': list of 365 dicts (only if exportDaily=True)
            - 'hours': list of 8760 dicts (only if exportHourly=True)
            - 'zone_months': list[list[dict]], per-zone monthly
                (only if exportByZone=True)
            - 'zone_days': list[list[dict]], per-zone daily
                (only if exportByZone=True and exportDaily=True)
            - 'zone_hours': list[list[dict]], per-zone hourly
                (only if exportByZone=True and exportHourly=True)

    Raises:
        FileError: The output file cannot be parsed.

    Examples:
        >>> e_data = parseEnergyOutput('Energy.o', exportDaily=True)
        >>> print(len(e_data['days']))  # 365
    """
    try:
        output = parseFile(resultPath)

        # ── Section 0: TOTAL (1 row) ──────────────────────
        total_row = output[0][0]
        total = {
            "cooling": total_row[0],
            "heating": total_row[1],
            "lighting": total_row[2],
            "total": np.array(total_row).astype(float).sum(),
        }

        # ── Section 1: SPACE RESULT (N rows) ─────────────
        if zoneList:
            for i in range(len(zoneList)):
                zoneList[i].load = {
                    'cooling': output[1][i][0],
                    'heating': output[1][i][1],
                    'lighting': output[1][i][2],
                    'total': np.array(output[1][i]).astype(float).sum(),
                }
        else:
            zoneList = [{
                'cooling': res[0],
                'heating': res[1],
                'lighting': res[2],
                'total': np.array(res).astype(float).sum(),
            } for res in output[1]]

        # ── Section 2: MONTH RESULT (12 rows) ────────────
        months_result = {}
        for mon, result in zip(dateSetting.MONTH_NAME, output[2]):
            months_result[mon] = {
                "cooling": result[0],
                "heating": result[1],
                "lighting": result[2],
                "total": np.array(result).astype(float).sum(),
            }

        e_data = {
            "total": total,
            "spaces": zoneList,
            "months": months_result,
        }

        # ── Track the next section index ─────────────────
        # Sections 0, 1, 2 are always present (TOTAL, SPACE, MONTH).
        # Additional sections are appended in the order defined by the
        # Go executable: DAY, HOUR, ZONE MONTH, ZONE DAY, ZONE HOUR.
        section_idx = 3

        # ── Section 3 (optional): DAY RESULT (365 rows) ──
        if exportDaily:
            e_data["days"] = _parse_energy_rows(output[section_idx])
            section_idx += 1

        # ── Section 4 (optional): HOUR RESULT (8760 rows) ─
        if exportHourly:
            # temporary interpolation path: generate hourly loads from daily rows.
            if "days" not in e_data:
                raise ValueError("exportHourly=True requires exportDaily=True for temporary interpolation.")
            if weather_temperature is None:
                raise ValueError("weather_temperature is required for temporary hourly interpolation.")
            zone_h = zoneList[0].params.get("zone_h_temp", 18) if zoneList else 18
            zone_c = zoneList[0].params.get("zone_c_temp", 26) if zoneList else 26
            e_data["hours"] = _interpolate_daily_to_hourly(
                e_data["days"], weather_temperature, zone_h, zone_c
            )
            # old direct parser path retained intentionally:
            # e_data["hours"] = _parse_energy_rows(output[section_idx])
            # section_idx += 1

        # ── Section 5 (optional): ZONE MONTH RESULT ──────
        if exportByZone:
            num_zones = len(output[1])  # number of spaces
            e_data["zone_months"] = _parse_zone_energy_rows(
                output[section_idx], num_zones, 12
            )
            section_idx += 1

            # ── Section 6 (optional): ZONE DAY RESULT ────
            if exportDaily:
                e_data["zone_days"] = _parse_zone_energy_rows(
                    output[section_idx], num_zones, 365
                )
                section_idx += 1

            # ── Section 7 (optional): ZONE HOUR RESULT ───
            if exportHourly:
                # temporary interpolation path from zone daily rows.
                if weather_temperature is None:
                    raise ValueError("weather_temperature is required for temporary zone hourly interpolation.")
                zone_days = e_data.get("zone_days", [])
                e_data["zone_hours"] = []
                for zi in range(num_zones):
                    z_daily = zone_days[zi] if zi < len(zone_days) else [{"cooling": 0, "heating": 0, "lighting": 0}] * 365
                    z_h = zoneList[zi].params.get("zone_h_temp", 18) if zoneList and zi < len(zoneList) else 18
                    z_c = zoneList[zi].params.get("zone_c_temp", 26) if zoneList and zi < len(zoneList) else 26
                    e_data["zone_hours"].append(
                        _interpolate_daily_to_hourly(z_daily, weather_temperature, z_h, z_c)
                    )
                # old direct parser path retained intentionally:
                # e_data["zone_hours"] = _parse_zone_energy_rows(
                #     output[section_idx], num_zones, 8760
                # )
                # section_idx += 1

        return e_data

    except Exception:
        raise FileError(resultPath)


def _parse_energy_rows(section_data):
    """Parse a list of [cooling, heating, lighting] rows into dicts.

    Args:
        section_data: List of rows, each row is a list of 3 string values.

    Returns:
        list[dict]: Each dict has 'cooling', 'heating', 'lighting', 'total'.
    """
    return [{
        "cooling": row[0],
        "heating": row[1],
        "lighting": row[2],
        "total": np.array(row).astype(float).sum(),
    } for row in section_data]


def _parse_zone_energy_rows(section_data, num_zones, items_per_zone):
    """Parse zone-level output rows into a nested list structure.

    The Go executable outputs zone results as flat rows in the format:
    SpaceIndex,Cooling,Heating,Lighting
    This function groups them by zone index.

    Args:
        section_data: List of rows, each row is [spaceIdx, cooling, heating,
            lighting].
        num_zones (int): Number of zones/spaces.
        items_per_zone (int): Number of items per zone (12 for months,
            365 for days, 8760 for hours).

    Returns:
        list[list[dict]]: Outer list indexed by zone, inner list contains
            dicts with 'cooling', 'heating', 'lighting', 'total'.
    """
    zone_results = [[] for _ in range(num_zones)]
    for row in section_data:
        zone_idx = int(float(row[0]))
        zone_results[zone_idx].append({
            "cooling": row[1],
            "heating": row[2],
            "lighting": row[3],
            "total": np.array(row[1:4]).astype(float).sum(),
        })
    return zone_results


def getEnergyInput(model: MoosasModel,
                   core=buildingType.RESIDENTIAL,
                   requireRadiation=False,
                   exportDaily=False,
                   exportHourly=False,
                   exportByZone=False,
                   schedulePath=None):
    """Get the energy input configuration for a given MoosasModel.

    This function computes geometry-derived parameters for each space,
    populates ThermalSettings objects, and builds the command-line argument
    list for the unified MoosasEnergy executable.

    Args:
        model (MoosasModel): The model for which to generate the energy input.
        core: Building type selector. Use buildingType.RESIDENTIAL for
            residential buildings, or any other buildingType value for public
            buildings. (default: buildingType.RESIDENTIAL)
        requireRadiation (bool): If True, enables accurate radiation
            calculation using MoosasRad. (default: False)
        exportDaily (bool): If True, adds '-d 1' to command-line args.
            (default: False)
        exportHourly (bool): If True, adds '-r 1' to command-line args.
            (default: False)
        exportByZone (bool): If True, adds '-z 1' to command-line args.
            (default: False)
        schedulePath (str or None): Path to the schedule CSV file. If
            provided, adds '-sch <path>' to command-line args. (default: None)

    Returns:
        dict: A dictionary containing the energy input configuration:
            - 'zones': list of ThermalSettings objects
            - 'args': list of command-line argument strings

    Examples:
        >>> energyInput = getEnergyInput(model, core=buildingType.OFFICE)
        >>> for z in energyInput['zones']:
        ...     print(z)

        >>> # With all export options
        >>> energyInput = getEnergyInput(
        ...     model,
        ...     exportDaily=True,
        ...     exportHourly=True,
        ...     exportByZone=True,
        ...     schedulePath='office_schedule.csv',
        ... )
    """
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

    # Perform radiation calculation if requested
    if requireRadiation:
        t2 = datetime.now()
        if model.spaceList[0].settings['zone_summerrad'] is None:
            modelRadiation(model, reflection=0)
        t3 = datetime.now()
        print(f"Radiation calculation time: {t3 - t2}")

    total_outside_area, total_volume = 0, 0
    zones = []

    for i, s in enumerate(model.spaceList):
        outside_area, facade_area, window_area = 0, 0, 0
        roof_area, skylight_area, floor_area = 0, 0, 0
        summer_solar, winter_solar = 0.0, 0.0
        theZone = ThermalSettings(**(s.settings))
        theZone.id = s.id

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

        if requireRadiation:
            summer_solar = s.settings['zone_summerrad'] * 60
            winter_solar = s.settings['zone_winterrad'] * 60

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
            'summer_solar': round(summer_solar, 2),
            'winter_solar': round(winter_solar, 2),
        }

        theZone.updateParams(**addSettings)
        zones.append(theZone)

    # Load weather data if not already loaded
    if model.weather is None:
        model.loadWeatherData()
    weather = model.weather

    # ── Build command-line arguments ──────────────────────
    # Determine the building type integer for the -t parameter.
    # buildingType.RESIDENTIAL maps to 0; all others map to their
    # integer value (1=OFFICE, 2=HOTEL, 3=SCHOOL, etc.)
    building_type_int = 0 if core == buildingType.RESIDENTIAL else 1

    args = [
        '-w', f'"{weather.weatherFile}"',
        '-t', str(building_type_int),
        '-l', str(round(float(weather.location.latitude), 2)),
        '-a', str(round(float(weather.location.altitude), 2)),
        '-s', str(round(total_outside_area / total_volume, 2)),
    ]

    # Append optional export flags
    if exportDaily:
        args += ['-d', '1']
    # temporary interpolation path:
    # keep old logic as comment, do not request engine hourly output.
    # if exportHourly:
    #     args += ['-r', '1']
    if exportByZone:
        args += ['-z', '1']

    # Append schedule file path if provided
    if schedulePath is not None:
        abs_schedule_path = os.path.abspath(schedulePath)
        args += ['-sch', f'"{abs_schedule_path}"']

    return {'zones': zones, 'args': args}
