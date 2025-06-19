"""
    Corresponding with MoosasAFN.exe
    More information can be found by sending MoosasAFN.exe -h in command line
"""
from __future__ import annotations

from ..geometry.element import *
from ..geometry.geos import Vector
from ..utils.constant import geom
from ..utils.tools import path, generate_code, callCmd, parseFile
from ..rad import modelRadiation
from ..weather.cumsky import MoosasCumSky
import numpy as np
import os


class AfnZone(MoosasSpace):
    """
        input for networkFile(zones):
        zoneName: user define zoneName
        heatLoad: total heat load in Watt (W)
        temperature: zone initial temperature (C)
        volume: zone volume (m3)
        positionX,positionY,positionZ: a position to match the zone in meter (m)
        boundaryPolygon: define the zone boundary in meter (m) with ' ' as sep
    """
    __slots__ = ['username', 'temperature', 'prjIndex', 'heatLoad']

    def __init__(self, space: MoosasSpace, name=None, temperature=27):
        spaceId = space.parent.spaceList.index(space)
        if space.settings['zone_summerrad'] is None:
            modelRadiation(space.parent, reflection=0)
            space = space.parent.spaceList[spaceId]
        super(AfnZone, self).__init__(space.floor, space.edge, space.ceiling)

        if name is not None:
            self.username = name
        else:
            self.username = space.id
        self.temperature = temperature
        self.prjIndex = 0
        self.settings = space.settings
        self.heatLoad = self.calculateHeatLoad()

    @property
    def volume(self):
        return self.area * self.height

    @property
    def position(self) -> Vector:
        return Vector(self.floor.getWeightCenter())

    def calculateHeatLoad(self):
        heat = 0
        heat += self.settings['zone_summerrad'] / (MoosasCumSky.SUMMER_END_HOY - MoosasCumSky.SUMMER_START_HOY) * 1000
        heat += float(self.settings['zone_ppsm']) * float(self.settings['zone_popheat']) * self.area
        heat += float(self.settings['zone_equipment']) * self.area
        heat += float(self.settings['zone_lighting']) * self.area
        return heat

    def printHeatLoad(self):
        print('\nzone total', self.calculateHeatLoad())
        print('solar heat',
              self.settings['zone_summerrad'] / (MoosasCumSky.SUMMER_END_HOY - MoosasCumSky.SUMMER_START_HOY) * 1000)
        print('people', float(self.settings['zone_ppsm']) * float(self.settings['zone_popheat']) * self.area)
        print('equipment', float(self.settings['zone_equipment']) * self.area)
        print('lighting', float(self.settings['zone_lighting']) * self.area)
        print('area', self.area)

    def dump(self):
        """
            input for networkFile(zones):
            zoneName: user define zoneName
            heatLoad: total heat load in Watt (W)
            temperature: zone initial temperature (C)
            volume: zone volume (m3)
            positionX,positionY,positionZ: a position to match the zone in meter (m)
            boundaryPolygon: define the zone boundary in meter (m) with ' ' as sep
        """
        zoneStr = [self.username]
        zoneStr += ['z' + '%03d' % self.prjIndex]
        zoneStr += ['%.2f' % self.heatLoad]
        zoneStr += ['%.2f' % self.temperature]
        zoneStr += ['%.2f' % self.volume]
        zoneStr += ['%.2f' % self.position.x]
        zoneStr += ['%.2f' % self.position.y]
        zoneStr += ['%.2f' % self.position.z]
        zoneStr += [' '.join([' '.join(coor) for coor in pygeos.get_coordinates(self.edge.force_2d()).astype(str)])]
        return ','.join(zoneStr)


