# MoosasEnergy Direct Integration Guide

This document is for callers that want to execute `MoosasEnergy` directly, without going through `MoosasPy`.

The current implementation is defined by:

- `MoosasPy/libs/energy/MoosasEnergy.go`
- `MoosasPy/energy/analysis.py`
- `MoosasPy/thermal/settings.py`

## Overview

`MoosasEnergy` is a command-line engine that:

1. reads one building input file (`.i`);
2. optionally reads one schedule file (`.sch` / CSV-like text);
3. reads one weather file (`.csv`, DeST-style);
4. writes one result file (`.o`).

The executable supports:

- residential buildings: `-t 0`
- public buildings: `-t 1` to `-t 6`
- monthly, daily, and hourly outputs
- whole-building and per-space outputs
- fixed values or schedule-driven values for selected input fields

## Command Line Interface

### Syntax

```bash
MoosasEnergy [options] inputFile.i
```

The input file path is required and must be the last argument.

### Options

| Option | Long option | Type | Meaning |
| --- | --- | --- | --- |
| `-h` | `-help` | none | Print help and exit |
| `-w` | `-weather` | path | Weather file path |
| `-t` | `-type` | int | Building type |
| `-l` | `-lat` | float | Site latitude in radians |
| `-a` | `-alt` | float | Site altitude in meters |
| `-s` | `-shape` | float | Building shape factor = exterior surface area / building volume |
| `-o` | `-output` | path | Output file path |
| `-d` | `-daily` | `0` or `1` | Export daily result section |
| `-r` | `-hourly` | `0` or `1` | Export hourly result section |
| `-z` | `-zone` | `0` or `1` | Export per-space result sections |
| `-sch` | `-schedule` | path | Schedule CSV file |

### Building Type Values

| Value | Meaning |
| --- | --- |
| `0` | Residential |
| `1` | Office |
| `2` | Hotel |
| `3` | School |
| `4` | Commercial |
| `5` | Opera / Theater |
| `6` | Hospital |

### Example

```bash
MoosasEnergy.exe ^
  -w weather_545110.csv ^
  -t 1 ^
  -l 0.69691 ^
  -a 43.3 ^
  -s 0.78 ^
  -d 1 ^
  -r 1 ^
  -z 1 ^
  -sch office_schedule.csv ^
  -o result.o ^
  Energy.i
```

## Weather File Contract

`MoosasEnergy` expects a DeST-style weather CSV and reads specific columns by index:

| CSV column index | Meaning | Used by |
| --- | --- | --- |
| `3` | dry-bulb temperature | residential and public |
| `4` | dew-point temperature | public only |
| `7` | ground temperature | residential and public |

Notes:

- The code reads the weather file as plain CSV without validating a header.
- A direct caller should provide 8760 hourly rows in the same ordering expected by the DeST weather data used in MOOSAS.

## Input File Format (`.i`)

### File Rules

- Plain text CSV.
- One row per space / zone.
- Comment rows starting with `!` are ignored.
- Each data row must contain at least 27 comma-separated fields.
- Field order is fixed.

The field order below matches the actual order written by `MoosasPy.simulation.energy.runner.energyAnalysis()` through `ThermalSettings.paramToString()`.

### Field Definitions

| Index | Field name | Meaning | Unit / value domain |
| --- | --- | --- | --- |
| `0` | `StoryHeight` | Space height | m |
| `1` | `FloorArea` | Total floor area of the space | m2 |
| `2` | `PerimeterZoneArea` | Exterior/perimeter zone area | m2 |
| `3` | `ExteriorWallArea` | Opaque exterior wall area | m2 |
| `4` | `ExteriorWindowArea` | Exterior window area | m2 |
| `5` | `RoofArea` | Exterior roof area | m2 |
| `6` | `SkylightArea` | Skylight area | m2 |
| `7` | `GroundFloorArea` | Ground-contact floor area | m2 |
| `8` | `SummerSolarGain` | Summer solar input | seasonal total in Wh, or schedule name |
| `9` | `WinterSolarGain` | Winter solar input | seasonal total in Wh, or schedule name |
| `10` | `WallUValue` | U-value for wall, roof, and ground floor conduction in this model | W/(m2*K) |
| `11` | `WindowUValue` | U-value for windows and skylights | W/(m2*K) |
| `12` | `WindowSHGC` | Solar heat gain coefficient of windows/skylights | 0 to 1 in normal use |
| `13` | `CoolingSetpointTemp` | Cooling setpoint temperature | degC or schedule name |
| `14` | `CoolingSetpointHumidity` | Cooling setpoint relative humidity | 0 to 1, or schedule name |
| `15` | `HeatingSetpointTemp` | Heating setpoint temperature | degC or schedule name |
| `16` | `CoolingEER` | Cooling efficiency ratio | positive number |
| `17` | `HeatingEER` | Heating efficiency ratio | positive number |
| `18` | `OccupancyStartHour` | Occupancy/work start hour | integer, typically `0` to `23` |
| `19` | `OccupancyEndHour` | Occupancy/work end hour | integer, typically `0` to `23` |
| `20` | `OccupantDensity` | Occupant density | people/m2 or schedule name |
| `21` | `FreshAirPerPerson` | Outdoor air rate per person | m3/(h*person) or schedule name |
| `22` | `OccupantHeatGain` | Sensible/internal gain per person | W/person or schedule name |
| `23` | `EquipmentHeatGain` | Equipment internal gain intensity | W/m2 or schedule name |
| `24` | `LightingHeatGain` | Lighting internal gain intensity | W/m2 or schedule name |
| `25` | `InfiltrationACH` | Infiltration air change rate during occupied period | ACH |
| `26` | `NightVentilationACH` | Night ventilation air change rate | ACH |

