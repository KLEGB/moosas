# MOOSAS+
Moosas is a SketchUp plugin program working on **building performance anaylsis 
and optimization for the building sketch design stage**. 
Most of the detail settings and geometrical representations transforming, 
which are always confusing to architects, will be solved behind the interface. 
The core of MOOSAS is built on ruby, the interface is built on javascript & html, 
and the extensions are built on python and golong including *.epw transformation, 
*.geo\*.obj transformation, wind pressure prediction, etc.
<br> Moosas+ is the **plug-in version** for moosas, 
which is detached from sketchUp for better compatibility of any other software.
<br> In this package we have provided a isolated python environment in pythonDict, 
which allow any users to call Moosas function without installation of python as well as 
have better stability while using Moosas.

## Package Structure
Moosas+ is reform in ***python/golang/javascript***. We kindly invite contributions to the python package MoosasPy for better performance.
- ***.\python:*** the python environment
  - ***.\python\Lib\MoosasPy:*** the MoosasPy package
- ***.\libs:*** the core execution for energy, radiation, and ventilation analysis
  - ***.\libs\energy:*** residential/public building energy analysis.
  - ***.\libs\vent:*** pressure based / buoyancy based ventilation analysis by contamX.
  - ***.\libs\rad:*** fast ray-face test module for radiation analysis.
- ***.\db:*** the database for building templates, materials and weather file.
- ***.\view:*** Moosas+ interface coded in html / javascript. currently is not functioned.
- ***.\data:*** Some of the input files and analysis result (like ventilation) can be found here
- ***.\temp:*** Files will be clean here when start moosas+ ro import MoosasPy.

## Usage
### MoosasPy Package
We have embedded a portable python 3.11 in the python folder.
The [MoosasPy](python/Lib/MoosasPy) could be call directly in this portable python
```python
import MoosasPy
```
If you want to call MoosasPy with your own Interpreter, you should include the MoosasPy in your system path like
```python
import os
os.environ['PATH']+=os.path.abspath(r'python/Lib')
import MoosasPy
```
please do not move the MoosasPy module to elsewhere since the directories were lock with relative path
like /db or /data, etc.
following module would need if an external Interpreter was implemented:  
numpy==1.24.4  
eppy==0.5.63  
xgboost==2.1.2  
scikit-learn==1.5.2  
rdflib==7.1.4  
pygeos==0.14  
Generally, you can call energy analysis and afn analysis like:

```python
import MoosasPy

# model transformation
model = MoosasPy.transform(r'geo\selection0.geo', stdout=None)

# apply weather and building template
model.loadWeatherData('545110')
for space in model.spaceList:
    space.applySettings('climatezone3_GB/T51350-2019_RESIDENTIAL')

# energy analysis
eData = MoosasPy.energyAnalysis(model)

# get CONTAM project files and zoneInfoFiles
zoneList, pathList = MoosasPy.vent.getZoneAndPath(model)
prjFile = MoosasPy.vent.buildPrj(zoneList=zoneList, pathList=pathList)
zoneInfoFile = MoosasPy.vent.buildZoneInfoFile(zoneList=zoneList)

# Run ventilation analysis
result = MoosasPy.ventilation.contam_iteration(prjFile=prjFile, zoneInfoFile=zoneInfoFile)
```

### Geometry Transformation

This must be finished before any analysis. The main function is MoosasPy.Transforming.transform()
> **transforming.transform(input_path, output_path=None, geo_path=None, \*\*kwargs) -> model.MoosasModel**

Convert geometric data to structured spatial model with optional processing.

**Parameters:**  
- ***input_path*** : str  
    Path to input geometry file. Supported formats:  
    - *.obj : Wavefront OBJ format  
    - *.xml : Custom XML structure  
    - *.stl : STL format (future support)  
    - *.geo : Stream format (future support)  

- ***output_path*** : str, optional  
    Output path for structured spatial data. Supported formats:  
    - *.spc : Steam format with space/element descriptions  
    - *.xml : Tree-structured XML format  
    - *.json : JSON equivalent of XML structure  
    - *.idf : EnergyPlus input with default thermal settings  
    - *.rdf : RDF knowledge graph (Turtle format)  

- ***geo_path*** : str, optional  
    Export path for modified geometry (*.geo format).  

- ***input_type*** : str, optional  
    Explicit input format specification (e.g., 'obj', 'xml').  
    Auto-detected from input_path suffix if None.  

- ***output_type*** : str, optional  
    Explicit output format specification.  
    Auto-detected from output_path suffix if None.  

- ***method*** : callable, optional  
    Space generation algorithm (default: CCRSpaceGeneration). Options:  
    - VFGSpaceGeneration (L. Jones 2013)  
    - BTGSpaceGeneration (H. Chen 2018)  
    - CCRSpaceGeneration (J. Xiao 2023)  

- ***solve_duplicated*** : bool, optional  
    Resolve walls with identical 2D projections (default: True).  

- ***solve_redundant*** : bool, optional  
    Merge coplanar faces/walls (default: True).  

- ***solve_contains*** : bool, optional  
    Detect wall overlaps/containments (default: True).  

- ***triangulate_faces*** : bool, optional  
    Triangulate horizontal faces with holes (default: True).  

- ***break_wall_vertical*** : bool, optional  
    Vertically segment walls by building levels (default: True).  

- ***break_wall_horizontal*** : bool, optional  
    Horizontally segment walls at intersections (default: True).  