class AfnPath(MoosasGlazing):
    """
        input for networkFile(paths):
        pathName: user define pathName
        height: height of the aperture in meter (m)
        width: width of the aperture in meter (m)
        positionX,positionY,positionZ: a position to match the path in meter (m)
        fromZone: the zone index that the path from
        toZone: the zone index that the path to
        pressure: wind pressure of the path if it is connected to outdoor
    """
    __slots__ = ['pathName', 'fromZone', 'toZone', 'pressure', 'prjIndex']

    def __init__(self, moGeometry: MoosasGlazing | MoosasSkylight, model, pathName=None, fromZone=None, toZone=None,
                 pressure=0.0):
        super(AfnPath, self).__init__(model, moGeometry.faceId)
        self.Uid = moGeometry.Uid
        if pathName is None:
            pathName = moGeometry.Uid
        self.pathName = pathName
        self.prjIndex = 0
        self.fromZone = fromZone
        self.toZone = toZone
        self.pressure = pressure
        self.space = moGeometry.space
        self.parentFace = moGeometry.parentFace
        self.shading = moGeometry.shading
        self.orientation = moGeometry.orientation if not Vector.parallel(moGeometry.orientation, [0, 0, 1]) else Vector(
            [0, 0,
             1])

    @property
    def width(self):
        coordinates = pygeos.get_coordinates(self.face, include_z=True)
        minZ = np.min(coordinates[:, 2])
        sortlist = [[coor[0], coor[1]] for coor in coordinates if
                    minZ - geom.POINT_PRECISION < coor[2] < minZ + geom.POINT_PRECISION]
        sortlist.sort(key=lambda x: (x[0], x[1]))
        return Vector(np.array(sortlist[-1]) - np.array(sortlist[0])).length()

    @property
    def pathHeight(self):
        return self.area3d() / self.width

    @property
    def position(self) -> Vector:
        return Vector(self.getWeightCenter())

    def dump(self):
        """
            input for networkFile(paths):
            pathName: user define pathName
            height: height of the aperture in meter (m)
            width: width of the aperture in meter (m)
            positionX,positionY,positionZ: a position to match the path in meter (m)
            fromZone: the zone index that the path from
            toZone: the zone index that the path to
            pressure: wind pressure of the path if it is connected to outdoor
        """
        if self.fromZone is None or self.toZone is None:
            raise Exception('path topology have not been calculated')
        pathStr = [self.pathName]
        pathStr += ['p' + '%03d' % self.prjIndex]
        pathStr += [str(self.pathHeight)]
        pathStr += [str(self.width)]
        pathStr += [str(self.position.x)]
        pathStr += [str(self.position.y)]
        pathStr += [str(self.position.z)]
        pathStr += [str(self.fromZone)]
        pathStr += [str(self.toZone)]
        pathStr += [str(self.pressure)]
        return ','.join(pathStr)


class AfnNetwork:
    __slots__ = ('zones', 'paths', 'model')

    def __init__(self, model):
        self.model = model
        self.paths: list[AfnPath] = []
        self.zones: list[AfnZone] = []
        for s in model.spaceList:
            self.zones.append(AfnZone(s, s.id))
            self.zones[-1].prjIndex = len(self.zones)
            for gls in s.getAllFaces(to_dict=False):
                if isinstance(gls, MoosasGlazing) or isinstance(gls, MoosasSkylight):
                    self.paths.append(AfnPath(gls, model))
                    self.paths[-1].prjIndex = len(self.paths)
        self.paths = pathTopology(self.paths, self.zones)
        self.paths, self.zones = cleanseNetwork(self.paths, self.zones)

    def applyWindPressure(self, windVector: Vector, speed=None, airDensity=1.205, alpha=0.22):
        """connect to applyWindPressure()"""
        self.paths = applyWindPressure(self.paths, windVector=windVector, speed=speed, airDensity=airDensity,
                                       alpha=alpha)

    def toFile(self, networkFilePath=None):
        """connect to buildNetworkFile()"""
        return buildNetworkFile(pathList=self.paths, zoneList=self.zones, networkFilePath=networkFilePath)

    def toPrj(self, prjFilePath=None, networkFilePath=None, split=False,
              t0=25, simulate=False, resultFile=None):
        """connect to buildPrj()"""
        return buildPrj(pathList=self.paths, zoneList=self.zones, prjFilePath=prjFilePath,
                        networkFilePath=networkFilePath, split=split,
                        t0=t0, simulate=simulate, resultFile=resultFile)

    def toZoneFile(self, zoneInfoFilePath=None):
        """connect to buildZoneInfoFile()"""
        return buildZoneInfoFile(zoneList=self.zones, pathList=self.paths, zoneInfoFilePath=zoneInfoFilePath)