### Minimal Example

```csv
!StoryHeight,FloorArea,PerimeterZoneArea,ExteriorWallArea,ExteriorWindowArea,RoofArea,SkylightArea,GroundFloorArea,SummerSolarGain,WinterSolarGain,WallUValue,WindowUValue,WindowSHGC,CoolingSetpointTemp,CoolingSetpointHumidity,HeatingSetpointTemp,CoolingEER,HeatingEER,OccupancyStartHour,OccupancyEndHour,OccupantDensity,FreshAirPerPerson,OccupantHeatGain,EquipmentHeatGain,LightingHeatGain,InfiltrationACH,NightVentilationACH
3.0,120.0,48.0,85.0,22.0,120.0,0.0,120.0,150000.0,90000.0,0.5,2.4,0.6,26,0.4,18,2.5,2.0,8,18,0.02,30,88,8,6,0.5,1.0
3.0,80.0,30.0,55.0,16.0,0.0,0.0,0.0,90000.0,50000.0,0.5,2.4,0.6,Office_CoolingSetpoint,Office_CoolingRH,Office_HeatingSetpoint,2.5,2.0,8,18,Office_OccDensity,Office_FreshAir,Office_PeopleGain,Office_EquipmentGain,Office_LightingGain,0.5,1.0
```

### Fields That Accept a Schedule Name

These 10 fields may be either:

- a numeric literal, or
- a schedule name resolved through `-sch`

| Field index | Field name |
| --- | --- |
| `8` | `SummerSolarGain` |
| `9` | `WinterSolarGain` |
| `13` | `CoolingSetpointTemp` |
| `14` | `CoolingSetpointHumidity` |
| `15` | `HeatingSetpointTemp` |
| `20` | `OccupantDensity` |
| `21` | `FreshAirPerPerson` |
| `22` | `OccupantHeatGain` |
| `23` | `EquipmentHeatGain` |
| `24` | `LightingHeatGain` |

If one of these fields is not numeric and no schedule file is loaded, the program exits with an error.

### Solar Input Semantics

Fields `8` and `9` support two different input modes:

- numeric input: keep the legacy behavior
- schedule input: use explicit hourly solar gains from `-sch`

#### Numeric solar input

- `SummerSolarGain` and `WinterSolarGain` are interpreted as seasonal totals in `Wh`.
- The engine keeps the original residential/public seasonal averaging logic.
- This is backward-compatible with old `.i` files.

#### Schedule solar input

- `SummerSolarGain` and `WinterSolarGain` are interpreted as schedule names.
- The referenced schedule values must be absolute hourly solar gains in `Wh`.
- These values are not normalized weights.
- When a solar schedule is used, it replaces the old equal-split seasonal fallback for that season.
- `WindowSHGC` is still applied inside the engine at the normal solar-gain injection step.

Practical meaning:

- if field `8` is a schedule name, each expanded hourly value is the summer-season solar gain for that hour in `Wh`
- if field `9` is a schedule name, each expanded hourly value is the winter-season solar gain for that hour in `Wh`

## Schedule File Format (`-sch`)

The schedule file is a CSV library keyed by schedule name.

### Supported schedule record types

| Type name in column 2 | Meaning |
| --- | --- |
| `Daily` | 24 values, repeated for all 365 days |
| `Hourly` | 8760 explicit hourly values |
| `Weekly` | 7 references to `Daily` schedules, ordered Monday to Sunday |

### Record formats

#### Daily

```csv
ScheduleName,Daily,v1,v2,...,v24
```

#### Hourly

```csv
ScheduleName,Hourly,v1,v2,...,v8760
```

#### Weekly

```csv
ScheduleName,Weekly,MondayDaily,TuesdayDaily,WednesdayDaily,ThursdayDaily,FridayDaily,SaturdayDaily,SundayDaily
```

### Important rules

- `Weekly` schedules can only reference `Daily` schedules.
- The engine expands schedules to a full 8760-hour array internally.
- In the weekly expansion logic, day `0` of the year is treated as Monday.
- Schedule values are not limited to `0..1`; any valid float is accepted.

