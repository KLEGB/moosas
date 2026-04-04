# MoosasEnergyReadMe_English.md

MoosasEnergy is a lightweight tool for calculating annual hourly cooling/heating load and energy consumption of buildings. This version merges the calculation engines for **residential buildings** and **public buildings** into a unified executable program, and supports the advanced Schedule system, multi-granularity result output (monthly, daily, hourly), as well as zone-based result export.

---

## 1. Command Line Parameter Description

The program is configured via command line parameters, and all parameters have both short and full forms.

|Parameter|Full Name|Default Value|Description|
|---|---|---|---|
|`-h`|`-help`|None|Print help information and exit|
|`-w`|`-weather`|`....\db\weather\545110.csv`|Weather file path (DeST CSV format)|
|`-t`|`-type`|`0`|Building type: `0`=Residential, `1`=Office, `2`=Hotel, `3`=School, `4`=Commercial, `5`=Theater, `6`=Hospital|
|`-l`|`-lat`|`0.0`|Site latitude (in radians)|
|`-a`|`-alt`|`0.0`|Site altitude (in meters)|
|`-s`|`-shape`|`0.78`|Building shape factor (exterior surface area / volume)|
|`-o`|`-output`|`MoosasEnergy.o`|Output file path|
|`-d`|`-daily`|`0`|Whether to output daily results: `1`=Output, `0`=Do not output|
|`-r`|`-hourly`|`0`|Whether to output hourly results: `1`=Output, `0`=Do not output|
|`-z`|`-zone`|`0`|Whether to output results by zone: `1`=Output, `0`=Do not output|
|`-sch`|`-schedule`|None|Schedule file path (CSV format). If not specified, the schedule function cannot be used|
|(None)|(None)|Required|**Input file path** (must be the last parameter of the command line)|
|**Example Command**:||||
```bash

./MoosasEnergy -w 545110.csv -t 1 -d 1 -r 1 -z 1 -sch office_schedule.csv -o result.o Energy.i
```

---

## 2. Input File Format (`.i` File)

The input file contains the geometric, thermal, and operational parameters of each functional space in the building. The file is comma-separated (CSV format), with each line representing a zone. Lines starting with `!` are comment lines and will be ignored by the parser.
Each line must contain at least 27 fields (index 0~26).

### 2.1 Field Definition List

|Index|Field Name|Type|Description|
|---|---|---|---|
|0|`StoryHeight`|Numeric|Floor height (m)|
|1|`FloorArea`|Numeric|Floor area (m²)|
|2|`PerimeterZoneArea`|Numeric|Perimeter zone area (m²)|
|3|`ExteriorWallArea`|Numeric|Exterior wall area (m²)|
|4|`ExteriorWindowArea`|Numeric|Exterior window area (m²)|
|5|`RoofArea`|Numeric|Roof area (m²)|
|6|`SkylightArea`|Numeric|Skylight area (m²)|
|7|`GroundFloorArea`|Numeric|Ground floor area (m²)|
|8|`SummerSolarGain`|Numeric|Total summer solar heat gain (Wh)|
|9|`WinterSolarGain`|Numeric|Total winter solar heat gain (Wh)|
|10|`WallUValue`|Numeric|Exterior wall heat transfer coefficient (W/(m²·K))|
|11|`WindowUValue`|Numeric|Exterior window heat transfer coefficient (W/(m²·K))|
|12|`WindowSHGC`|Numeric|Exterior window Solar Heat Gain Coefficient|
|13|`CoolingSetpointTemp`|**Numeric/Schedule**|Cooling setpoint temperature (°C)|
|14|`CoolingSetpointHumidity`|**Numeric/Schedule**|Cooling setpoint relative humidity (0~1)|
|15|`HeatingSetpointTemp`|**Numeric/Schedule**|Heating setpoint temperature (°C)|
|16|`CoolingEER`|Numeric|Cooling Energy Efficiency Ratio|
|17|`HeatingEER`|Numeric|Heating Energy Efficiency Ratio|
|18|`OccupancyStartHour`|Integer|Occupancy start hour (0~24)|
|19|`OccupancyEndHour`|Integer|Occupancy end hour (0~24)|
|20|`OccupantDensity`|**Numeric/Schedule**|Occupant density (person/m²)|
|21|`FreshAirPerPerson`|**Numeric/Schedule**|Fresh air per person (m³/(h·person))|
|22|`OccupantHeatGain`|**Numeric/Schedule**|Occupant heat gain intensity (W/person)|
|23|`EquipmentHeatGain`|**Numeric/Schedule**|Equipment heat gain intensity (W/m²)|
|24|`LightingHeatGain`|**Numeric/Schedule**|Lighting heat gain intensity (W/m²)|
|25|`InfiltrationACH`|Numeric|Air change rate during working hours (times/h)|
|26|`NightVentilationACH`|Numeric|Night ventilation air change rate (times/h)|
> **Note**: Fields 13\15 and 20\24 support **schedule reference**. If you fill in a number, this fixed value will be used for all 8760 hours of the year; if you fill in a string, the program will treat it as a schedule name, and look up the corresponding hourly varying value in the schedule file specified by `-sch`.
> 
> 