def applyWindPressure(pathList: list[AfnPath], windVector: Vector, speed: float = None,
                      airDensity=1.205, alpha=0.22) -> list[AfnPath]:
    """apply wind pressure to paths.

    -------------------------------------------
    pathList: list of AfnPath which need to apply wind pressure
    windVector: a Vector represents the wind direction and speed.
    speed: wind speed unit in m/s, if none, the length of vector will be the wind speed
    airDensity: default is 1.205 kg/m3
    alpha: default 0.22

    -------------------------------------------
    xgboost is large, therefore we import it only if users want a pressure input.
    The output value from call Xgb is the Wind Pressure Coefficient (Wp):

        P = Wp * airDensity * velocity^2 * ((altitude/10)^(alpha * 2)) / 2
        alpha = 0.22
        airDensity = 1.205
    """
    from .ventXgb import pressureInput, callXgb
    if speed is not None:
        windVector *= speed
    xgbInput = [pressureInput(windVector, path) for path in pathList]
    Wp = callXgb(xgbInput)

    pressure = Wp * airDensity * windVector.length(power=True) * np.power(([p.elevation for p in pathList]),
                                                                          (alpha * 2)) / 2
    for _path, _pressure in zip(pathList, pressure):
        _path.pressure = _pressure

    return pathList


def getZoneAndPath(model):
    pathList: list[AfnPath] = []
    zoneList: list[AfnZone] = []
    for s in model.spaceList:
        zoneList.append(AfnZone(s))
        zoneList[-1].prjIndex = len(zoneList)
        for gls in s.getAllFaces(to_dict=False):
            if isinstance(gls, MoosasGlazing) or isinstance(gls, MoosasSkylight):
                pathList.append(AfnPath(gls, model))
                pathList[-1].prjIndex = len(pathList)
    pathList = pathTopology(pathList, zoneList)
    return zoneList, pathList


def pathTopology(pathList: list[AfnPath], zoneList: list[AfnZone]) -> list[AfnPath]:
    zoneUid = [zone.id for zone in zoneList]
    invalidPath = []

    for i, p in enumerate(pathList):
        if len(p.space) == 0:
            invalidPath.append(i)
        elif len(p.space) == 1:
            p.fromZone = -1
            p.toZone = zoneUid.index(p.space[0])

        elif len(p.space) == 2:
            p.fromZone = zoneUid.index(p.space[0])
            p.toZone = zoneUid.index(p.space[1])

    return list(np.delete(pathList, invalidPath))


def buildNetworkFile(model=None, pathList: list[AfnPath] = None, zoneList: list[AfnZone] = None,
                     networkFilePath=None) -> str:
    """
        Build *.net file from model or pathList/zoneList.
        It is the input for MoosasAFN.exe and record zone and path data.
        model and pathList/zoneList cannot be all None.
        ------------------------------------------------------

        model : MoosasModel by transforming.transform()
        pathList : you can construct AfnPath by getZoneAndPath() method and edit somthing.
        zoneList : you can construct AfnZone by getZoneAndPath() method and edit somthing.
        file_path : If None, the file string will be returned directly.
        ------------------------------------------------------

        The network file can be decoded like this:
        ! All line with the prefix "!" are annotations and will be ignored.
        ! Zone Data or Path Data are identified be the length of the line, so dont worry about that.
        ! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon
        Bedroom0, z01, 1760, 27, 180, 16.2, 18.5, 3.0, 16.2 18.5 20.2 18.5 20.2 23.5 16.2 23.5 (len==9)
        ....
        ! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure (len==10)
        BedroomWin0, p01, 1.8, 1.2, 17.4, 19.1, 3.6, -1, 2, 12.5
        ....
        ------------------------------------------------------

    """
    if pathList is None or zoneList is None:
        if model is None:
            raise Exception("model, pathList and zoneList cannot be all None")
        zoneList, pathList = getZoneAndPath(model)

    pathList, zoneList = cleanseNetwork(pathList, zoneList)
    networkStr = "! All annotations has prefix as !\n"
    networkStr += "! ZONE DATA\n"
    networkStr += "! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon\n"
    for z in zoneList:
        networkStr += z.dump() + "\n"
    networkStr += ";\n! PATH DATA\n"
    networkStr += "! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure\n"
    for p in pathList:
        networkStr += p.dump() + "\n"
    if networkFilePath is None:
        networkFilePath = os.path.join(path.tempDir, generate_code(4) + '.net')

    with open(networkFilePath, 'w+') as f:
        f.write(networkStr)
    return networkFilePath


