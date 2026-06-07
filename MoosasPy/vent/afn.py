"""
    Corresponding with MoosasAFN.exe
    More information can be found by sending MoosasAFN.exe -h in command line
"""
from __future__ import annotations

import os

from ..geometry.element import *
from ..geometry.geos import Vector
from ..rad import modelRadiation
from ..utils.constant import geom
from ..utils.tools import path, generate_code, callCmd, parseFile
from ..weather.cumsky import MoosasCumSky


VENT_EXE_SUFFIX = ".exe" if os.name == "nt" else ""


class AfnZone(object):
    """
        input for networkFile(zones):
        zoneName: user define zoneName
        heatLoad: total heat load in Watt (W)
        temperature: zone initial temperature (C)
        volume: zone volume (m3)
        positionX,positionY,positionZ: a position to match the zone in meter (m)
        boundaryPolygon: define the zone boundary in meter (m) with ' ' as sep
    """
    __slots__ = ['userName', 'temperature', 'prjIndex', 'heatLoad', 'volume', 'position_x', 'position_y', 'position_z',
                 'boundary', 'element']

    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key in kwargs.keys():
                setattr(self, key, kwargs[key])

    @classmethod
    def fromElement(cls, space: MoosasSpace, temperature=27) -> AfnZone:
        """
        Initialize an AfnZone instance with space data and settings.
        
        Parameters
        ----------
        space : MoosasSpace
            The space object containing geometry, settings, and parent project information.
        name : str, optional
            Custom name for the zone. If not provided, defaults to the space ID.
        temperature : float or int, optional
            Operating temperature of the zone in degrees Celsius. Default is 27.
        
        Returns
        -------
        None
            This constructor does not return a value.
        """
        spaceId = space.parent.spaceList.index(space)
        if space.settings['zone_summerrad'] is None:
            try:
                modelRadiation(space.parent, reflection=0)
            except:
                space.settings['zone_summerrad'] = 0
                space.settings['zone_winterrad'] = 0
            space = space.parent.spaceList[spaceId]
        theZone = {}
        theZone["userName"] = space.id
        theZone["temperature"] = temperature
        theZone["prjIndex"] = 0
        theZone["heatLoad"] = 0
        theZone["volume"] = space.area * space.height
        pos = space.floor.getWeightCenter()
        theZone["position_x"] = pos[0]
        theZone["position_y"] = pos[1]
        theZone["position_z"] = pos[2]
        theZone["boundary"] = ' '.join(
            [' '.join(coor) for coor in shapely.get_coordinates(space.edge.force_2d()).astype(str)])
        theZone['element'] = space
        z = cls(**theZone)
        z.heatLoad = z.calculateHeatLoad()
        return z

    def calculateHeatLoad(self):
        """
        Calculate the total heat load for a thermal zone.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the settings and area attributes.
            - self.settings (dict): A dictionary containing various zone settings including:
                - 'zone_summerrad' (float): Summer radiation value for the zone.
                - 'zone_ppsm' (float): People per square meter in the zone.
                - 'zone_popheat' (float): Heat gain per person (W/person).
                - 'zone_equipment' (float): Equipment power density (W/m²).
                - 'zone_lighting' (float): Lighting power density (W/m²).
            - self.area (float): Floor area of the zone in square meters.
        
        Returns
        -------
        float
            The total heat load in watts (W), calculated as the sum of solar, occupant,
            equipment, and lighting heat gains.
        """
        def _safe_float(value, default=0.0):
            if value is None:
                return default
            if isinstance(value, str) and value.strip().lower() in ("", "none", "null", "nan"):
                return default
            try:
                return float(value)
            except Exception:
                return default

        def _resolve_setting(value, default=0.0):
            numeric = _safe_float(value, None)
            if numeric is not None:
                return numeric
            if not isinstance(value, str):
                return default
            schedule = getattr(getattr(self.element, "parent", None), "schedule", {}) or {}
            schedule_item = schedule.get(value)
            if not isinstance(schedule_item, dict):
                return default
            schedule_type = str(schedule_item.get("type", "")).strip().lower()
            if schedule_type == "daily":
                daily_values = [_safe_float(v, 0.0) for v in schedule_item.get("value", [])]
                return sum(daily_values) / len(daily_values) if daily_values else default
            if schedule_type == "weekly":
                daily_values = []
                for daily_name in schedule_item.get("value", []):
                    daily_item = schedule.get(str(daily_name))
                    if not isinstance(daily_item, dict):
                        continue
                    if str(daily_item.get("type", "")).strip().lower() != "daily":
                        continue
                    vals = [_safe_float(v, 0.0) for v in daily_item.get("value", [])]
                    if vals:
                        daily_values.append(sum(vals) / len(vals))
                return sum(daily_values) / len(daily_values) if daily_values else default
            return default

        heat = 0
        heat += _resolve_setting(self.element.settings.get('zone_summerrad')) / (
                MoosasCumSky.SUMMER_END_HOY - MoosasCumSky.SUMMER_START_HOY) * 1000 * _resolve_setting(
            self.element.settings.get('zone_win_SHGC'))
        heat += _resolve_setting(self.element.settings.get('zone_ppsm')) * _resolve_setting(
            self.element.settings.get('zone_popheat')) * self.element.area
        heat += _resolve_setting(self.element.settings.get('zone_equipment')) * self.element.area
        heat += _resolve_setting(self.element.settings.get('zone_lighting')) * self.element.area
        return heat

    def printHeatLoad(self):
        """
        Prints the breakdown of heat load components for the zone.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the method. It is expected to have
            attributes `settings`, `area`, and a method `calculateHeatLoad`. The `settings`
            dictionary should contain keys 'zone_summerrad', 'zone_ppsm', 'zone_popheat',
            'zone_equipment', and 'zone_lighting'.
        
        Returns
        -------
        None
            This function does not return any value. It prints the heat load details to stdout.
        """
        def _safe_float(value, default=0.0):
            if value is None:
                return default
            if isinstance(value, str) and value.strip().lower() in ("", "none", "null", "nan"):
                return default
            try:
                return float(value)
            except Exception:
                return default

        def _resolve_setting(value, default=0.0):
            numeric = _safe_float(value, None)
            if numeric is not None:
                return numeric
            if not isinstance(value, str):
                return default
            schedule = getattr(getattr(self.element, "parent", None), "schedule", {}) or {}
            schedule_item = schedule.get(value)
            if not isinstance(schedule_item, dict):
                return default
            schedule_type = str(schedule_item.get("type", "")).strip().lower()
            if schedule_type == "daily":
                vals = [_safe_float(v, 0.0) for v in schedule_item.get("value", [])]
                return sum(vals) / len(vals) if vals else default
            if schedule_type == "weekly":
                vals = []
                for daily_name in schedule_item.get("value", []):
                    daily_item = schedule.get(str(daily_name))
                    if not isinstance(daily_item, dict):
                        continue
                    if str(daily_item.get("type", "")).strip().lower() != "daily":
                        continue
                    daily_vals = [_safe_float(v, 0.0) for v in daily_item.get("value", [])]
                    if daily_vals:
                        vals.append(sum(daily_vals) / len(daily_vals))
                return sum(vals) / len(vals) if vals else default
            return default

        solar = _resolve_setting(self.element.settings.get('zone_summerrad')) / (
            MoosasCumSky.SUMMER_END_HOY - MoosasCumSky.SUMMER_START_HOY
        ) * 1000 * _resolve_setting(self.element.settings.get('zone_win_SHGC'))
        people = _resolve_setting(self.element.settings.get('zone_ppsm')) * _resolve_setting(
            self.element.settings.get('zone_popheat')
        ) * self.element.area
        equipment = _resolve_setting(self.element.settings.get('zone_equipment')) * self.element.area
        lighting = _resolve_setting(self.element.settings.get('zone_lighting')) * self.element.area
        print('\nzone total', solar + people + equipment + lighting)
        print('solar heat', solar)
        print('people', people)
        print('equipment', equipment)
        print('lighting', lighting)
        print('area', self.element.area)

    def dump(self):
        """
        Dump the zone data into a formatted string for network file input.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the zone data. Expected attributes include:
            - userName (str): User-defined zone name.
            - prjIndex (int): Project index used to generate zone ID.
            - heatLoad (float): Total heat load in Watts (W).
            - temperature (float): Initial zone temperature in Celsius (C).
            - volume (float): Zone volume in cubic meters (m³).
            - position (object): Object with x, y, z attributes representing position in meters (m).
            - edge (shapely geometry): Geometry representing the zone boundary; must have `force_2d()` method and coordinates accessible via `shapely.get_coordinates()`.
        
        Returns
        -------
        str
            A comma-separated string containing the zone name, index, heat load, temperature,
            volume, position coordinates (x, y, z), and flattened boundary polygon coordinates in meters (m),
            with space-separated coordinate pairs.
        """

        zoneStr = [self.userName]
        zoneStr += ['z' + '%03d' % int(self.prjIndex)]
        zoneStr += [str(self.heatLoad)]
        zoneStr += [str(self.temperature)]
        zoneStr += [str(self.volume)]
        zoneStr += [str(self.position_x)]
        zoneStr += [str(self.position_y)]
        zoneStr += [str(self.position_z)]
        zoneStr += [self.boundary]
        return ','.join(zoneStr)

    def toDict(self) -> dict:
        pathDict = {}
        for key in self.__slots__:
            pathDict[key] = str(getattr(self, key))
        return pathDict


