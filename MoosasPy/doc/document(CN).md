# MOOSAS+ Ver 0.4.2
Moosas 是一个 SketchUp 插件程序，致力于构建性能分析
以及建筑草图设计阶段的优化**。
大多数细节设置和几何表示都变换了，
总是让架构师感到困惑的问题，将在界面后面解决。
MOOSAS的核心是建立在ruby之上的，界面是建立在javascript和html之上的。
扩展是基于 Python 和 Golong 构建的，包括 *.epw 转换，
*.geo\*.obj变换、风压预测等
<br> Moosas+ 是 moosas 的**插件版本**，
它与 sketchUp 分离，以便更好地兼容任何其他软件。
<br> 在这个包中，我们在 pythonDict 中提供了一个隔离的 python 环境，
它允许任何用户在不安装 python 的情况下调用 Moosas 函数以及
使用 Moosas 时具有更好的稳定性。

## 使用方法

### MoosasPy Package
如果你想通过python调用Moosas+，请确保你已经安装了以下软件包：
<br> **pygeos == 0.14**
<br> **xgboost == 2.0.3**
<br> **numpy == 1.26.3**
<br> 所有需要的包实际上都嵌入在 **.\pythonDist** 中。
因此，在运行 moosas+ 之前，您只需将 pythonDist 添加到您的系统路径即可。
<br> 您可以像这样导入 MoosasPy：
```python
import os
os.environ['PATH']+=os.path.abspath('pythonDist')+';'
from python.Lib import MoosasPy
```

通常，您可以调用能量分析和 afn 分析，例如：

```python
from python.Lib import MoosasPy

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

### 使用无环境依赖的接口调用Moosas+ 
我们在 *.\python* 中提供了一个隔离的、稳定的 python 环境。
将所有 python 代码写入某文档(请使用绝对路径)中，然后调用 python.exe。
必须特别注意的是，该方法运行时的路径是 *.\python* ，
请注意MoosasPy的引用目录("import MoosasPy" but not "from python.Lib import MoosasPy")

    Invoke any pyhon file via I/O
    commandLine should be: MoosasMain [-h,-o, -err] moosasPythonFile.py
    -h: reprint this massage
    -o: redirect stdout of this script, print to console directly if None.
    -err: redirect stderr of this script, print to console directly if None.
标准输出（用 python 打印的消息）与错误记录也可以用相同的办法保存
<br> 此外，python.exe有两个版本：
- ***pythonw.exe*** ： Moosas+ 将静默运行
- ***python.exe*** ： Moosas+ 将在 shell （cmd） 中运行
更多详细资料请输入MoosasMain -h命令.例如，您有几行 python 行，并且想在 Java 中调用 Moosas+：

```java
package test;
 
import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
 
public class Test2 {
 