---

## 3. Schedule System (`-sch` File)

The schedule file is used to define time-varying parameters. The file is in CSV format, with each line defining a schedule record.

### 3.1 Schedule Types

The system supports three types of schedules, specified by the second column:

1. **Hourly Schedule**

    - Format: `[Schedule Name], Hourly, [Value1], [Value2], ..., [Value8760]`

    - Description: Directly provide values for all 8760 hours of the year.

2. **Daily Schedule**

    - Format: `[Schedule Name], Daily, [Value1], [Value2], ..., [Value24]`

    - Description: Provide values for 24 hours of one day. The program will automatically repeat it 365 times to expand into 8760 values.

3. **Weekly Schedule**

    - Format: `[Schedule Name], Weekly, [Monday Daily Name], [Tuesday Daily Name], ..., [Sunday Daily Name]`

    - Description: Provide the names of 7 Daily schedules. The program will automatically splice the corresponding Daily schedules according to the dates of the year (assuming the first day is Monday), and expand into 8760 values.

### 3.2 Value Rules and Error Handling

- Values in the schedule **are no longer limited to 0.0~1.0**, they can be any floating point number (for example, directly specify temperature `25.5` or heat gain `20.0`).

- If a schedule name is used in the `.i` file, but the schedule file is not provided via `-sch`, or the name cannot be found in the file, the program will **directly report an error and terminate the operation**, and will not use default values for fault tolerance.

---

## 4. Output File Format (`.o` File)

The output file contains multiple data segments, each segment is separated by `;`, and starts with `!Section Name`. The unit of all energy consumption values is **kWh/m²**.

### 4.1 Basic Output Sections (Always Output)

1. **`!TOTAL:`**

    - Contains 1 line of data, representing the total annual energy consumption of the entire building.

    - Format: `Cooling,Heating,Lighting`

2. **`!SPACE RESULT:`**

    - Contains N lines of data (N is the number of zones), representing the total annual energy consumption of each zone.

    - Format: `Cooling,Heating,Lighting`

3. **`!MONTH RESULT:`**

    - Contains 12 lines of data, representing the monthly total energy consumption of the entire building.

    - Format: `Cooling,Heating,Lighting`

### 4.2 Extended Output Sections (Output on Demand)

According to the combination of command line parameters, the program will append the following output sections:

|Enable Parameter|Appended Section|Number of Lines|Format|
|---|---|---|---|
|`-d 1`|`!DAY RESULT:`|365|`Cooling,Heating,Lighting`|
|`-r 1`|`!HOUR RESULT:`|8760|`Cooling,Heating,Lighting`|
|`-z 1`|`!ZONE MONTH RESULT:`|N × 12|`SpaceIndex,Cooling,Heating,Lighting`|
|`-z 1 -d 1`|`!ZONE DAY RESULT:`|N × 365|`SpaceIndex,Cooling,Heating,Lighting`|
|`-z 1 -r 1`|`!ZONE HOUR RESULT:`|N × 8760|`SpaceIndex,Cooling,Heating,Lighting`|
> **Note**: `SpaceIndex` is the zone index, starting from `0`, corresponding to the order in which the zones appear in the `.i` file.
> 
> 

---

## 5. Calculation Differences Between Residential and Public Buildings

After being routed by the `-t` parameter, the two building types have the following core differences in the physical model:

|Calculation Module|Residential Building (`-t 0`)|Public Building (`-t 1~6`)|
|---|---|---|
|**Weather Data**|Only uses dry-bulb temperature and ground temperature|Uses dry-bulb temperature, dew point temperature and ground temperature|
|**Envelope Load**|No weekend correction factor|Includes weekend correction factor (based on shape factor and heat transfer coefficient)|
|**Thermal Storage Correction**|Fixed temperature offset (±3.0°C)|Dynamic calculation (based on night average temperature and air change rate)|
|**Fresh Air and Enthalpy Difference**|Does not calculate fresh air load and enthalpy difference|Includes complete fresh air load and enthalpy difference calculation|
|**Lighting Energy Consumption**|Uses hard-coded residential lighting schedule|Dynamically calculated using solar radiation daylighting model|
|**Equipment Energy Consumption**|Uses hard-coded residential equipment schedule|Uniform heat generation throughout the period (unless overridden by a schedule)|
|**Air Specific Heat Capacity**|`0.717` kJ/(kg·K)|`1.40` kJ/(kg·K)|
> **Tip**: Although residential buildings have built-in hard-coded lighting and equipment schedules, if you specify a custom schedule name for `LightingHeatGain` or `EquipmentHeatGain` in the `.i` file, the custom schedule will **override** the built-in schedule.
> 
> 
> （注：文档部分内容可能由 AI 生成）