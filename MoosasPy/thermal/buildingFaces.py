from ..geometry.element import MoosasElement
from ..utils import shapely,GeometryError
from .settings import MoosasSettings, FaceDefault, WindowDefault
from eppy.modeleditor import IDF


def createThermalSurface(idf: IDF, element: MoosasElement, surfaceType='Floor',
                         Construction_Name="Office_External_Wall",
                         Construction_Name_Window="Office_External_Window"):
    """
    Create thermal surface(s) in an IDF model based on a MoosasElement.
    
    Parameters
    ----------
    idf : IDF
        The EnergyPlus IDF object to which the thermal surface will be added.
    element : MoosasElement
        The geometric and spatial element used to define the thermal surface.
    surfaceType : str, optional
        Type of the surface (e.g., 'Floor', 'Wall', 'Roof'). Default is 'Floor'.
    Construction_Name : str, optional
        Name of the construction used for the main surface. Default is "Office_External_Wall".
    Construction_Name_Window : str, optional
        Name of the construction used for window surfaces. Default is "Office_External_Window".
    
    Returns
    -------
    list
        A list of IDF objects representing the created thermal surfaces, including interior paired surfaces and any associated window surfaces.
    """
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
    coordinates = shapely.get_coordinates(element.representation(), include_z=True)
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
    """
    Create one or two FenestrationSurface:Detailed objects in an IDF file based on a given element and its parent.
    
    Parameters
    ----------
    idf : IDF
        The EnergyPlus IDF object to which the new fenestration surface(s) will be added.
    element : MoosasElement
        The Moosas element representing the window or fenestration geometry.
    parentElement : MoosasElement
        The parent Moosas element, typically a wall, that hosts the fenestration element.
    Construction_Name : str, optional
        The name of the construction used for the fenestration surface. Default is "Office_External_Wall".
    
    Returns
    -------
    list
        A list containing one or two FenestrationSurface:Detailed objects created in the IDF. 
        Returns two surfaces if the parent element is internal (not outer), otherwise returns one.
    """

    kwargs = {'Name': parentElement.space[0] + '-' + parentElement.Uid + '-' + element.Uid,
              "Building_Surface_Name": parentElement.space[0] + '-' + parentElement.Uid,
              "Construction_Name": Construction_Name}
    ThermalSettings = MoosasSettings(default=WindowDefault,**kwargs)
    coordinates = shapely.get_coordinates(element.representation(), include_z=True)
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