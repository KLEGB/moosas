# 从 GEO 到 OpenFOAM：导出算例

OpenFOAM 只通过 `MoosasPy.model.io.foam.exportFoam` 导出；通用的 `model.save(...)` / `save_model(model, ...)` 不接受 `.foam`：

```python
from MoosasPy.transform import transform
from MoosasPy.model.io.foam import exportFoam

model = transform("test/caseFile/test0_6spacesIntersection.geo", input_type="geo")
model.save("building.idf")
exportFoam(model, "cases/room/room.foam", space_index=0, grid_size=1.0, layers=8)
```

`exportFoam` 显式接收 `space_index`、`grid_size`、`layers`、`scenario` 和 `conditions` 参数。`SaveResult.primary_path` 是传入的目标文件；
OpenFOAM 的 `.foam` 是 ParaView 入口，其父目录就是算例目录。
`generated_paths` 列出保存操作生成的全部文件。`load` 不支持读取 `.foam`。

## 1. 准备运行环境

保存算例不依赖 OpenFOAM。生成 CFD 网格、检查和求解需要
**OpenFOAM Foundation 12**，并确保这些命令及动态库在环境中可用：

`surfaceCheck`、`blockMesh`、`snappyHexMesh`、`checkMesh`、`foamRun`。

Linux 请按安装说明加载 OpenFOAM 12 的 `etc/bashrc`。
本机使用已安装的 blueCFD-Core 2024。PowerShell 可在当前会话中配置：

```powershell
$foamRoot = "C:/Program Files/blueCFD-Core-2024/OpenFOAM-12"
$foamPlatform = "$foamRoot/platforms/mingw_w64Gcc122DPInt32Opt"
$env:WM_PROJECT_DIR = $foamRoot
$env:FOAM_ETC = "$foamRoot/etc"
$env:FOAM_LIBBIN = "$foamPlatform/lib"
$env:PATH = "$foamPlatform/bin;$foamPlatform/lib;$foamPlatform/lib/dummy;C:/Program Files/blueCFD-Core-2024/msys64/mingw64/bin;C:/Program Files/blueCFD-Core-2024/ThirdParty-12/platforms/mingw_w64Gcc122DPInt32/lib;$env:PATH"
checkMesh -help
```

以下命令从仓库根目录执行。本机 Python 是 `./.venv/Scripts/python.exe`；
其他环境替换为安装了 MoosasPy 的 Python。

## 2. 室内空气流动

首轮支持一个房间、一个指定入口和一个指定出口，计算等温速度场和压力场。
GEO 不包含完整运行工况，需要另外提供边界条件。

以下代码使用 `test6_twoVolumes.geo` 的第 37 个空间，入口为
`gls_g_80`、出口为 `gls_g_79`。在仓库根目录运行：

```python
from MoosasPy.transform import transform
from MoosasPy.model.io.foam import exportFoam

model = transform("test/caseFile/test6_twoVolumes.geo", input_type="geo")
conditions = {
    "viscosity": 1.5e-5,
    "turbulence_intensity": 0.05,
    "turbulence_length": 1.0,
    "iterations": 1000,
    "inlet": {"opening": "gls_g_80", "velocity": [0.409451, 0.286966, 0.0]},
    "outlet": {"opening": "gls_g_79", "pressure": 0.0},
}
saved = exportFoam(
    model,
    "cases/indoor/case.foam",
    scenario="indoor",
    space_index=37,
    grid_size=2,
    conditions=conditions,
)
print(saved.primary_path.parent)  # 交给 OpenFOAM 的算例目录
```

工况参数中：

- `inlet.opening`：选中房间的窗或天窗 `Uid`。
- `inlet.velocity`：世界坐标系下的速度向量，单位 m/s，必须指向房间内部。
- `outlet.opening`：另一个开口的 `Uid`。
- `outlet.pressure`：运动学表压，单位 m²/s²，即表压除以密度；0 表示参考压力。
- 未指定为入口或出口的窗保持封闭；墙面为无滑移边界。

自己的 GEO 应先查看房间和开口：

```python
for index, space in enumerate(model.spaceList):
    faces = space.getAllFaces(to_dict=True)
    openings = faces["MoosasGlazing"] + faces["MoosasSkylight"]
    print(index, space.id, [(opening.Uid, opening.area) for opening in openings])
```

不能把示例的开口 ID 直接套用到另一个 GEO。
模型没有所需开口时，应补充实际开口几何；程序不会替用户虚构送排风口。

## 3. 室外风环境

以下代码使用 `test0_6spacesIntersection.geo` 的完整建筑外表面：

```python
from MoosasPy.transform import transform
from MoosasPy.model.io.foam import exportFoam

model = transform("test/caseFile/test0_6spacesIntersection.geo", input_type="geo")
conditions = {
    "viscosity": 1.5e-5,
    "turbulence_intensity": 0.05,
    "turbulence_length": 1.0,
    "iterations": 1000,
    "velocity": [2.0, 0.0, 0.0],
    "domain": [[-100.0, 120.0, 0.0], [0.0, 240.0, 45.0]],
    "inside_point": [-90.0, 130.0, 5.0],
}
saved = exportFoam(
    model,
    "cases/outdoor/case.foam",
    scenario="outdoor",
    grid_size=4,
    conditions=conditions,
)
print(saved.primary_path.parent)  # 交给 OpenFOAM 的算例目录
```