def cleanseNetwork(pathList: list[AfnPath], zoneList: list[AfnZone]) -> (list[AfnPath], list[AfnZone]):
    """clean the zones that are not linked to the ambient.
    those zones will cause error in ContamX and their air change is 0.
    """
    invalidZone = np.arange(len(zoneList))
    topology = {i: set() for i in invalidZone}
    topology[-1] = set()
    validZone = {-1}
    invalidZone = set(invalidZone)

    for p in pathList:
        topology[p.fromZone].add(p.toZone)
        topology[p.toZone].add(p.fromZone)

    invalid = 0
    while invalid != len(invalidZone):
        invalid = len(invalidZone)
        _oriValid = list(validZone)
        for zIdx in _oriValid:
            validZone = validZone | topology[zIdx]
        invalidZone = invalidZone.difference(validZone)

    if len(invalidZone) > 0:
        print(f'******Warning: some zones do not linked to ambient.')
        invalidPath = [i for i, p in enumerate(pathList) if p.fromZone in invalidZone or p.toZone in invalidZone]
        print(f'******Warning: those zone will be removed:{list(invalidZone)}')
        print(f'******Warning: those path will be removed:{list(invalidPath)}')
        ZoneIdOri = [z.id for z in zoneList]
        for p in pathList:
            p.fromZone = ZoneIdOri[p.fromZone] if p.fromZone >= 0 else -1
            p.toZone = ZoneIdOri[p.toZone] if p.toZone >= 0 else -1

        zoneList = np.delete(zoneList, list(invalidZone))
        pathList = np.delete(pathList, list(invalidPath))
        ZoneIdOri = [z.id for z in zoneList]
        for i, p in enumerate(pathList):
            p.fromZone = ZoneIdOri.index(p.fromZone) if p.fromZone != -1 else -1
            p.toZone = ZoneIdOri.index(p.toZone) if p.toZone != -1 else -1

    return pathList, zoneList