- ***attach_shading*** : bool, optional  
    Attach unused faces as shading/thermal mass (default: False).  

- ***divided_zones*** : bool, optional  
    Split complex zones into ≤4-edge polygons (default: False).  

- ***standardize*** : bool, optional  
    Simplify output geometry representations (default: False).  

- ***stdout*** : object, optional  
    Output stream for transformation logs (default: sys.stdout).  

**Returns**
MoosasModel  
    Structured spatial model with properties (More information could be found in models module):  
    - spacesList : List[MoosasSpace] - Spatial units with thermal properties  
    - wallList : List[MoosasWall] - Architectural components  
    - buildingTemplate : dict -  dictionary of the termal building templates and properties  
    - weather : MoosasWeather - weather object and information  

**Examples**
```python
from MoosasPy import transform
from MoosasPy.geometry.spaceGen import CCRSpaceGeneration
model = transform('test.obj',output_path='test.xml', method=CCRSpaceGeneration)
```

Energy analysis example:
```python
from MoosasPy import transform
from MoosasPy import energyAnalysis
model = transform('test.obj')
model.loadWeatherData('545110') # Beijing TMY weather data
results = energyAnalysis(model)
print(f"Total energy demand: {results['total']['cooling'] + results['total']['heating']} kWh")
```
**Notes**
1. For RDF/XML or other outputs, use .saveModel() instead of output_path
2. IDF generation includes default thermal settings from ASHRAE 90.1
3. Geometry standardization reduces model fidelity for simulation efficiency

<br>All data for a project can be search/edit in the return MoosasModel. More feature about Moosasmodel please check the document for MoosasPy.model
<br>To get more detail data about the model:

```python

from MoosasPy import transform
model = transform(r'geo\selection0.geo',output_path='output.xml')
model = transform(r'geo\selection0.geo',output_path='output.rdf')
model = transform(r'geo\selection0.geo',output_path='output.json')
model = transform(r'geo\selection0.geo',output_path='output.idf')
```
or:
```python
from MoosasPy import transform,saveModel,IO
model = transform(r'geo\selection0.geo')
saveModel(model,'output.ttl', fileFormat='turtle') # *.rdf graph file
IO.writeRDF(model,'output.ttl', fileFormat='turtle')# *.rdf graph file (the same function above)
IO.writeXml('output.xml',model) # *.xml tree file
IO.writeGeo('test.geo',model) # *.geo file for geometry
IO.writeJson('test.json',model) # *.json file for the model
IO.writeIDF(model,r'template.idf',r'test.idf') # *.idf file
```

### Apply Thermal Settings
> **model.MoosasSpace.applySettings(buildingTemplateHint str) -> None**

- ***buildingTemplateHint*** : str  
any hint about the template you want to apply. Those template data can be found in *.\db\building_template.csv* 
you can add any templates or space settings in this file and search that template using the words you fill in climatezone, building type or building code.
<br>There are 17 thermal parameters in total. they are:

        "zone_wallU"=>            #外墙U值 / External Wall U-value (W/m2-K)
        "zone_winU"=>             #外窗U值 / External Window U-value (W/m2-K)
        "zone_win_SHGC"=>         #外窗SHGC值 / External Window SHGC
        "zone_c_temp"=>           #空调控制温度 / Cooling Set Point Temperature (C)
        "zone_c_hum":=>           #空调控制湿度 / Cooling Set Point Humidity (%)
        "zone_h_temp"=>           #采暖控制温度 / Heating Set Point Temperature (C)
        "zone_collingEER"=>       #空调能效比 / Cooling COP
        "zone_HeatingEER"=>       #空调能效比 / Heating COP
        "zone_work_start"=>       #系统开启时间 / Working Schedule Start time [0-24]
        "zone_work_end"=>         #系统关闭时间 / Working Schedule Start time [0-24]
        "zone_ppsm"=>             #每平米人数 / Population per Area (people/m2)
        "zone_pfav"=>             #人均新风量 / Air Change Requirement Per Person (ACH/people)
        "zone_popheat"=>          #人员散热 / Heat Generation per Person (W/people)
        "zone_equipment"=>        #设备散热 / Heat Generation by Equipment (W/m2)
        "zone_lighting"=>         #灯光散热 / Heat Generation by Lighting (W/m2)
        "zone_inflitration"=>     #渗风换气次数 / Air Change by Inflitration (ACH)
        "zone_nightACH"=>         #夜间换气次数 / Air Change by in Nighttime (ACH)

In addition, you can manually change the settings for any spaces. All space are documented in **Moosasmodel.Moosasspacelist []**; and 
the thermal settings are documented in MoosasSpace.settings as **dictionary** using the keys above.
<br> **Example:**

```python

from MoosasPy import transform

model = transform(r'geo\selection0.geo', stdout=None)
# apply building template
for space in model.spaceList:
    space.applySettings('climatezone3_GB/T51350-2019_RESIDENTIAL')
# change thermal settings for any spaces, for example the third space
model.spaceList[2].settings['zone_equipment'] = 8.8
```

### Load Weather Data
> **model.MoosasModel.loadWeatherData(stationId) -> None**

- ***stationId*** : str  
Climate Station Id which can be found in EPW file.

