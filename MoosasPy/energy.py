"""
quick energy analysis module.
this energy analysis based on simplified physical model,
which only takes 0.01s for a space and gets acceptable accuracy.
the analysis result has been validated by ASHRAE 140.
more information can be found in this article:
https://doi.org/10.1016/j.buildenv.2021.107929.
"""
from .utils.support import os
from datetime import datetime
from .utils import path, callCmd, parseFile,FileError
from .utils.constant import buildingType, dateSetting
from .rad import modelRadiation

from .thermal.settings import ThermalSettings

from .models import *

# a quick radiation estimation based on measured data
SUMMER_RADIATION = [280100, 175200, 213200, 116300, 280100]
WINTER_RADIATION = [150800, 355200, 123600, 51500, 150800]
energyScriptDir = os.path.join(path.libDir, "energy")
energyDataDir = os.path.join(path.dataDir, "energy")


def energyAnalysis(model: MoosasModel, core=buildingType.RESIDENTIAL,
                   requireRadiation=False,
                   inputPath=os.path.join(energyDataDir, "Energy.i"),
                   resultPath=os.path.join(energyDataDir, "Energy.o")) -> dict:
    """Quick energy analysis function.

    It takes two different cores for residential buildings and others.
    if you don't require a radiation calculation,
    you must change the SUMMER_RADIATION and WINTER_RADIATION before you use this function.
    Otherwise, the solar heat will be estimated based on Beijing's cumSky.

    Args:
        model(MoosasModel): the model you want to analysis
        core: which core you want to use, please take buildingType.RESIDENTIAL or others (default: buildingType.RESIDENTIAL)
        requireRadiation(bool): True if you want to take an accurate radiation calculation by MoosasRad. (default: False)
        inputPath(str): save the input file to this path. (default: data\energy\Energy.i)
        inputPath(str): save the output file to this path. (default: data\energy\Energy.o)

    Returns:
        e_data(dict):
        a dictionary to show the result in:
        total:{ cooling: total cooling energy demand,
                heating: total heating energy demand,
                lighting: total lighting energy demand,
                total: total energy demand }
        spaces: list[ThermalSettings] (the result are recorded in ThermalSettings.load)
        months: {Jan : {cooling: total cooling energy demand,
                        heating: total heating energy demand,
                        lighting: total lighting energy demand,
                        total: total energy demand }
                Feb : {...}
                ...}

    Raises:
        ShellError: error occured in MoosasResidential.exe or MoosasPublic.exe

    Examples:
        >>> e_data = energyAnalysis(model,requireRadiation=True)
        >>> print(e_data['total'])

    References:
        https://doi.org/10.1016/j.buildenv.2021.107929.

    """
    energyInput = getEnergyInput(model, requireRadiation)

    inputPath = os.path.abspath(inputPath)
    resultPath = os.path.abspath(resultPath)
    with open(inputPath, "w") as file:
        lines = [zone.paramToString() for zone in energyInput['zones']]
        file.write('!' + energyInput['zones'][0].paramTags() + '\n')
        file.write('\n'.join(lines))

    energyInput['args'] += ['-o', f"\"{resultPath}\""] + [f"\"{inputPath}\""]
    exe_command = os.path.abspath(os.path.join(energyScriptDir,
                                               "MoosasEnergyResidential.exe")) if core == buildingType.RESIDENTIAL else os.path.join(
        energyScriptDir, "MoosasEnergyPublic.exe")
    exe_command=f"\"{exe_command}\""
    exe_command = [exe_command] + energyInput['args']
    callCmd(exe_command, cwd=os.path.abspath(energyScriptDir))

    return parseEnergyOutput(resultPath, energyInput['zones'])


