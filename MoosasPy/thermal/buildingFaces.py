from ..geometry.element import MoosasElement
from ..utils import pygeos,GeometryError
from .settings import MoosasSettings, FaceDefault, WindowDefault
from eppy.modeleditor import IDF


def createThermalSurface(idf: IDF, element: MoosasElement, surfaceType='Floor',
                         Construction_Name="Office_External_Wall",
                         Construction_Name_Window="Office_External_Window"):
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
    coordinates = pygeos.get_coordinates(element.representation(), include_z=True)
    ThermalSettings.params['Number_of_Vertices'] = len(coordinates)
    for i, point in enumerate(coordinates):
        ThermalSettings.params[f'Vertex_{i}_Xcoordinate'] = point[0]
        ThermalSettings.params[f'Vertex_{i}_Ycoordinate'] = point[1]
        ThermalSettings.params[f'Vertex_{i}_Zcoordinate'] = point[2]
    # create objects
    surface1 = idf.newidfobject('BuildingSurface:Detailed')
    ThermalSettings.applyToIDF(surface1)
    faceObject = [surface1]
    if not element.isOuter:
        surface2 = idf.newidfobject('BuildingSurface:Detailed')
        ThermalSettings.params["Name"] = element.space[1] + '-' + element.Uid
        ThermalSettings.params["Zone_Name"] = element.space[1]
        ThermalSettings.params["Outside_Boundary_Condition_Object"] = element.space[0] + '-' + element.Uid
        ThermalSettings.applyToIDF(surface2)
        faceObject.append(surface2)
    for gls in element.glazingElement:
        faceObject+=createWindowSurface(idf,gls,element,Construction_Name_Window)
    return faceObject


def createWindowSurface(idf: IDF, element: MoosasElement, parentElement: MoosasElement,
                        Construction_Name="Office_External_Wall"):

    kwargs = {'Name': parentElement.space[0] + '-' + parentElement.Uid + '-' + element.Uid,
              "Building_Surface_Name": parentElement.space[0] + '-' + parentElement.Uid,
              "Construction_Name": Construction_Name}
    ThermalSettings = MoosasSettings(default=WindowDefault,**kwargs)
    coordinates = pygeos.get_coordinates(element.representation(), include_z=True)
    if len(coordinates) >4:
        raise GeometryError(element.representation(),"idf FenestrationSurface:Detailed do not allow over 4 coordinates")
    ThermalSettings.params['Number_of_Vertices'] = len(coordinates)
    for i, point in enumerate(coordinates):
        ThermalSettings.params[f'Vertex_{i}_Xcoordinate'] = point[0]
        ThermalSettings.params[f'Vertex_{i}_Ycoordinate'] = point[1]
        ThermalSettings.params[f'Vertex_{i}_Zcoordinate'] = point[2]
    surface1 = idf.newidfobject('FenestrationSurface:Detailed')
    ThermalSettings.applyToIDF(surface1)
    if not parentElement.isOuter:
        kwargs = {'Name': parentElement.space[1] + '-' + parentElement.Uid + '-' + element.Uid,
                  "Building_Surface_Name": parentElement.space[1] + '-' + parentElement.Uid,
                  "View_Factor_to_Ground": 0}
        ThermalSettings.updateParams(**kwargs)
        surface2 = idf.newidfobject('FenestrationSurface:Detailed')
        ThermalSettings.applyToIDF(surface2)
        return [surface1, surface2]
    else:
        return [surface1]