### Solar Schedule Rules

For `SummerSolarGain` and `WinterSolarGain`, the schedule values mean:

- unit: `Wh`
- meaning: absolute solar gain for that hour
- not allowed interpretation: normalized profile multiplier

Recommended patterns:

- `Daily + Weekly` if you want one typical day repeated by weekday
- `Hourly` if you want a full 8760-hour solar sequence

Example solar schedules:

```csv
RAD_SpaceA_SUMMER_DAILY,Daily,0,0,0,0,0,0,0,0,120,260,380,470,520,470,380,260,120,40,0,0,0,0,0,0
RAD_SpaceA_SUMMER_WEEKLY,Weekly,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY,RAD_SpaceA_SUMMER_DAILY
RAD_SpaceA_WINTER_DAILY,Daily,0,0,0,0,0,0,0,0,80,150,220,280,310,280,220,150,80,20,0,0,0,0,0,0
RAD_SpaceA_WINTER_WEEKLY,Weekly,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY,RAD_SpaceA_WINTER_DAILY
```

Matching `.i` row fragment:

```csv
...,RAD_SpaceA_SUMMER_WEEKLY,RAD_SpaceA_WINTER_WEEKLY,...
```

### MoosasPy Generation Note

When calling through `MoosasPy.simulation.energy.runner.energyAnalysis()`:

- `requireRadiation=False` or `0`: keep the fast geometric estimate
- `requireRadiation=True` or `1`: write numeric seasonal solar totals into fields `8` and `9`
- `requireRadiation=2`: generate summer/winter solar schedules in `model.schedule`, write them to `-sch`, and place the generated weekly schedule names into fields `8` and `9`

In mode `2`, `MoosasPy` currently builds a simplified typical-day profile:

- first divide the seasonal total by the built-in season day count
- then distribute the daily total across hours `8` to `17`
- the daytime distribution follows a sine curve from `0` to `pi`
- all other hours are `0`

This is an approximation used to provide schedule-driven solar input without requiring a full maintained hourly radiation model.

## Output File Format (`.o`)

### File Rules

- Plain text.
- Sections are separated by a line containing `;`.
- Each section starts with a `!` header row.
- The data columns are comma-separated.

All reported values in the output file are area-normalized:

- whole-building sections are normalized by total building floor area
- per-space sections are normalized by each space floor area
- units are therefore `kWh/m2`

### Always-present sections

### `!TOTAL:`

One row:

```text
Cooling,Heating,Lighting
```

Meaning: whole-building annual result.

### `!SPACE RESULT:`

One row per space:

```text
Cooling,Heating,Lighting
```

Meaning: annual result for each space, in the same order as the input `.i` rows.

### `!MONTH RESULT:`

12 rows:

```text
Cooling,Heating,Lighting
```

Meaning: whole-building monthly result from January to December.

### Optional sections

### `!DAY RESULT:`

Enabled by `-d 1`.

- 365 rows
- format: `Cooling,Heating,Lighting`

### `!HOUR RESULT:`

Enabled by `-r 1`.

- 8760 rows
- format: `Cooling,Heating,Lighting`

### `!ZONE MONTH RESULT:`

Enabled by `-z 1`.

- `N * 12` rows
- format: `SpaceIndex,Cooling,Heating,Lighting`

### `!ZONE DAY RESULT:`

Enabled by `-z 1 -d 1`.

- `N * 365` rows
- format: `SpaceIndex,Cooling,Heating,Lighting`

### `!ZONE HOUR RESULT:`

Enabled by `-z 1 -r 1`.

- `N * 8760` rows
- format: `SpaceIndex,Cooling,Heating,Lighting`

`SpaceIndex` is zero-based and matches the row order in the input `.i` file.

## Output Example

```text
!TOTAL:
!Cooling,Heating,Lighting
12.45,8.77,4.31
;
!SPACE RESULT:
!Cooling,Heating,Lighting
13.02,7.91,4.00
11.61,9.85,4.77
;
!MONTH RESULT:
!Cooling,Heating,Lighting
0.00,1.25,0.36
0.00,0.91,0.33
...
```

## Notes on Residential vs Public Modes

- `-t 0` uses the residential path.
- `-t 1` to `-t 6` all use the public-building path in the current Go implementation.
- Residential mode reads dry-bulb and ground temperature from the weather file.
- Public mode additionally reads dew-point temperature.
- Residential mode uses built-in residential lighting and equipment schedules, but schedule-driven input values can still override the intensity fields.

## Practical Advice for Direct Callers

- Pass latitude in radians, not degrees.
- Keep the `.i` field order exactly as documented above.
- If you use schedule names in any schedulable field, always provide `-sch`.
- Treat output values as `kWh/m2`, not absolute building energy.
- Keep the input file row order stable if you need to map `SpaceIndex` back to your own zone identifiers.