室外不传 `space_index`。额外工况字段：

- `velocity`：世界坐标下的水平来流向量，单位 m/s，风向由该向量定义。
- `domain`：计算域最小、最大 XYZ 坐标，单位 m，必须容纳建筑。
- `inside_point`：严格处于计算域内、建筑外的空气点，用于网格区域选择。

四个竖直外边界根据风向分别设为入口、出口或对称面。
顶面为对称面；地面和建筑外墙为无滑移壁面。
本轮使用**均匀来流和光滑地面**，尚未实现大气边界层风速剖面或地表粗糙度。

## 4. 两种 CFD 场景的共同配置

`conditions` 必须明确提供以下物理参数：

| 字段 | 含义 |
| --- | --- |
| `viscosity` | 运动黏度，m²/s |
| `turbulence_intensity` | 来流湍流强度，小数比例，如 0.05 |
| `turbulence_length` | 来流湍流长度尺度，m |
| `iterations` | 稳态求解的最大迭代次数 |

采用稳态、等温、不可压缩 RANS，湍流模型为 k-epsilon。
入口 k 和 epsilon 由速度、湍流强度及长度尺度计算。
`grid_size` 是背景网格间距；表面细化一级，最终单元形状由 snappyHexMesh 生成。
`layers` 仅用于下文的单房间网格导出，不适用于 CFD 场景。

算例保存后包含三角表面、网格配置、物性、初始场和求解字典：

```text
case.foam
0/{U,p,k,epsilon,nut}
constant/{physicalProperties,momentumTransport,moosasCase.json}
constant/geometry/model.stl
system/{blockMeshDict,snappyHexMeshDict,meshQualityDict,controlDict,fvSchemes,fvSolution}
```

`moosasCase.json` 保存场景、模型空间、网格间距和用户工况，便于复现。
CFD 算例要求目标目录为空，避免混入旧结果。

## 5. 在 OpenFOAM 中运行

MoosasPy 到导出算例为止，不启动网格工具或求解器，也不判断收敛。
在已加载 OpenFOAM Foundation 12 环境的终端中进入算例目录，再由 OpenFOAM 执行：

```sh
surfaceCheck constant/geometry/model.stl
blockMesh
snappyHexMesh -overwrite
checkMesh -allTopology -meshQuality
foamRun -solver incompressibleFluid
```

检查命令输出及 `postProcessing/flow_*` 中的边界流量；用 ParaView 打开
`case.foam` 查看 U、p。求解结果、收敛判断和失败处理由外部 OpenFOAM 工作流负责。

## 6. 仅导出单房间体网格

默认 `scenario="mesh"` 保留无需 OpenFOAM 的网格保存功能：

```python
exportFoam(model, "cases/room/room.foam", space_index=0, grid_size=1, layers=8)
```

必须指定房间；只支持一个水平楼板的等截面拉伸。
高度取自模型，底部为楼板标高。默认边界为 bottom、top、walls。
生成五个 `constant/polyMesh` 文件、`constant/moosasGrid.json` 和 `.foam` 标记，
不生成求解设置或初始场。

映射文件保存采样点、层高以及单元对应的网格和采样索引。
边缘裁切可能改变单元中心；无对应采样点的单元标为 null。
采样高度为楼板以上 0.78 m，体网格从楼板本身开始。
这个映射仅属于直接拉伸的网格；snappyHexMesh 的 CFD 算例不提供该映射。

## 7. 验证与适用范围

```powershell
./.venv/Scripts/python.exe -m pytest -q
```

OpenFOAM 在 PATH 中时，测试会真正执行原生程序；缺少程序时，原生集成测试会明确跳过。
仅通过 Python 测试不能代替实际求解验证。

已验证案例：

| 场景 | 真实 GEO | 设置 | 收敛步 | 相对流量不平衡 |
| --- | --- | --- | --- | --- |
| 室内 | test6_twoVolumes.geo | 空间 37，背景网格 2 m | 166 | 1.82e-12 |
| 室外 | test0_6spacesIntersection.geo | 背景网格 4 m | 344 | 2.78e-12 |

本机复核产物在 `temp/openfoam-indoor-verified` 和 `temp/openfoam-outdoor-verified`。
另外，test0 的全部六个房间和 test3_geomove 均有专用导出入口的网格回归测试，
原有 IDF 保存由 I/O 测试继续覆盖。

几何表面按项目既有的 0.01 m 精度合并顶点、匹配共享边、去除重复面并统一法向；
仍未闭合的表面直接报错。小于该精度的细节不适用。
当前室内流程处理单个封闭房间；内部障碍物、多房间耦合、温度、浮力和污染物输运不在本轮范围内。

这些示例用于验证完整工作流，采用较粗网格。工程使用还需做网格独立性、
开口面积分辨率和计算域尺寸检查。
贴体多面体网格可能包含凹单元；`-allGeometry` 的额外严格凹性检查会报告这些单元。
这里按完整拓扑检查及明确的质量限值验收，未把示例声称为工程精度验证。

参考：[OpenFOAM 12 算例结构](https://doc.cfd.direct/openfoam/user-guide-v12/case-file-structure)。
