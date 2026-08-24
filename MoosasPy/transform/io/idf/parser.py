import re
import os

from eppy.modeleditor import IDF

from .construction import Construction
from .model import *
from ...geometry.element import MoosasSpace
from ....utils import path


class ZoneTemplate():
    __slots__ = ("idf", "zoneObject", "objectList", "constructionList", "scheduleList")
    FALLBACK_ZONE_HEIGHT = 3.5

    def __init__(self, idf, zoneObject, objectList, constructionList, scheduleList):
        self.idf = idf
        self.zoneObject = copy.deepcopy(zoneObject)
        self.objectList = copy.deepcopy(objectList)
        self.constructionList = copy.deepcopy(constructionList)
        self.scheduleList = copy.deepcopy(scheduleList)

    @staticmethod
    def _match_zone_related_object(idfObject, zoneName: str):
        """
        Check whether an IDF object is related to a target zone by common zone-name fields.
        """
        zoneFields = [
            'Zone_or_ZoneList_Name',
            'Zone_or_ZoneList_or_Space_or_SpaceList_Name',
            'Zone_or_Space_Name',
            'Zone_Name',
            'Name',
        ]
        for field in zoneFields:
            if field in idfObject.objls:
                fieldValue = str(idfObject[field]).strip()
                if fieldValue == zoneName:
                    return True
        return False

    def isEmpty(self):
        """
        Return whether this template carries no valid zone geometry settings.
        """
        if not isinstance(self.zoneObject, MoosasSettings):
            return True
        return ('Floor_Area' not in self.zoneObject.params) and ('Volume' not in self.zoneObject.params)

    @staticmethod
    def _as_positive_float(value):
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        return numeric if numeric > 0 else None

    def _infer_zone_geometry(self):
        zone_name = str(self.zoneObject.params.get("Name", "")).strip()
        if zone_name == "":
            return None, None, None

        area = None
        volume = self._as_positive_float(self.zoneObject.params.get("Volume"))
        height = self._as_positive_float(self.zoneObject.params.get("Ceiling_Height"))

        z_values = []
        for surface in self.idf.idfobjects['BuildingSurface:Detailed']:
            try:
                if str(surface['Zone_Name']).strip() != zone_name:
                    continue
            except Exception:
                continue

            for idx in range(1, 256):
                x_field = f'Vertex_{idx}_Xcoordinate'
                z_field = f'Vertex_{idx}_Zcoordinate'
                if x_field not in surface.objls or z_field not in surface.objls:
                    break
                z_val = surface[z_field]
                if z_val == '':
                    break
                try:
                    z_values.append(float(z_val))
                except (TypeError, ValueError):
                    continue

        if height is None and len(z_values) >= 2:
            inferred_height = max(z_values) - min(z_values)
            if inferred_height > 0:
                height = inferred_height

        if area is not None and volume is not None and height is None:
            height = volume / area
        elif area is not None and height is not None and volume is None:
            volume = area * height
        elif volume is not None and height is not None and area is None:
            area = volume / height

        return area, volume, height

    @classmethod
    def fromIDF(cls, idf: IDF, zoneName: str = ""):
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
        templateZone = None
        for zoneObj in idf.idfobjects['Zone']:
            if str(zoneObj['Name']).strip() == zoneName:
                templateZone = zoneObj
                break

        if templateZone is None:
            print(f"******Warning: no Zone found with Name='{zoneName}' in template IDF")
            return cls(idf, MoosasSettings({}), {}, constructionList, {})

        zoneObject = MoosasSettings.fromIdfObject(templateZone)

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
        sourceObjectList = {}
        found, unfound = [], []
        for objHint in objectHint:
            selectedObj = None
            for refObj in idf.idfobjects[objHint]:
                if cls._match_zone_related_object(refObj, zoneName):
                    selectedObj = refObj
                    break

            if selectedObj is None and len(idf.idfobjects[objHint]) > 0:
                selectedObj = idf.idfobjects[objHint][0]

            if selectedObj is None:
                unfound.append(objHint)
                continue

            template = MoosasSettings.fromIdfObject(selectedObj)
            objectList[objHint] = template
            sourceObjectList[objHint] = selectedObj
            found.append(objHint)
        print('foundObj:', found)
        print('unfoundObj:', unfound)

        # get schedules
        scheduleList = {}
        # locate schedule
        for objHint in objectList:
            scheduleList[objHint] = {}
            for field in objectList[objHint].params.keys():
                if re.search("Schedule_Name", field, re.IGNORECASE):
                    try:
                        ref_obj = sourceObjectList[objHint].get_referenced_object(field)
                    except Exception:
                        ref_obj = None
                    if ref_obj is None:
                        continue
                    scheduleList[objHint][field] = MoosasSettings.fromIdfObject(ref_obj)
                    scheduleList[objHint][field].updateParams(**{"Name": ""})

        return cls(idf, zoneObject, objectList, constructionList, scheduleList)

    @classmethod
    def createFromZone(cls, zone: MoosasSpace, idfTemplatePath=None, baseTemplate=None, zoneName: str = ""):
        """
        Build a ZoneTemplate by reversing zone settings back to IDF template objects.
        """
        if baseTemplate is None:
            idd = os.path.join(path.dataBaseDir, "Energy+.idd")
            if os.path.isfile(idd):
                try:
                    IDF.setiddname(idd)
                except Exception:
                    pass

            if idfTemplatePath is None:
                idfTemplatePath = os.path.join(path.dataBaseDir, "in.idf")
            baseIDF = IDF(idfTemplatePath)
            baseTemplate = cls.fromIDF(baseIDF, zoneName=zoneName)

        template = cls(baseTemplate.idf,
                       baseTemplate.zoneObject,
                       baseTemplate.objectList,
                       baseTemplate.constructionList,
                       baseTemplate.scheduleList)

        if template.isEmpty():
            return template

        zoneArea = max(float(zone.area), 1e-6)
        zoneHeight = max(float(zone.height), 1e-6)
        zoneVolume = zoneArea * zoneHeight

        def _setting(key, fallback):
            if key in zone.settings:
                try:
                    return float(zone.settings[key])
                except (TypeError, ValueError):
                    return fallback
            return fallback

        zoneInfiltration = _setting('zone_infiltration', SpaceDefault['zone_infiltration'])
        zonePPSM = _setting('zone_ppsm', SpaceDefault['zone_ppsm'])
        zoneEquipment = _setting('zone_equipment', SpaceDefault['zone_equipment'])
        zoneLighting = _setting('zone_lighting', SpaceDefault['zone_lighting'])
        zonePFAV = _setting('zone_pfav', SpaceDefault['zone_pfav'])

        template.zoneObject.updateParams(**{
            'Name': '',
            'Floor_Area': zoneArea,
            'Volume': zoneVolume,
            'Ceiling_Height': zoneHeight,
        })

        if 'ZoneInfiltration:DesignFlowRate' in template.objectList:
            template.objectList['ZoneInfiltration:DesignFlowRate'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Design_Flow_Rate_Calculation_Method': 'Flow/Zone',
                'Design_Flow_Rate': zoneInfiltration / 3600.0 * zoneVolume,
            })

        if 'ZoneVentilation:DesignFlowRate' in template.objectList:
            template.objectList['ZoneVentilation:DesignFlowRate'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Flow_Rate_per_Person': zonePFAV / 3600.0,
            })

        if 'ZoneVentilation:WindandStackOpenArea' in template.objectList:
            template.objectList['ZoneVentilation:WindandStackOpenArea'].updateParams(**{
                'Name': '',
                'Zone_or_Space_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
            })

        if 'OtherEquipment' in template.objectList:
            template.objectList['OtherEquipment'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Power_per_Zone_Floor_Area': zoneEquipment,
                'Watts_per_Floor_Area': zoneEquipment,
            })

        if 'ElectricEquipment' in template.objectList:
            template.objectList['ElectricEquipment'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Watts_per_Zone_Floor_Area': zoneEquipment,
                'Watts_per_Floor_Area': zoneEquipment,
            })

        if 'People' in template.objectList:
            template.objectList['People'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'People_per_Zone_Floor_Area': zonePPSM,
                'People_per_Floor_Area': zonePPSM,
            })

        if 'Lights' in template.objectList:
            template.objectList['Lights'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Watts_per_Zone_Floor_Area': zoneLighting,
                'Watts_per_Floor_Area': zoneLighting,
            })

        if 'Sizing:Zone' in template.objectList:
            template.objectList['Sizing:Zone'].updateParams(**{
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Design_Specification_Outdoor_Air_Object_Name': '',
                'Design_Specification_Zone_Air_Distribution_Object_Name': '',
            })

        if 'DesignSpecification:OutdoorAir' in template.objectList:
            template.objectList['DesignSpecification:OutdoorAir'].updateParams(**{
                'Name': '',
                'Outdoor_Air_Flow_per_Person': zonePFAV / 3600.0,
            })

        if 'DesignSpecification:ZoneAirDistribution' in template.objectList:
            template.objectList['DesignSpecification:ZoneAirDistribution'].updateParams(**{'Name': ''})

        if 'ZoneControl:Thermostat' in template.objectList:
            template.objectList['ZoneControl:Thermostat'].updateParams(**{
                'Name': '',
                'Zone_or_ZoneList_Name': '',
                'Zone_or_ZoneList_or_Space_or_SpaceList_Name': '',
                'Control_1_Name': '',
            })

        if 'ThermostatSetpoint:DualSetpoint' in template.objectList:
            template.objectList['ThermostatSetpoint:DualSetpoint'].updateParams(**{'Name': ''})

        if 'ZoneHVAC:EquipmentConnections' in template.objectList:
            template.objectList['ZoneHVAC:EquipmentConnections'].updateParams(**{
                'Zone_Name': '',
                'Zone_Conditioning_Equipment_List_Name': '',
                'Zone_Air_Inlet_Node_or_NodeList_Name': '',
                'Zone_Air_Node_Name': '',
                'Zone_Return_Air_Node_or_NodeList_Name': '',
                'Zone_Air_Exhaust_Node_or_NodeList_Name': '',
            })

        if 'ZoneHVAC:EquipmentList' in template.objectList:
            template.objectList['ZoneHVAC:EquipmentList'].updateParams(**{
                'Name': '',
                'Zone_Equipment_1_Name': '',
            })

        if 'ZoneHVAC:IdealLoadsAirSystem' in template.objectList:
            template.objectList['ZoneHVAC:IdealLoadsAirSystem'].updateParams(**{
                'Name': '',
                'Zone_Supply_Air_Node_Name': '',
                'Zone_Exhaust_Air_Node_Name': '',
                'Design_Specification_Outdoor_Air_Object_Name': '',
            })

        if 'NodeList' in template.objectList:
            template.objectList['NodeList'].updateParams(**{
                'Name': '',
                'Node_1_Name': '',
            })

        for objHint in template.scheduleList:
            for field in template.scheduleList[objHint]:
                template.scheduleList[objHint][field].updateParams(**{'Name': ''})

        return template

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
        zoneTemplateArea = self._as_positive_float(self.zoneObject.params.get("Floor_Area"))
        zoneTemplateVolume = self._as_positive_float(self.zoneObject.params.get("Volume"))
        zoneTemplateHeight = self._as_positive_float(self.zoneObject.params.get("Ceiling_Height"))
        if zoneTemplateArea and zoneTemplateVolume:
            zoneTemplateHeight = zoneTemplateVolume / zoneTemplateArea
        elif zoneTemplateArea and zoneTemplateHeight:
            zoneTemplateVolume = zoneTemplateArea * zoneTemplateHeight
        elif zoneTemplateVolume and zoneTemplateHeight:
            zoneTemplateArea = zoneTemplateVolume / zoneTemplateHeight
        else:
            zoneTemplateArea, zoneTemplateVolume, zoneTemplateHeight = self._infer_zone_geometry()
            if zoneTemplateVolume and not zoneTemplateArea:
                zoneTemplateHeight = self.FALLBACK_ZONE_HEIGHT
                zoneTemplateArea = zoneTemplateVolume / zoneTemplateHeight
                print(
                    f"******Warning: fallback zone geometry activated for '{zone.id}'; "
                    f"using height={zoneTemplateHeight}m to infer floor area from template volume"
                )
            if not (zoneTemplateArea and zoneTemplateVolume and zoneTemplateHeight):
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
                 'Design_Specification_Zone_Air_Distribution_Object_Name': ''
                 },
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
                 "Design_Specification_Outdoor_Air_Object_Name":
                 zone.id if 'DesignSpecification:OutdoorAir' in self.objectList else '',
                 },
            'NodeList':
                {'Name': zone.id + " Inlets",
                 'Node_1_Name': "Node " + zone.id + " In"
                 }
        }

        for key in self.objectList:
            self.objectList[key].updateParams(**params[key])

        # block items:
        # blockObjects = ['DesignSpecification:OutdoorAir', 'DesignSpecification:ZoneAirDistribution']
        # for item in blockObjects:
        #     if item in self.objectList:
        #         del self.objectList[item]
        #         del self.scheduleList[item]

        # create zone objects
        self.zoneObject.updateParams(
            **{'Name': zone.id, 'Floor_Area': zone.area, 'Volume': zone.area * zone.height})

        return ZoneTemplate(self.idf, self.zoneObject, self.objectList, self.constructionList, self.scheduleList)

    def applyToIDF(self, idf=None):
        if idf == None:
            idf = self.idf
        # print(self.zoneObject)
        self.zoneObject.applyToIDF(idf)
        for objHint in self.scheduleList:
            for field in self.scheduleList[objHint]:
                self.scheduleList[objHint][field].applyToIDF(idf)
        for key in self.objectList:
            self.objectList[key].applyToIDF(idf)