class AfnPath(object):
    """
        input for networkFile(paths):
        pathName: user define pathName
        height: height of the aperture in meter (m)
        width: width of the aperture in meter (m)
        positionX,positionY,positionZ: a position to match the path in meter (m)
        fromZone: the zone index that the path from
        toZone: the zone index that the path to
        pressure: wind pressure of the path if it is connected to outdoor
        orientation: orientation of the aperture if it is connected to outdoor
        element: reference MoosasElement (optional)
    """
    __slots__ = ['userName', 'prjIndex', 'pathHeight', 'pathWidth', 'position_x', 'position_y', 'position_z',
                 'fromZone', 'toZone', 'pressure',
                 'winType', 'orientation', 'operable','element']

    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key in kwargs.keys():
                setattr(self, key, kwargs[key])

    @classmethod
    def fromElement(cls, moGeometry: MoosasGlazing | MoosasSkylight, pathName=None, fromZone=None, toZone=None,
                    pressure=0.0) -> AfnPath:
        """
        Initialize an AfnPath object for airflow network modeling.
        
        Parameters
        ----------
        moGeometry : MoosasGlazing or MoosasSkylight
            The geometry object representing a glazing or skylight, providing face ID, Uid, space, parent face, shading, and orientation.
        model : object
            The model instance to which this path belongs; passed to the parent class constructor.
        pathName : str, optional
            Name identifier for the path. If None, defaults to the Uid of moGeometry.
        fromZone : object, optional
            The zone from which air flows. Default is None.
        toZone : object, optional
            The zone to which air flows. Default is None.
        pressure : float, optional
            Pressure difference across the path, used in airflow calculations. Default is 0.0.
        
        Returns
        -------
        None
            This method initializes the object and does not return a value.
        """
        thePath = {}
        thePath["winType"] = 1 if isinstance(moGeometry, MoosasGlazing) else 0
        thePath["Uid"] = moGeometry.Uid
        if pathName is None:
            pathName = moGeometry.Uid
        thePath["userName"] = pathName
        thePath["prjIndex"] = 0
        thePath["fromZone"] = fromZone
        thePath["toZone"] = toZone
        thePath["pressure"] = pressure
        thePath["orientation"] = moGeometry.orientation if not Vector.parallel(moGeometry.orientation,
                                                                               [0, 0, 1]) else Vector(
            [0, 0,
             1])
        pos = list(moGeometry.getWeightCenter())
        thePath['position_x'] = pos[0]
        thePath['position_y'] = pos[1]
        thePath['position_z'] = pos[2]
        thePath["pathHeight"] = None
        thePath["pathWidth"] = None
        thePath["operable"]=1.0
        thePath["element"] = moGeometry
        thePath = cls(**thePath)
        thePath._width
        thePath._height
        return thePath

    @property
    def _width(self):
        """
        Calculate the width of the face along the minimum Z-plane.

        Returns
        -------
        float
            The length (magnitude) of the vector representing the width of the face, computed as the 
            distance between the first and last points in the sorted 2D projection of the face's 
            boundary points lying on the minimum Z-plane.
        """
        if self.pathWidth is None:
            coordinates = shapely.get_coordinates(self.element.face, include_z=True)
            minZ = np.min(coordinates[:, 2])
            sortlist = [[coor[0], coor[1]] for coor in coordinates if
                        minZ - geom.POINT_PRECISION < coor[2] < minZ + geom.POINT_PRECISION]
            sortlist.sort(key=lambda x: (x[0], x[1]))
            self.pathWidth = Vector(np.array(sortlist[-1]) - np.array(sortlist[0])).length()
        return self.pathWidth

    @property
    def _height(self):
        """
        Height of the path calculated as the ratio of 3D area to width.

        
        Returns
        -------
        float
            The height of the path, computed as the 3D area divided by the width.
        """
        if self.pathHeight is None:
            self.pathHeight = self.element.area3d() / self._width
        return self.pathHeight

    def toDict(self) -> dict:
        pathDict = {}
        for key in self.__slots__:
            pathDict[key] = str(getattr(self, key))
        return pathDict

    def dump(self):
        """
        Dump the path data into a comma-separated string format for network file input.
        
        Parameters
        ----------
        self
            The instance of the class containing the path data. Expected attributes include:
            - pathName (str): User-defined name for the path.
            - prjIndex (int): Project index used to generate a formatted identifier.
            - pathHeight (float): Height of the aperture in meters (m).
            - width (float): Width of the aperture in meters (m).
            - position (object): Object with attributes x, y, z representing the 3D position in meters (m).
            - fromZone (int or None): Index of the originating zone; must not be None.
            - toZone (int or None): Index of the destination zone; must not be None.
            - pressure (float): Wind pressure value if the path is connected to the outdoor environment.
            - winType (int or str): Type identifier for the window or opening.
        
        Returns
        -------
        str
            A comma-separated string containing the formatted path data, including generated ID,
            dimensions, position, zone indices, pressure, and window type.
        """
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
        # Internal Python pipeline uses 1-based zone prjIndex.
        # MoosasAFN *.net parser indexes zones as 0-based array slots.
        # Convert only at file-export boundary to keep both sides consistent.
        from_zone = int(self.fromZone)
        to_zone = int(self.toZone)
        from_zone_out = -1 if from_zone == -1 else from_zone - 1
        to_zone_out = -1 if to_zone == -1 else to_zone - 1
        pathStr = [self.userName]
        pathStr += ['p' + '%03d' % int(self.prjIndex)]
        pathStr += [str(float(self.pathHeight)*float(self.operable))]
        pathStr += [str(float(self.pathWidth)*float(self.operable))]
        pathStr += [str(self.position_x)]
        pathStr += [str(self.position_y)]
        pathStr += [str(self.position_z)]
        pathStr += [str(from_zone_out)]
        pathStr += [str(to_zone_out)]
        pathStr += [str(self.pressure)]
        pathStr += [str(self.winType)]
        return ','.join(pathStr)


