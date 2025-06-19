"""Connection to most of the functions in moosas+.
It records the space data we need in the analysis.

we split the MoosasModel definition from geometry.element to avoid circular import
"""
from __future__ import annotations

import os.path

import pygeos
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
        """initialize the MoosasModel with default list, and apply type to these list"""
        super(MoosasModel, self).__init__()

        self.weather: MoosasWeather | None = None
        self.__template = loadBuildingTemplate(path.dataBaseDir+r'\building_template.csv')
    @property
    def buildingTemplate(self) -> dict:
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
                        "zone_popheat"=>          heat generation (W) per person
                        "zone_equipment"=>        equipment heat generation (W)
                        "zone_lighting"=>         lighting heat generation (W)
                        "zone_infiltration"=>     infiltration air change coefficient (ACH)
                        "zone_nightACH"=>         air change coefficient in nighttime (ACH)
                    }

        """
        return self.__template

    def includeTemplate(self, templateName: str,templateDict:dict):
        self.__template[templateName] = templateDict
    def loadWeatherData(self, stationIdOrPath: str = '545110') -> MoosasWeather:
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

    def summary(self,wall_count):
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
            print(f"\t\t{len(searchBy('level', bld_level, self.spaceList))}", end='')
            print(
                f"\t\t{np.round(np.sum([self.spaceList[i].area for i in searchBy('level', bld_level, self.spaceList)]), 1)}\n",
                end='')

        if wall_count:
            print(
                f"    \t\t{len(self.wallList)}({len(self.wallList) - sum(wall_count)})"
                f"\t\t{len(self.glazingList)}"
                f"\t\t{len(self.skylightList)}"
                f"\t\t{len(self.faceList)}"
                f"\t\t{len(self.spaceList)}"
                f"\t\t{np.round(np.sum([s.area for s in self.spaceList]), 1)}")

        else:
            print(
                f"    \t\t{len(self.wallList)}"
                f"\t\t{len(self.glazingList)}"
                f"\t\t{len(self.skylightList)}"
                f"\t\t{len(self.faceList)}"
                f"\t\t{len(self.spaceList)}"
                f"\t\t{np.round(np.sum([s.area for s in self.spaceList]), 1)}")

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
        """build a geojson from the model's geometry library.
        the geojson file can be read by gis software or by pygeos package.

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
            validGeo = np.array(self.geometryList)[list(geoIdSet)]
        features = [
            {
                "type": "Feature",
                "properties": {
                    "normal": pygeos.get_coordinates(geo.normal, include_z=True),
                    "id": geo.faceId,
                    "is_glazing": geo.category
                },
                "geometries": {
                    "type": "Polygon",
                    "coordinates": pygeos.get_coordinates(geo.face, include_z=True)
                }
            }
            for geo in validGeo
        ]
        geo_json = {
            "type": "FeatureCollection",
            "features": features
        }
        return geo_json