def parseEnergyOutput(resultPath, zoneList: list[ThermalSettings] = None):
    """Parse the output file from MoosasResidential.exe or MoosasPublic.exe

    Args:
        resultPath(str): the result file to parse.
        zoneList(list[ThermalSettings]) ThermalSettings list to record the result.
        if None, the result will be given directly. (default: None)

    Returns:
        e_data(dict):
        a dictionary to show the result in:
        total:{ cooling: total cooling energy demand,
                heating: total heating energy demand,
                lighting: total lighting energy demand,
                total: total energy demand }
        spaces: list[ThermalSettings] (the result are recorded in ThermalSettings.load)
        or spaces: [{   cooling: total cooling energy demand,
                        heating: total heating energy demand,
                        lighting: total lighting energy demand,
                        total: total energy demand }...]
        months: {Jan : {cooling: total cooling energy demand,
                        heating: total heating energy demand,
                        lighting: total lighting energy demand,
                        total: total energy demand }
                Feb : {...}
                ...}

    Raises:
        FileError: get an invalid file which cannot be parsed.

    Examples:
        >>> e_data = parseEnergyOutput(r'data\energy\Energy.o')
    """

    try:
        output = parseFile(resultPath)
        total = output[0][0]
        total = {"cooling": total[0], "heating": total[1], "lighting": total[2],
                 "total": np.array(total).astype(float).sum()}
        monthsResult = {}
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

        for mon, result in zip(dateSetting.MONTH_NAME, output[2]):
            monthsResult[mon] = {"cooling": result[0], "heating": result[1], "lighting": result[2],
                                 "total": np.array(result).astype(float).sum()}

        e_data = {"total": total, "spaces": zoneList, "months": monthsResult}
        return e_data

    except:
        raise FileError(resultPath)


def getEnergyInput(model: MoosasModel, require_radiation=False):
    """Parse the output file from MoosasResidential.exe or MoosasPublic.exe

        Args:
            model(MoosasModel): the model to get the energy input file
            requireRadiation(bool): True if you want to take an accurate radiation calculation by MoosasRad. (default: False)

        Returns:
            energyInput(dict):
            a dictionary to show the energy input:
            zones: list[ThermalSettings]
            args: list[ '-w', weatherFile,
                        '-l', lantitute,
                        '-a', altitude,
                        '-s', shapeFactor ]

        Examples:
            >>> energyInput = getEnergyInput(model, True)
            >>> for z in energyInput['zones']:
            >>>     print(z)
    """
    def calculate_orientation(n):
        o = int((np.arccos((-1) * n[0] / np.sqrt(n[0] ** 2 + n[1] ** 2)) * 180 / np.pi).round())
        if n[1] > 0:
            o = 360 - o
        if o == 360:
            o = 0
        return o

    def non(x):
        return x if x > 0 else 0

    if require_radiation:
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
                outside_area += non(pygeos.length(b.force_2d()) - 5.0) * 5.0
                facade_area += b.area * (1 - b.wwr)
                window_area += b.area * b.wwr
                o = calculate_orientation(b.normal)  # W:0 S:90 E:180 N:270
                summer_solar += (SUMMER_RADIATION[o // 90] + ((o % 90) / 90.0) * (
                        SUMMER_RADIATION[o // 90 + 1] - SUMMER_RADIATION[o // 90])) * b.area * b.wwr
                winter_solar += (WINTER_RADIATION[o // 90] + ((o % 90) / 90.0) * (
                        WINTER_RADIATION[o // 90 + 1] - WINTER_RADIATION[o // 90])) * b.area * b.wwr

        if require_radiation:
            summer_solar, winter_solar = s.settings['zone_summerrad'] * 60, s.settings['zone_winterrad'] * 60

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
            'outside_area': round(s.area, 2),
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

    if model.weather is None:
        model.loadWeatherData()
    weather = model.weather
    args = [
        '-w', f"\"{weather.weatherFile}\"",
        '-l', str(round(float(weather.location.latitude), 2)),
        '-a', str(round(float(weather.location.altitude), 2)),
        '-s', str(round(total_outside_area / total_volume, 2))
    ]

    return {'zones': zones, 'args': args}