class AfnNetwork:
    __slots__ = ('zones', 'paths', 'model')

    def __init__(self, model=None, paths=None, zones=None):
        """
        Initialize the object with a model and construct airflow network paths and zones.
        
        Parameters
        ----------
        model : object
            The model containing space and glazing information used to create airflow network 
            paths and zones. Expected to have a `spaceList` attribute with spaces that provide 
            face data via `getAllFaces()`.
        
        Returns
        -------
        None
            This method does not return a value.
        """
        if model:
            self.model = model
            self.paths: list[AfnPath] = []
            self.zones: list[AfnZone] = []
            for s in model.spaceList:
                self.zones.append(AfnZone.fromElement(s))
                self.zones[-1].prjIndex = len(self.zones)
                for gls in s.getAllFaces(to_dict=False):
                    if isinstance(gls, MoosasGlazing) or isinstance(gls, MoosasSkylight):
                        self.paths.append(AfnPath.fromElement(gls))
                        self.paths[-1].prjIndex = len(self.paths)
        elif (paths and zones):
            self.paths = paths
            self.zones = zones
        self.paths = pathTopology(self.paths, self.zones)
        self.paths, self.zones = cleanseNetwork(self.paths, self.zones)

    def checkTopology(self):
        topology = {z.prjIndex:[] for z in self.zones}
        topology[-1]=[]
        for p in self.paths:
            topology[p.fromZone].append(p.prjIndex)
            topology[p.toZone].append(p.prjIndex)
        print(topology)
        print({k: len(i) for k, i in topology.items()})

    def applyWindPressure(self, windVector: Vector, speed=None, airDensity=1.205, alpha=0.22):
        """
        Apply wind pressure to the paths of the object.
        
        Parameters
        ----------
        windVector : Vector
            A vector representing the direction and magnitude of the wind.
        speed : float, optional
            The speed of the object relative to the wind. If not provided, defaults to None.
        airDensity : float, default=1.205
            The density of air in kg/m³. Default corresponds to standard conditions at sea level.
        alpha : float, default=0.22
            A coefficient representing the aerodynamic properties of the object.
        
        Returns
        -------
        None
            This method modifies the `paths` attribute in place and does not return a value.
        """
        """connect to applyWindPressure()"""
        self.paths = applyWindPressure(self.paths, windVector=windVector, speed=speed, airDensity=airDensity,
                                       alpha=alpha)

    def applyZoneHeat(self, zoneInfoFile):
        """
        Copy heat information from a zone info file to corresponding zones.
        
        Parameters
        ----------
        zoneInfoFile : str
            Path to the file containing zone information, including heat load and zone names.
            The file is parsed to extract heat data which is then applied to zones.
        
        Returns
        -------
        None
            This function does not return any value. It modifies the `heatLoad` attribute of 
            each zone in `self.zones` if the zone's userName matches an entry in the heat info.
        """
        """copy the heat information in zoneInfoFile"""
        zoneInfo = parseFile(zoneInfoFile)[0]
        heatIdx, nameIdx = 2, 3
        if len(zoneInfo[0]) == 2:
            heatIdx, nameIdx = 1, 2
        heatInfo = {line[nameIdx]: float(line[heatIdx]) for line in zoneInfo}
        for zone in self.zones:
            if zone.userName in heatInfo.keys():
                zone.heatLoad = heatInfo[zone.userName]

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
    """
    Apply wind pressure to a list of AfnPath objects based on wind conditions.
    
    Parameters
    ----------
    pathList : list of AfnPath
        List of AfnPath objects to which wind pressure will be applied.
    windVector : Vector
        Direction and magnitude of the wind. If `speed` is provided, the vector is scaled accordingly.
    speed : float, optional
        Wind speed in m/s. If None, the magnitude of `windVector` is used as the wind speed.
    airDensity : float, default=1.205
        Air density in kg/m³, used in pressure calculation.
    alpha : float, default=0.22
        Empirical exponent related to altitude effects on wind pressure.
    
    Returns
    -------
    list of AfnPath
        The input list of AfnPath objects with updated `pressure` attributes.
    """
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
        if Vector.parallel(_path.normal, [0, 0, 1]):
            _pressure = 0
        _path.pressure = _pressure

    return pathList


