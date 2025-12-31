import re

from eppy.modeleditor import IDF

from .construction import Construction
from ..encoding.convexify import triangulate2dFace
from .settings import *
from ..geometry.element import MoosasSpace, MoosasElement
from ..geometry.geos import faceNormal, Vector
from ..utils import pygeos,mixItemListToList
import copy

class ZoneTemplate():
    __slots__ = ("idf", "zoneObject", "objectList", "constructionList", "scheduleList")

    def __init__(self, idf, zoneObject, objectList, constructionList, scheduleList):
        self.idf = idf
        self.zoneObject = copy.deepcopy(zoneObject)
        self.objectList = copy.deepcopy(objectList)
        self.constructionList = copy.deepcopy(constructionList)
        self.scheduleList = copy.deepcopy(scheduleList)

    @classmethod
    def fromIDF(cls, idf: IDF):
        """
        Initialize the object by extracting and processing construction and zone-related data from an IDF file.
        
        Parameters
        ----------
        idf : IDF
            The IDF object containing the building energy model data, used to extract constructions, zones, 
            and related objects for further processing.
        
        Returns
        -------
        ZoneTemplate

        """
        constructionList: list[Construction] = []
        for obj in idf.idfobjects['Construction']:
            con = Construction.fromIDFConstructionList(idf, obj)
            if con:
                constructionList.append(con)
        zoneObject = MoosasSettings.fromIdfObject(idf.idfobjects['Zone'][0])

        # Extract zone objects
        objectHint = ['ZoneInfiltration:DesignFlowRate',
                      'ZoneVentilation:DesignFlowRate',
                      'ZoneVentilation:WindandStackOpenArea',
                      'OtherEquipment',
                      'ElectricEquipment',
                      'People',
                      'Lights',
                      'Sizing:Zone',
                      'DesignSpecification:OutdoorAir',
                      'DesignSpecification:ZoneAirDistribution',
                      'ZoneControl:Thermostat',
                      'ThermostatSetpoint:DualSetpoint',
                      'ZoneHVAC:EquipmentConnections',
                      'ZoneHVAC:EquipmentList',
                      'ZoneHVAC:IdealLoadsAirSystem',
                      'NodeList']
        objectList = {}
        found, unfound = [], []
        for objHint in objectHint:
            try:
                template = MoosasSettings.fromIdfObject(idf.idfobjects[objHint][0])
                # for key in template.params.keys():
                #     for spc in oriZoneList:
                #         if re.search(spc,str(template.params[key]),re.IGNORECASE) is not None:
                #             template.params[key] = ''
                objectList[objHint] = template

                found.append(objHint)
            except IndexError:
                unfound.append(objHint)
        print('foundObj:', found)
        print('unfoundObj:', unfound)

        # get schedules
        scheduleList = {}
        # locate schedule
        for objHint in objectList:
            scheduleList[objHint] = {}
            for field in objectList[objHint].params.keys():
                if re.search("Schedule_Name", field, re.IGNORECASE):
                    ref_obj = idf.idfobjects[objHint][0].get_referenced_object(field)
                    scheduleList[objHint][field] = MoosasSettings.fromIdfObject(ref_obj)
                    scheduleList[objHint][field].updateParams(**{"Name": ""})

        return cls(idf, zoneObject, objectList, constructionList, scheduleList)

    def getConstruction(self, _type, UFactor, SHGC=None):
        """
        Find or create a construction by type and U-factor.
        
        Parameters
        ----------
        self : object
            The instance of the class containing the construction list and IDF.
        _type : str
            The type of construction to find or create.
        UFactor : float or str
            The U-factor value for the construction; will be converted to float.
        SHGC : float, optional
            The Solar Heat Gain Coefficient (SHGC) for the new construction. Default is None.
        
        Returns
        -------
        Construction
            The existing construction with closest U-factor match or a newly created 
            and added Construction object.
        """
        UFactor = float(UFactor)
        constr = [construction for construction in self.constructionList if construction.type == _type]
        if len(constr) > 0:
            Ufc = [abs(construction.UFactor - UFactor) for construction in constr]
            return np.array(constr)[np.argmin(Ufc)]

        construction = Construction.create(_type=_type, UFactor=UFactor, SHGC=SHGC)
        construction.applyToIDF(self.idf)
        self.constructionList.append(construction)
        return construction

    def appliedToZone(self, zone: MoosasSpace):
        """
        Apply zone-specific settings and schedules to an IDF model.
        
        Parameters
        ----------
        zone : MoosasSpace
            A zone object containing settings such as work hours, temperature setpoints,
            occupancy, equipment, lighting, infiltration, ventilation, and other zone-level
            parameters. The settings are used to construct schedules and apply HVAC and load
            specifications.
        
        Returns
        -------
        ZoneTemplate
            This function return a new Zone object containing settings to the zone.
        """

        # rename and update Schedule
        for objHint in self.scheduleList:
            for field in self.scheduleList[objHint]:
                schName = zone.id + objHint + field
                self.scheduleList[objHint][field].updateParams(**{"Name": schName})
                self.objectList[objHint].updateParams(**{field: schName})

        # get zone property
        zoneTemplateArea, zoneTemplateVolume, zoneTemplateHeight = None, None, None
        if "Floor_Area" in self.zoneObject.params:
            zoneTemplateArea = self.zoneObject.params["Floor_Area"]
        if "Volume" in self.zoneObject.params:
            zoneTemplateVolume = self.zoneObject.params["Volume"]
        if "Ceiling_Height" in self.zoneObject.params:
            zoneTemplateHeight = self.zoneObject.params["Ceiling_Height"]
        if zoneTemplateArea and zoneTemplateVolume:
            zoneTemplateHeight = zoneTemplateVolume / zoneTemplateArea
        elif zoneTemplateArea and zoneTemplateHeight:
            zoneTemplateVolume = zoneTemplateArea * zoneTemplateHeight
        elif zoneTemplateVolume and zoneTemplateHeight:
            zoneTemplateArea = zoneTemplateVolume / zoneTemplateHeight
        else:
            raise ValueError("idf does not contain valid zone-specific settings: height/area/volume")

        zoneOutGlazingArea = (sum([gls.area for wall in zone.edge.wall if wall.isOuter for gls in
                                   wall.glazingElement]) + sum(
            [gls.area for face in zone.ceiling.face if face.isOuter for gls in face.glazingElement]))
        zoneOutWallArea = (sum([wall.area for wall in zone.edge.wall if wall.isOuter]) + sum(
            [face.area for face in zone.ceiling.face if face.isOuter]))

        # zone_infiltration
        if "ZoneInfiltration:DesignFlowRate" in self.objectList:
            if 'Design_Flow_Rate' in self.objectList["ZoneInfiltration:DesignFlowRate"].params:
                inftM3s = self.objectList["ZoneInfiltration:DesignFlowRate"]['Design_Flow_Rate']  # {m3/s}
                zone.settings['zone_infiltration'] = inftM3s / zoneTemplateVolume * 3600  # ac/h
            if 'Flow_Rate_per_Floor_Area' in self.objectList["ZoneInfiltration:DesignFlowRate"].params:
                inftM3sM2 = self.objectList["ZoneInfiltration:DesignFlowRate"]['Flow_Rate_per_Floor_Area']  # {m3/s-m2}
                zone.settings['zone_infiltration'] = inftM3sM2 / zoneTemplateHeight * 3600  # ac/h
            if 'Flow_Rate_per_Exterior_Surface_Area' in self.objectList["ZoneInfiltration:DesignFlowRate"].params:
                inftM3sM2 = self.objectList["ZoneInfiltration:DesignFlowRate"][
                    'Flow_Rate_per_Exterior_Surface_Area']  # {m3/s-m2}
                zone.settings[
                    'zone_infiltration'] = inftM3sM2 * zoneOutWallArea / zone.height / zone.area * 3600  # ac/h
        zone.settings['zone_infiltration'] = float(zone.settings['zone_infiltration'])

        # population
        if 'People' in self.objectList:
            if 'Number_of_People' in self.objectList["People"].params:
                zone.settings['zone_ppsm'] = self.objectList["People"]["Number_of_People"] / zoneTemplateArea
            if 'People_per_Floor_Area' in self.objectList["People"].params:
                zone.settings['zone_ppsm'] = self.objectList["People"]["People_per_Floor_Area"]
            if 'Floor_Area_per_Person' in self.objectList["People"].params:
                zone.settings['zone_ppsm'] = 1 / self.objectList["People"]["Floor_Area_per_Person"]
        zone.settings['zone_ppsm'] = float(zone.settings['zone_ppsm'])

        # equipment (equip elec)
        if 'ElectricEquipment' in self.objectList:
            if 'Design_Level' in self.objectList["ElectricEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["ElectricEquipment"][
                                                      'Design_Level'] / zoneTemplateArea
            if 'Watts_per_Floor_Area' in self.objectList["ElectricEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["ElectricEquipment"]["Watts_per_Floor_Area"]
            if 'Watts_per_Person' in self.objectList["ElectricEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["ElectricEquipment"]["Watts_per_Person"] * \
                                                  zone.settings['zone_ppsm']

        # equipment (equip heat)
        if 'OtherEquipment' in self.objectList:
            if 'Design_Level' in self.objectList["OtherEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["OtherEquipment"]['Design_Level'] / zoneTemplateArea
            if 'Watts_per_Floor_Area' in self.objectList["OtherEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["OtherEquipment"]["Watts_per_Floor_Area"]
            if 'Watts_per_Person' in self.objectList["OtherEquipment"].params:
                zone.settings['zone_equipment'] = self.objectList["OtherEquipment"]["Watts_per_Person"] * zone.settings[
                    'zone_ppsm']
        zone.settings['zone_equipment'] = float(zone.settings['zone_equipment'])

        # light

        if 'Lights' in self.objectList:
            if 'Lighting_Level' in self.objectList["Lights"].params:
                zone.settings['zone_lighting'] = self.objectList["Lights"]['Lighting_Level'] / zoneTemplateArea
            if 'Watts_per_Floor_Area' in self.objectList["Lights"].params:
                zone.settings['zone_lighting'] = self.objectList["Lights"]["Watts_per_Floor_Area"]
            if 'Watts_per_Person' in self.objectList["Lights"].params:
                zone.settings['zone_lighting'] = self.objectList["Lights"]["Watts_per_Person"] * zone.settings[
                    'zone_ppsm']
        zone.settings['zone_lighting'] = float(zone.settings['zone_lighting'])

        # ventilation Flow_Rate_per_Person
        if 'ZoneVentilation:DesignFlowRate' in self.objectList:
            if 'Design_Flow_Rate' in self.objectList["ZoneVentilation:DesignFlowRate"].params:
                inftM3s = self.objectList["ZoneVentilation:DesignFlowRate"]['Design_Flow_Rate']  # {m3/s}
                zone.settings['zone_pfav'] = inftM3s * 3600 / zone.settings['zone_ppsm'] / zone.area  # m3/h-pp
            if 'Flow_Rate_per_Floor_Area' in self.objectList["ZoneVentilation:DesignFlowRate"].params:
                inftM3sM2 = self.objectList["ZoneVentilation:DesignFlowRate"]['Flow_Rate_per_Floor_Area']  # {m3/s-m2}
                zone.settings['zone_pfav'] = inftM3sM2 * 3600 / zone.settings['zone_ppsm']  # m3/h-pp
            if 'Flow_Rate_per_Person' in self.objectList["ZoneVentilation:DesignFlowRate"].params:
                inftM3pp = self.objectList["ZoneVentilation:DesignFlowRate"]['Flow_Rate_per_Person']  # {m3/s-pp}
                zone.settings['zone_pfav'] = inftM3pp * 3600  # m3/h-pp
            if 'Air_Changes_per_Hour' in self.objectList["ZoneVentilation:DesignFlowRate"]:
                ach = self.objectList["ZoneVentilation:DesignFlowRate"]['Air_Changes_per_Hour']  # {ac/h}
                zone.settings['zone_pfav'] = ach * zoneTemplateVolume * 3600  # m3/h-pp

        if 'DesignSpecification:OutdoorAir' in self.objectList:
            if 'Outdoor_Air_Flow_per_Zone' in self.objectList['DesignSpecification:OutdoorAir'].params:
                inftM3s = self.objectList['DesignSpecification:OutdoorAir']['Outdoor_Air_Flow_per_Zone']  # {m3/s}
                zone.settings['zone_pfav'] = inftM3s * 3600 / zone.settings['zone_ppsm'] / zone.area  # m3/h-pp
            if 'Outdoor_Air_Flow_per_Zone_Floor_Area' in self.objectList['DesignSpecification:OutdoorAir'].params:
                inftM3sM2 = self.objectList['DesignSpecification:OutdoorAir'][
                    'Outdoor_Air_Flow_per_Zone_Floor_Area']  # {m3/s-m2}
                zone.settings['zone_pfav'] = inftM3sM2 * 3600 / zone.settings['zone_ppsm']  # m3/h-pp
            if 'Outdoor_Air_Flow_per_Person' in self.objectList['DesignSpecification:OutdoorAir'].params:
                inftM3pp = self.objectList['DesignSpecification:OutdoorAir']['Outdoor_Air_Flow_per_Person']  # {m3/s-pp}
                zone.settings['zone_pfav'] = inftM3pp * 3600  # m3/h-pp
            if 'Outdoor_Air_Flow_Air_Changes_per_Hour' in self.objectList['DesignSpecification:OutdoorAir'].params:
                ach = self.objectList['DesignSpecification:OutdoorAir'][
                    'Outdoor_Air_Flow_Air_Changes_per_Hour']  # {ac/h}
                zone.settings['zone_pfav'] = ach * zoneTemplateVolume * 3600  # m3/h-pp
        zone.settings['zone_pfav'] = float(zone.settings['zone_pfav'])

        params = {
            'ZoneInfiltration:DesignFlowRate':
                {'Name': zone.id + '_Infiltration', 'Zone_or_ZoneList_Name': zone.id,
                 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Design_Flow_Rate_Calculation_Method': "Flow/Zone",
                 'Design_Flow_Rate': zone.settings['zone_infiltration'] / 3600 * zone.area * zone.height},
            'ZoneVentilation:DesignFlowRate':
                {'Name': zone.id + "_Ventilation",  # Block2:Zone5 Ventilation
                 'Zone_or_ZoneList_Name': zone.id, 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 "Flow_Rate_per_Person": zone.settings['zone_pfav'] / 3600},
            'ZoneVentilation:WindandStackOpenArea':
                {'Name': zone.id + '_Opening', 'Zone_or_Space_Name': zone.id,
                 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Opening_Area': zoneOutGlazingArea * 0.6,
                 },
            'OtherEquipment':
                {'Name': zone.id + '_Equipment', 'Zone_or_ZoneList_Name': zone.id,
                 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Power_per_Zone_Floor_Area': zone.settings['zone_equipment'],
                 },
            'ElectricEquipment':
                {'Name': zone.id + '_Equipment', 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Watts_per_Zone_Floor_Area': zone.settings['zone_equipment'],
                 },
            'People':
                {'Name': zone.id + '_People', 'Zone_or_ZoneList_Name': zone.id,
                 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'People_per_Zone_Floor_Area': zone.settings['zone_ppsm'],
                 },
            'Lights':
                {'Name': zone.id + '_Lights', 'Zone_or_ZoneList_Name': zone.id,
                 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Watts_per_Zone_Floor_Area': zone.settings['zone_lighting'],
                 },
            'Sizing:Zone':
                {'Zone_or_ZoneList_Name': zone.id, 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Design_Specification_Outdoor_Air_Object_Name':
                     zone.id if 'DesignSpecification:OutdoorAir' in self.objectList else '',
                 'Design_Specification_Zone_Air_Distribution_Object_Name':'',
                     # zone.id if 'DesignSpecification:ZoneAirDistribution' in self.objectList else ''},
            'DesignSpecification:OutdoorAir':
                {'Name': zone.id,
                 'Outdoor_Air_Flow_per_Person': zone.settings['zone_pfav'] / 3600,
                 },
            'DesignSpecification:ZoneAirDistribution':
                {'Name': zone.id},
            'ZoneControl:Thermostat':
                {'Name': zone.id + "_Thermostat",
                 'Zone_or_ZoneList_Name': zone.id, 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
                 'Control_1_Name': zone.id + "_SetPoint",
                 },
            'ThermostatSetpoint:DualSetpoint':
                {'Name': zone.id + "_SetPoint",
                 },
            'ZoneHVAC:EquipmentConnections':
                {'Zone_Name': zone.id,
                 'Zone_Conditioning_Equipment_List_Name': zone.id + '_EquipmentList',
                 'Zone_Air_Inlet_Node_or_NodeList_Name': zone.id + ' Inlets',
                 'Zone_Air_Node_Name': 'Node ' + zone.id + ' Zone',
                 'Zone_Return_Air_Node_or_NodeList_Name': 'Node ' + zone.id + ' Out',
                 'Zone_Air_Exhaust_Node_or_NodeList_Name': ''
                 },
            'ZoneHVAC:EquipmentList':
                {'Name': zone.id + '_EquipmentList',
                 'Zone_Equipment_1_Name': zone.id + '_Ideal Loads Air'
                 },
            'ZoneHVAC:IdealLoadsAirSystem':
                {'Name': zone.id + '_Ideal Loads Air',
                 'Zone_Supply_Air_Node_Name': 'Node ' + zone.id + ' In',
                 'Zone_Exhaust_Air_Node_Name': '',
                 "Design_Specification_Outdoor_Air_Object_Name": '',
                 # zone.id if 'DesignSpecification:OutdoorAir' in self.objectList else '',
                 },
            'NodeList':
                {'Name': zone.id + " Inlets",
                 'Node_1_Name': "Node " + zone.id + " In"
                 }
        }

        for key in self.objectList:
            self.objectList[key].updateParams(**params[key])

        # block items:
        blockObjects = ['DesignSpecification:OutdoorAir', 'DesignSpecification:ZoneAirDistribution']
        for item in blockObjects:
            if item in self.objectList:
                del self.objectList[item]
                del self.scheduleList[item]

        # create zone objects
        self.zoneObject.updateParams(
            **{'Name': zone.id, 'Floor_Area': zone.area, 'Volume': zone.area * zone.height})

        return ZoneTemplate(self.idf, self.zoneObject, self.objectList, self.constructionList, self.scheduleList)

    def applyToIDF(self,idf=None):
        if idf == None:
            idf = self.idf
        # print(self.zoneObject)
        self.zoneObject.applyToIDF(idf)
        for objHint in self.scheduleList:
            for field in self.scheduleList[objHint]:
                self.scheduleList[objHint][field].applyToIDF(idf)
        for key in self.objectList:
            self.objectList[key].applyToIDF(idf)

    def __repr__(self):
        return str(self.idf)

    def __str__(self):
        return self.__repr__()


def createThermalSurface(idf: IDF, element: MoosasElement, surfaceType='Floor',
                         Construction_Name="Office_External_Wall",
                         Construction_Name_Window="Office_External_Window",
                         normal=None, encodeWindow=True):
    """
    Create a thermal surface in an EnergyPlus IDF file based on a MoosasElement.
    
    Parameters
    ----------
    idf : IDF
        The EnergyPlus Input Data File (IDF) object to which the thermal surface will be added.
    element : MoosasElement
        The building element (e.g., wall, floor) used to create the thermal surface. Must have valid space and geometric properties.
    surfaceType : str, optional
        Type of the surface, one of 'Floor', 'Wall', 'Ceiling', or 'Roof'. Default is 'Floor'.
    Construction_Name : str, optional
        Name of the construction used for the main surface. Default is "Office_External_Wall".
    Construction_Name_Window : str, optional
        Name of the construction used for any associated window surfaces. Default is "Office_External_Window".
    normal : Vector, optional
        Normal vector to define the orientation of the surface. If None, it is automatically determined based on geometry and surface type.
    
    Returns
    -------
    list
        A list of IDF objects (surfaces) created, including the main thermal surface and any associated window surfaces. Returns None if the element is invalid or belongs to a void space.
    """
    model = element.parent
    space0 = model.spaceIdDict[element.space[0]]
    if len(element.space) == 2:
        if space0.is_void():
            element.isOuter = True
            space0 = model.spaceIdDict[element.space[1]]
        if model.spaceIdDict[element.space[1]].is_void():
            element.isOuter = True
    elif len(element.space) == 1:
        if space0.is_void():
            return None
    else:
        return None
    if surfaceType == 'Floor':
        if element in space0.ceiling.face:
            surfaceType = 'Ceiling'

    ThermalSettings = MoosasSettings(default=FaceDefault)
    kwargs = {'Name': element.space[0] + '-' + element.Uid,
              "Zone_Name": element.space[0],
              "Surface_Type": surfaceType,
              "Construction_Name": Construction_Name}
    if element.isOuter:
        if surfaceType == 'Floor' and (element.parent.levelList.index(element.level) == 0):
            kwargs["Outside_Boundary_Condition"] = 'Ground'
            kwargs["Sun_Exposure"] = 'NoSun'
            kwargs["Wind_Exposure"] = 'NoWind'
            kwargs["View_Factor_to_Ground"] = '0'
        else:
            kwargs["Outside_Boundary_Condition"] = 'Outdoors'
            kwargs["Sun_Exposure"] = 'SunExposed'
            kwargs["Wind_Exposure"] = 'WindExposed'
            kwargs["View_Factor_to_Ground"] = 'AutoCalculate'
    else:
        kwargs["Outside_Boundary_Condition"] = 'Surface'
        kwargs["Outside_Boundary_Condition_Object"] = element.space[1] + '-' + element.Uid
        kwargs["Sun_Exposure"] = 'NoSun'
        kwargs["Wind_Exposure"] = 'NoWind'
        kwargs["View_Factor_to_Ground"] = '0'
    ThermalSettings.updateParams(**kwargs)
    if normal is None:
        if surfaceType == 'Floor':
            normal = Vector(0, 0, 1)
        elif surfaceType == 'Ceiling' or surfaceType == 'Roof':
            normal = Vector(0, 0, -1)
        else:
            try:
                normal = space0.edge.FactorOfWall[space0.edge.wall.index(element)]
            except IndexError:
                normal = element.normal
    encodeFace(ThermalSettings, element.representation(), normal)
    # create objects
    surface1 = ThermalSettings.applyToIDF(idf)
    faceObject = [surface1]
    if not element.isOuter:
        ThermalSettings.params["Name"] = element.space[1] + '-' + element.Uid
        ThermalSettings.params["Zone_Name"] = element.space[1]
        ThermalSettings.params["Outside_Boundary_Condition_Object"] = element.space[0] + '-' + element.Uid
        encodeFace(ThermalSettings, element.representation(), -normal)
        if surfaceType == 'Floor':
            surfaceType = 'Ceiling'
        elif surfaceType == 'Ceiling':
            surfaceType = 'Floor'
        ThermalSettings.params["Surface_Type"] = surfaceType
        surface2 = ThermalSettings.applyToIDF(idf)
        faceObject.append(surface2)
    if encodeWindow:
        for gls in element.glazingElement:
            faceObject += createWindowSurface(idf, gls, element, Construction_Name_Window, normal=normal)
    return faceObject


def encodeFace(obj: MoosasSettings, polygon: pygeos.Geometry, normal: Vector):
    """
    Encode face geometry into a given settings object by storing vertex coordinates.
    
    Parameters
    ----------
    obj : MoosasSettings
        The settings object where face parameters will be stored.
    polygon : pygeos.Geometry
        A polygonal geometry whose coordinates define the face.
    normal : Vector
        A vector used to determine the orientation of the face; 
        if the dot product with the face normal is negative, vertex order is reversed.
    
    Returns
    -------
    None
        This function modifies the `obj` in place and does not return a value.
    """
    coordinates = pygeos.get_coordinates(polygon, include_z=True)
    if Vector.dot(faceNormal(polygon), normal) < 0:
        coordinates = coordinates[::-1]
    obj.params['Number_of_Vertices'] = len(coordinates) - 1
    for i, point in enumerate(coordinates[:-1]):
        obj.params[f'Vertex_{i + 1}_Xcoordinate'] = np.round(point[0], 2)
        obj.params[f'Vertex_{i + 1}_Ycoordinate'] = np.round(point[1], 2)
        obj.params[f'Vertex_{i + 1}_Zcoordinate'] = np.round(point[2], 2)


def createWindowSurface(idf: IDF, element: MoosasElement, parentElement: MoosasElement,
                        Construction_Name="Office_External_Wall",
                        normal=None):
    """
    Create window surface(s) in an EnergyPlus IDF file based on element geometry and thermal settings.
    
    Parameters
    ----------
    idf : IDF
        The EnergyPlus Input Data File (IDF) object to which the surface will be added.
    element : MoosasElement
        The element representing the window geometry to be encoded.
    parentElement : MoosasElement
        The parent building element (e.g., wall) that hosts the window; used to derive space and boundary information.
    Construction_Name : str, optional
        The name of the construction to be assigned to the window surface. Default is "Office_External_Wall".
    normal : array-like, optional
        The normal vector to the surface face; used during geometry encoding. If not provided, inferred from geometry.
    
    Returns
    -------
    list of Surface
        A list containing one or two Surface objects added to the IDF:
        - One surface for outer (exterior) parent elements.
        - Two surfaces (with opposite orientations and linked boundary conditions) for inner (interior) parent elements.
    """
    faceObjects = []
    for face in mixItemListToList(element.face):
        for triFace in triangulate2dFace(face):
            kwargs = {'Name': parentElement.space[0] + '-' + parentElement.Uid + '-' + element.Uid,
                      "Building_Surface_Name": parentElement.space[0] + '-' + parentElement.Uid,
                      "Construction_Name": Construction_Name}
            ThermalSettings = MoosasSettings(default=WindowDefault, **kwargs)
            encodeFace(ThermalSettings, triFace, normal)

            if not parentElement.isOuter:
                ThermalSettings.params["Outside_Boundary_Condition_Object"] = parentElement.space[
                                                                                  1] + '-' + parentElement.Uid + '-' + element.Uid
                surface1 = ThermalSettings.applyToIDF(idf)
                kwargs = {'Name': parentElement.space[1] + '-' + parentElement.Uid + '-' + element.Uid,
                          "Building_Surface_Name": parentElement.space[1] + '-' + parentElement.Uid,
                          "Outside_Boundary_Condition_Object": parentElement.space[
                                                                   0] + '-' + parentElement.Uid + '-' + element.Uid,
                          "View_Factor_to_Ground": 0}
                ThermalSettings.updateParams(**kwargs)
                encodeFace(ThermalSettings, element.representation(), -normal)
                surface2 = ThermalSettings.applyToIDF(idf)
                faceObjects+= [surface1, surface2]
            else:
                surface1 = ThermalSettings.applyToIDF(idf)
                faceObjects+= [surface1]
    return faceObjects