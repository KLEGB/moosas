"""Connection to most of the functions in moosas+.
It records the space data we need in the analysis.

we split the MoosasModel definition from geometry.element to avoid circular import
"""
from __future__ import annotations

import os.path
import uuid

import shapely
import xml.etree.ElementTree as ET
from .utils.standard import loadBuildingTemplate
from .utils.tools import path
from .weather.dest import MoosasWeather
from .weather.cumsky import loadCumSky, MoosasCumSky
from .weather.include import includeEpw

from .geometry.element import *
from .geometry.geos import faceNormal

"""you can apply the inch to meter translation here"""
# from .utils.constant import geom
# INCH_METER_MULTIPLIER = geom.INCH_METER_MULTIPLIER
# INCH_METER_MULTIPLIER_SQR = geom.INCH_METER_MULTIPLIER_SQR
INCH_METER_MULTIPLIER = 1
INCH_METER_MULTIPLIER_SQR = 1


class MoosasModel(MoosasContainer):
    """Define all the global variables needed for Moosas+.

    This class does not have slots for the sake of flexible attributes.

    Attributes:
        weather (MoosasWeather): MoosasWeather in this model, default is None.
        builtData (Object): Data used to construct space manually.

    Properties:
        buildingTemplate (dict): A dictionary to show all building templates in the database.

    Methods:
        loadWeatherData(self, stationId: str = '545110') -> MoosasWeather: Load the weather data to self.weather.
        loadCumSky(self, stationId: str = '545110') -> dict: Load a cumulative sky model to self.cumSky.
        plotPlan(self, level_index: int) -> None: Plot the building plan on the given index of building level.
        buildXml(self) -> ET.Element: Build an XML tree file of all spaces.
        buildGeojson(self) -> dict: Build a GeoJSON file of all geometries.
    """

    def __init__(self):
        """
        Initialize the MoosasModel with default lists and assign types to these lists.
        
        Parameters
        ----------
        self : object
            The instance of the MoosasModel class being initialized.
        
        Returns
        ------
        None
            This constructor does not return any value.
        """
        """initialize the MoosasModel with default list, and apply type to these list"""
        super(MoosasModel, self).__init__()

        self.weather: MoosasWeather | None = None
        self.__template = loadBuildingTemplate(os.path.join(path.dataBaseDir, 'building_template.csv'))
        self.idfZoneTemplate = {}
        self.schedulePath = os.path.join(path.dataBaseDir, 'office.sch')
        self.schedule = {}
        self.scheduleByType = {}
        self.loadSchedule(self.schedulePath)
    @property
    def buildingTemplate(self) -> dict:
        """
        Get a dictionary containing all building template data from the database.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the template data.
        
        Returns
        -------
        dict
            A dictionary with string keys representing template parameters and corresponding
            values for each parameter. The dictionary includes:
            - "zone_wallU": Exterior wall U-value
            - "zone_winU": Exterior window U-value
            - "zone_win_SHGC": Exterior window Solar Heat Gain Coefficient
            - "zone_c_temp": Cooling set point temperature
            - "zone_h_temp": Heating set point temperature
            - "zone_collingEER": Cooling COP (Coefficient of Performance)
            - "zone_HeatingEER": Heating COP
            - "zone_work_start": Working schedule start time
            - "zone_work_end": Working schedule end time
            - "zone_ppsm": Population per square meter
            - "zone_pfav": Ventilation rate per person (ACH)
            - "zone_popheat": Heat generation per person (W/pp)
            - "zone_equipment": Equipment heat generation (W/m2)
            - "zone_lighting": Lighting heat generation (W/m2)
            - "zone_infiltration": Infiltration air change coefficient (ACH)
            - "zone_nightACH": Nighttime air change coefficient (ACH)
        """
        """get a dictionary showing all template in the database

        Returns:
            dict: {Hint:templateData}
            templateData = {
                        "zone_wallU"=>            exterior wall u value
                        "zone_winU"=>             exterior window u value
                        "zone_win_SHGC"=>         exterior window SHGC
                        "zone_c_temp"=>           cooling set point
                        "zone_h_temp"=>           heating set point
                        "zone_collingEER"=>       cooling COP
                        "zone_HeatingEER"=>       heating COP
                        "zone_work_start"=>       working schedule start time
                        "zone_work_end"=>         working schedule end time
                        "zone_ppsm"=>             population per m2
                        "zone_pfav"=>             ventilation (ACH) per person
                        "zone_popheat"=>          heat generation (W/pp) per person
                        "zone_equipment"=>        equipment heat generation (W/m2)
                        "zone_lighting"=>         lighting heat generation (W/m2)
                        "zone_infiltration"=>     infiltration air change coefficient (ACH)
                        "zone_nightACH"=>         air change coefficient in nighttime (ACH)
                    }

        """
        return self.__template

    def includeTemplate(self, templateName: str,templateDict:dict):
        """
        Include a template in the internal template dictionary.
        
        Parameters
        ----------
        templateName : str
            The name of the template to be added.
        templateDict : dict
            The dictionary containing the template data.
        
        Returns
        -------
        None
            This function does not return any value.
        """
        self.__template[templateName] = templateDict

    @staticmethod
    def _schedule_type_from_path(schedulePath: str) -> str:
        schedule_name = os.path.splitext(os.path.basename(str(schedulePath)))[0].upper()
        return schedule_name

    @staticmethod
    def _schedule_role_from_name(scheduleName: str) -> str | None:
        lower = str(scheduleName).lower()
        if "occdens" in lower or "occupantdensity" in lower:
            return "zone_ppsm"
        if "equip" in lower or "equipmentheatgain" in lower:
            return "zone_equipment"
        if "light" in lower or "lightingheatgain" in lower:
            return "zone_lighting"
        return None

    def _rebuildScheduleByType(self):
        prefix_to_type = {
            "OFF": "OFFICE",
            "RES": "RESIDENTIAL",
            "COM": "COMMERCIAL",
            "SCH": "SCHOOL",
            "HOT": "HOTEL",
        }
        rebuilt = {}
        for scheduleName, scheduleValue in self.schedule.items():
            if not isinstance(scheduleValue, dict):
                continue
            scheduleType = str(scheduleValue.get("type", "")).strip().title()
            prefix = str(scheduleName).split("_", 1)[0].upper()
            typeName = prefix_to_type.get(prefix, scheduleType.upper())
            if not typeName:
                continue
            role = self._schedule_role_from_name(scheduleName)
            if role is None:
                continue
            rebuilt.setdefault(typeName, {})[role] = scheduleName
        self.scheduleByType = rebuilt

    def getScheduleName(self, templateType: str, fieldName: str):
        if templateType is None:
            return None
        return self.scheduleByType.get(str(templateType).upper(), {}).get(fieldName)

    def loadSchedule(self, schedulePath: str = os.path.join(path.dataBaseDir, 'office.sch')):
        """
        Load a schedule library from a .sch file into the in-memory schedule dict.

        The file format supports Daily and Weekly rows. Daily schedules keep 24
        hourly values; Weekly schedules keep 7 daily schedule references.
        """
        if schedulePath is None:
            schedulePath = os.path.join(path.dataBaseDir, 'office.sch')
        schedulePath = os.path.abspath(schedulePath)
        if not os.path.isfile(schedulePath):
            raise FileNotFoundError(f"Schedule file not found: {schedulePath}")

        loaded = {}
        with open(schedulePath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                text = line.strip()
                if (not text) or text.startswith("!"):
                    continue
                parts = [p.strip() for p in text.split(",")]
                if len(parts) < 3:
                    continue
                name = parts[0]
                mode = parts[1].strip().lower()
                if mode == "daily":
                    values = parts[2:26]
                    if len(values) != 24:
                        raise ValueError(f"Invalid daily schedule row '{name}', expected 24 hourly values.")
                    loaded[name] = {"type": "Daily", "value": values}
                elif mode == "weekly":
                    values = parts[2:9]
                    if len(values) != 7:
                        raise ValueError(f"Invalid weekly schedule row '{name}', expected 7 day references.")
                    loaded[name] = {"type": "Weekly", "value": values}

        self.schedule.update(loaded)
        self.schedulePath = schedulePath
        self._rebuildScheduleByType()
        return self.schedule

    def writeSchedule(self, schedulePath: str = None):
        """
        Write the current schedule library to a .sch file.

        If schedulePath is None, a unique temporary file is created under
        MoosasPy/__temp__.
        """
        if schedulePath is None:
            schedulePath = os.path.join(path.tempDir, f"schedule_{uuid.uuid4().hex}.sch")
        schedulePath = os.path.abspath(schedulePath)
        path.checkBuildDir(schedulePath)

        daily_items = [(name, value) for name, value in self.schedule.items()
                       if str(value.get("type", "")).lower() == "daily"]
        weekly_items = [(name, value) for name, value in self.schedule.items()
                        if str(value.get("type", "")).lower() == "weekly"]

        with open(schedulePath, "w", encoding="utf-8") as f:
            f.write("! Moosas schedule export\n")
            for name, item in daily_items:
                values = item.get("value", [])
                if len(values) != 24:
                    raise ValueError(f"Daily schedule '{name}' must have 24 values.")
                f.write(f"{name},Daily,{','.join([str(v) for v in values])}\n")
            for name, item in weekly_items:
                values = item.get("value", [])
                if len(values) != 7:
                    raise ValueError(f"Weekly schedule '{name}' must have 7 values.")
                f.write(f"{name},Weekly,{','.join([str(v) for v in values])}\n")
        return schedulePath
    def loadWeatherData(self, stationIdOrPath: str = '545110') -> MoosasWeather:
        """
        Load weather data from the database or import an external EPW file.
        
        Parameters
        ----------
        stationIdOrPath : str, optional
            The ID of the weather station or the file path to an EPW file. If a valid file path is provided, 
            the EPW file will be imported using `includeEpw`. Default is '545110'.
        
        Returns
        -------
        MoosasWeather
            An instance of MoosasWeather containing the loaded weather data.
        """
        """load weather data from the database,
        or import an external epw file using weather.includeEpw method

        Args:
            stationIdOrPath(str): the id of the station in epw file, or the path of the epw file

        Returns:
            MoosasWeather: loaded weather data
        """
        if os.path.isfile(stationIdOrPath):
            stationIdOrPath = includeEpw(stationIdOrPath)
        self.weather = MoosasWeather(stationIdOrPath)
        return self.weather

    def loadCumSky(self, stationIdOrPath: str = '545110') -> dict:
        """
        Load cumulative sky data for a given station or EPW file.
        
        Parameters
        ----------
        stationIdOrPath : str, optional
            The ID of the weather station or the file path to an EPW file. If a valid file path is provided, 
            the EPW file will be imported and processed. Default is '545110'.
        
        Returns
        -------
        dict
            A dictionary containing the loaded cumulative sky data with the following keys:
            - 'annualCumSky': annual cumulative sky dome (numpy array or similar structure)
            - 'summerCumSky': summer period cumulative sky dome
            - 'winterCumSky': winter period cumulative sky dome
        """
        """load cumSky data from the database,
                or import an external epw file using weather.includeEpw method

        Args:
            stationIdOrPath(str): the id of the station in epw file, or the path of the epw file

        Returns:
            dict: loaded cumSky data, including:
            {   annualCumSky: annual cumulative sky dom,
                summerCumSky: summer cumulative sky dom,
                winterCumSky: winter cumulative sky dom,
                }
        """
        if os.path.isfile(stationIdOrPath):
            stationIdOrPath = includeEpw(stationIdOrPath)
        self.cumSky = {}
        m_cumSky = loadCumSky(
            stationIdOrPath,
            [0, MoosasCumSky.SUMMER_START_HOY, MoosasCumSky.SUMMER_END_HOY],
            [8760, MoosasCumSky.WINTER_START_HOY, MoosasCumSky.WINTER_END_HOY],
        )
        self.cumSky['annualCumSky'] = m_cumSky[0]
        self.cumSky['summerCumSky'] = m_cumSky[1]
        self.cumSky['winterCumSky'] = m_cumSky[2]
        return self.cumSky

    def plotPlan(self, level_index: int, show=True) -> None:
        """
        Plot the plan view for a specified level index.
        
        Parameters
        ----------
        level_index : int
            The index of the level to plot, corresponding to an entry in self.levelList.
        show : bool, optional
            Whether to display the figure immediately. Default is True.
        
        Returns
        -------
        None
        """
        """plot the plan view for defined level index in self.levelList
        since the pythonDist folder does not contain matplotlib package,
        we need to import the package inside this method

        The black lines in the figure shows the wall in the plan;
        the blue lines mean apertures or windows or walls;
        toe gry lines mean apertures or skylight on the floor;
        and the dot blue lines means skylight or aperture on the ceilings.

        Args:
            level_index (int): the index of the level to plot
            show (bool, optional): whether to show the figure
        """
        from .visual import plot_object
        spaces: list[MoosasSpace] = np.array(self.spaceList)[
            searchBy('level', self.levelList[level_index], self.spaceList)]
        walls = []
        floors = []
        ceilings = []
        gls = []
        skylight = []
        aperture = []
        for s in spaces:
            walls += s.getAllFaces(to_dict=True)['MoosasWall']
            floors += s.floor.face
            ceilings += s.ceiling.face
        for w in walls:
            gls += w.glazingElement
        for f in floors:
            aperture += f.glazingElement
        for f in ceilings:
            skylight += f.glazingElement
        plot_object(walls, gls, aperture, skylight, colors=['black', 'blue', 'grey', 'blue'], lineSize=[1, 3, 1, 1],
                    lineType=['-', '-', '-', '--'], show=show)

    def autoDescribe(self):
        """automatically generate description for each space and element in the model, based on their geometry and settings.
        the description will be stored in the 'description' attribute of each space and element, and can be used in the analysis or output.
        """
        for spc in self.spaceList:
            if spc.description == "":
                walls = self.getAllFaces(dumpUseless=True)['MoosasWall']
                description = f"This is a space named{spc.id} located in the level {spc.level},"
                description += f" with an area of {spc.area} m2 and a height of {spc.height} m. "
                description += f" average Window to wall ratio of this space is {np.round(np.mean([w.wwr for w in walls]), 2)}. "
                spc.description = description
            
            for face in spc.getAllFaces():
                if face.description == "":
                    if isinstance(face, MoosasWall):
                        face.description = f"This is a wall with an area of {face.area} m2, and a U-value of {face.U_Value} W/m2K. "
                    elif isinstance(face, MoosasFace):
                        face.description = f"This is a floor with an area of {face.area} m2, and a U-value of {face.U_Value} W/m2K. "
                    elif isinstance(face, MoosasGlazing):
                        face.description = f"This is a glazing with an area of {face.area} m2, and a U-value of {face.U_Value} W/m2K. "
                    elif isinstance(face, MoosasSkylight):
                        face.description = f"This is a skylight with an area of {face.area} m2, and a U-value of {face.U_Value} W/m2K. "
                    else:
                        face.description = f"This is a face with an area of {face.area} m2. "
                    
                    if len(face.space)==1:
                        face.description += f" It belongs to space {face.space[0]}. "
                    elif len(face.space)>1:
                        face.description += f" It belongs to spaces {', '.join(face.space)}. "
                    if face.isOuter:
                        face.description += " It is an external face. "
                    else:
                        face.description += " It is an internal face. "

    def summary(self,wall_count=None):
        """
        Prints a formatted summary of building elements by level.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the lists of building elements.
            Must have attributes: `levelList`, `wallList`, `glazingList`, `skylightList`,
            `faceList`, and `spaceList`.
        wall_count : list of int, optional
            A list specifying the previous count of walls per level for change tracking.
            If provided, differences in wall counts are displayed in parentheses.
        
        Returns
        -------
        None
            This function does not return a value. It prints the summary directly to stdout.
        """
        print('LEVEL\t\tWALL\t\tGLS\t\tSKY\t\tFACE\t\tSPACE\t\tAREA')

        for i, bld_level in enumerate(self.levelList):
            print(f"%.2f" % bld_level, end='')
            if wall_count:
                print(
                    f"\t\t{len(searchBy('level', bld_level, self.wallList))}({len(searchBy('level', bld_level, self.wallList)) - wall_count[i]})",
                    end='')
            else:
                print(
                    f"\t\t{len(searchBy('level', bld_level, self.wallList))}",
                    end='')
            print(f"\t\t{len(searchBy('level', bld_level, self.glazingList))}", end='')
            print(f"\t\t{len(searchBy('level', bld_level, self.skylightList))}", end='')
            print(f"\t\t{len(searchBy('level', bld_level, self.faceList))}", end='')
            print(f"\t\t{len(searchBy('level', bld_level, self.spaceList))}({len(searchBy('level', bld_level, self.voidList))})", end='')
            print(
                f"\t\t{np.round(np.sum([self.spaceList[i].area for i in searchBy('level', bld_level, self.spaceList)]), 1)}({np.round(np.sum([self.voidList[i].area for i in searchBy('level', bld_level, self.voidList)]), 1)})\n",
                end='')

        if wall_count:
            print(
                f"    \t\t{len(self.wallList)}({len(self.wallList) - sum(wall_count)})"
                f"\t\t{len(self.glazingList)}"
                f"\t\t{len(self.skylightList)}"
                f"\t\t{len(self.faceList)}"
                f"\t\t{len(self.spaceList)}"
                f"\t\t{np.round(np.sum([s.area for s in self.spaceList]), 1)}({np.round(np.sum([s.area for s in self.voidList]), 1)})")

        else:
            print(
                f"    \t\t{len(self.wallList)}"
                f"\t\t{len(self.glazingList)}"
                f"\t\t{len(self.skylightList)}"
                f"\t\t{len(self.faceList)}"
                f"\t\t{len(self.spaceList)}"
                f"\t\t{np.round(np.sum([s.area for s in self.spaceList]), 1)}({np.round(np.sum([s.area for s in self.voidList]), 1)})")

        # for bld_level in self.levelList:
        #     spaceList = searchBy("level", bld_level,self.spaceList,asObject=True)
        #     spaceType = [s.spaceType for s in spaceList]
        #     Corridor = [s for s,t in zip(spaceList,spaceType) if t == 'Corridor']
        #     privateSpace = [s for s, t in zip(spaceList, spaceType) if t == 'privateSpace']
        #     MainSpace = [s for s, t in zip(spaceList, spaceType) if t == 'MainSpace']
        #     print(f"level: {bld_level}, "
        #           f"Corridor {len(Corridor)} area: {np.sum([s.area for s in Corridor])},"
        #           f"privateSpace {len(privateSpace)} area: {np.sum([s.area for s in privateSpace])},"
        #           f"MainSpace {len(MainSpace)} area: {np.sum([s.area for s in MainSpace])}")

    def buildXml(self, writeGeometry=False) -> ET.Element:
        """
        Build an XML element tree representing the model information.
        
        Parameters
        ----------
        writeGeometry : bool, optional
            Whether to include geometry data in the XML output. Default is False.
        
        Returns
        -------
        ET.Element
            The root element of the constructed XML tree containing model data including faces, 
            topology, spaces, settings, and shading information.
        """
        """build a xmlTree for the model information.
        the XML file have 3 level of data:
        <face>
            <Uid> unique id, which is random generated. </Uid>
            <faceId> the faceId of the faces in the geo data or file. </faceId>
            <level> the faceId of the faces in the geo data or file. </level>
            <offset> the element's offset from the building level. </offset>
            <area> the total surface area. </area>
            <glazingId> glazing faceId in the geo data or file. </glazingId>
            <height> level + offset </height>
            <normal> element's normal, point to exterior. (x y z) </normal>
            <external> whether the element is connected to exterior. </external>
            <space> the space id which this element belongs to. </space>
        </face>

        <topology>
            <floor>
                <face>...</face>
            </floor>
            <ceiling>
                <face>...</face>
            </ceiling>
            <edge>
                <face>...</face>
            </edge>
        </topology>

        <space>
            <id>
                unique space id, which is calculated based on the shape & location of the space.
                It is the same in each we call transfrom()
            </id>
            <area> space area </area>
            <height> space height </height>
            <boundary> space 1 level space boundary (1LSB) {pt:[[x,y,z]...]}
                <pt>216.53 393.70 0.0</pt>
                <pt>... ... ...</pt>
                <pt>216.53 177.16 0.0</pt>
            </boundary>

            <internal_wall> the internalMass in the space
                <face>...</face>
            </internal_wall>
            <topology>
                <floor>...</floor>
                <ceiling>...</ceiling>
                <edge>...</edge>
            </topology>
            <neighbor> the neighborhood space share the same 2 level space boundary (2LSB)
                <faceId> the faceId of the 2LSB in the geo file, </faceId>
                <id> the neighbor space id </id>
            </neighbor>
            <setting> thermal settings of the space in dictionary, you can find their names in .thermal.settings
                ...
            </setting>
            <void> the void inside the space, also formatted in space[{space}..]
                ...
            </void>
        </space>

        Args:
            writeGeometry(bool, optional): whether to write the geometry to file. Defaults to False.

        Returns:
            ET.Element: xml tree
        """
        root = ET.Element('model')
        mElements = {'MoosasFace': set(), 'MoosasSkylight': set(), 'MoosasWall': set(), 'MoosasGlazing': set()}
        for space in self.spaceList + self.voidList:
            root.append(space.to_xml(self, writeGeometry=writeGeometry))
            elementDict = space.getAllFaces(to_dict=True)
            mElements['MoosasFace'] = mElements['MoosasFace'] | set(
                elementDict['MoosasFloor'] + elementDict['MoosasCeiling'])
            mElements['MoosasWall'] = mElements['MoosasWall'] | set(
                elementDict['MoosasWall'] + elementDict['InternalMass'])
            mElements['MoosasSkylight'] = mElements['MoosasSkylight'] | set(elementDict['MoosasSkylight'])
            mElements['MoosasGlazing'] = mElements['MoosasGlazing'] | set(elementDict['MoosasGlazing'])

        for face in mElements['MoosasFace']:
            root.append(face.to_xml(self, writeGeometry=writeGeometry))

        for wall in mElements['MoosasWall']:
            root.append(wall.to_xml(self, writeGeometry=writeGeometry))
        for gls in mElements['MoosasGlazing']:
            root.append(gls.to_xml(self, writeGeometry=writeGeometry))
        for skl in mElements['MoosasSkylight']:
            root.append(skl.to_xml(self, writeGeometry=writeGeometry))

        shading = ET.SubElement(root, 'shading')
        for glazing in self.glazingList:
            for shad in glazing.shading:
                face = ET.SubElement(shading, 'face')
                face.text = str(shad)
                face.set("glazingId", str(glazing.faceId))
        ET.SubElement(root, 'level').text = ' '.join(np.array(self.levelList).astype(str))
        return root

    def buildGeojson(self, mask=None) -> dict:
        """
        Build a GeoJSON dictionary from the model's geometry library.
        
        Parameters
        ----------
        mask : array-like, optional
            A mask to filter faces. If provided, only faces matching the mask are included.
            Default is None, which includes all faces.
        
        Returns
        -------
        dict
            A dictionary representing a GeoJSON FeatureCollection, containing features 
            with properties such as normal vector, face ID, category (is_glazing), 
            and polygon geometry defined by coordinates.
        """
        """build a geojson from the model's geometry library.
        the geojson file can be read by gis software or by shapely package.

        Returns:
            dict: geojson dictionary
        """
        validGeo = []
        if mask is not None:
            validGeo = self.findFace(mask)
        else:
            geoIdSet = set([])
            for f in self.getAllFaces():
                geoIdSet = geoIdSet.union(mixItemListToList(f.faceId))
            validGeo = self.findFace(list(geoIdSet))
        features = [
            {
                "type": "Feature",
                "properties": {
                    "normal": shapely.get_coordinates(geo.normal, include_z=True).tolist(),
                    "id": geo.faceId,
                    "is_glazing": geo.category
                },
                "geometries": {
                    "type": "Polygon",
                    "coordinates": shapely.get_coordinates(geo.face, include_z=True).tolist()
                }
            }
            for geo in validGeo
        ]
        geo_json = {
            "type": "FeatureCollection",
            "features": features
        }
        return geo_json