def buildPrj(model=None, pathList: list[AfnPath] = None, zoneList: list[AfnZone] = None,
             prjFilePath=None, networkFilePath=None, split=False,
             t0=25, simulate=False, resultFile=None) -> list[str]:
    """
        Build *.prj file(s) from model or pathList/zoneList.
        networkFile,model and pathList/zoneList cannot be all None.
        ------------------------------------------------------

        model : MoosasModel by transforming.transform()
        pathList : you can construct AfnPath by getZoneAndPath() method and edit somthing.
        zoneList : you can construct AfnZone by getZoneAndPath() method and edit somthing.
        prjFilePath : file path to export *.prj file. The directory of this file will be used to export other things.
            If None the file will be exported to data\vent
        networkFilePath : export the MoosasAFN.exe input file here. If None the file will be exported to __temp__
        split : If True, the network will be automatically split into several isolate parts and files.
        t0 : outdoor temperature.
        simulate : If True, contamX will be called and result will be exported to *.prj directory.
        resultFile : you cen redirect the result file to other place.
        ------------------------------------------------------

        Moosas ContamX Builder and reader.
        Command line should be: MoosasAFN.exe [-h,-p...] inputNetworkFile.net
        Optional command:
        -h / -help : reprint the help information
        -p / -project : base name of the prj file  (default: network)
        -d / -directory : directory where the project file and result to put  (default: execution directory)
        -o / -output : result output file path (default: execution directory\airVel.o)
        -r / -run : 1 if run contamX for all built *.prj files and gather the results (default: 0)
        -s / -split : 1 if split the input network into several networks (default: 1)
        -t / -t0 : OutdoorTemperature (default: 25)
    """
    prjTempName = 'afn_' + generate_code(4)
    if networkFilePath is None:
        networkFilePath = os.path.join(path.tempDir, prjTempName + '.net')
        if pathList is None or zoneList is None:
            if model is None:
                raise Exception("model, pathList and zoneList cannot be all None")
            zoneList, pathList = getZoneAndPath(model)
        networkFilePath = buildNetworkFile(pathList=pathList, zoneList=zoneList, networkFilePath=networkFilePath)

    if prjFilePath is None:
        prjName = prjTempName
        prjDirectory = path.tempDir
        prjFilePath = os.path.join(prjDirectory, prjName + '.prj')
    else:
        prjName = os.path.basename(prjFilePath)[:-4]
        prjDirectory = os.path.dirname(prjFilePath)

    command = [path.libDir + r'\vent\MoosasAFN.exe']
    command += ['-p', prjName]
    command += ['-d', prjDirectory]
    command += ['-t', str(t0)]
    if resultFile is not None:
        command += ['-o', resultFile]
    if simulate:
        command += ['-r', "1"]
    if not split:
        command += ['-s', "0"]
    command += [networkFilePath]

    callCmd(command)

    return prjFilePath


def buildZoneInfoFile(model=None, zoneList: list[AfnZone] = None, networkFilePath=None, pathList: list[AfnPath] = None,
                      zoneInfoFilePath=None) -> str:
    """
        This method can build the zoneInfo file by:
        model: MoosasModel, given by transforming.transform() method
        zoneList: list[AfnZone], given by getZoneAndPath() method
        networkFile: given by buildNetworkFile() method, or construct by other script like MoosasAFN.exe
        ------------------------------------------------------

        The zoneInfo file can be decoded like this:
        [[prjroomname, roomheatload, userroomname]..[]]
        in which:
            prjroomname: the room name set in the *.prj file, must be the same in every character
            roomheatload: the gross load of the room in (W).
            userroomname: the room name define by the users, and it will occur in the result file.

        The roomInfo file can exclude the roomname and only provide roomInfo, which means that:
        the room heat file can only have 2 columns:
        [[prjroomname,roomheatload]...[]]
        in this case, the roomnome will be the same to the prjroomname

        or 2 columns:
        [[roomheatload,usersroomname]...[]]
        iin this case, the roomInfo data should be in the same sequence of zones in the project file

        or only 1 column:
        [[roomheatload]...[]]
        in this case, the roomheatload data should be in the same sequence of zones in the project file
        ------------------------------------------------------
    """

    zoneStr = []
    zoneStr += ["! All line with the prefix ! are annotations and will be ignored."]
    zoneStr += ["! zonePrjName,heatLoad,zoneName"]
    if networkFilePath is None:
        prjTempName = 'afn_' + generate_code(4)
        networkFilePath = os.path.join(path.tempDir, prjTempName + '.net')
        if zoneList is None:
            if model is None:
                raise Exception("model, pathList and zoneList cannot be all None")
            zoneList, pathList = getZoneAndPath(model)
        networkFilePath = buildNetworkFile(pathList=pathList, zoneList=zoneList, networkFilePath=networkFilePath)

    lines = parseFile(networkFilePath)[0]

    for arr in lines:
        # ! zoneName,zonePrjName, heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon (len==9)
        if len(arr) == 9:
            zoneStr += [','.join([arr[1], arr[2], arr[0]])]

    zoneStr = '\n'.join(zoneStr)
    if zoneInfoFilePath is None:
        zoneInfoFilePath = os.path.join(path.tempDir, generate_code(4) + '.info')

    path.checkBuildDir(zoneInfoFilePath)
    with open(zoneInfoFilePath, 'w+') as f:
        f.write(zoneStr)
    return zoneInfoFilePath
