from ..geometry.element import MoosasSpace, MoosasElement
from ..geometry.geos import faceNormal, Vector
from .settings import *
from .construction import Construction
from .schedule import dailySchedule, schType, schDesignDay,typeLimitSettings
from eppy.modeleditor import IDF
from ..utils import pygeos, GeometryError, FileError,generate_code
import re

class ZoneTemplate():
    def __init__(self, idf: IDF):
        self.idf = idf
        self.constructionList: list[Construction] = []
        for obj in idf.idfobjects['Construction']:
            con = Construction.fromIDFConstructionList(idf, obj)
            if con:
                self.constructionList.append(con)
        self.zoneObject = MoosasSettings.fromIdfObject(idf.idfobjects['Zone'][0])
        oriZoneList = [idfobj['Name'] for idfobj in idf.idfobjects['Zone']]
        self.objectHint = ['ZoneInfiltration:DesignFlowRate',
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
        self.objectList: list[MoosasSettings] = []
        found,unfound = [],[]
        for objHint in self.objectHint:
            try:
                template = MoosasSettings.fromIdfObject(idf.idfobjects[objHint][0])
                for key in template.params.keys():
                    for spc in oriZoneList:
                        if re.search(spc,str(template.params[key]),re.IGNORECASE) is not None:
                            template.params[key] = ''
                self.objectList.append(template)

                found.append(objHint)
            except IndexError:
                unfound.append(objHint)
                self.objectList.append(None)
        print('foundObj:', found)
        print('unfoundObj:', unfound)
        typeLimitsName = [idfobj['Name'] for idfobj in idf.idfobjects['ScheduleTypeLimits']]
        for typeLimit in typeLimitSettings:
            if typeLimit.params['Name'] not in typeLimitsName:
                typeLimit.applyToIDF(idf)

    def getConstruction(self, _type, UFactor, SHGC=None):
        UFactor = float(UFactor)
        constr = [construction for construction in self.constructionList if construction.type == _type]
        if len(constr)>0:
            Ufc = [abs(construction.UFactor - UFactor) for construction in constr]
            return np.array(constr)[np.argmin(Ufc)]

        construction = Construction.create(_type=_type, UFactor=UFactor, SHGC=SHGC)
        construction.applyToIDF(self.idf)
        self.constructionList.append(construction)
        return construction

    def appliedToZone(self, zone: MoosasSpace):
        # construct schedule
        for idx in zone.settings.keys():
            try:
                zone.settings[idx] = float(zone.settings[idx])
            except:
                pass
        routine = ([0 for _ in range(int(zone.settings['zone_work_start']))] +
                   [1.0 for _ in range(int(zone.settings['zone_work_start']), int(zone.settings['zone_work_end']))] +
                   [0 for _ in range(int(zone.settings['zone_work_end']), 24)])

        heatingSchedule = dailySchedule({schDesignDay.AllDays: [zone.settings['zone_h_temp']] * 24},
                                        _type=schType.Temperature)
        coolingSchedule = dailySchedule({schDesignDay.AllDays: [zone.settings['zone_c_temp']] * 24},
                                        _type=schType.Temperature)
        pHeatSchedule = dailySchedule({schDesignDay.AllDays: [zone.settings['zone_popheat']] * 24},
                                      _type=schType.AnyNumber)
        ThermostatSchedule = dailySchedule({schDesignDay.AllDays: [4] * 24},
                                      _type=schType.AnyNumber)
        if re.search('Office',zone.settings['zone_template'],re.IGNORECASE) is not None:
            OnSchedule = dailySchedule(
                {schDesignDay.Weekends: [0] * 24, schDesignDay.Holidays: [0] * 24, schDesignDay.AllOtherDays: routine}
            ,_name ='on_'+generate_code(4)
            )
            OccSchedule = dailySchedule(
                {schDesignDay.Weekends: [0] * 24, schDesignDay.Holidays: [0] * 24, schDesignDay.AllOtherDays: routine}
                , _type=schType.Fraction
                , _name='Occ_' + generate_code(4)
            )
        else:
            OnSchedule = dailySchedule({schDesignDay.AllDays: routine})
            OccSchedule = dailySchedule({schDesignDay.AllDays: routine}, _type=schType.Fraction)
        OnSchedule.applyToIDF(self.idf)
        OccSchedule.applyToIDF(self.idf)
        coolingSchedule.applyToIDF(self.idf)
        heatingSchedule.applyToIDF(self.idf)
        pHeatSchedule.applyToIDF(self.idf)
        ThermostatSchedule.applyToIDF(self.idf)
        self.zoneObject.updateParams(
            **{'Name': zone.id, 'Floor_Area': zone.area, 'Volume': zone.area * zone.height}).applyToIDF(self.idf)
        params = [
            # 'ZoneInfiltration:DesignFlowRate',
            {'Name': zone.id + '_Infiltration', 'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Design_Flow_Rate': zone.settings['zone_infiltration'] / 3600 * zone.area * zone.height},
            # 'ZoneVentilation:DesignFlowRate',
            {'Name': zone.id + "_Ventilation",  # Block2:Zone5 Ventilation
             'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             "Schedule_Name": OnSchedule.params['Name'],
             "Flow_Rate_per_Person": zone.settings['zone_pfav'] / 3600 },
            # 'ZoneVentilation:WindandStackOpenArea',
            {'Name': zone.id + '_Opening', 'Zone_or_Space_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Opening_Area': (sum([gls.area for wall in zone.edge.wall if wall.isOuter for gls in wall.glazingElement]) + sum([gls.area for face in zone.ceiling.face if face.isOuter for gls in face.glazingElement]))*0.6,
             },
            # 'OtherEquipment',
            {'Name': zone.id + '_Equipment', 'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Power_per_Zone_Floor_Area': zone.settings['zone_equipment'],
             'Schedule_Name': OccSchedule.params['Name']
             },
            # 'ElectricEquipment',
            {'Name': zone.id + '_Equipment', 'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Watts_per_Zone_Floor_Area': zone.settings['zone_equipment'],
             'Schedule_Name': OccSchedule.params['Name']
             },
            # 'People',
            {'Name': zone.id + '_People', 'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'People_per_Zone_Floor_Area': zone.settings['zone_ppsm'],
             'Number_of_People_Schedule_Name': OccSchedule.params['Name'],
             'Activity_level_schedule_Name': pHeatSchedule.params['Name']
             },
            # 'Lights',
            {'Name': zone.id + '_Lights', 'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Watts_per_Zone_Floor_Area': zone.settings['zone_lighting'],
             'Schedule_Name': OnSchedule.params['Name']
             },
            # 'Sizing:Zone',
            {'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Design_Specification_Outdoor_Air_Object_Name':
                 zone.id if self.objectList[self.objectHint.index('DesignSpecification:OutdoorAir')] else '',
             'Design_Specification_Zone_Air_Distribution_Object_Name':
                 zone.id if self.objectList[self.objectHint.index('DesignSpecification:ZoneAirDistribution')] else ''},
            # 'DesignSpecification:OutdoorAir',
            {'Name': zone.id,
             'Outdoor_Air_Flow_per_Person': zone.settings['zone_pfav'] / 3600,
             'Outdoor_Air_Schedule_Name': OnSchedule.params['Name']
             },
            # 'DesignSpecification:ZoneAirDistribution',
            {'Name': zone.id},
            # 'ZoneControl:Thermostat',
            {'Name': zone.id + "_Thermostat",
             'Zone_or_ZoneList_Name': zone.id,'Zone_or_ZoneList_or_Space_or_SpaceList_Name': zone.id,
             'Control_1_Name': zone.id + "_SetPoint",
             'Control_Type_Schedule_Name':ThermostatSchedule.params['Name']
             },
            # 'ThermostatSetpoint:DualSetpoint',
            {'Name': zone.id + "_SetPoint",
             'Heating_Setpoint_Temperature_Schedule_Name': heatingSchedule.params['Name'],
             'Cooling_Setpoint_Temperature_Schedule_Name': coolingSchedule.params['Name']
             },
            # 'ZoneHVAC:EquipmentConnections',
            {'Zone_Name': zone.id,
             'Zone_Conditioning_Equipment_List_Name': zone.id + '_EquipmentList',
             'Zone_Air_Inlet_Node_or_NodeList_Name': zone.id + ' Inlets',
             'Zone_Air_Node_Name': 'Node ' + zone.id + ' Zone',
             'Zone_Return_Air_Node_or_NodeList_Name': 'Node ' + zone.id + ' Out',
             'Zone_Air_Exhaust_Node_or_NodeList_Name':''
             },
            # 'ZoneHVAC:EquipmentList',
            {'Name': zone.id + '_EquipmentList',
             'Zone_Equipment_1_Name': zone.id + '_Ideal Loads Air'
             },
            # 'ZoneHVAC:IdealLoadsAirSystem',
            {'Name': zone.id + '_Ideal Loads Air',
             'Availability_Schedule_Name': OnSchedule.params['Name'],
             'Zone_Supply_Air_Node_Name': 'Node ' + zone.id + ' In',
             'Zone_Exhaust_Air_Node_Name':'',
             'Heating_Availability_Schedule_Name': OnSchedule.params['Name'],
             'Cooling_Availability_Schedule_Name': OnSchedule.params['Name']
             },
            # 'NodeList'
            {'Name': zone.id + " Inlets",
             'Node_1_Name': "Node " + zone.id + " In"
             }
        ]
        for i in range(len(self.objectList)):
            if self.objectList[i]:
                self.objectList[i].updateParams(**params[i])
        if self.objectList[self.objectHint.index('DesignSpecification:OutdoorAir')]:
            self.objectList[self.objectHint.index('ZoneHVAC:IdealLoadsAirSystem')].updateParams(
                Design_Specification_Outdoor_Air_Object_Name=zone.id)
        for i in range(len(self.objectList)):
            if self.objectList[i]:
                self.objectList[i].applyToIDF(self.idf)


def createThermalSurface(idf: IDF, element: MoosasElement, surfaceType='Floor',
                         Construction_Name="Office_External_Wall",
                         Construction_Name_Window="Office_External_Window",
                         normal=None):
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
    for gls in element.glazingElement:
        faceObject += createWindowSurface(idf, gls, element, Construction_Name_Window, normal=normal)
    return faceObject


def encodeFace(obj: MoosasSettings, polygon: pygeos.Geometry, normal: Vector):
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
    kwargs = {'Name': parentElement.space[0] + '-' + parentElement.Uid + '-' + element.Uid,
              "Building_Surface_Name": parentElement.space[0] + '-' + parentElement.Uid,
              "Construction_Name": Construction_Name}
    ThermalSettings = MoosasSettings(default=WindowDefault, **kwargs)
    encodeFace(ThermalSettings, element.representation(), normal)

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
        return [surface1, surface2]
    else:
        surface1 = ThermalSettings.applyToIDF(idf)
        return [surface1]