def getZoneAndPath(model):
    """
    Constructs zone and path lists from a building model for airflow network analysis.
    
    Parameters
    ----------
    model : object
        A building model object containing a list of spaces (spaceList). The model is used to extract spaces and their glazing elements to construct zones and airflow paths.
    
    Returns
    -------
    zoneList : list of AfnZone
        List of AfnZone objects created from the spaces in the model. Each zone is assigned a unique project index.
    pathList : list of AfnPath
        List of AfnPath objects representing airflow paths through glazing and skylight elements. The list is processed to establish topological relationships between paths and zones.
    """
    pathList: list[AfnPath] = []
    zoneList: list[AfnZone] = []
    for s in model.spaceList:
        zoneList.append(AfnZone.fromElement(s))
        zoneList[-1].prjIndex = len(zoneList)
        for gls in s.getAllFaces(to_dict=False):
            if isinstance(gls, MoosasGlazing) or isinstance(gls, MoosasSkylight):
                pathList.append(AfnPath.fromElement(gls))
                pathList[-1].prjIndex = len(pathList)
    pathList = pathTopology(pathList, zoneList)
    return zoneList, pathList


def pathTopology(pathList: list[AfnPath], zoneList: list[AfnZone]) -> list[AfnPath]:
    """
    Determine the zone topology for a list of paths based on their connected spaces.
    
    Parameters
    ----------
    pathList : list of AfnPath
        List of AfnPath objects, each representing a path with a `space` attribute 
        containing connected space IDs, and `fromZone` and `toZone` attributes to be set.
    zoneList : list of AfnZone
        List of AfnZone objects, each having an `id` attribute used to map space IDs to zone indices.
    
    Returns
    -------
    list of AfnPath
        Filtered list of AfnPath objects with valid spaces (non-empty), where `fromZone` 
        and `toZone` are set to the corresponding zone indices from `zoneList`. Paths 
        with no connected spaces are excluded.
    """
    zoneUid = {zone.element.id: zone.prjIndex for zone in zoneList}
    invalidPath = []

    for i, p in enumerate(pathList):
        if len(p.element.space) == 0:
            invalidPath.append(i)
            
        elif len(p.element.space) == 1:
            p.fromZone = -1
            if p.element.space[0] in zoneUid.keys():
                p.toZone = zoneUid[p.element.space[0]]
            else:
                invalidPath.append(i)

        elif len(p.element.space) == 2:
            if p.element.space[0] in zoneUid.keys() and p.element.space[1] in zoneUid.keys():
                p.fromZone = zoneUid[p.element.space[0]]
                p.toZone = zoneUid[p.element.space[1]]
            else:
                invalidPath.append(i)

    return list(np.delete(pathList, invalidPath))