Moosas+ works with a designed weather data file for the simulation software DeST, which is also known as the **Chinese Weather Standard Dataset (CWSD)**.
It can be accessed from **Library of Tsinghua University**. But, don't worry, we have also provide a transformation from **EnergyPlus Weather (EPW)** file to CWSD weather file.
You can find the weather file here:
<br>[https://energyplus.net/weather](https://energyplus.net/weather)

> **weather.include_epw(epw_file) -> str**

- ***epw_file*** : str  
EPW file path.

**return**  
stationId in string
<br>This method can translate and documented the epw file into our database.The weather database located in ***.\db\weather***

```python

from MoosasPy.weather import includeEpw
from MoosasPy import transform

model = transform(r'geo\selection0.geo', stdout=None)
stationId = includeEpw(epw_file=r'C:\EnergyPlusV22-2-0\WeatherData\AnyEpwFile.epw')
# we always load weather by the weather stationId
model.loadWeatherData(stationId)
```
You can find all weather file in **.\db\weather** or by loadStation() method.
It can get the station info from **.\db\dest_station.csv**

```python
from MoosasPy.weather.dest import MoosasWeather

print(MoosasWeather.loadStation())
```
### Energy Analysis
You must apply thermal settings before energy analysis. If not, a residential template will be applied to all spaces.
We use Beijing as the default weather.
> **analysis(model: Moosasmodel, building_type=buildingType.RESIDENTIAL, require_radiation=False, params_path=None,
             load_path=None) -> dict**

- ***model*** : MoosasModel  
which need to be calculated
- ***building_type*** : str , optional  
residential (0) or public building (>0) (default: 0)
- ***require_radiation*** : bool , optional  
True if you want a more accurate but slower calculation of solar heat gain (default: False)
- ***params_path*** : str , optional  
path to export zones' thermal parameters. Result in *.\data\energy* if None (default: None)
- ***load_path*** : str , optional  
path to export zones' energy load result. Result in *.\data\energy* if None (default: None)

We use different core to calculate load for residence or public buildings. So please change building_type while calculating
public building. Otherwise the result will present a great difference.
<br> You can also call the MoosasEnergy core execution in command line, if you have other ways to collect required thermal parameters.
```commandline
cd .\libs\energy
MoosasEnergyResidential.exe -h
```

        Moosas Energy Analysis for Residential Buildings.
        Command line should be: MoosasEnergyResidential.exe [-h,-w...] inputFile.i
        Optional command:
        -h / -help : reprint the help information
        -w / -weather [weather file path.csv]: weather file formatted in DeST. for file formatted in EPW, please use the script in MoosasPy/weather.py
        -t / -type [0,1,2,3,4,5,6]: input building type:
        0 => RESIDENTIAL
        1 => OFFICE
        2 => HOTEL
        3 => SCHOOL
        4 => COMMERCIAL
        5 => OPERA
        6 => HOSPITAL
        -l / -lat : latitude of the site
        -a / -alt : altitude of the site
        -s / -shape : shape factor of the building = gross surface area (m2) / gross building volume (m3)
        -o / -output : output file path (default: .\MoosasEnergy.o)

There are 27 parameters in total, 10 for the room geometry properties and 17 for thermal properties

        'space_height'=>         # Space internal height
        'zone_area'=>            # Zone total indoor floor area
        'outside_area'=>         # Zone total external surface area
        'facade_area'=>          # Zone total external facade area
        'window_area'=>          # Zone total external window area
        'roof_area'=>            # Area for the ceiling faces connected to outdoor air
        'skylight_area'=>        # Area for the skylight faces connected to outdoor air
        'floor_area'=>           # Area of ground floor. 0 if the space is not located on the first floor
        'summer_solar'=>         # total summer solar heat gain (Wh)
        'winter_solar'=>         # total winter solar heat gain (Wh)

        "zone_wallU"=>            #外墙U值 / External Wall U-value (W/m2-K)
        "zone_winU"=>             #外窗U值 / External Window U-value (W/m2-K)
        "zone_win_SHGC"=>         #外窗SHGC值 / External Window SHGC
        "zone_c_temp"=>           #空调控制温度 / Cooling Set Point Temperature (C)
        "zone_c_hum":=>           #空调控制湿度 / Cooling Set Point Humidity (%)
        "zone_h_temp"=>           #采暖控制温度 / Heating Set Point Temperature (C)
        "zone_collingEER"=>       #空调能效比 / Cooling COP
        "zone_HeatingEER"=>       #空调能效比 / Heating COP
        "zone_work_start"=>       #系统开启时间 / Working Schedule Start time [0-24]
        "zone_work_end"=>         #系统关闭时间 / Working Schedule Start time [0-24]
        "zone_ppsm"=>             #每平米人数 / Population per Area (people/m2)
        "zone_pfav"=>             #人均新风量 / Air Change Requirement Per Person (ACH/people)
        "zone_popheat"=>          #人员散热 / Heat Generation per Person (W/people)
        "zone_equipment"=>        #设备散热 / Heat Generation by Equipment (W/m2)
        "zone_lighting"=>         #灯光散热 / Heat Generation by Lighting (W/m2)
        "zone_inflitration"=>     #渗风换气次数 / Air Change by Inflitration (ACH)
        "zone_nightACH"=>         #夜间换气次数 / Air Change by in Nighttime (ACH)

### Ventilation Analysis
This module analyzes buoyancy ventilation and pressure-driven ventilation by *CONTAMX. CONTAM* is a software tool 
for modeling and simulating the airflow and contaminant transport in buildings. This module iterate the temperature
of all thermal zones in the building, and calculate heat gain and temperature change based on *Mass Flow balance on the 
Air Flow Network (AFN) matrix*.
<br> To get the ***Contam project file***, you can call these methods based on the model we get by transformation.
> **def buildPrj(model: MoosasModel = None, pathList: list\[AfnPath] = None, zoneList: list\[AfnZone] = None,
             prjFilePath=None, networkFilePath=None, split=False,
             t0=25.0, simulate=False, resultFile=None) -> list\[str]**

- ***model*** : MoosasModel  
by transforming.transform()
- ***pathList*** : list\[AfnPath] , optional  
you can construct AfnPath by getZoneAndPath() method and edit somthing. (Default : None)
- ***zoneList*** : list\[AfnZone] , optional  
you can construct AfnZone by getZoneAndPath() method and edit somthing. (Default : None)
- ***prjFilePath*** : str , optional  
file path to export *.prj file. The directory of this file will be used to export other things.
If None the file will be exported to data\vent (Default : None)
- ***networkFilePath*** : str , optional  
export the MoosasAFN.exe input file here. If None the file will be exported to temp directory (Default : None)
- ***split*** : bool , optional  
If True, the network will be automatically split into several isolate parts and files. (Default : True)
- ***t0*** : float , optional  
outdoor temperature. (Default : 25.0)
- ***simulate*** : bool , optional  
If True, contamX will be called and result will be exported to *.prj directory. (Default : True)
- ***resultFile*** : str , optional  
you cen redirect the result file to other place. (Default : None)

**return:**  
list\[str] for all prj file we get
<br>Build *.prj file(s) from model or pathList/zoneList. networkFile,model and pathList/zoneList cannot be all None.
This method can directly transform a model into CONTAM project file and all data we need will be calculated automatically.
However, you cannot change any settings for the space. If you want to edit the thermal settings, you can build the zone
and path list by this method:

> **def getZoneAndPath(model:MoosasModel) -> list\[AfnZone] , list\[AfnPath]**

- ***model*** : MoosasModel we get from transformation

**return** : A list for Zones and Paths in the AFN which records the topology of the flow network.
<br>You can change the initial temperature or heat load of the zone, or change the wind pressure on any paths(apertures).
They are only a structure to record data like this:

```python
from MoosasPy.vent.afn import getZoneAndPath, buildPrj
from MoosasPy.transformation import transform

model = transform(r'geo\selection0.geo', stdout=None)
zoneList, pathList = getZoneAndPath(model)
zoneList[0].heatLoad = 900  # unit in Watt (W)
pathList[0].pressure = 20.5  # unit in Pa
prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
```
Except for the CONTAM project file, one more thing we need to prepare before a buoyancy ventilation analysis.
We use the zoneInfo file as an input of the buoyancy iteration, which can be given by:

> **def buildZoneInfoFile(model: MoosasModel = None, zoneList: list\[AfnZone] = None, networkFilePath=None,
                      zoneInfoFilePath=None) -> str**

This method can build the zoneInfo file by:
- ***model*** : MoosasModel, given by transforming.transform() method 
- ***zoneList*** : list[AfnZone], given by getZoneAndPath() method 
- ***networkFile***: given by buildNetworkFile() method, or construct by other script like MoosasAFN.exe
<br>The zoneInfo file can be decoded like this:
<br>[[prjroomname, roomheatload, userroomname]..[]]
<br>in which:
- prjroomname: the room name set in the *.prj file, must be the same in every character
- roomheatload: the gross load of the room in (W).
- userroomname: the room name define by the users, and it will occur in the result file.

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

After we get all data prepared, the iteration can be started by this method:

> **def iterateProjects(prjFiles, zoneInfoFiles, resultFile=None, 
> outdoorTemperature=25, maxIteration=50, exitResidual=0.01) -> list\[ZoneResult]**

- ***prjFiles*** : str  
single contam project file. Initial indoor temperature should be carefully defined in this file.
        Users can use the contamW3.exe to build this file by a GUI.
        Documents about contamX and contamW can be found at:
        https://www.nist.gov/el/energy-and-environment-division-73200/nist-multizone-modeling/software/contam/documentation
- ***zoneInfoFiles*** : 
a standard roomInfo file(s) or roomInfo data should be given here:
        [[prjroomname, roomheatload, userroomname]..[]]
- ***resultFile*** : str , optional  
the iteration result path, will be coded into csv.
        In this file, the temperature changes and Volume Metric Flow Rate in ACH will be recorded.
        You can find all processing prj file in FilePath['project_dir'] and read the Air Flow Network by contamW.
- ***outdoorTemperature*** : float , optional   
The static outdoor temperature.
        Notice that only the indoor/outdoor temperature difference will be considered in contamX,
        which means that #25 indoor 20 outdoor# is equal to #20 outdoor 15 indoor#.
- ***maxIteration*** : int , optional   
The max iterations contamX should run. (Default : 50)
- ***exitResidual*** : float , optional   
Stop iteration if overall Residual is smaller than this value (Default : 0.01)

**return** : list\[ZoneResult] to record each data in iterations and the zone settings.
You can finish an iteration by following example:

```python
from MoosasPy.vent.afn import getZoneAndPath, buildPrj, buildZoneInfoFile
from MoosasPy.transformation import transform
from MoosasPy.ventilation import contam_iteration

model = transform(r'geo\selection0.geo', stdout=None)
zoneList, pathList = getZoneAndPath(model)
zoneList[0].heatLoad = 900  # unit in Watt (W)
pathList[0].pressure = 20.5  # unit in Pa
prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
zoneInfoFile = buildZoneInfoFile(zoneList=zoneList)
result = contam_iteration(prjFile=prjFile, zoneInfoFile=zoneInfoFile)
```

> **ZoneResult**

A structure to record the analysis result.<br>
__slots__ = \['name', 'heat', 'volume', 'userName', 'temperature', 'ACH']

- ***name*** : zone name in the prj file
- ***heat*** : zone total heat load
- ***volume*** : zone space volume
- ***userName*** : users define name of the zone, default is MoosasSpace.id
- ***temperature*** : a list[float] for temperature result in C. inf if invalid.
- ***ACH*** : a list[float] for mass flow result in m3/h. inf if invalid.

It can be matched to the space in model.MoosasSpaceList by userName:

```python
from MoosasPy.vent.afn import getZoneAndPath, buildPrj, buildZoneInfoFile
from MoosasPy.transformation import transform
from MoosasPy.ventilation import contam_iteration
import numpy as np

model = transform(r'geo\selection0.geo', stdout=None)
zoneList, pathList = getZoneAndPath(model)
zoneList[0].heatLoad = 900  # unit in Watt (W)
pathList[0].pressure = 20.5  # unit in Pa
prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
zoneInfoFile = buildZoneInfoFile(zoneList=zoneList)
zResult = contam_iteration(prjFile=prjFile, zoneInfoFile=zoneInfoFile)
spaceIdList = [s.id for s in model.spaceList]
sortList = [spaceIdList.index(z.userName) for z in zResult]
zResult = np.array(zResult)[sortList]
```

### Radiation Calculation
This module provides solar heat gain calculation for energy and ventilation analysis. 
Of course, you can also call this module directly. It provides several connections 
to the MoosasRad.exe in different scales.

> **positionRadiation(positionRay, sky: MoosasCumSky, model: MoosasModel = None, reflection=1, geo_path=None) -> list\[Ray]**

- ***positionRay*** : Ray or list\[Ray]  
to document the origins and directions for those positions.
- ***sky*** : MoosasCumSky  
cumSky for calculation. You can create a cumSky by MoosasCumSky(), or use those in model.cumSky
default cumSky in MoosasModel: 
<br>model.cumSky\['annualCumSky']<br>model.cumSky\['summerCumSky']<br>model.cumSky\['winterCumSky']
- ***model*** : MoosasModel , optional  
given by transforming.transform(). Model and geo_path cannot be all None. (Default : None)
- ***geo_path*** : str , optional  
.geo file path. You can write a geo file by utils.writeGeo() method  (Default : None)
- ***reflection*** : int , optional  
Reflection times in calculation, (default : 1)

**Examples:**
```python
from MoosasPy.transformation import transform
from MoosasPy.rad import positionRadiation
from MoosasPy.geometry import Ray
model = transform(r'geo\selection0.geo', stdout=None)
model.loadCumSky('545110')
position = Ray(origin=[0,0,0],direction=[0,0,1])
positionRadiation(position,model.cumSky['annualCumSky'],model)
```
the result of each ray will be recorded in ray.value in kWh/m2

> **spaceRadiation(space:MoosasSpce,reflection 1) -> MoosasSpce**

- ***space*** : MoosasSpace in model.MoosasSpacelist. The space's data will be change in this method.
- ***reflection*** : Reflection times in calculation, default 1.

> **modelRadiation(model: MoosasModel = None,reflection 1) -> MoosasSpce**

- ***model*** : MoosasModel given by transforming.transform().
- ***reflection*** : Reflection times in calculation, default 1.

This method is faster than spaceRadiation since it only call MoosasRad.exe once.
         Radiation Calculation in MoosasRad is parallel.
<br> For better using experience in this module, we strongly recommend you to learn about Ray class:

> **Ray(self, origin, direction, value=0)**

__slots__ = \['origin', 'direction', 'value']
    
- ***origin*** : The origin of the ray, of the Vector type
- ***direction*** : The direction of the ray, Vector type
- ***value*** : Used to store related data, which can be in any data format
    
> **Vector(vec)**

__slots__ = \['x', 'y', 'z', 'style']
- ***vec*** : pygeos.Geometry (POINT) or np.ndarry or list. It will be forced to 3d (z=0).

## EXE in moosas+
We kindly provide all executions in analysis for users. They are coded in Golang and enable their
parallel calculation, which can be far more fast than those in python.
> **MoosasEnergyPublic(Residential).exe**

In Moosas energy calculation is different for public and residential buildings.
<br>Command line should be: MoosasEnergyResidential.exe [-h,-w...] inputFile.i
<br>***Optional command***:
- **-h / -help** : reprint the help information
- **-w / -weather** [weather file path.csv]: weather file formatted in DeST. for file formatted in EPW, please use the script in MoosasPy/weather.py
- **-t / -type** [0,1,2,3,4,5,6]: input building type:
<br>0 => RESIDENTIAL
<br>1 => OFFICE
<br>2 => HOTEL
<br>3 => SCHOOL
<br>4 => COMMERCIAL
<br>5 => OPERA
<br>6 => HOSPITAL
- **-l / -lat** : latitude of the site
- **-a / -alt** : altitude of the site
- **-s / -shape** : shape factor of the building = gross surface area (m2) / gross building volume (m3)
- **-o / -output** : output file path (default: .\MoosasEnergy.o)

For example the command line in MoosasPy:
```commandline
libs\energy\MoosasEnergyResidential.exe -w db\weather\545110.csv -l 39.93 -a 55.0 -s 0.78 -o data\energy\Energy.o data\energy\Energy.i
```

> **MoosasRad.exe**

Command line should be: MoosasRad.exe [-h,-g...] inputFile.i<br>
***Optional command***:
- ***-h / -help*** : reprint the help information
- ***-g / -geo*** : geometrical input for ray test contents
- ***-o / -output*** : output file path (default: .\MoosasEnergy.o)

For example the command line in MoosasPy:
```commandline
libs\rad\MoosasRad.exe -g __temp__\ray_0x01ce.geo -o __temp__\ray_0xf8f3.o __temp__\ray_0xf8f3.i
```

> **MoosasAFN.exe**

Moosas ContamX Builder and reader.
<br>Command line should be: MoosasAFN.exe [-h,-p...] inputNetworkFile.net<br>
**Optional command**:
- ***-h / -help*** : reprint the help information
- ***-p / -project*** : base name of the prj file  (default: network)
- ***-d / -directory*** : directory where the project file and result to put  (default: execution directory)
- ***-o / -output*** : result output file path (default: execution directory\airVel.o)
- ***-r / -run*** : 1 if run contamX for all built *.prj files and gather the results (default: 0)
- ***-s / -split*** : 1 if split the input network into several networks (default: 1)
- ***-t / -t0*** : OutdoorTemperature (default: 25)

For example the command line in MoosasPy:
```commandline
libs\vent\MoosasAFN.exe -p afn_0x6a94 -d data\vent -t 25 -s 0 __temp__\0xe2i8.net
```

## File Structure
All input and output files in Moosas+ are encoded in a same file structure:<br>
'!' means following string are annotations until the end of the line;<br>
';' blocks are split by ';'<br>
'\n' items in a block are split by '\n' <br>
Empty lines are valid. It will be regraded as an empty data<br>

    ! block 0
    data,data,data,data ! items 0 \n
    data,data,data,data ! items 1 \n
    data,data,data,data ! items 2 \n
    ...
    data,data,data,data ! items n \n
    ;
    ! block 1
    data,data,data,data ! items 0 \n
    data,data,data,data ! items 1 \n
    data,data,data,data ! items 2 \n
    ...
    data,data,data,data ! items n \n
    ;
    ...
    
You can use this method to parse the file:
> **utils.parseFile(file_path) -> list\[list\[list\[str]]]**

Especially, these are detail file structure for each input and output:
(Annotations are not required)

### *.geo File for Geometry
.geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed.
The .geo file format like:<br>
(cat: 0 is the opaque surface, 1 is the translucent surface, and 2 is the air boundary)

        f,{polygon type cat},{polygon number idd}       ! Face's info
        fn, {normal x}, {normal y}, {normal z}          ! Face's normal
        fv, {vertex 1x}, {vertex 1y}, {vertex 1z}       ! Face's outer loop verties in sequence 
        ...
        fv,{vertex nx},{vertex ny},{vertex nz}          ! Face's outer loop verties in sequence 
        fh,{aperture n},{vertex 1x},{vertex 1y},{vertex 1z} ! Holes' verties in sequence 
        ...
        fh,{aperture n},{vertex nx},{vertex ny},{vertex nz} ! Holes' verties in sequence 
        ;                                               ! A face should end with ';'

For example, there are two vertical faces with two openings with a positive x-axis normal vector:

        ! Face 0 as a opque vertical surface with 2 holes
        f,0,0
        fn,1.0,0.0,0.0
        fv,15.5,10.0,2.2
        fv,15.5,10.0,0.0
        fv,15.5,10.8,0.0
        fv,15.5,10.8,2.2
        fh,0,15.5,10.1,1.8
        fh,0,15.5,10.1,0.9
        fh,0,15.5,10.3,0.9
        fh,0,15.5,10.3,1.8
        fh,1,15.5,10.5,1.8
        fh,1,15.5,10.5,0.9
        fh,1,15.5,10.7,0.9
        fh,1,15.5,10.7,1.8
        ;
        ! Face 1 as a transparent vertical surface with 0 holes
        f,1,1
        fn,-1.0,0.0,0.0
        fv,12.5,10.0,2.2
        fv,12.5,10.0,0.0
        fv,12.5,10.8,0.0
        fv,12.5,10.8,2.2
        ;
        ...

#### output
The output files of geometries and spaces can be formatted in different types: <br>
*.xml, *.json, stringFile, *.rdf(rdf/xml, turtle, etc.) (for space info)<br>
*.geojson, *.geo (for geo info)<br>
> *.xml, *.json

These format share the same tree-based structure. Take xml as an example.  
the space structured like:
```xml
<space>
    <id>0x12003g1b20476k</id>
    <area>32.14250000000006</area>
    <height>4.4</height>
    <is_void>False</is_void>
    <boundary>
        <pt>-59.95 182.05 0.0</pt>
        <pt>-56.75 176.5 0.0</pt>
        <pt>-52.4 179.0 0.0</pt>
        <pt>-55.6 184.55 0.0</pt>
        <pt>-59.95 182.05 0.0</pt>
    </boundary>
    <setting>
        <zone_name>0x12003g1b20476k</zone_name>
        <zone_summerrad>None</zone_summerrad>
        <zone_winterrad>None</zone_winterrad>
        <zone_template>climatezone3_GB/T51350-2019_RESIDENTIAL</zone_template>
        <zone_wallU>0.35</zone_wallU>
        <zone_winU>1.8</zone_winU>
        <zone_win_SHGC>0.4</zone_win_SHGC>
        <zone_c_temp>26</zone_c_temp>
        <zone_c_hum>0.4</zone_c_hum>
        <zone_h_temp>18</zone_h_temp>
        <zone_collingEER>2.5</zone_collingEER>
        <zone_HeatingEER>2</zone_HeatingEER>
        <zone_work_start>0</zone_work_start>
        <zone_work_end>23</zone_work_end>
        <zone_ppsm>0.0196</zone_ppsm>
        <zone_pfav>30</zone_pfav>
        <zone_popheat>88</zone_popheat>
        <zone_equipment>3.8</zone_equipment>
        <zone_lighting>5</zone_lighting>
        <zone_infiltration>0.5</zone_infiltration>
        <zone_nightACH>1</zone_nightACH>
    </setting>
    <topology>
        <floor>
            <face>face_0_18</face>
        </floor>
        <ceiling>
            <face>face_0_41</face>
        </ceiling>
        <edge>
            <wall>
                <Uid>wall_0_11</Uid>
                <normal>-5.550000000000011 -3.200000000000003 0</normal>
            </wall>
            <wall>
                <Uid>wall_0_2</Uid>
                <normal>2.5 -4.350000000000001 0</normal>
            </wall>
            <wall>
                <Uid>wall_0_12</Uid>
                <normal>5.550000000000011 3.200000000000003 0</normal>
            </wall>
            <wall>
                <Uid>wall_0_16</Uid>
                <normal>-2.5 4.350000000000001 0</normal>
            </wall>
        </edge>
    </topology>
    <neighbor>
    <Uid> </Uid>
    <id>0x42003d432052hk</id>
    </neighbor>
    <neighbor>
    <Uid> </Uid>
    <id>0x12203g1b22476k</id>
    </neighbor>
</space>
```
those Uids are linked to the Uid field of the element as following:
```xml
<wall>
    <Uid>wall_0_14</Uid>
    <faceId>n47</faceId>
    <level>0.0</level>
    <offset>0.0</offset>
    <area>31.73569860407208</area>
    <glazingId/>
    <height>0.0</height>
    <normal>0.5000000000000002 -0.8660254037844386 -0.0</normal>
    <external>True</external>
    <s>['0x42003d432052hk']</s>
    <neighbor>
        <edge key="-6165_19510_0_-6165_19510_440_">wall_0_19</edge>
        <edge key="-6790_19150_0_-6165_19510_0_">face_0_17</edge>
        <edge key="-6790_19150_0_-6790_19150_440_">wall_0_15</edge>
        <edge key="-6790_19150_440_-6165_19510_440_">wall_0_21 face_0_22</edge>
    </neighbor>
    <length>7.212662476506165</length>
    <force2d>[[-67.9 191.5 ] [-61.65 195.1 ]]</force2d>
    <toplevel>4.4</toplevel>
    <topoffset>0.0</topoffset>
</wall>
```
those faceIds are linked to the geometries' id in the [*.geo file](#geo-file-for-geometry)

> *.rdf file

This is a graph description file format coded in Ontology Web Language (OWL), usually were in rdf/xml and turtle format.  
For better compatibility with other OWL-like file (idf,ifc,brick,etc.), the rdf using several related namespace:
@prefix bes: <http://www.hkust.edu.hk/zhaojiwu/performance_based_generative_design#> .  
@prefix bot: <https://w3id.org/bot#> .  
@prefix geo: <http://www.opengis.net/ont/geosparql#> .  
@prefix moosas: <https://moosas#> .  
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .  
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .  

since the rdf file can be interpreted and visualized by may tools,
we strongly recommend to directly try the module and take a look on the output by Neo4j etc.

### File for MoosasEnergy.exe
#### input
There are 27 parameters in total, 10 for the room geometry properties and 17 for thermal properties.
you should place all rooms in a single block as different items

    ! This file has only one block
    ! 27 params for zone 0 
    3.0,7.43,7.43,9.09,5.16,0,10.81,14.85,943506.5,474012.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 1 
    3.0,47.58,47.58,47.22,14.97,80.3,10.81,110.0,2812698.5,3041388.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 2 
    3.0,72.9,72.9,111.96,27.52,80.3,10.81,255.8,5360750.5,6274976.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 3 
    3.0,7.6,7.6,126.94,28.88,80.3,10.81,271.0,5624862.5,6600560.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 4 
    3.0,16.2,16.2,130.84,28.88,112.7,10.81,271.0,5624862.5,6600560.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 5 
    3.0,12.15,12.15,145.06,28.88,137.0,10.81,271.0,5624862.5,6600560.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 6 
    3.0,20.35,20.35,165.0,49.88,177.7,10.81,271.0,9643868.5,10413262.5,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 7 
    3.0,8.1,8.1,172.93,54.11,193.9,10.81,271.0,10135236.0,10630850.0,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 8 
    3.0,24.3,24.3,185.08,54.11,242.5,10.81,271.0,10135236.0,10630850.0,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 9 
    3.0,6.65,6.65,198.56,55.47,255.8,10.81,271.0,10359296.0,10749918.0,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1
    ! 27 params for zone 10 
    3.0,7.6,7.6,213.54,56.83,271.0,10.81,271.0,10623408.0,11075502.0,0.35,1.8,0.4,26,0.4,18,2.5,2,0,23,0.0196,30,88,3.8,5,0.5,1

#### output
There are 3 different blocks in the output file recording the total / spacial / monthly energy load result.
It is quite readable:

    !TOTAL Energy Load:
    !Cooling,Heating,Lighting
    66.87,271.53,5.84
    ;
    !SPACE Energy Load result:
    !Cooling,Heating,Lighting
    26.18,118.00,5.84
    15.06,65.22,5.84
    17.83,73.85,5.84
    158.99,698.44,5.84
    77.49,349.21,5.84
    105.01,489.97,5.84
    88.01,324.42,5.84
    227.59,847.72,5.84
    79.34,307.02,5.84
    290.90,1145.09,5.84
    261.81,1034.26,5.84
    ;
    !MONTH Energy Load result:
    !Cooling,Heating,Lighting
    0.00,79.96,0.50
    0.00,61.70,0.45
    0.00,23.05,0.50
    0.00,2.61,0.48
    0.00,0.00,0.50
    23.37,0.00,0.48
    21.68,0.00,0.50
    21.82,0.00,0.50
    0.00,0.00,0.48
    0.00,3.86,0.50
    0.00,35.05,0.48
    0.00,65.30,0.50

### File for MoosasRad.exe
#### input
The input geometries are formatted as *.geo
And the input ray file is like:
    
    ! This file has only one block
    ! x,y,z for the origin and x,y,z for the direction
    0,0,0,0,0,1
    ......

#### output
Output for this module is also formatted as ray, suggest the reflection of each ray:

    ! This file has only one block
    ! x,y,z for the origin and x,y,z for the direction
    3.5,4.4,2.8,0,0,-1
    ......
    ! reflection is invalid if the origin is -1,-1,-1
    -1,-1,-1,0,0,1
    ......

### File for MoosasAfn.exe
#### networkFile
This file shows the topology of the building.<br>
Zone items have 9 parameters:
- ***zoneName*** : user define zoneName
- ***heatLoad*** : total heat load in Watt (W)
- ***temperature*** : zone initial temperature (C)
- ***volume*** : zone volume (m3)
- ***positionX,positionY,positionZ*** : a position to match the zone in meter (m)
- ***boundaryPolygon*** : define the zone boundary in meter (m) with ' ' as sep

path items have 10 parameters:
- ***pathName*** : user define pathName
- ***pathIndex*** : path index in the prj file
- ***height*** : height of the aperture in meter (m)
- ***width*** : width of the aperture in meter (m)
- ***positionX,positionY,positionZ*** : a position to match the path in meter (m)
- ***fromZone*** : the zone index that the path from
- ***toZone*** : the zone index that the path to
- ***pressure*** : wind pressure of the path if it is connected to outdoor

It has two blocks like:

    ! ZONE DATA
    ! zoneName,zonePrjName,heatLoad,temperature,volume,positionX,positionY,positionZ,boundaryPolygon
    0x0100304079049b50,z001,290.48,27.00,22.28,1.10,8.92,0.00,0.0 7.3 2.75 7.3 2.75 10.0 0.0 10.0 0.0 7.3
    0x2100f12059075fh0,z002,726.26,27.00,142.73,3.68,5.99,0.00,5.5 4.5 5.5 10.0 2.75 10.0 2.75 7.3 0.0 7.3 0.0 0.0 5.5 0.0 5.5 4.5
    0x3100h44099096h70,z003,1287.13,27.00,218.70,10.13,9.19,-0.00,13.6 4.5 13.6 8.5 15.5 8.5 15.5 12.0 5.5 12.0 2.75 12.0 2.75 10.0 5.5 10.0 5.5 4.5 13.6 4.5
    ...
    ;
    ! PATH DATA
    ! pathName,pathIndex,height,width,positionX,positionY,positionZ,fromZone,toZone,pressure
    0xa1j417,p001,1.3,2.35,1.14,10.0,1.68,-1,0,0.0
    0xkfg9a2,p002,2.1,1.0,0.0,8.75,1.74,-1,0,0.0
    0x62c2hj,p003,1.3,3.9,5.5,7.65,1.42,1,2,0.0
    ...

#### ZoneFile
The zoneInfo itmes can be decoded like this:

        prjroomname, roomheatload, userroomname
        in which:
            prjroomname: the room name set in the *.prj file, must be the same in every character
            roomheatload: the gross load of the room in (W).
            userroomname: the room name define by the users, and it will occur in the result file.

The roomInfo file can exclude the roomname and only provide roomInfo, which means that:
the room heat file can only have 2 columns:<br>
        prjroomname,roomheatload<br>
in this case, the roomnome will be the same to the prjroomname<br>
or 2 columns:<br>
roomheatload,usersroomname<br>
in this case, the roomInfo data should be in the same sequence of zones in the project file<br>
        or only 1 column:<br>
        roomheatload<br>
        in this case, the roomheatload data should be in the same sequence of zones in the project file

## Credits and acknowledgements
Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.
<br> All Right Reserved.
<br> For collaboration, Please contact:
<br> linbr@mails.tsinghua.edu.cn
<br> If you have any technical problems, Please reach to:
<br> junx026@gmail.com

