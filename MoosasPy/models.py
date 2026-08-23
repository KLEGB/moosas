"""Connection to most of the functions in moosas+.
It records the space data we need in the analysis.

we split the MoosasModel definition from geometry.element to avoid circular import
"""
from __future__ import annotations

import shapely
import xml.etree.ElementTree as ET

from .transformation.geometry.element import *
from .transformation.geometry.geos import faceNormal

"""you can apply the inch to meter translation here"""
# from .utils.constant import geom
# INCH_METER_MULTIPLIER = geom.INCH_METER_MULTIPLIER
# INCH_METER_MULTIPLIER_SQR = geom.INCH_METER_MULTIPLIER_SQR
INCH_METER_MULTIPLIER = 1
INCH_METER_MULTIPLIER_SQR = 1


class MoosasModel(MoosasContainer):
    """Domain state for a building geometry and its analysis configuration.

    Resource loading is deliberately handled by ``MoosasPy.model_resources``.
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

        self.weather = None
        self.cumSky = None
        self.buildingTemplate = {}
        self.idfZoneTemplate = {}
        self.schedulePath = None
        self.schedule = {}
        self.scheduleByType = {}

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
            <setting> thermal settings of the space in dictionary, defined by transformation.io.idf.model
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