def buildNetworkFile(model=None, pathList: list[AfnPath] = None, zoneList: list[AfnZone] = None,
                     networkFilePath=None, windVector: Vector = None,
                     airDensity=1.205, alpha=0.22) -> str:
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

    # Always run cleansing here, no matter path/zone source.
    # buildPrj/buildZoneInfoFile may pass pre-built lists and previously bypass cleaning.
    pathList, zoneList = cleanseNetwork(pathList, zoneList)

    if windVector:
        pathList = applyWindPressure(pathList, windVector=windVector, speed=windVector.length(), airDensity=airDensity,
                                     alpha=alpha)
    networkStr = "! All annotations has prefix as !\n"
    networkStr += "! ZONE DATA\n"
    networkStr += "! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon\n"
    for z in zoneList:
        networkStr += z.dump() + "\n"
    networkStr += ";\n! PATH DATA\n"
    networkStr += "! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure,winType\n"
    for p in pathList:
        networkStr += p.dump() + "\n"
    if networkFilePath is None:
        networkFilePath = os.path.join(path.tempDir, generate_code(4) + '.net')

    with open(networkFilePath, 'w+') as f:
        f.write(networkStr)
    return networkFilePath


def cleanseNetwork(pathList: list[AfnPath], zoneList: list[AfnZone]) -> (list[AfnPath], list[AfnZone]):
    """
    Clean the zones that are not linked to the ambient and remove associated paths.
    
    Parameters
    ----------
    pathList : list of AfnPath
        List of path objects representing connections between zones. Each path has 'fromZone' and 'toZone' attributes indicating connectivity.
    zoneList : list of AfnZone
        List of zone objects. Each zone object must have an 'id' attribute. Zones not connected to the ambient (index -1) are considered invalid.
    
    Returns
    -------
    tuple of (list of AfnPath, list of AfnZone)
        A tuple containing the filtered pathList and zoneList with unconnected (invalid) zones and their associated paths removed.
        Zone indices in paths are remapped to reflect the new positions after deletion.
    """
    """clean the zones that are not linked to the ambient.
    those zones will cause error in ContamX and their air change is 0.
    """

    zone_count = len(zoneList)
    if zone_count == 0:
        return list(pathList), list(zoneList)

    # Keep topology indices consistent with zone.prjIndex (1-based in AFN pipeline).
    zone_ids = [int(z.prjIndex) for z in zoneList]
    zone_id_set = set(zone_ids)
    zone_by_id = {int(z.prjIndex): z for z in zoneList}

    def _is_variable_path(p: AfnPath, eps=1e-9):
        try:
            h = float(p.pathHeight)
            w = float(p.pathWidth)
            op = float(p.operable) if p.operable is not None else 1.0
            return h > eps and w > eps and op > eps
        except Exception:
            return False

    # keep only paths with valid endpoint indices first
    valid_index_paths: list[AfnPath] = []
    dropped_invalid_index = []
    for i, p in enumerate(pathList):
        fz = int(p.fromZone)
        tz = int(p.toZone)
        f_ok = (fz == -1) or (fz in zone_id_set)
        t_ok = (tz == -1) or (tz in zone_id_set)
        if f_ok and t_ok:
            valid_index_paths.append(p)
        else:
            dropped_invalid_index.append(i)
    if dropped_invalid_index:
        print(f'******Warning: drop paths with invalid zone index: {dropped_invalid_index}')

    # BFS on variable flow topology from ambient (-1)
    topology = {-1: set()}
    for zid in zone_ids:
        topology[zid] = set()

    for p in valid_index_paths:
        if not _is_variable_path(p):
            continue
        fz = int(p.fromZone)
        tz = int(p.toZone)
        topology[fz].add(tz)
        topology[tz].add(fz)

    visited = {-1}
    queue = [-1]
    while queue:
        cur = queue.pop(0)
        for nxt in topology.get(cur, ()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)

    keep_zone_ids = sorted([z for z in visited if z >= 0])
    remove_zone_ids = sorted(set(zone_ids).difference(keep_zone_ids))

    if remove_zone_ids:
        print('******Warning: some zones do not linked to ambient by variable flow path.')
        print(f'******Warning: those zone will be removed:{remove_zone_ids}')

    # Reindex remaining zones to contiguous 1..N and map old zone prjIndex -> new prjIndex.
    idx_map = {old: new for new, old in enumerate(keep_zone_ids, start=1)}
    new_zones: list[AfnZone] = [zone_by_id[i] for i in keep_zone_ids]
    for i, z in enumerate(new_zones, start=1):
        z.prjIndex = i

    new_paths: list[AfnPath] = []
    removed_path_idx = []
    for i, p in enumerate(valid_index_paths):
        fz = int(p.fromZone)
        tz = int(p.toZone)
        f_keep = (fz == -1) or (fz in idx_map)
        t_keep = (tz == -1) or (tz in idx_map)
        if not (f_keep and t_keep):
            removed_path_idx.append(i)
            continue
        p.fromZone = -1 if fz == -1 else idx_map[fz]
        p.toZone = -1 if tz == -1 else idx_map[tz]
        new_paths.append(p)

    if removed_path_idx:
        print(f'******Warning: those path will be removed:{removed_path_idx}')

    for i, p in enumerate(new_paths, start=1):
        p.prjIndex = i

    return new_paths, new_zones