    public static void main(String[] args) throws IOException{
        String path = "e:\\test\\test\\test3.txt";
        File file = new File(path);
        if(!file.exists()){
            file.getParentFile().mkdirs();          
        }
        file.createNewFile();
        
        FileStr="""
        from MoosasPy.afn import getZoneAndPath, buildPrj, buildZoneInfoFile
        from MoosasPy.transforming import transform
        from MoosasPy.ventilation import contam_iteration
        
        model = transform(r'geo\selection0.geo', stdout=None)
        zoneList, pathList = getZoneAndPath(model)
        zoneList[0].heatLoad = 900  # unit in Watt (W)
        pathList[0].pressure = 20.5  # unit in Pa
        prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
        
        zoneInfoFile = buildZoneInfoFile(zoneList=zoneList)
        result = contam_iteration(prjFile=prjFile, zoneInfoFile=zoneInfoFile)
        """
        
        // write
        FileWriter fw = new FileWriter(file, true);
        BufferedWriter bw = new BufferedWriter(fw);
        bw.write(FileStr);
        bw.flush();
        bw.close();
        fw.close();
        
        Process proc = Runtime.getRuntime().exec("moosas+\python\python.exe "+ path);
 
        // read
        FileReader fr = new FileReader(file);
        BufferedReader br = new BufferedReader(fr);
        String str = br.readLine();
        System.out.println(str);
    }
```

### 几何转换

#### 自动转换几何模型为空间
这必须在进行任何分析之前完成。主要函数是 MoosasPy.Transforming.transform（）
> **transforming.transform(inputpath, outputpath=None, geopath=None, input_type=None, output_type=None, solve_redundant=False,stdout=sys.stdout) -> model.MoosasModel**

- ***inputpath*** ：输入几何文件。*.obj* *.xml* *.stl*（将来）*.geo*（流格式）。
- ***outputpath*** ： 输出结构化空间信息。*支持 .xml* *.json* *.spc*（流格式）。
- ***geopath*** ：输出几何信息。格式为 *.geojson*。
- ***input_type*** ：输入几何文件类型。如果为空，则从路径中标识。
- ***output_type*** ：输出空间信息文件类型。如果为空，则从路径中标识。
- ***solve_redundant*** ：我们建议任何输入几何体都不应有冗余线。
- ***stdout*** ： 许多按摩将在此模块中打印。您可以将其设置为“无”或任何其他标准来绑带按摩。

返回：<MoosasPy.model.Moosasmodel>
<br>项目的所有数据都可以在返回的 MoosasModel 中搜索/编辑。有关Moosasmodel的更多功能，请查看MoosasPy.model文档
<br>要获取有关模型的更多详细信息，请执行以下操作：

```python

from python.Lib.MoosasPy import transform,utils

model = transform(r'geo\selection0.geo', stdout=None)
# get model xmlTree
xmlTree = model.buildXml()
# or, export the xml file
utils.writeXml('temp.xml',model)
# get model dictionary
modelDict = utils.to_dictionary(model.buildXml)
# or, export the json file
utils.writeJson('temp.xml',model)
```

#### 直接定义空间
> **MoosasModel.fromDict(spaceDict:dict)->None**
> **geometry.MoosasSpace.fromDict(spaceDict:dict,model:MoosasModel)->MoosasSpace**

- ***spaceDict*** : 包含空间信息的dictionary,可由xml或者json获得。
生成一个合法的空间至少要包含一个边界(edge),边界中包含至少3个face,每个face至少包含一个faceId.
更多spaceDict中的可选信息结构和命名要求详见[space File](#spaceFile)<br>

```xml
<space>
    <edge>
        <face>
            <faceId>...</faceId>
        </face>
        <face>
            <faceId>...</faceId>
        </face>
        <face>
            <faceId>...</faceId>
        </face>
        ...
    </edge>
</space>
```

### 对空间应用热工参数
> **model.MoosasSpace.applySettings(buildingTemplateHint str) -> None**

- ***buildingTemplateHint*** : 有关要应用的模板的任何提示。这些模板数据可以在 *.\db\building_template.csv* 中找到
您可以在此文件中添加任何模板或空间设置，并使用您在 climatezone、building type 或 building code 中填写的词语搜索该模板。
<br>总共有 17 个热参数。 他们是：

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

此外，您可以手动更改任何空间的设置。所有空间都记录在 **Moosasmodel.Moosasspacelist []**;和
使用上面的键，在MoosasSpace.settings中将热设置记录为**dictionary**。
<br> **Example:**

```python

from python.Lib.MoosasPy import transform

model = transform(r'geo\selection0.geo', stdout=None)
# apply building template
for space in model.spaceList:
    space.applySettings('climatezone3_GB/T51350-2019_RESIDENTIAL')
# change thermal settings for any spaces, for example the third space
model.spaceList[2].settings['zone_equipment'] = 8.8
```

### 读取气象数据
> **model.Moosasmodel.loadWeatherData(stationId) -> None**

- ***stationId*** : 气候站 ID，可以在 EPW 文件中找到;或直接传入epw file path

Moosas+ 使用为模拟软件 DeST 设计的天气数据文件，也称为“中国天气标准数据集 （CWSD）”。
可从清华大学图书馆访问。但是，别担心，我们还提供了从**EnergyPlus Weather （EPW）**文件到CWSD天气文件的转换。
因此该参数也可以直接传入epw文件，将会自动调用下面的includeEpw()方法。
您可以在此处找到天气文件：
<br>[https://energyplus.net/weather](https://energyplus.net/weather)

> **model.Moosasmodel.loadCumSky(stationId) -> None**

- ***stationId*** : 气候站 ID，可以在 EPW 文件中找到;或直接传入epw file path

通过此方法加载天空模型，该天空模型通过RADIANCE相关插件计算，并储存在.\db\cumSky当中。
该参数也可以直接传入epw文件，将会自动调用下面的includeEpw()方法。
您可以在此处找到天气文件：
<br>[https://energyplus.net/weather](https://energyplus.net/weather)

> **weather.includeEpw(epw_file) -> str**

- ***epw_file*** : EPW file path.

**return**: stationId in string
<br>此方法可以将 epw 文件翻译并记录到我们的数据库中。位于 ***.\db\weather*** 中的天气数据库

```python

from python.Lib.MoosasPy import weather
stationId = weather.includeEpw(epw_file=r'C:\EnergyPlusV22-2-0\WeatherData\AnyEpwFile.epw')
```
您可以在 **.\db\weather** 或通过 loadStation（） 方法找到所有天气文件。它可以从 **.\db\dest_station.csv** 获取电台信息

```python
from python.Lib.MoosasPy.weather.dest import MoosasWeather

print(MoosasWeather.loadStation())
```

### 能耗分析
在能量分析之前，必须应用热设置。如果没有，住宅模板将应用于所有空间。
我们使用北京作为默认天气。
> **analysis(model: Moosasmodel, building_type=buildingType.RESIDENTIAL, require_radiation=False, params_path=None,
             load_path=None) -> dict**

- ***model*** ： 需要计算的Moosasmodel
- ***building_type*** ： 住宅 （0） 或公共建筑 （>0） （默认： 0）
- ***require_radiation*** ： 如果您想要更准确但更慢的太阳热增益计算，则为 True（默认值：False）
- ***params_path*** ：导出区域热参数的路径。如果 None （默认值：None）
- ***load_path*** ： 导出区域能量负荷结果的路径。如果 None （默认值：None）

我们使用不同的核心来计算住宅或公共建筑的荷载。所以请在计算时更改building_type
公共建筑。否则，结果将呈现出很大的差异。
<br> 如果您有其他方法可以收集所需的热参数，也可以在命令行中调用 MoosasEnergy 核心执行。
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

总共有 27 个参数，10 个用于房间几何属性，17 个用于热属性

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

### 通风分析
该模块通过*CONTAMX分析浮力通风和压力驱动通风。CONTAM* 是一种软件工具
用于对建筑物中的气流和污染物传输进行建模和仿真。此模块迭代温度
建筑物中所有热区，并根据 *质量流量平衡计算热增益和温度变化
气流管网 （AFN） 矩阵*。
<br> 要获取 ***Contam 项目文件***，您可以根据我们通过转换获得的模型调用这些方法。
> **def buildPrj(model: MoosasModel = None, pathList: list\[AfnPath] = None, zoneList: list\[AfnZone] = None,
             prjFilePath=None, networkFilePath=None, split=False,
             t0=25, simulate=False, resultFile=None) -> list\[str]**

- ***model*** ： 通过 transforming.transform（） 的 MoosasModel
- ***pathList*** ：您可以通过 getZoneAndPath（） 方法构造 AfnPath 并编辑一些东西。
- ***zoneList*** ：您可以通过 getZoneAndPath（） 方法构造 AfnZone 并编辑一些东西。
- ***prjFilePath*** ：导出 *.prj 文件的文件路径。此文件的目录将用于导出其他内容。
            如果为 None，则文件将导出到 data\vent
- ***networkFilePath*** ：在此处导出MoosasAFN.exe输入文件。如果为 None，则文件将导出到 temp 目录
- ***split*** ：如果为 True，网络将自动拆分为多个隔离部分和文件。
- ***t0*** ： 室外温度。
- ***simulate*** ： 如果为 True，则调用 contamX，并将结果导出到 *.prj 目录。
- ***resultFile*** ：您将结果文件重定向到其他地方。

**return： list\[str] 对于我们得到的所有 prj 文件**
<br>从 model 或 pathList/zoneList 构建 *.prj 文件。 networkFile，model 和 pathList/zoneList 不能全部为 None。
这种方法可以直接将模型转换为CONTAM项目文件，我们需要的所有数据都会自动计算出来。
但是，您无法更改空间的任何设置。如果要编辑热设置，可以构建区域
和路径列表：

> **def getZoneAndPath(model:MoosasModel) -> list\[AfnZone] , list\[AfnPath]**

- ***model*** ： 我们从转译中得到的MoosasModel

**return** ：AFN 中的区域和路径列表，用于记录流网络的拓扑。
<br>您可以更改区域的初始温度或热负荷，或更改任何路径（孔径）上的风压。
它们只是一个记录数据的结构，如下所示：

```python
from python.Lib.MoosasPy.vent import getZoneAndPath, buildPrj
from python.Lib.MoosasPy.transformation import transform

model = transform(r'geo\selection0.geo', stdout=None)
zoneList, pathList = getZoneAndPath(model)
zoneList[0].heatLoad = 900  # unit in Watt (W)
pathList[0].pressure = 20.5  # unit in Pa
prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
```
除了CONTAM项目文件外，在进行浮力通风分析之前，我们还需要准备一件事。
我们使用 zoneInfo 文件作为浮力迭代的输入，可以由下式给出：
> **def buildZoneInfoFile(model: MoosasModel = None, zoneList: list\[AfnZone] = None, networkFilePath=None,
                      zoneInfoFilePath=None) -> str**

此方法可以通过以下方式生成 zoneInfo 文件：
- ***model*** ： MoosasModel，由 transforming.transform（） 方法给出
- ***zoneList*** ： list[AfnZone]，由 getZoneAndPath（） 方法给出
- ***networkFile***：由 buildNetworkFile（） 方法给出，或由 MoosasAFN.exe 等其他脚本构造
<br>zoneInfo 文件可以像这样解码：
<br>[[prjroomname， roomheatload， userroomname]..[]]
<br>其中：
- prjroomname：在 *.prj 文件中设置的房间名称，每个字符都必须相同
- roomheatload：房间的总负荷（W）。
- userroomname：用户定义的房间名称，将出现在结果文件中。

roomInfo 文件可以排除房间名称，仅提供 roomInfo，这意味着：
        房间热量文件只能有 2 列：
        [[prjroomname，roomheatload]...[]]
        在这种情况下，roomnome 将与 prjroomname 相同

或 2 列：
        [[roomheatload，usersroomname]...[]]
        在这种情况下，roomInfo 数据应与项目文件中的区域序列相同

或只有 1 列：
        [[房间热负荷]...[]]
        在这种情况下，RoomHeatload 数据应与项目文件中的区域序列相同

准备好所有数据后，可以通过以下方法开始迭代：

> **def iterateProjects(prjFiles, zoneInfoFiles, resultFile=None, 
> outdoorTemperature=25, maxIteration=50, exitResidual=0.01) -> list\[ZoneResult]**

- ***prjFiles*** ：单个 contam 项目文件。应在此文件中仔细定义初始室内温度。
        用户可以使用contamW3.exe通过 GUI 构建此文件。
        有关 contamX 和 contamW 的文档，请访问：
        https://www.nist.gov/el/energy-and-environment-division-73200/nist-multizone-modeling/software/contam/documentation
- ***zoneInfoFiles*** ： 此处应提供标准 roomInfo 文件或 roomInfo 数据：
        [[prjroomname， roomheatload， userroomname]..[]]
- ***resultFile*** ：迭代结果路径，将被编码为 csv。
        在此文件中，将记录温度变化和 ACH 中的体积公制流量。
        您可以在 FilePath['project_dir'] 中找到所有正在处理的 prj 文件，并通过 contamW 读取 Air Flow Network。
- ***outdoorTemperature*** ： 室外静态温度。
        请注意，contamX 中仅考虑室内/室外温差，
        这意味着 #25 室内 20 室外#等于 #20 室外 15 室内#。
- ***maxIteration*** ：最大迭代次数 contamX 应该运行。
- ***exitResidual*** ： 如果整体残差小于此值，则停止迭代

**return** ： list\[ZoneResult] 记录迭代中的每个数据和区域设置。
您可以通过以下示例完成迭代：

```python
from python.Lib.MoosasPy.vent.afn import getZoneAndPath, buildPrj, buildZoneInfoFile
from python.Lib.MoosasPy.transformation import transform
from python.Lib.MoosasPy.ventilation import contam_iteration

model = transform(r'geo\selection0.geo', stdout=None)
zoneList, pathList = getZoneAndPath(model)
zoneList[0].heatLoad = 900  # unit in Watt (W)
pathList[0].pressure = 20.5  # unit in Pa
prjFile = buildPrj(zoneList=zoneList, pathList=pathList)
zoneInfoFile = buildZoneInfoFile(zoneList=zoneList)
result = contam_iteration(prjFile=prjFile, zoneInfoFile=zoneInfoFile)
```

> **ZoneResult**

用于记录分析结果的结构。<br>
__slots__ = \['名称'， '热量'， '音量'， '用户名'， '温度'， 'ACH']

- ***name*** ： PRJ 文件中的区域名称
- ***heat*** ： 区域总热负荷
- ***volume*** ： 区域空间体积
- ***userName*** ：用户定义区域名称，默认值为 MoosasSpace.id
- ***temperature*** ： 如果无效，则为 C. inf 的温度结果的 list[float]。
- ***ACH*** ： 质量流量的列表[浮点数]，结果为 m3/h。 如果无效，则为 inf。

它可以与模型中的空间相匹配。MoosasSpaceList by userName：

```python
spaceIdList = [s.id for s in model.spaceList]
sortList = [spaceIdList.index(z.userName) for z in zResult]
zResult = np.array(zResult)[sortList]
```

### 日照计算
该模块提供考虑地点，气象，年份，冬令时的，针对任意时间点与时间段的日照统计。
该模块只有一个方法来实现这些功能：
> **def positionSunHour(positionRay: Ray | Iterable\[Ray], location: Location, sky: MoosasDirectSky = None,
                    model: MoosasModel = None, geo_path=None,
                    periodStart: datetime | DateTime = DateTime(1, 1, 0),
                    periodEnd: datetime | DateTime = DateTime(12, 31, 23),
                    leapYear: bool = False)->Iterable\[float]:**

- ***positionRay*** : Iterable\[Ray] 计算日照的position(origin, factor)。请尽可能一次性把所有的position
- ***location*** : Location 类型，可以从MoosasWeather中读取，而MoosasWeather的实例存放在model中:model.weather.location 
- ***sky*** : optional 另外创建的MoosasDirectSky模型。若需要定义更复杂的计算可传入，否则直接基于location创建
- ***model*** : optional MoosasModel用于导出几何体
- ***geo_path*** : optional *.geo file已经导出的几何体，model与geo_path至少提供一个
- ***periodStart*** : datetime | DateTime optional 日照计算的开始时间，可由utils.DateTime或者datetime.datetime定义
- ***periodEnd*** : datetime | DateTime optional 日照计算的结束时间，可由utils.DateTime或者datetime.datetime定义
- ***leapYear*** : optional bool to analysis a leap year

***returns***: Iterable\[float] 以日照小时数/日(h/d)定义的结果，长度与positionRay对应

<br>在调用该方法前必须先加载气象文件，即MoosasModel.loadWeatherData()方法

### 辐射计算
该模块提供用于能源和通风分析的太阳能热增益计算。
当然，也可以直接调用这个模块。它提供了多个连接
到不同规模的MoosasRad.exe。

> **pointRadiation(positionRay, sky: MoosasCumSky, model: MoosasModel = None, reflection=1, geo_path=None) -> list\[Ray]**

- ***positionRay*** ： Ray 或 list\[Ray] 来记录这些位置的原点和方向。
- ***sky*** ： cumSky 用于计算。你可以通过MoosasCumSky（）创建一个cumSky，或者使用这三个
MoosasModel 中的默认 cumSky：
<br>model.cumSky\['annualCumSky']<br>model.cumSky\['summerCumSky']<br>model.cumSky\['winterCumSky']
- ***model*** ： 由 transforming.transform（） 给出的 MoosasModel。模型和geo_path不能全部为“无”。
- ***geo_path*** ：.geo 文件路径。您可以通过 utils.writeGeo（） 方法编写地理文件
- ***reflection*** ： 计算中的反射次数，默认为 1。

每条射线的结果将以 ray.value 的形式记录，单位为 kWh/m2
<br>在调用该方法前必须先加载累积天空模型，即MoosasModel.loadCumSky()方法

> **spaceRadiation(space:MoosasSpce,reflection 1) -> MoosasSpce**

- ***space*** ： 模型中的MoosasSpace。MoosasSpace列表。在这种方法中，空间的数据将发生变化。
- ***reflection*** ： 计算中的反射次数，默认为 1。

> **modelRadiation(model: MoosasModel = None,reflection 1) -> MoosasSpce**

- ***model*** ： 由 transforming.transform（） 给出的 MoosasModel。
- ***reflection*** ： 计算中的反射次数，默认为 1。

此方法比 spaceRadiation 更快，因为它只调用MoosasRad.exe一次。
         MoosasRad 中的辐射计算是并行的。
<br> 为了更好地使用本模块，我们强烈建议您了解 Ray 类：

> **Ray(self, origin, direction, value=0)**

__slots__ = \['原点'， '方向'， '值']
    
- ***origin*** ： 射线的原点，矢量类型
- ***direction*** ： 射线的方向，矢量类型
- ***value*** ：用于存储相关数据，可以是任何数据格式
    
> **Vector(vec)**

__slots__ = \['x', 'y', 'z', 'style']
- ***vec*** : 皮吉奥斯。几何 （POINT） 或 np.ndarry 或列表。它将被强制为 3d （z=0）。

## Moosas+中的可执行程序(*.exe)
我们恳请为用户提供分析中的所有执行。它们用 Golang 编码，并启用它们的
并行计算，可以比python快得多。
> **MoosasEnergyPublic(Residential).exe**

在Moosas中，公共建筑和住宅建筑的能源计算是不同的。
<br>命令行应为：MoosasEnergyResidential.exe [-h，-w...] inputFile.i
<br>***可选命令***：
- **-h / -help** ： 转载帮助信息
- **-w / -weather** [weather file path.csv]：以 DeST 格式格式化的天气文件。 对于以 EPW 格式格式的文件，请使用 MoosasPy/weather.py 中的脚本
- **-t / -type** [0,1,2,3,4,5,6]：输入建筑类型：
<br>0 => 住宅
<br>1 => 办公室
<br>2 =>酒店
<br>3 => 学校
<br>4 => 商业
<br>5 =>歌剧
<br>6 => 医院
- **-l / -lat** ： 站点的纬度
- **-a / -alt** ： 场地海拔高度
- **-s / -shape** ： 建筑物的形状系数 = 总表面积 （m2） / 建筑总容积 （m3）
- **-o / -output** ： 输出文件路径（默认：.\MoosasEnergy.o）

例如，MoosasPy 中的命令行：
```commandline
libs\energy\MoosasEnergyResidential.exe -w db\weather\545110.csv -l 39.93 -a 55.0 -s 0.78 -o data\energy\Energy.o data\energy\Energy.i
```

> **MoosasRad.exe**

命令行应为：MoosasRad.exe [-h，-g...] inputFile.i<br>
可选命令***：
- ***-h / -help*** ： 转载帮助信息
- ***-g / -geo*** ： 射线测试内容的几何输入
- ***-o / -output*** ： 输出文件路径（默认：.\MoosasEnergy.o）

例如，MoosasPy 中的命令行：
```commandline
libs\rad\MoosasRad.exe -g __temp__\ray_0x01ce.geo -o __temp__\ray_0xf8f3.o __temp__\ray_0xf8f3.i
```

> **MoosasAFN.exe**

Moosas ContamX 生成器和阅读器。
<br>命令行应为：MoosasAFN.exe [-h，-p...] inputNetworkFile.net<br>
**可选命令**：
- ***-h / -help*** ： 转载帮助信息
- ***-p / -project*** ： prj 文件的基本名称（默认值：network）
- ***-d / -directory*** ： 放置项目文件和结果的目录（默认：执行目录）
- ***-o / -output*** ： 结果输出文件路径（默认：执行目录\airVel.o）
- ***-r / -run*** ： 如果对所有构建的 *.prj 文件运行 contamX 并收集结果，则为 1（默认值：0）
- ***-s / -split*** ： 如果将输入网络拆分为多个网络，则为 1（默认值：1）
- ***-t / -t0*** ： OutdoorTemperature（默认值：25）

例如，MoosasPy 中的命令行：
```commandline
libs\vent\MoosasAFN.exe -p afn_0x6a94 -d data\vent -t 25 -s 0 __temp__\0xe2i8.net
```

## File Structure
Moosas+ 中的所有输入和输出文件都采用相同的文件结构进行编码：<br>
'！' 表示以下字符串是直到行尾的注释;<br>
';' 块被 ';' 拆分<br>
块中的“\n”项由“\n”<br>拆分
空行有效。它将被重新分级为空数据<br>

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
    
您可以使用此方法解析文件：
> **utils.parseFile(file_path) -> list\[list\[list\[str]]]**

特别是，这些是每个输入和输出的详细文件结构：
（注释不是必要的）

### Geometry
#### *.geo File
.geo 是一种 moosasPy 专用文件格式，它使用简化的文件结构来提高 I/O 速度。
.geo 文件格式如下：<br>
（猫：0 是不透明表面，1 是半透明表面，2 是空气边界）

        f,{polygon type cat},{polygon number idd}       ! Face's info
        fn, {normal x}, {normal y}, {normal z}          ! Face's normal
        fv, {vertex 1x}, {vertex 1y}, {vertex 1z}       ! Face's outer loop verties in sequence 
        ...
        fv,{vertex nx},{vertex ny},{vertex nz}          ! Face's outer loop verties in sequence 
        fh,{aperture n},{vertex 1x},{vertex 1y},{vertex 1z} ! Holes' verties in sequence 
        ...
        fh,{aperture n},{vertex nx},{vertex ny},{vertex nz} ! Holes' verties in sequence 
        ;                                               ! A face should end with ';'

例如，有两个垂直面，有两个开口，具有正 x 轴法向量：

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
#### <a id="spaceFile">space File</a>
几何图形和空间的输出/输入文件可以格式化为不同的类型： <br>
*.xml、*.json、stringFile（用于空间信息）<br>
*.geojson， *.geo （用于几何信息）<br>
由于各种输出的底层都是相同的，所以他们采用了相同的结构与命名，此处以xml文件为例。
文件中存在三个级别的数据：
> space/void: 虚空间或实空间，包含0-1个floor/edge/ceiling
>> floor/edge/ceiling: 空间的楼板/边界/天花，包含若干个face
>>> face: 几何面

face数据结构:
```xml
<face>面
    <Uid>该组合面的Uid,随机生成，并不与形状挂钩</Uid>
    <faceid>geo文件中的id, 即faceid，可能包含多个,sep = " "</faceid>
    <level>该组合面所在楼层</level>
    <offset>该组合面针对楼层的偏移</offset>
    <area>面的面积,单位(m2)</area>
    <glazingid>附着在面上的透明面或空气墙,以faceid给出,可能包含多个sep = " "</glazingid>
    <height>面的标高,可能经过修正</height>
    <normal>面的法向量，朝向空间外部,sep = " "(x y z)</normal>
    <external>是否为外立面/屋面/基础地面</external>
    <space>面所属的空间Uid</space>
</face>
```
floor/edge/ceiling数据结构:
```xml
<topology>
    <floor>楼板/地面，由若干个face组成
        <face>...</face>
    </floor>
    <ceiling>屋顶/天花，由若干个face组成
        <face>...</face>
    </ceiling>
    <edge>房间边界(二级空间边界),由若干个face组成
        <face>...</face>
    </edge>
</topology>
```
space 数据结构:
```xml
<model>
    <space>
        <id>空间id,根据房间形体、位置计算获得，多次识别获得相同id</id>
        <area>空间面积(m2)</area>
        <height>空间高度(m)</height>
        <boundary>空间平面边界(一级空间边界),按顺序给出点,不包含闭合点
            <pt>点x 点y 点z</pt>
            <pt>216.53 393.70 0.0</pt>
            <pt>... ... ...</pt>
            <pt>216.53 177.16 0.0</pt>
        </boundary>
        <internal_wall>内部孤立墙体,模拟中将被认为是蓄热体
            <face>...</face>
        </internal_wall>
        <topology>
            <floor>...</floor>
            <ceiling>...</ceiling>
            <edge>...</edge>
        </topology>
        <neighbor>相邻空间
            <faceId>Faceid指该相邻空间的连接面,可能包含多个,sep = " "</faceId>
            <id>相邻空间的id</id>
        </neighbor>
        <setting>空间的热工参数, 详见MoosasEnergy相关信息
            ...
        </setting>
        <void>此空间的负形, 同样为space数据
            ...
        </void>
    </space>
</model>
```

### File for MoosasEnergy.exe
#### input
总共有 27 个参数，其中 10 个用于房间几何属性，17 个用于热属性。
您应该将所有房间放在一个街区中作为不同的项目

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
输出文件中有 3 个不同的块，记录总/空间/每月能量负荷结果。
它的可读性很强：

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
输入几何的格式为 *.geo
输入的光线文件如下：
    
    ! This file has only one block
    ! x,y,z for the origin and x,y,z for the direction
    0,0,0,0,0,1
    ......

#### output
此模块的输出也格式化为射线，建议每条射线的反射：

    ! This file has only one block
    ! x,y,z for the origin and x,y,z for the direction
    3.5,4.4,2.8,0,0,-1
    ......
    ! reflection is invalid if the origin is -1,-1,-1
    -1,-1,-1,0,0,1
    ......

### File for MoosasAfn.exe
#### networkFile
此文件显示建筑物的拓扑。<br>
区域项目有 9 个参数：
- ***zoneName*** ： 用户定义 zoneName
- ***heatLoad*** ： 总热负荷，单位：瓦特 （W）
- ***温度*** ： 区域初始温度 （C）
- ***体积*** ： 区域体积 （m3）
- ***positionX，positionY，positionZ*** ： 以米 （m） 为单位与区域匹配的位置
- ***boundaryPolygon*** ： 以米 （m） 为单位定义区域边界，以 ' ' 为 sep

路径项有 10 个参数：
- ***pathName*** ： 用户定义路径名
- ***pathIndex*** ： prj 文件中的路径索引
- ***height*** ： 孔径高度（米）
- ***width*** ： 孔径宽度（米）
- ***positionX，positionY，positionZ*** ： 与路径匹配的位置，单位为米 （m）
- ***fromZone*** ： 路径从的区域索引
- ***toZone*** ：路径指向的区域索引
- ***pressure*** ： 如果连接到室外，路径的风压

它有两个块，例如：

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
zoneInfo itmes 可以这样解码：

        prjroomname, roomheatload, userroomname
        in which:
            prjroomname: the room name set in the *.prj file, must be the same in every character
            roomheatload: the gross load of the room in (W).
            userroomname: the room name define by the users, and it will occur in the result file.

roomInfo 文件可以排除房间名称，仅提供 roomInfo，这意味着：
房间热量文件只能有 2 列：<br>
        prjroomname，roomheatload<br>
在这种情况下，roomnome 将与 prjroomname <br>相同
或 2 列：<br>
房间热荷，用户房间名称<br>
在这种情况下，roomInfo 数据应与项目文件中<br>的区域序列相同
        或只有 1 列：<br>
        房间热负荷<br>
        在这种情况下，RoomHeatload 数据应与项目文件中的区域序列相同

## Credits and acknowledgements
Developed by Research team directed by **Prof. Borong Lin** from Key Laboratory of Eco Planning & Green Building, Ministry of Education, Tsinghua University.
<br> All Right Reserved.
<br> For collaboration, Please contact:
<br> linbr@mails.tsinghua.edu.cn
<br> If you have any technical problems, Please reach to:
<br> junx026@gmail.com