def buildPrj(model=None, pathList: list[AfnPath] = None, zoneList: list[AfnZone] = None,
             prjFilePath=None, networkFilePath=None, split=False,
             t0=25, windVector: Vector = None, airDensity=1.205, alpha=0.22,
             simulate=False, resultFile=None) -> str:
    """
    Build one or more CONTAM *.prj file(s) from a model or provided path and zone lists.
    
    Parameters
    ----------
    model : MoosasModel, optional
        A model object obtained from transforming.transform(). Used to derive zone and path data if pathList and zoneList are not provided.
    pathList : list of AfnPath, optional
        List of AfnPath objects representing airflow paths. Can be constructed using getZoneAndPath().
    zoneList : list of AfnZone, optional
        List of AfnZone objects representing zones. Can be constructed using getZoneAndPath().
    prjFilePath : str, optional
        File path for the output *.prj file. If None, defaults to a temporary directory under 'data\\vent'.
    networkFilePath : str, optional
        File path for the generated network (.net) input file for MoosasAFN.exe. If None, defaults to a temporary location.
    split : bool, default False
        If True, the network is split into isolated parts and multiple files are generated.
    t0 : float or int, default 25
        Outdoor temperature in degrees Celsius.
    windVector : Vector, optional
        Wind vector defining direction and speed for simulation.
    airDensity : float, default 1.205
        Air density in kg/m³.
    alpha : float, default 0.22
        Power law exponent for airflow modeling.
    simulate : bool, default False
        If True, runs CONTAM simulation after building the project and collects results.
    resultFile : str, optional
        Custom file path to save simulation results. If not specified, defaults to the project directory.
    
    Returns
    -------
    list of str
        A list containing the path(s) to the generated *.prj file(s).
    """
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
        networkFilePath = buildNetworkFile(pathList=pathList, zoneList=zoneList, networkFilePath=networkFilePath,
                                           windVector=windVector, airDensity=airDensity, alpha=alpha)

    if prjFilePath is None:
        prjName = prjTempName
        prjDirectory = path.tempDir
        prjFilePath = os.path.join(prjDirectory, prjName + '.prj')
    else:
        prjName = os.path.basename(prjFilePath)[:-4]
        prjDirectory = os.path.dirname(prjFilePath)

    command = [os.path.join(path.libDir, 'vent', f'MoosasAFN{VENT_EXE_SUFFIX}')]
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
    Builds a zone information file (.info) for thermal zone data based on model, zone list, and network file inputs.

    Parameters
    ----------
    model : MoosasModel, optional
        The transformed model object obtained from the `transform()` method. Used to extract zone and path data if not provided directly.
    zoneList : list of AfnZone, optional
        List of AfnZone objects representing thermal zones. If not provided, will be extracted from the model.
    networkFilePath : str, optional
        Path to the network file (.net). If not provided, a temporary network file will be generated using `buildNetworkFile()`.
    pathList : list of AfnPath, optional
        List of AfnPath objects representing airflow paths. Required if generating a network file.
    zoneInfoFilePath : str, optional
        Output file path for the generated zone info file. If not specified, a temporary file path is created.

    Returns
    -------
    str
        If `zoneInfoFilePath` is provided, returns generated file path.
        If `zoneInfoFilePath` is None, returns in-memory zoneInfo text stream.
    """
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
        return zoneStr

    path.checkBuildDir(zoneInfoFilePath)
    with open(zoneInfoFilePath, 'w+') as f:
        f.write(zoneStr)
    return zoneInfoFilePath
