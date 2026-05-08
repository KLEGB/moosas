
This is an auto-generated documentation for Ruby files by tongyi AI, including classes, global methods and their comments.
The description may have confusion due to the poor interpretability of LLM. If you are confused please directly contact me.

# Project Documentation

## 📁 Folder Structure
```
📂 **MoosasPy**
├── 📂 data
├── 📂 db
├── 📂 doc
├── 📂 encoding
├── 📂 geometry
├── 📂 IO
├── 📂 libs
├── 📂 rad
├── 📂 src
├── 📂 thermal
├── 📂 utils
├── 📂 vent
├── 📂 view
├── 📂 visual
├── 📂 weather
├── 📂 __pycache__
├── 📂 __temp__
├── 📄 [daylightFactor.py](#daylightFactor_py)
├── 📄 [daylighting.py](#daylighting_py)
├── 📄 [encoding.py](#encoding_py)
├── 📄 [energy.py](#energy_py)
├── 📄 [models.py](#models_py)
├── 📄 [preprocess.py](#preprocess_py)
├── 📄 [radiation.py](#radiation_py)
├── 📄 [sunhour.py](#sunhour_py)
└── 📄 [transformation.py](#transformation_py)
├── 📂 energy
├── 📂 geometry
├── 📂 script
└── 📂 vent
│   ├── 📂 project
├── 📂 cum_sky
├── 📂 settings
├── 📂 weather
├── 📂 __pycache__
├── 📄 [convexify.py](#encoding_convexify_py)
├── 📄 [graph.py](#encoding_graph_py)
├── 📄 [graphIO.py](#encoding_graphIO_py)
├── 📄 [main.py](#encoding_main_py)
└── 📄 [quad.py](#encoding_quad_py)
├── 📂 __pycache__
├── 📄 [cleanse.py](#geometry_cleanse_py)
├── 📄 [contour.py](#geometry_contour_py)
├── 📄 [contour_lagacy.py](#geometry_contour_lagacy_py)
├── 📄 [element.py](#geometry_element_py)
├── 📄 [geos.py](#geometry_geos_py)
├── 📄 [grid.py](#geometry_grid_py)
├── 📄 [spaceGen.py](#geometry_spaceGen_py)
├── 📄 [topology.py](#geometry_topology_py)
├── 📄 [viewFactor.py](#geometry_viewFactor_py)
└── 📄 [visualization.py](#geometry_visualization_py)
├── 📂 __pycache__
├── 📄 [transIO.py](#IO_transIO_py)
├── 📄 [_geo.py](#IO__geo_py)
├── 📄 [_idf.py](#IO__idf_py)
├── 📄 [_json.py](#IO__json_py)
├── 📄 [_obj.py](#IO__obj_py)
├── 📄 [_rdf.py](#IO__rdf_py)
└── 📄 [_xml.py](#IO__xml_py)
├── 📂 .idea
├── 📂 energy
├── 📂 json
├── 📂 rad
├── 📂 ui
├── 📂 vent
├── 📂 weather
│   ├── 📂 .idea
│   ├── 📂 add
│   ├── 📂 pure
│   ├── 📂 bootstrap
│   ├── 📂 css
│   ├── 📂 fonts
│   ├── 📂 gijgo
│   ├── 📂 images
│   ├── 📂 js
│   │   ├── 📂 css
│   │   ├── 📂 fonts
│   │   └── 📂 js
│   │   │   ├── 📂 plugin
│   │   │   ├── 📂 vendor
│   │   ├── 📂 images
│   │   ├── 📂 0.5x
│   │   ├── 📂 1x
│   │   ├── 📂 legacy
│   │   ├── 📂 textures
│   │   ├── 📂 ext
│   ├── 📂 afn
│   ├── 📂 contam
│   ├── 📂 mkdir
│   ├── 📂 thermal
│   ├── 📂 triangulate
├── 📂 __pycache__
├── 📄 [radiance.py](#rad_radiance_py)
└── 📄 [radiation.py](#rad_radiation_py)
├── 📂 __pycache__
├── 📄 [buildingFaces.py](#thermal_buildingFaces_py)
├── 📄 [construction.py](#thermal_construction_py)
├── 📄 [idfGeometry.py](#thermal_idfGeometry_py)
├── 📄 [schedule.py](#thermal_schedule_py)
└── 📄 [settings.py](#thermal_settings_py)
├── 📂 __pycache__
├── 📄 [constant.py](#utils_constant_py)
├── 📄 [date.py](#utils_date_py)
├── 📄 [error.py](#utils_error_py)
├── 📄 [standard.py](#utils_standard_py)
├── 📄 [support.py](#utils_support_py)
└── 📄 [tools.py](#utils_tools_py)
├── 📂 __pycache__
├── 📄 [afn.py](#vent_afn_py)
├── 📄 [conread.py](#vent_conread_py)
├── 📄 [iteration.py](#vent_iteration_py)
└── 📄 [ventXgb.py](#vent_ventXgb_py)
├── 📂 __pycache__
└── 📄 [geometry.py](#visual_geometry_py)
├── 📂 __pycache__
├── 📄 [cumsky.py](#weather_cumsky_py)
├── 📄 [dest.py](#weather_dest_py)
├── 📄 [directsky.py](#weather_directsky_py)
└── 📄 [include.py](#weather_include_py)
```

## 📄 File: daylightFactor.py
<a id='daylightFactor_py'></a>

### Contents
- Functions:
  - [spaceDaylightFactor_quick()](#daylightFactor_py_func_spaceDaylightFactor_quick)
  - [spaceDaylightFactor()](#daylightFactor_py_func_spaceDaylightFactor)

---

### 🔧 Functions
###### <a id='daylightFactor_py_func_spaceDaylightFactor_quick'></a>`spaceDaylightFactor_quick`
- **Type:** Function
- **Parameters:** space: MoosasSpace, light_transmittance: Any
- **Returns:** float
    the daylight factor
- **Comments:**
  > Function:
  > a very simple model to predict the daylight factor of a space
  > Parameters:
  > space : MoosasSpace
  >     the space
  > light_transmittance : float
  >     the light transmittance of the glazing
  > 
  > Returns
  > float
  >     the daylight factor
  > Returns:
  > float
  >     the daylight factor

---

###### <a id='daylightFactor_py_func_spaceDaylightFactor'></a>`spaceDaylightFactor`
- **Type:** Function
- **Parameters:** space: MoosasSpace, light_transmittance: Any
- **Returns:** float
    the daylight factor
- **Comments:**
  > Function:
  > grid based method to calculate the daylight factor of a space
  > Parameters:
  > space : MoosasSpace
  >     the space
  > light_transmittance : float
  >     the light transmittance of the glazing
  > 
  > Returns
  > float
  >     the daylight factor
  > Returns:
  > float
  >     the daylight factor

---


## 📄 File: daylighting.py
<a id='daylighting_py'></a>

### Contents
- Functions:
  - [simModel()](#daylighting_py_func_simModel)
  - [_generateRadGeo()](#daylighting_py_func__generateRadGeo)
  - [modelToRad()](#daylighting_py_func_modelToRad)
  - [triOpaque()](#daylighting_py_func_triOpaque)
  - [spaceToRad()](#daylighting_py_func_spaceToRad)
  - [writeGrid()](#daylighting_py_func_writeGrid)

---

### 🔧 Functions
###### <a id='daylighting_py_func_simModel'></a>`simModel`
- **Type:** Function
- **Parameters:** model: MoosasModel, date: datetime, skyType: Any, lat: Any, lon: Any, diff: Any, radPath: Any, gridPath: Any
- **Returns:** dict
    the daylighting simulation result on the floor:
    [{df:daylight factor, satisfied: satification}...{}]
- **Comments:**
  > Function:
  > Simulate a model by embedded RADIANCE module.
  > gensky.exe is implemented with the params input.
  > Parameters:
  > model : MoosasModel
  >     the model for simulation
  > date : datetime
  >     the date to generate the sky
  > skyType : str
  >     the skyType hint for radiance, -c means the cloudy sky
  > lat : float
  >     latitude of the location
  > lon : float
  >     longitude of the location
  > diff : float , optional
  >     diffuse illuminance for the cloudy sky (Default : 15000)
  > radPath : str , optional
  >     redirect the rad output file.
  > gridPath : str , optional
  >     redirect the grid output file
  > 
  > Returns
  > dict
  >     the daylighting simulation result on the floor:
  >     [{df:daylight factor, satisfied: satification}...{}]
  > Returns:
  > dict
  >     the daylighting simulation result on the floor:
  >     [{df:daylight factor, satisfied: satification}...{}]

---

###### <a id='daylighting_py_func__generateRadGeo'></a>`_generateRadGeo`
- **Type:** Function
- **Parameters:** roof: Any, floor: Any, others: Any
- **Returns:** str
    A string containing the Radiance-formatted geometry representation.
- **Comments:**
  > Function:
  > Generate a Radiance geometry string from roof, floor, and other building elements.
  > Parameters:
  > roof : list of MeshFace
  >     List of mesh faces representing the roof elements.
  > floor : list of MeshFace
  >     List of mesh faces representing the floor elements.
  > others : list of MeshFace
  >     List of mesh faces representing other elements (e.g., walls, glazing).
  >     The category attribute of each face determines its treatment:
  >     category 0 for walls, category 1 for glazing.
  > 
  > Returns
  > str
  >     A string containing the Radiance-formatted geometry representation.
  > Returns:
  > str
  >     A string containing the Radiance-formatted geometry representation.

---

###### <a id='daylighting_py_func_modelToRad'></a>`modelToRad`
- **Type:** Function
- **Parameters:** model: MoosasModel, date: datetime, skyType: Any, lat: Any, lon: Any, diff: Any, radPath: Any
- **Returns:** str
    The complete Radiance input string containing sky, materials, and geometry definitions.
- **Comments:**
  > Function:
  > Convert a MoosasModel to a Radiance input file (.rad) string and write it to disk.
  > Parameters:
  > model : MoosasModel
  >     The building model containing spaces, walls, glazing, and other geometry.
  > date : datetime
  >     The date and time for which the sky conditions are generated.
  > skyType : object
  >     Specifies the type of sky (e.g., sunny, cloudy) for Radiance sky generation.
  > lat : float or int
  >     Latitude of the site in degrees, used for solar position calculation.
  > lon : float or int
  >     Longitude of the site in degrees, used for solar position calculation.
  > diff : int, optional
  >     Diffuse solar irradiance value (in W/m²). Default is 10000.
  > radPath : str, optional
  >     File path where the generated .rad file will be saved. Default is a path within `path.libDir`.
  > 
  > Returns
  > str
  >     The complete Radiance input string containing sky, materials, and geometry definitions.
  > Returns:
  > str
  >     The complete Radiance input string containing sky, materials, and geometry definitions.

---

###### <a id='daylighting_py_func_triOpaque'></a>`triOpaque`
- **Type:** Function
- **Parameters:** moFace: MoosasElement
- **Returns:** list[pygeos.Geometry]
    A list of pygeos Geometry objects representing the triangulated opaque regions in world coordinates,
    with glazing areas subtracted as holes and projected back from UV to 3D space.
- **Comments:**
  > Function:
  > Compute triangulated opaque geometry from a MoosasElement face.
  > Parameters:
  > moFace : MoosasElement
  >     The input MoosasElement containing the face and glazing elements. The face is used to generate base geometry,
  >     and its normal is used for projection. Glazing elements are treated as holes in the base face.
  > 
  > Returns
  > list[pygeos.Geometry]
  >     A list of pygeos Geometry objects representing the triangulated opaque regions in world coordinates,
  >     with glazing areas subtracted as holes and projected back from UV to 3D space.
  > Returns:
  > list[pygeos.Geometry]
  >     A list of pygeos Geometry objects representing the triangulated opaque regions in world coordinates,
  >     with glazing areas subtracted as holes and projected back from UV to 3D space.

---

###### <a id='daylighting_py_func_spaceToRad'></a>`spaceToRad`
- **Type:** Function
- **Parameters:** space: MoosasSpace, date: datetime, skyType: Any, lat: Any, lon: Any, diff: Any, radPath: Any
- **Returns:** str
    The complete Radiance input string, including sky, materials, and geometry definitions.
- **Comments:**
  > Function:
  > Generate a Radiance input file string and write it to disk based on the provided space geometry and environmental conditions.
  > Parameters:
  > space : MoosasSpace
  >     The space object containing the 3D geometry, from which faces are extracted.
  > date : datetime
  >     The date and time for which the sky conditions are computed.
  > skyType : object
  >     Specifies the type of sky model to use (e.g., sunny, cloudy); passed to `_getSky`.
  > lat : float or int
  >     Latitude of the location, used in sky calculation.
  > lon : float or int
  >     Longitude of the location, used in sky calculation.
  > diff : int, optional
  >     Diffuse solar radiation value (in Wh/m²), default is 10000.
  > radPath : str, optional
  >     File path where the Radiance script will be saved. Defaults to a path in `path.libDir`.
  > 
  > Returns
  > str
  >     The complete Radiance input string, including sky, materials, and geometry definitions.
  > Returns:
  > str
  >     The complete Radiance input string, including sky, materials, and geometry definitions.

---

###### <a id='daylighting_py_func_writeGrid'></a>`writeGrid`
- **Type:** Function
- **Parameters:** element: MoosasElement, gridPath: Any, normal: Any, append: Any
- **Returns:** list of str
    List of formatted strings representing grid points and normals written to the file.
- **Comments:**
  > Function:
  > Write grid points and their normal vectors to a file.
  > Parameters:
  > element : MoosasElement
  >     The element used to generate the grid.
  > gridPath : str, optional
  >     Path to the output file where grid data will be written. Default is constructed using `path.libDir`.
  > normal : array-like or Vector, optional
  >     Normal vector to be written with each point; if None, uses the grid's default normal. Default is None.
  > append : bool, optional
  >     If True, appends to the file; otherwise, overwrites it. Default is True.
  > 
  > Returns
  > list of str
  >     List of formatted strings representing grid points and normals written to the file.
  > Returns:
  > list of str
  >     List of formatted strings representing grid points and normals written to the file.

---


## 📄 File: encoding.py
<a id='encoding_py'></a>

### Contents
- Classes:
  - [Moosasboundary](#encoding_py_class_Moosasboundary)
- Functions:
  - [encodingModel()](#encoding_py_func_encodingModel)
  - [standarizeSpace()](#encoding_py_func_standarizeSpace)

---

### 📦 Class: Moosasboundary
<a id='encoding_py_class_Moosasboundary'></a>
**Description:** No class documentation.

#### Methods
###### <a id='encoding_py_class_Moosasboundary_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, polygon: pygeos.Geometry
- **Returns:** None
    This method initializes instance attributes and does not return any value.
- **Comments:**
  > Function:
  > Initialize the object with a polygon geometry and compute transformed edges based on angular thresholds.
  > Parameters:
  > polygon : pygeos.Geometry
  >     A PyGEOS geometry object representing a polygon. The polygon's coordinates are used to create edge linestrings
  >     and apply transformations based on alignment with orthogonal basis vectors.
  > 
  > Returns
  > None
  >     This method initializes instance attributes and does not return any value.
  > Returns:
  > None
  >     This method initializes instance attributes and does not return any value.

---

###### <a id='encoding_py_class_Moosasboundary_method_regularize'></a>`regularize`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** object
    The result of connecting the regular edge segment, type depends on `connectSegment` implementation.
- **Comments:**
  > Function:
  > Regularize the edge by connecting segments.
  > Parameters:
  > self : object
  >     The instance of the class containing the `regularEdge` attribute and `connectSegment` method.
  > 
  > Returns
  > object
  >     The result of connecting the regular edge segment, type depends on `connectSegment` implementation.
  > Returns:
  > object
  >     The result of connecting the regular edge segment, type depends on `connectSegment` implementation.

---

###### <a id='encoding_py_class_Moosasboundary_method_connectSegment'></a>`connectSegment`
- **Type:** Instance Method
- **Parameters:** self: Any, segments: Any
- **Returns:** pygeos.geometry.Polygon
    A closed polygon formed by connecting the input segments, with intersections computed at joints.
    If consecutive segments are parallel, their common vertex is replaced with an intersection point 
    from the previous and current segment to ensure proper closure and geometry continuity.
- **Comments:**
  > Function:
  > Connect a sequence of line segments into a closed polygon, handling parallel segments.
  > Parameters:
  > self : object
  >     The instance of the class containing this method.
  > segments : array-like of pygeos geometries (LineString)
  >     A sequence of line segment geometries. Each segment is expected to be a two-point LineString.
  > 
  > Returns
  > pygeos.geometry.Polygon
  >     A closed polygon formed by connecting the input segments, with intersections computed at joints.
  >     If consecutive segments are parallel, their common vertex is replaced with an intersection point 
  >     from the previous and current segment to ensure proper closure and geometry continuity.
  > Returns:
  > pygeos.geometry.Polygon
  >     A closed polygon formed by connecting the input segments, with intersections computed at joints.
  >     If consecutive segments are parallel, their common vertex is replaced with an intersection point 
  >     from the previous and current segment to ensure proper closure and geometry continuity.

---

###### <a id='encoding_py_class_Moosasboundary_method_deRegularize'></a>`deRegularize`
- **Type:** Instance Method
- **Parameters:** self: Any, geo: pygeos.Geometry
- **Returns:** pygeos.Geometry
    A reconnected geometry formed by transforming and connecting de-regularized edges.
- **Comments:**
  > Function:
  > De-regularizes a geometry by applying transformation based on a reference regularized polygon.
  > Parameters:
  > geo : pygeos.Geometry
  >     Input geometry whose coordinate structure is used to compute new edge transformations.
  >     Must have the same number of coordinates as the original regularized polygon.
  > 
  > Returns
  > pygeos.Geometry
  >     A reconnected geometry formed by transforming and connecting de-regularized edges.
  > Returns:
  > pygeos.Geometry
  >     A reconnected geometry formed by transforming and connecting de-regularized edges.

---

###### <a id='encoding_py_class_Moosasboundary_method_getRadius'></a>`getRadius`
- **Type:** Instance Method
- **Parameters:** self: Any, axis: Any, vector: Any
- **Returns:** float
    The signed angle (in radians) between the axis and vector. Positive if counter-clockwise,
    negative if clockwise when viewed along the [0,0,1] direction.
- **Comments:**
  > Function:
  > Calculate the signed angular radius between a given axis and vector.
  > Parameters:
  > axis : array-like
  >     The reference axis direction as a 3D vector. Will be converted to a numpy array.
  > vector : array-like
  >     The input vector as a 3D vector. Will be converted to a numpy array.
  > 
  > Returns
  > float
  >     The signed angle (in radians) between the axis and vector. Positive if counter-clockwise,
  >     negative if clockwise when viewed along the [0,0,1] direction.
  > Returns:
  > float
  >     The signed angle (in radians) between the axis and vector. Positive if counter-clockwise,
  >     negative if clockwise when viewed along the [0,0,1] direction.

---

###### <a id='encoding_py_class_Moosasboundary_method_orthogonalization'></a>`orthogonalization`
- **Type:** Instance Method
- **Parameters:** self: Any, proj: Projection
- **Returns:** spliter : list of pygeos geometries (LineString)
    A list of splitting lines used to subdivide the input boundary when it cannot be represented as a quadrilateral after 
    orthogonalization. Each LineString connects vertices to reduce the number of boundary points until a quadrilateral is formed.
- **Comments:**
  > Function:
  > Perform orthogonalization of a polygon boundary by projecting it onto an orthogonal basis and adjusting non-orthogonal edges.
  > Parameters:
  > proj : Projection, optional
  >     A projection object defining the coordinate system for orthogonalization. If None, an orthogonal basis is automatically 
  >     determined from the regularized boundary using `Projection.findOrthogonalBasis`. Default is None.
  > 
  > Returns
  > spliter : list of pygeos geometries (LineString)
  >     A list of splitting lines used to subdivide the input boundary when it cannot be represented as a quadrilateral after 
  >     orthogonalization. Each LineString connects vertices to reduce the number of boundary points until a quadrilateral is formed.
  > Returns:
  > spliter : list of pygeos geometries (LineString)
  >     A list of splitting lines used to subdivide the input boundary when it cannot be represented as a quadrilateral after 
  >     orthogonalization. Each LineString connects vertices to reduce the number of boundary points until a quadrilateral is formed.

---

### 🔧 Functions
###### <a id='encoding_py_func_encodingModel'></a>`encodingModel`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The input model after processing each space by standardization and boundary regularization.
- **Comments:**
  > Function:
  > Apply encoding process to the model by standardizing spaces and regularizing boundaries.
  > Parameters:
  > model : MoosasModel
  >     The input model containing levels, spaces, and associated geometric data to be processed.
  > 
  > Returns
  > MoosasModel
  >     The input model after processing each space by standardization and boundary regularization.
  > Returns:
  > MoosasModel
  >     The input model after processing each space by standardization and boundary regularization.

---

###### <a id='encoding_py_func_standarizeSpace'></a>`standarizeSpace`
- **Type:** Function
- **Parameters:** space: MoosasSpace
- **Returns:** MoosasSpace
    The standardized space object.
- **Comments:**
  > Function:
  > Standardize the given space object.
  > Parameters:
  > space : MoosasSpace
  >     The space object to be standardized.
  > 
  > Returns
  > MoosasSpace
  >     The standardized space object.
  > Returns:
  > MoosasSpace
  >     The standardized space object.

---


## 📄 File: energy.py
<a id='energy_py'></a>

### Contents
- Functions:
  - [energyAnalysis()](#energy_py_func_energyAnalysis)
  - [parseEnergyOutput()](#energy_py_func_parseEnergyOutput)
  - [getEnergyInput()](#energy_py_func_getEnergyInput)
  - [calculate_orientation()](#energy_py_func_calculate_orientation)
  - [non()](#energy_py_func_non)

---

### 🔧 Functions
###### <a id='energy_py_func_energyAnalysis'></a>`energyAnalysis`
- **Type:** Function
- **Parameters:** model: MoosasModel, core: Any, requireRadiation: Any, inputPath: Any, resultPath: Any
- **Returns:** dict
    A dictionary containing the energy analysis results with the following structure:
    - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing annual energy demands.
    - 'spaces': list of ThermalSettings objects, with energy loads recorded in their `load` attribute.
    - 'months': dict for each month (Jan, Feb, ...) with daily energy demand breakdown including 'cooling', 'heating', 'lighting', and 'total'.
- **Comments:**
  > Function:
  > Quick energy analysis function.
  > 
  > Performs an energy demand analysis on a building model using specified core type and radiation settings.
  > Parameters:
  > model : MoosasModel
  >     The building model to be analyzed.
  > core : buildingType, optional
  >     Specifies the analysis core to use; choose between `buildingType.RESIDENTIAL` and other types. 
  >     Default is `buildingType.RESIDENTIAL`.
  > requireRadiation : bool, optional
  >     If True, performs accurate radiation calculation using MoosasRad. If False, uses default solar heat estimation based on Beijing's cumSky. 
  >     Default is False.
  > inputPath : str, optional
  >     Path to save the input file for the energy simulation. 
  >     Default is "data\energy\Energy.i".
  > resultPath : str, optional
  >     Path to save the output result file from the energy simulation. 
  >     Default is "data\energy\Energy.o".
  > 
  > Returns
  > dict
  >     A dictionary containing the energy analysis results with the following structure:
  >     - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing annual energy demands.
  >     - 'spaces': list of ThermalSettings objects, with energy loads recorded in their `load` attribute.
  >     - 'months': dict for each month (Jan, Feb, ...) with daily energy demand breakdown including 'cooling', 'heating', 'lighting', and 'total'.
  > Returns:
  > dict
  >     A dictionary containing the energy analysis results with the following structure:
  >     - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing annual energy demands.
  >     - 'spaces': list of ThermalSettings objects, with energy loads recorded in their `load` attribute.
  >     - 'months': dict for each month (Jan, Feb, ...) with daily energy demand breakdown including 'cooling', 'heating', 'lighting', and 'total'.

---

###### <a id='energy_py_func_parseEnergyOutput'></a>`parseEnergyOutput`
- **Type:** Function
- **Parameters:** resultPath: Any, zoneList: list[ThermalSettings]
- **Returns:** e_data : dict
    A dictionary containing the parsed energy results with the following keys:
    - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing total energy demands.
    - 'spaces': list of ThermalSettings (if zoneList provided) with load attributes set, or list of dicts with energy demands per space.
    - 'months': dict mapping month names to their respective energy demand dictionaries (cooling, heating, lighting, total).
- **Comments:**
  > Function:
  > Parse the output file from MoosasResidential.exe or MoosasPublic.exe.
  > Parameters:
  > resultPath : str
  >     Path to the result file to parse.
  > zoneList : list of ThermalSettings, optional
  >     List of ThermalSettings objects to record the results. If None, results are returned as dictionaries.
  >     Default is None.
  > 
  > Returns
  > e_data : dict
  >     A dictionary containing the parsed energy results with the following keys:
  >     - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing total energy demands.
  >     - 'spaces': list of ThermalSettings (if zoneList provided) with load attributes set, or list of dicts with energy demands per space.
  >     - 'months': dict mapping month names to their respective energy demand dictionaries (cooling, heating, lighting, total).
  > Returns:
  > e_data : dict
  >     A dictionary containing the parsed energy results with the following keys:
  >     - 'total': dict with keys 'cooling', 'heating', 'lighting', and 'total' representing total energy demands.
  >     - 'spaces': list of ThermalSettings (if zoneList provided) with load attributes set, or list of dicts with energy demands per space.
  >     - 'months': dict mapping month names to their respective energy demand dictionaries (cooling, heating, lighting, total).

---

###### <a id='energy_py_func_getEnergyInput'></a>`getEnergyInput`
- **Type:** Function
- **Parameters:** model: MoosasModel, require_radiation: Any
- **Returns:** dict
    A dictionary containing the energy input configuration with the following keys:
    - 'zones': list of ThermalSettings objects representing thermal settings for each zone.
    - 'args': list of command-line arguments including weather file, latitude, altitude, and shape factor.
- **Comments:**
  > Function:
  > Get the energy input configuration for a given MoosasModel.
  > Parameters:
  > model : MoosasModel
  >     The model for which to generate the energy input file.
  > require_radiation : bool, optional
  >     If True, enables accurate radiation calculation using MoosasRad. Default is False.
  > 
  > Returns
  > dict
  >     A dictionary containing the energy input configuration with the following keys:
  >     - 'zones': list of ThermalSettings objects representing thermal settings for each zone.
  >     - 'args': list of command-line arguments including weather file, latitude, altitude, and shape factor.
  > Returns:
  > dict
  >     A dictionary containing the energy input configuration with the following keys:
  >     - 'zones': list of ThermalSettings objects representing thermal settings for each zone.
  >     - 'args': list of command-line arguments including weather file, latitude, altitude, and shape factor.

---

###### <a id='energy_py_func_calculate_orientation'></a>`calculate_orientation`
- **Type:** Function
- **Parameters:** n: Any
- **Returns:** int
    The orientation angle in degrees, measured clockwise from the positive y-axis, 
    ranging from 0 to 360 degrees.
- **Comments:**
  > Function:
  > Calculate the orientation angle in degrees from a 2D vector.
  > Parameters:
  > n : array_like
  >     A 2-element array or list representing a 2D vector [n[0], n[1]].
  > 
  > Returns
  > int
  >     The orientation angle in degrees, measured clockwise from the positive y-axis, 
  >     ranging from 0 to 360 degrees.
  > Returns:
  > int
  >     The orientation angle in degrees, measured clockwise from the positive y-axis, 
  >     ranging from 0 to 360 degrees.

---

###### <a id='energy_py_func_non'></a>`non`
- **Type:** Function
- **Parameters:** x: Any
- **Returns:** int or float
    The input value `x` if it is greater than 0, otherwise 0.
- **Comments:**
  > Function:
  > Return the input value if it is positive, otherwise return 0.
  > Parameters:
  > x : float or int
  >     The input number to be evaluated.
  > 
  > Returns
  > int or float
  >     The input value `x` if it is greater than 0, otherwise 0.
  > Returns:
  > int or float
  >     The input value `x` if it is greater than 0, otherwise 0.

---


## 📄 File: models.py
<a id='models_py'></a>

### Contents
- Classes:
  - [MoosasModel](#models_py_class_MoosasModel)

---

### 📦 Class: MoosasModel
<a id='models_py_class_MoosasModel'></a>
**Description:** Define all the global variables needed for Moosas+.

#### Methods
###### <a id='models_py_class_MoosasModel_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This constructor does not return any value.
- **Comments:**
  > Function:
  > Initialize the MoosasModel with default lists and assign types to these lists.
  > Parameters:
  > self : object
  >     The instance of the MoosasModel class being initialized.
  > 
  > Returns
  > None
  >     This constructor does not return any value.
  > Returns:
  > None
  >     This constructor does not return any value.

---

###### <a id='models_py_class_MoosasModel_method_buildingTemplate'></a>`buildingTemplate`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** dict
    A dictionary with string keys representing template parameters and corresponding
    values for each parameter. The dictionary includes:
    - "zone_wallU": Exterior wall U-value
    - "zone_winU": Exterior window U-value
    - "zone_win_SHGC": Exterior window Solar Heat Gain Coefficient
    - "zone_c_temp": Cooling set point temperature
    - "zone_h_temp": Heating set point temperature
    - "zone_collingEER": Cooling COP (Coefficient of Performance)
    - "zone_HeatingEER": Heating COP
    - "zone_work_start": Working schedule start time
    - "zone_work_end": Working schedule end time
    - "zone_ppsm": Population per square meter
    - "zone_pfav": Ventilation rate per person (ACH)
    - "zone_popheat": Heat generation per person (W)
    - "zone_equipment": Equipment heat generation (W)
    - "zone_lighting": Lighting heat generation (W)
    - "zone_infiltration": Infiltration air change coefficient (ACH)
    - "zone_nightACH": Nighttime air change coefficient (ACH)
- **Comments:**
  > Function:
  > Get a dictionary containing all building template data from the database.
  > Parameters:
  > self : object
  >     The instance of the class containing the template data.
  > 
  > Returns
  > dict
  >     A dictionary with string keys representing template parameters and corresponding
  >     values for each parameter. The dictionary includes:
  >     - "zone_wallU": Exterior wall U-value
  >     - "zone_winU": Exterior window U-value
  >     - "zone_win_SHGC": Exterior window Solar Heat Gain Coefficient
  >     - "zone_c_temp": Cooling set point temperature
  >     - "zone_h_temp": Heating set point temperature
  >     - "zone_collingEER": Cooling COP (Coefficient of Performance)
  >     - "zone_HeatingEER": Heating COP
  >     - "zone_work_start": Working schedule start time
  >     - "zone_work_end": Working schedule end time
  >     - "zone_ppsm": Population per square meter
  >     - "zone_pfav": Ventilation rate per person (ACH)
  >     - "zone_popheat": Heat generation per person (W)
  >     - "zone_equipment": Equipment heat generation (W)
  >     - "zone_lighting": Lighting heat generation (W)
  >     - "zone_infiltration": Infiltration air change coefficient (ACH)
  >     - "zone_nightACH": Nighttime air change coefficient (ACH)
  > Returns:
  > dict
  >     A dictionary with string keys representing template parameters and corresponding
  >     values for each parameter. The dictionary includes:
  >     - "zone_wallU": Exterior wall U-value
  >     - "zone_winU": Exterior window U-value
  >     - "zone_win_SHGC": Exterior window Solar Heat Gain Coefficient
  >     - "zone_c_temp": Cooling set point temperature
  >     - "zone_h_temp": Heating set point temperature
  >     - "zone_collingEER": Cooling COP (Coefficient of Performance)
  >     - "zone_HeatingEER": Heating COP
  >     - "zone_work_start": Working schedule start time
  >     - "zone_work_end": Working schedule end time
  >     - "zone_ppsm": Population per square meter
  >     - "zone_pfav": Ventilation rate per person (ACH)
  >     - "zone_popheat": Heat generation per person (W)
  >     - "zone_equipment": Equipment heat generation (W)
  >     - "zone_lighting": Lighting heat generation (W)
  >     - "zone_infiltration": Infiltration air change coefficient (ACH)
  >     - "zone_nightACH": Nighttime air change coefficient (ACH)

---

###### <a id='models_py_class_MoosasModel_method_includeTemplate'></a>`includeTemplate`
- **Type:** Instance Method
- **Parameters:** self: Any, templateName: str, templateDict: dict
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Include a template in the internal template dictionary.
  > Parameters:
  > templateName : str
  >     The name of the template to be added.
  > templateDict : dict
  >     The dictionary containing the template data.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='models_py_class_MoosasModel_method_loadWeatherData'></a>`loadWeatherData`
- **Type:** Instance Method
- **Parameters:** self: Any, stationIdOrPath: str
- **Returns:** MoosasWeather
    An instance of MoosasWeather containing the loaded weather data.
- **Comments:**
  > Function:
  > Load weather data from the database or import an external EPW file.
  > Parameters:
  > stationIdOrPath : str, optional
  >     The ID of the weather station or the file path to an EPW file. If a valid file path is provided, 
  >     the EPW file will be imported using `includeEpw`. Default is '545110'.
  > 
  > Returns
  > MoosasWeather
  >     An instance of MoosasWeather containing the loaded weather data.
  > Returns:
  > MoosasWeather
  >     An instance of MoosasWeather containing the loaded weather data.

---

###### <a id='models_py_class_MoosasModel_method_loadCumSky'></a>`loadCumSky`
- **Type:** Instance Method
- **Parameters:** self: Any, stationIdOrPath: str
- **Returns:** dict
    A dictionary containing the loaded cumulative sky data with the following keys:
    - 'annualCumSky': annual cumulative sky dome (numpy array or similar structure)
    - 'summerCumSky': summer period cumulative sky dome
    - 'winterCumSky': winter period cumulative sky dome
- **Comments:**
  > Function:
  > Load cumulative sky data for a given station or EPW file.
  > Parameters:
  > stationIdOrPath : str, optional
  >     The ID of the weather station or the file path to an EPW file. If a valid file path is provided, 
  >     the EPW file will be imported and processed. Default is '545110'.
  > 
  > Returns
  > dict
  >     A dictionary containing the loaded cumulative sky data with the following keys:
  >     - 'annualCumSky': annual cumulative sky dome (numpy array or similar structure)
  >     - 'summerCumSky': summer period cumulative sky dome
  >     - 'winterCumSky': winter period cumulative sky dome
  > Returns:
  > dict
  >     A dictionary containing the loaded cumulative sky data with the following keys:
  >     - 'annualCumSky': annual cumulative sky dome (numpy array or similar structure)
  >     - 'summerCumSky': summer period cumulative sky dome
  >     - 'winterCumSky': winter period cumulative sky dome

---

###### <a id='models_py_class_MoosasModel_method_plotPlan'></a>`plotPlan`
- **Type:** Instance Method
- **Parameters:** self: Any, level_index: int, show: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Plot the plan view for a specified level index.
  > Parameters:
  > level_index : int
  >     The index of the level to plot, corresponding to an entry in self.levelList.
  > show : bool, optional
  >     Whether to display the figure immediately. Default is True.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='models_py_class_MoosasModel_method_summary'></a>`summary`
- **Type:** Instance Method
- **Parameters:** self: Any, wall_count: Any
- **Returns:** None
    This function does not return a value. It prints the summary directly to stdout.
- **Comments:**
  > Function:
  > Prints a formatted summary of building elements by level.
  > Parameters:
  > self : object
  >     The instance of the class containing the lists of building elements.
  >     Must have attributes: `levelList`, `wallList`, `glazingList`, `skylightList`,
  >     `faceList`, and `spaceList`.
  > wall_count : list of int, optional
  >     A list specifying the previous count of walls per level for change tracking.
  >     If provided, differences in wall counts are displayed in parentheses.
  > 
  > Returns
  > None
  >     This function does not return a value. It prints the summary directly to stdout.
  > Returns:
  > None
  >     This function does not return a value. It prints the summary directly to stdout.

---

###### <a id='models_py_class_MoosasModel_method_buildXml'></a>`buildXml`
- **Type:** Instance Method
- **Parameters:** self: Any, writeGeometry: Any
- **Returns:** ET.Element
    The root element of the constructed XML tree containing model data including faces, 
    topology, spaces, settings, and shading information.
- **Comments:**
  > Function:
  > Build an XML element tree representing the model information.
  > Parameters:
  > writeGeometry : bool, optional
  >     Whether to include geometry data in the XML output. Default is False.
  > 
  > Returns
  > ET.Element
  >     The root element of the constructed XML tree containing model data including faces, 
  >     topology, spaces, settings, and shading information.
  > Returns:
  > ET.Element
  >     The root element of the constructed XML tree containing model data including faces, 
  >     topology, spaces, settings, and shading information.

---

###### <a id='models_py_class_MoosasModel_method_buildGeojson'></a>`buildGeojson`
- **Type:** Instance Method
- **Parameters:** self: Any, mask: Any
- **Returns:** dict
    A dictionary representing a GeoJSON FeatureCollection, containing features 
    with properties such as normal vector, face ID, category (is_glazing), 
    and polygon geometry defined by coordinates.
- **Comments:**
  > Function:
  > Build a GeoJSON dictionary from the model's geometry library.
  > Parameters:
  > mask : array-like, optional
  >     A mask to filter faces. If provided, only faces matching the mask are included.
  >     Default is None, which includes all faces.
  > 
  > Returns
  > dict
  >     A dictionary representing a GeoJSON FeatureCollection, containing features 
  >     with properties such as normal vector, face ID, category (is_glazing), 
  >     and polygon geometry defined by coordinates.
  > Returns:
  > dict
  >     A dictionary representing a GeoJSON FeatureCollection, containing features 
  >     with properties such as normal vector, face ID, category (is_glazing), 
  >     and polygon geometry defined by coordinates.

---


## 📄 File: preprocess.py
<a id='preprocess_py'></a>

### Contents
- Functions:
  - [coPlanner()](#preprocess_py_func_coPlanner)
  - [overlap()](#preprocess_py_func_overlap)

---

### 🔧 Functions
###### <a id='preprocess_py_func_coPlanner'></a>`coPlanner`
- **Type:** Function
- **Parameters:** inputFile: str, outputFile: str
- **Returns:** None
- **Comments:**
  > Function:
  > Solve co-planarity issues in a 3D geometry file by merging co-planar faces and removing redundant edges.
  > Parameters:
  > inputFile : str
  >     Path to the input geometry file. Supported formats include *.geo, *.obj, and *.stl.
  >     Alternatively, a `MoosasModel` object can be passed directly.
  > outputFile : str
  >     Path to the output file. Only *.geo format is supported.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='preprocess_py_func_overlap'></a>`overlap`
- **Type:** Function
- **Parameters:** inputFile: str, outputFile: str
- **Returns:** None
- **Comments:**
  > Function:
  > Solve overlap issues in the input geometry file by removing overlapping co-planar faces and merging elements.
  > Parameters:
  > inputFile : str
  >     Path to the input geometry file. Supported formats are *.geo, *.obj, or *.stl.
  >     Alternatively, a `MoosasModel` object can be passed directly.
  > outputFile : str
  >     Path to the output file. Only *.geo format is supported.
  > 
  > Returns
  > None
  > Returns:
  > None

---


## 📄 File: radiation.py
<a id='radiation_py'></a>

### Contents
- Functions:
  - [modelRadiation()](#radiation_py_func_modelRadiation)
  - [spaceRadiation()](#radiation_py_func_spaceRadiation)
  - [positionRadiation()](#radiation_py_func_positionRadiation)
  - [rayTest()](#radiation_py_func_rayTest)
  - [WriteRadGeo()](#radiation_py_func_WriteRadGeo)

---

### 🔧 Functions
###### <a id='radiation_py_func_modelRadiation'></a>`modelRadiation`
- **Type:** Function
- **Parameters:** model: MoosasModel, reflection: Any
- **Returns:** MoosasModel
    The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad' values.
- **Comments:**
  > Function:
  > Calculate radiation for model spaces using parallelized ray tracing.
  > Parameters:
  > model : MoosasModel
  >     The Moosas model containing spaces, geometry, and sky data for radiation calculation.
  > reflection : int, optional
  >     The number of ground reflections to consider in radiation calculation. Default is 1.
  > 
  > Returns
  > MoosasModel
  >     The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad' values.
  > Returns:
  > MoosasModel
  >     The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad' values.

---

###### <a id='radiation_py_func_spaceRadiation'></a>`spaceRadiation`
- **Type:** Function
- **Parameters:** space: MoosasSpace, reflection: Any
- **Returns:** MoosasSpace
    The input space object with updated settings including 'zone_summerrad' and 'zone_winterrad' values.
- **Comments:**
  > Function:
  > Calculate seasonal radiation for a space by summing weighted contributions from skylights and glazing.
  > Parameters:
  > space : MoosasSpace
  >     The space object containing faces (e.g., glazing, skylights) for which radiation is calculated.
  > reflection : float, optional
  >     The surface reflection coefficient used in radiation calculation. Default is 1.
  > 
  > Returns
  > MoosasSpace
  >     The input space object with updated settings including 'zone_summerrad' and 'zone_winterrad' values.
  > Returns:
  > MoosasSpace
  >     The input space object with updated settings including 'zone_summerrad' and 'zone_winterrad' values.

---

###### <a id='radiation_py_func_positionRadiation'></a>`positionRadiation`
- **Type:** Function
- **Parameters:** positionRay: Ray | Iterable[Ray], sky: MoosasCumSky, model: MoosasModel, reflection: Any, geo_path: Any
- **Returns:** Iterable[float]
    Cumulative radiation values in kWh/m² for each input position.
- **Comments:**
  > Function:
  > Calculate cumulative radiation for given positions considering reflections.
  > Parameters:
  > positionRay : Ray or Iterable[Ray]
  >     Position(s) defined as Ray objects with origin and direction. 
  >     Each Ray may also include a factor. Can be a single Ray, list of Rays, or numpy array of Rays.
  > sky : MoosasCumSky
  >     Cumulative sky model used for radiation calculation.
  > model : MoosasModel, optional
  >     Model containing geometry and reflectance information for ray tracing. 
  >     Required if geo_path is not provided.
  > reflection : int, default=1
  >     Number of reflection bounces to consider in the radiation calculation.
  > geo_path : str, optional
  >     Path to a *.geo file representing the geometry for ray tracing. 
  >     If not provided, the model parameter must be given to generate the geometry.
  > 
  > Returns
  > Iterable[float]
  >     Cumulative radiation values in kWh/m² for each input position.
  > Returns:
  > Iterable[float]
  >     Cumulative radiation values in kWh/m² for each input position.

---

###### <a id='radiation_py_func_rayTest'></a>`rayTest`
- **Type:** Function
- **Parameters:** rays: Iterable[Ray], model: MoosasModel, geo_path: str, ray_path: str
- **Returns:** list[Ray | None]
    A list of results corresponding to each input ray. If a ray intersects a face, 
    the reflected ray is returned. If no intersection occurs, `None` is returned 
    for that ray.
- **Comments:**
  > Function:
  > Test ray-face intersections and reflections using MoosasRad.exe.
  > Parameters:
  > rays : Iterable[Ray]
  >     The rays to test. It is recommended to batch as many rays as possible for efficiency.
  > model : MoosasModel, optional
  >     The model containing the geometry and material data for the reflectance test. 
  >     Either `model` or `geo_path` must be provided.
  > geo_path : str, optional
  >     Path to a *.geo file representing the geometry for the test. If not provided, 
  >     the geometry will be exported from the `model`.
  > ray_path : str, optional
  >     Temporary file path to store the input ray data. If not provided, a default 
  >     path in the temporary directory will be used.
  > 
  > Returns
  > list[Ray | None]
  >     A list of results corresponding to each input ray. If a ray intersects a face, 
  >     the reflected ray is returned. If no intersection occurs, `None` is returned 
  >     for that ray.
  > Returns:
  > list[Ray | None]
  >     A list of results corresponding to each input ray. If a ray intersects a face, 
  >     the reflected ray is returned. If no intersection occurs, `None` is returned 
  >     for that ray.

---

###### <a id='radiation_py_func_WriteRadGeo'></a>`WriteRadGeo`
- **Type:** Function
- **Parameters:** model: Any
- **Returns:** str
    The absolute file path to the generated .geo file.
- **Comments:**
  > Function:
  > Write a geometry file for the given model in Radiance format.
  > Parameters:
  > model : object
  >     The geometric model to be written to the Radiance .geo file. The exact type depends on the expected input of `write_geo`, typically a structured representation of 3D geometry.
  > 
  > Returns
  > str
  >     The absolute file path to the generated .geo file.
  > Returns:
  > str
  >     The absolute file path to the generated .geo file.

---


## 📄 File: sunhour.py
<a id='sunhour_py'></a>

### Contents
- Functions:
  - [positionSunHour()](#sunhour_py_func_positionSunHour)

---

### 🔧 Functions
###### <a id='sunhour_py_func_positionSunHour'></a>`positionSunHour`
- **Type:** Function
- **Parameters:** positionRay: Ray | Iterable[Ray], location: Location, sky: MoosasDirectSky, model: MoosasModel, geo_path: Any, periodStart: datetime | DateTime, periodEnd: datetime | DateTime, leapYear: bool
- **Returns:** Iterable[float]
    Average daily sun hours for each position, in units of hours per day.
    The result accounts for shading, orientation, and valid sun exposure during the specified period.
- **Comments:**
  > Function:
  > Direct sun hour calculation for given positions considering shadows and orientation.
  > Parameters:
  > positionRay : Ray or Iterable[Ray]
  >     Position(s) defined as Ray objects with origin and direction. Each Ray may include a weighting factor.
  >     Can be a single Ray or an iterable of Rays.
  > location : Location, optional
  >     Location object containing latitude and longitude. Used to create the MoosasDirectSky if sky is not provided.
  >     If both location and sky are None, an exception is raised.
  > sky : MoosasDirectSky, optional
  >     Predefined direct sun sky model. If not provided, a new MoosasDirectSky is created from the location.
  > model : MoosasModel, optional
  >     Model containing geometry for reflectance and shadow testing. Required if geo_path is not provided.
  > geo_path : str, optional
  >     Path to a *.geo file representing the scene geometry for ray tracing. If not provided, generated from model.
  > periodStart : datetime or DateTime, default=DateTime(1, 1, 0)
  >     Start time of the analysis period. Defaults to beginning of the year.
  > periodEnd : datetime or DateTime, default=DateTime(12, 31, 23)
  >     End time of the analysis period. Defaults to end of the year.
  > leapYear : bool, default=False
  >     Whether to consider a leap year in the sky matrix generation and day count.
  > 
  > Returns
  > Iterable[float]
  >     Average daily sun hours for each position, in units of hours per day.
  >     The result accounts for shading, orientation, and valid sun exposure during the specified period.
  > Returns:
  > Iterable[float]
  >     Average daily sun hours for each position, in units of hours per day.
  >     The result accounts for shading, orientation, and valid sun exposure during the specified period.

---


## 📄 File: transformation.py
<a id='transformation_py'></a>

### Contents
- Functions:
  - [loadModel()](#transformation_py_func_loadModel)
  - [saveModel()](#transformation_py_func_saveModel)
  - [transform()](#transformation_py_func_transform)
  - [structured()](#transformation_py_func_structured)
  - [_classification()](#transformation_py_func__classification)
  - [_matchFaceGlazing()](#transformation_py_func__matchFaceGlazing)
  - [_glazingToFace()](#transformation_py_func__glazingToFace)
  - [_break_vertical_faces()](#transformation_py_func__break_vertical_faces)
  - [_packing_model()](#transformation_py_func__packing_model)
  - [_capFloor()](#transformation_py_func__capFloor)
  - [_capFloorSimple()](#transformation_py_func__capFloorSimple)
  - [_findVoidAbove()](#transformation_py_func__findVoidAbove)
  - [_findCoCeiling()](#transformation_py_func__findCoCeiling)
  - [spaceTopology()](#transformation_py_func_spaceTopology)
  - [faceTopology()](#transformation_py_func_faceTopology)
  - [_attach_shading()](#transformation_py_func__attach_shading)
  - [_copy_air_boundaries()](#transformation_py_func__copy_air_boundaries)
  - [_standardize()](#transformation_py_func__standardize)

---

### 🔧 Functions
###### <a id='transformation_py_func_loadModel'></a>`loadModel`
- **Type:** Function
- **Parameters:** filePath: str, fileFormat: Any
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > Loading MoosasModel from rdf format file. See doc/MoosasRDF for file namespace and description.
  > Parameters:
  > filePath : str
  >     any input rdf file
  > fileFormat : str, optional
  >     rdf format, following the definition of rdflib module. Default : 'turtle'
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func_saveModel'></a>`saveModel`
- **Type:** Function
- **Parameters:** model: MoosasModel, out_path: str, fileFormat: Any, dumpUseless: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Save the model into any rdf format.
  > Parameters:
  > model : MoosasModel
  >     the model includes space and face topology, and other weather or material issues.
  > out_path : str
  >     output rdf file path
  > fileFormat : str, optional
  >     rdf format, following the definition of rdflib module. Default : 'turtle'
  > dumpUseless : bool, optional
  >     cut out the unuse nodes (elements and faces)
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='transformation_py_func_transform'></a>`transform`
- **Type:** Function
- **Parameters:** input_path: str, output_path: str, geo_path: str, input_type: str, output_type: str, method: Any, solve_duplicated: Any, solve_redundant: Any, solve_contains: Any, triangulate_faces: Any, break_wall_vertical: Any, break_wall_horizontal: Any, attach_shading: Any, divided_zones: Any, standardize: Any, stdout: Any
- **Returns:** MoosasModel
    Structured spatial model with properties (More information could be found in models module):
    - spacesList : List[MoosasSpace] - Spatial units with thermal properties
    - wallList : List[MoosasWall] - Architectural components
    - buildingTemplate : dict -  dictionary of the termal building templates and properties
    - weather : MoosasWeather - weather object and information

Examples
>>> from MoosasPy.geometry.spaceGen import CCRSpaceGeneration
>>> model = transform('test.obj', method=CCRSpaceGeneration)
>>> model.save('output.xml', fmt='xml')

Energy analysis example:
>>> from MoosasPy import energyAnalysis
>>> results = energyAnalysis(model)
>>> print(f"Total energy demand: {results['total']['cooling'] + results['total']['heating']} kWh")

Notes
1. For RDF/XML output, use `.saveModel()` instead of output_path
2. IDF generation includes default thermal settings from ASHRAE 90.1
3. Geometry standardization reduces model fidelity for simulation efficiency
- **Comments:**
  > Function:
  > Convert geometric data to structured spatial model with optional processing.
  > Parameters:
  > input_path : str
  >     Path to input geometry file. Supported formats:
  >     - *.obj : Wavefront OBJ format
  >     - *.xml : Custom XML structure
  >     - *.stl : STL format (future support)
  >     - *.geo : Stream format (future support)
  > 
  > output_path : str, optional
  >     Output path for structured spatial data. Supported formats:
  >     - *.spc : Steam format with space/element descriptions
  >     - *.xml : Tree-structured XML format
  >     - *.json : JSON equivalent of XML structure
  >     - *.idf : EnergyPlus input with default thermal settings
  >     - *.rdf : RDF knowledge graph (Turtle format)
  > 
  > geo_path : str, optional
  >     Export path for modified geometry (*.geo format).
  > 
  > input_type : str, optional
  >     Explicit input format specification (e.g., 'obj', 'xml').
  >     Auto-detected from input_path suffix if None.
  > 
  > output_type : str, optional
  >     Explicit output format specification.
  >     Auto-detected from output_path suffix if None.
  > 
  > method : callable, optional
  >     Space generation algorithm (default: CCRSpaceGeneration). Options:
  >     - VFGSpaceGeneration (L. Jones 2013)
  >     - BTGSpaceGeneration (H. Chen 2018)
  >     - CCRSpaceGeneration (J. Xiao 2023)
  > 
  > solve_duplicated : bool, optional
  >     Resolve walls with identical 2D projections (default: True).
  > 
  > solve_redundant : bool, optional
  >     Merge coplanar faces/walls (default: True).
  > 
  > solve_contains : bool, optional
  >     Detect wall overlaps/containments (default: True).
  > 
  > triangulate_faces : bool, optional
  >     Triangulate horizontal faces with holes (default: True).
  > 
  > break_wall_vertical : bool, optional
  >     Vertically segment walls by building levels (default: True).
  > 
  > break_wall_horizontal : bool, optional
  >     Horizontally segment walls at intersections (default: True).
  > 
  > attach_shading : bool, optional
  >     Attach unused faces as shading/thermal mass (default: False).
  > 
  > divided_zones : bool, optional
  >     Split complex zones into ≤4-edge polygons (default: False).
  > 
  > standardize : bool, optional
  >     Simplify output geometry representations (default: False).
  > 
  > stdout : object, optional
  >     Output stream for transformation logs (default: sys.stdout).
  > 
  > Returns
  > MoosasModel
  >     Structured spatial model with properties (More information could be found in models module):
  >     - spacesList : List[MoosasSpace] - Spatial units with thermal properties
  >     - wallList : List[MoosasWall] - Architectural components
  >     - buildingTemplate : dict -  dictionary of the termal building templates and properties
  >     - weather : MoosasWeather - weather object and information
  > 
  > Examples
  > >>> from MoosasPy.geometry.spaceGen import CCRSpaceGeneration
  > >>> model = transform('test.obj', method=CCRSpaceGeneration)
  > >>> model.save('output.xml', fmt='xml')
  > 
  > Energy analysis example:
  > >>> from MoosasPy import energyAnalysis
  > >>> results = energyAnalysis(model)
  > >>> print(f"Total energy demand: {results['total']['cooling'] + results['total']['heating']} kWh")
  > 
  > Notes
  > 1. For RDF/XML output, use `.saveModel()` instead of output_path
  > 2. IDF generation includes default thermal settings from ASHRAE 90.1
  > 3. Geometry standardization reduces model fidelity for simulation efficiency
  > Returns:
  > MoosasModel
  >     Structured spatial model with properties (More information could be found in models module):
  >     - spacesList : List[MoosasSpace] - Spatial units with thermal properties
  >     - wallList : List[MoosasWall] - Architectural components
  >     - buildingTemplate : dict -  dictionary of the termal building templates and properties
  >     - weather : MoosasWeather - weather object and information
  > 
  > Examples
  > >>> from MoosasPy.geometry.spaceGen import CCRSpaceGeneration
  > >>> model = transform('test.obj', method=CCRSpaceGeneration)
  > >>> model.save('output.xml', fmt='xml')
  > 
  > Energy analysis example:
  > >>> from MoosasPy import energyAnalysis
  > >>> results = energyAnalysis(model)
  > >>> print(f"Total energy demand: {results['total']['cooling'] + results['total']['heating']} kWh")
  > 
  > Notes
  > 1. For RDF/XML output, use `.saveModel()` instead of output_path
  > 2. IDF generation includes default thermal settings from ASHRAE 90.1
  > 3. Geometry standardization reduces model fidelity for simulation efficiency
  > Notes:
  > 1. For RDF/XML output, use `.saveModel()` instead of output_path
  > 2. IDF generation includes default thermal settings from ASHRAE 90.1
  > 3. Geometry standardization reduces model fidelity for simulation efficiency

---

###### <a id='transformation_py_func_structured'></a>`structured`
- **Type:** Function
- **Parameters:** model: MoosasModel, solve_duplicated: Any, solve_redundant: Any, solve_contains: Any, triangulate_faces: Any, break_wall_vertical: Any, break_wall_horizontal: Any, attach_shading: Any, divided_zones: Any, standardize: Any, generationMethod: Any
- **Returns:** MoosasModel
    Structured spatial model with properties (More information could be found in models module):
    - spacesList : List[MoosasSpace] - Spatial units with thermal properties
    - wallList : List[MoosasWall] - Architectural components
    - buildingTemplate : dict -  dictionary of the termal building templates and properties
    - weather : MoosasWeather - weather object and information
- **Comments:**
  > Function:
  > Convert a draft model with unstructured geometric data to structured spatial model with optional processing.
  > Parameters:
  > model : MoosasModel
  >     a model only include geometry information (model.geometryList)
  > 
  > 
  > generationMethod : callable, optional
  >     Space generation algorithm (default: CCRSpaceGeneration). Options:
  >     - VFGSpaceGeneration (L. Jones 2013)
  >     - BTGSpaceGeneration (H. Chen 2018)
  >     - CCRSpaceGeneration (J. Xiao 2023)
  > 
  > solve_duplicated : bool, optional
  >     Resolve walls with identical 2D projections (default: True).
  > 
  > solve_redundant : bool, optional
  >     Merge coplanar faces/walls (default: True).
  > 
  > solve_contains : bool, optional
  >     Detect wall overlaps/containments (default: True).
  > 
  > triangulate_faces : bool, optional
  >     Triangulate horizontal faces with holes (default: True).
  > 
  > break_wall_vertical : bool, optional
  >     Vertically segment walls by building levels (default: True).
  > 
  > break_wall_horizontal : bool, optional
  >     Horizontally segment walls at intersections (default: True).
  > 
  > attach_shading : bool, optional
  >     Attach unused faces as shading/thermal mass (default: False).
  > 
  > divided_zones : bool, optional
  >     Split complex zones into ≤4-edge polygons (default: False).
  > 
  > standardize : bool, optional
  >     Simplify output geometry representations (default: False).
  > 
  > Returns
  > MoosasModel
  >     Structured spatial model with properties (More information could be found in models module):
  >     - spacesList : List[MoosasSpace] - Spatial units with thermal properties
  >     - wallList : List[MoosasWall] - Architectural components
  >     - buildingTemplate : dict -  dictionary of the termal building templates and properties
  >     - weather : MoosasWeather - weather object and information
  > Returns:
  > MoosasModel
  >     Structured spatial model with properties (More information could be found in models module):
  >     - spacesList : List[MoosasSpace] - Spatial units with thermal properties
  >     - wallList : List[MoosasWall] - Architectural components
  >     - buildingTemplate : dict -  dictionary of the termal building templates and properties
  >     - weather : MoosasWeather - weather object and information

---

###### <a id='transformation_py_func__classification'></a>`_classification`
- **Type:** Function
- **Parameters:** model: MoosasModel, triangulate_faces: Any, break_wall_vertical: Any
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > Structuring data by elevation:
  > In principle, all changes are made only for MoosasGeometry, ensuring a unique faceId
  > 1. Point multiplication vectors distinguish horizontal/vertical planes and are packaged into
  > a MoosasFace/MoosasWall** Levels are automatically assigned or generated during __init__ packing process
  > 2. Find the transparent object with geo_category=1 and pack it into MoosasGlazing/MoosasSkylight
  >     2.1 Conversion of glazing to curtain wall for bottom elevation close to floor slab (glazingId==faceId)
  > 3. Interrupt the wall at full height, and update the bottom projection set self.
  > __botProjection at different levels
  > 4. Call force_2d() to match the window
  >     4.1 Call the rewrite dwithin method to fuzzily match the window wall
  >     4.2 Windows that do not match the wall are considered curtain walls
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > triangulate_faces : bool, optional
  >     Triangulate horizontal faces with holes (default: True).
  > 
  > break_wall_vertical : bool, optional
  >     Vertically segment walls by building levels (default: True).
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__matchFaceGlazing'></a>`_matchFaceGlazing`
- **Type:** Function
- **Parameters:** face: MoosasFace | MoosasWall, glazing: MoosasSkylight | MoosasGlazing
- **Returns:** bool
    True if successfully matched.
- **Comments:**
  > Function:
  > attach the glazing element to the face or wall element.
  > the faces topology would be directly added and do not need further treatment.
  > Parameters:
  > face : MoosasFace | MoosasWall
  >     any input MoosasFace | MoosasWall as potential parent face
  > 
  > glazing : MoosasSkylight | MoosasGlazing
  >     any input MoosasSkylight | MoosasGlazing as potential child face
  > 
  > Returns
  > bool
  >     True if successfully matched.
  > Returns:
  > bool
  >     True if successfully matched.

---

###### <a id='transformation_py_func__glazingToFace'></a>`_glazingToFace`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > check each glazings and skylights to find their parent faces.
  > if not found, the glazings/ skylights will be changed to a curtain wall or glass roof, whose faceId == glazingId
  > but still need to have a copy in model.glazingList/model.skylightList
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__break_vertical_faces'></a>`_break_vertical_faces`
- **Type:** Function
- **Parameters:** model: MoosasModel, faceId: Any
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > break a vertical face by the building level it crosses
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > faceId : str
  >     the faceId of the input geometry to break
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__packing_model'></a>`_packing_model`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > Packaging MoosasSpace:
  >     1.1 searching floor and ceiling shadow the MoosasEdge, and use the edge to split those faces.
  >         1.1.1 this boolean calculation only work for the flat planes.
  >         if the plane is incline it is seldom used as a floor.
  >         we ignore them since the boolean only works for 2LSB calculation.
  >     1.2 determine whether the edge is solid space or void space based on the identified result
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__capFloor'></a>`_capFloor`
- **Type:** Function
- **Parameters:** boundary: pygeos.Geometry, level: Any, model: MoosasModel, baseFloor: MoosasFloor | None
- **Returns:** MoosasFloor
    The MooosasFloor object matched the boundary
- **Comments:**
  > Function:
  > cap a boundary using MoosasFloor, based on the floor input.
  > faces in the base floor will be split and move to the new floor.
  > glazing will also be split and tested to apply to any faces.
  > Parameters:
  > boundary : pygeos.Geometry
  >     the void boundary to cap (2d or 3d)
  > 
  > level : float
  >     the z value of the boundary, it would not be automatically identified.
  > 
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > baseFloor : MoosasFloor | None , optional
  >     if any floor faces were located (potentially) in the boundary, it could be reuse in this module
  > 
  > Returns
  > MoosasFloor
  >     The MooosasFloor object matched the boundary
  > Returns:
  > MoosasFloor
  >     The MooosasFloor object matched the boundary

---

###### <a id='transformation_py_func__capFloorSimple'></a>`_capFloorSimple`
- **Type:** Function
- **Parameters:** boundary: pygeos.Geometry, level: Any, model: MoosasModel, baseFaces: MoosasFloor | None
- **Returns:** MoosasFloor
    The MooosasFloor object matched the boundary
- **Comments:**
  > Function:
  > cap a boundary using MoosasFloor, based on the floor input.
  > faces in the base floor will be split and move to the new floor.
  > glazing will also be split and tested to apply to any faces.
  > Parameters:
  > boundary : pygeos.Geometry
  >     the void boundary to cap (2d or 3d)
  > 
  > level : float
  >     the z value of the boundary, it would not be automatically identified.
  > 
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > baseFloor : MoosasFloor | None , optional
  >     if any floor faces were located (potentially) in the boundary, it could be reuse in this module
  > 
  > Returns
  > MoosasFloor
  >     The MooosasFloor object matched the boundary
  > Returns:
  > MoosasFloor
  >     The MooosasFloor object matched the boundary

---

###### <a id='transformation_py_func__findVoidAbove'></a>`_findVoidAbove`
- **Type:** Function
- **Parameters:** voidWithFloor: MoosasSpace
- **Returns:** MoosasSpace | None
    The void object above, or None
- **Comments:**
  > Function:
  > find the void above for an void, which can be potentially merged together.
  > Parameters:
  > voidWithFloor : MoosasSpace
  >     the void as MoosasSpace (voidWithFloor.is_void()==True)
  >     which must contain a floor (voidWithFloor.floor is not None)
  > 
  > Returns
  > MoosasSpace | None
  >     The void object above, or None
  > Returns:
  > MoosasSpace | None
  >     The void object above, or None

---

###### <a id='transformation_py_func__findCoCeiling'></a>`_findCoCeiling`
- **Type:** Function
- **Parameters:** spaceBottom: MoosasSpace, spaceTop: MoosasSpace
- **Returns:** MoosasFloor , MoosasFloor
    The bottom floor and the top floor.
- **Comments:**
  > Function:
  > find the overlap part of the floor, clip and regenerate the floors.
  > Parameters:
  > spaceBottom : MoosasSpace
  >     bottom space
  > 
  > spaceTop : MoosasSpace
  >     top space
  > 
  > Returns
  > MoosasFloor , MoosasFloor
  >     The bottom floor and the top floor.
  > Returns:
  > MoosasFloor , MoosasFloor
  >     The bottom floor and the top floor.

---

###### <a id='transformation_py_func_spaceTopology'></a>`spaceTopology`
- **Type:** Function
- **Parameters:** model: MoosasModel, break_wall_vertical: Any
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > extract the space topology in the model.
  > This module should be run after loading a file.
  > 
  > 1.calculate the containment of spaces and void.
  > 2.join void together if they can be a complete space.
  > 3.calculate the topology for edge,ceiling and floor.
  > 
  > besides, the isOuter attribute of all Element will be decided here.
  > the space information has already recorded in the elements.
  > we only need to retrieve them and create a neighborhood relations
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func_faceTopology'></a>`faceTopology`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > extrude the face topology in the model.
  > This module should be run after loading a file.
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__attach_shading'></a>`_attach_shading`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > attach shading elements to glazings.
  > if the elements locate in the space, they will be treated as internal mass.
  > if the elements locate outside, they will be allocated to the closed windows。
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__copy_air_boundaries'></a>`_copy_air_boundaries`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > copy all the air boundaries in different level.
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---

###### <a id='transformation_py_func__standardize'></a>`_standardize`
- **Type:** Function
- **Parameters:** model: MoosasModel
- **Returns:** MoosasModel
    The model for further transformation or analysis.
- **Comments:**
  > Function:
  > standardize the walls and faces to simplify the model.
  > Parameters:
  > model : MoosasModel
  >     any input MoosasModel
  > 
  > Returns
  > MoosasModel
  >     The model for further transformation or analysis.
  > Returns:
  > MoosasModel
  >     The model for further transformation or analysis.

---


## 📄 File: encoding\convexify.py
<a id='encoding_convexify_py'></a>

### Contents
- Classes:
  - [BasicOptions](#encoding_convexify_py_class_BasicOptions)
  - [Geometry_Option](#encoding_convexify_py_class_Geometry_Option)
  - [MoosasConvexify](#encoding_convexify_py_class_MoosasConvexify)
- Functions:
  - [triangulate2dFace()](#encoding_convexify_py_func_triangulate2dFace)
  - [in_cone()](#encoding_convexify_py_func_in_cone)
  - [diagonalie()](#encoding_convexify_py_func_diagonalie)

---

### 📦 Class: BasicOptions
<a id='encoding_convexify_py_class_BasicOptions'></a>
**Description:** No class documentation.

#### Methods
###### <a id='encoding_convexify_py_class_BasicOptions_method_left_on'></a>`left_on`
- **Type:** Instance Method
- **Parameters:** p1: Any, p2: Any, p3: Any
- **Returns:** bool
    True if p3 is strictly to the left of the directed line from p1 to p2,
    False otherwise (including collinear or right-side cases).
- **Comments:**
  > Function:
  > Determine if point p3 is to the left of the line formed by points p1 and p2 in 2D space.
  > Parameters:
  > p1 : array-like, shape (N,) or (2,)
  >     First point in N-dimensional space; only the first two coordinates are used.
  > p2 : array-like, shape (N,) or (2,)
  >     Second point in N-dimensional space; only the first two coordinates are used.
  > p3 : array-like, shape (N,) or (2,)
  >     Third point in N-dimensional space; only the first two coordinates are used.
  > 
  > Returns
  > bool
  >     True if p3 is strictly to the left of the directed line from p1 to p2,
  >     False otherwise (including collinear or right-side cases).
  > Returns:
  > bool
  >     True if p3 is strictly to the left of the directed line from p1 to p2,
  >     False otherwise (including collinear or right-side cases).

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_angle'></a>`angle`
- **Type:** Instance Method
- **Parameters:** p1: Any, p2: Any, p3: Any
- **Returns:** float
    The signed angle in degrees between the vectors (p2 - p1) and (p3 - p2). 
    Positive if the rotation from v1 to v2 is counterclockwise (right-hand rule), 
    negative if clockwise. Returns 0 if the vectors are colinear or nearly so.
- **Comments:**
  > Function:
  > Calculate the signed angle in degrees between three points in 2D or 3D space.
  > Parameters:
  > p1 : array_like
  >     First point (tail of the first vector).
  > p2 : array_like
  >     Second point (vertex of the angle, shared by both vectors).
  > p3 : array_like
  >     Third point (tip of the second vector).
  > 
  > Returns
  > float
  >     The signed angle in degrees between the vectors (p2 - p1) and (p3 - p2). 
  >     Positive if the rotation from v1 to v2 is counterclockwise (right-hand rule), 
  >     negative if clockwise. Returns 0 if the vectors are colinear or nearly so.
  > Returns:
  > float
  >     The signed angle in degrees between the vectors (p2 - p1) and (p3 - p2). 
  >     Positive if the rotation from v1 to v2 is counterclockwise (right-hand rule), 
  >     negative if clockwise. Returns 0 if the vectors are colinear or nearly so.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_get_angle_tan'></a>`get_angle_tan`
- **Type:** Instance Method
- **Parameters:** p1: Any, p2: Any, verts_all: Any
- **Returns:** float
    The angle in radians between the vector from p1 to p2 and the positive x-axis.
- **Comments:**
  > Function:
  > Calculate the angle of the vector between two points using arctangent.
  > Parameters:
  > p1 : int
  >     Index of the first point in verts_all.
  > p2 : int
  >     Index of the second point in verts_all.
  > verts_all : numpy.ndarray
  >     Array of vertex coordinates, where each vertex is a row with at least 2D coordinates.
  > 
  > Returns
  > float
  >     The angle in radians between the vector from p1 to p2 and the positive x-axis.
  > Returns:
  > float
  >     The angle in radians between the vector from p1 to p2 and the positive x-axis.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_is_obtuse'></a>`is_obtuse`
- **Type:** Instance Method
- **Parameters:** v1: Any, v2: Any, v3: Any
- **Returns:** bool
    True if the angle at v2 formed by v1, v2, and v3 is greater than 90 degrees, False otherwise.
- **Comments:**
  > Function:
  > Check if the angle formed by three points is obtuse.
  > Parameters:
  > v1 : array-like
  >     First point in space.
  > v2 : array-like
  >     Second point (vertex of the angle).
  > v3 : array-like
  >     Third point in space.
  > 
  > Returns
  > bool
  >     True if the angle at v2 formed by v1, v2, and v3 is greater than 90 degrees, False otherwise.
  > Returns:
  > bool
  >     True if the angle at v2 formed by v1, v2, and v3 is greater than 90 degrees, False otherwise.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_collinear'></a>`collinear`
- **Type:** Instance Method
- **Parameters:** p1: Any, p2: Any, p3: Any
- **Returns:** bool
    True if the points are approximately collinear, False otherwise.
- **Comments:**
  > Function:
  > Check if three points are approximately collinear.
  > Parameters:
  > p1 : numpy.ndarray
  >     First point in 2D or 3D space.
  > p2 : numpy.ndarray
  >     Second point in 2D or 3D space.
  > p3 : numpy.ndarray
  >     Third point in 2D or 3D space.
  > 
  > Returns
  > bool
  >     True if the points are approximately collinear, False otherwise.
  > Returns:
  > bool
  >     True if the points are approximately collinear, False otherwise.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_between'></a>`between`
- **Type:** Instance Method
- **Parameters:** p1: Any, p2: Any, p3: Any
- **Returns:** bool
    True if p3 lies between p1 and p2 along the x-axis (if x differs) or y-axis (if x is same), False otherwise.
- **Comments:**
  > Function:
  > Check if point p3 lies between points p1 and p2 along one axis in 2D space.
  > Parameters:
  > p1 : array-like
  >     First 2D point, represented as a sequence of at least two coordinates (x, y).
  > p2 : array-like
  >     Second 2D point, represented as a sequence of at least two coordinates (x, y).
  > p3 : array-like
  >     Query 2D point, represented as a sequence of at least two coordinates (x, y).
  > 
  > Returns
  > bool
  >     True if p3 lies between p1 and p2 along the x-axis (if x differs) or y-axis (if x is same), False otherwise.
  > Returns:
  > bool
  >     True if p3 lies between p1 and p2 along the x-axis (if x differs) or y-axis (if x is same), False otherwise.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_intersect'></a>`intersect`
- **Type:** Instance Method
- **Parameters:** a: Any, b: Any, c: Any, d: Any
- **Returns:** bool
    True if the two line segments intersect, False otherwise.
- **Comments:**
  > Function:
  > Determine if two line segments intersect in 2D space.
  > Parameters:
  > a : array-like
  >     The first endpoint of the first line segment, as a 2D point (x, y).
  > b : array-like
  >     The second endpoint of the first line segment, as a 2D point (x, y).
  > c : array-like
  >     The first endpoint of the second line segment, as a 2D point (x, y).
  > d : array-like
  >     The second endpoint of the second line segment, as a 2D point (x, y).
  > 
  > Returns
  > bool
  >     True if the two line segments intersect, False otherwise.
  > Returns:
  > bool
  >     True if the two line segments intersect, False otherwise.

---

###### <a id='encoding_convexify_py_class_BasicOptions_method_diagonal'></a>`diagonal`
- **Type:** Instance Method
- **Parameters:** verts: np.ndarray, indices: np.ndarray, ia: int, ib: int
- **Returns:** bool
    True if the segment between verts[ia] and verts[ib] is a valid diagonal; False otherwise.
- **Comments:**
  > Function:
  > Check if the line segment between two vertices is a valid diagonal in a polygon.
  > Parameters:
  > verts : numpy.ndarray
  >     Array of vertex coordinates, where each row represents a point in 2D space.
  > indices : numpy.ndarray
  >     Array of indices defining the order of vertices in the polygon.
  > ia : int
  >     Index of the first vertex in the diagonal.
  > ib : int
  >     Index of the second vertex in the diagonal.
  > 
  > Returns
  > bool
  >     True if the segment between verts[ia] and verts[ib] is a valid diagonal; False otherwise.
  > Returns:
  > bool
  >     True if the segment between verts[ia] and verts[ib] is a valid diagonal; False otherwise.

---

### 📦 Class: Geometry_Option
<a id='encoding_convexify_py_class_Geometry_Option'></a>
**Description:** No class documentation.

#### Methods
###### <a id='encoding_convexify_py_class_Geometry_Option_method_reorder_vertices'></a>`reorder_vertices`
- **Type:** Instance Method
- **Parameters:** face: Any, is_upward: Any
- **Returns:** reordered_face : numpy.ndarray
    Array of shape (n, 3) with vertices reordered according to the specified normal direction.
- **Comments:**
  > Function:
  > Re-order vertices of a face to make the normal face upward or downward.
  > Parameters:
  > face : numpy.ndarray
  >     Array of shape (n, 3) representing the sequence of vertices of a face.
  > is_upward : bool
  >     If True, reorders vertices so that the face normal points upward;
  >     if False, reorders for downward normal.
  > 
  > Returns
  > reordered_face : numpy.ndarray
  >     Array of shape (n, 3) with vertices reordered according to the specified normal direction.
  > Returns:
  > reordered_face : numpy.ndarray
  >     Array of shape (n, 3) with vertices reordered according to the specified normal direction.

---

###### <a id='encoding_convexify_py_class_Geometry_Option_method_is_same_polygon'></a>`is_same_polygon`
- **Type:** Instance Method
- **Parameters:** polygon1: Any, polygon2: Any, projection: Any
- **Returns:** bool
    True if the polygons are the same, considering point order and reverse order (with fixed first point), otherwise False.
- **Comments:**
  > Function:
  > Check if two polygons are the same, with support for 2D projection or 3D coordinates.
  > Parameters:
  > polygon1 : numpy.ndarray
  >     A numpy array of shape (n, 2) or (n, 3) representing the first polygon.
  > polygon2 : numpy.ndarray
  >     A numpy array of the same shape as polygon1 representing the second polygon.
  > projection : bool
  >     If True, only the first two columns (x, y) are compared (projection on xoy plane).
  > 
  > Returns
  > bool
  >     True if the polygons are the same, considering point order and reverse order (with fixed first point), otherwise False.
  > Returns:
  > bool
  >     True if the polygons are the same, considering point order and reverse order (with fixed first point), otherwise False.

---

###### <a id='encoding_convexify_py_class_Geometry_Option_method_process_hole'></a>`process_hole`
- **Type:** Instance Method
- **Parameters:** hole: Any, faces: Any, check_projection: Any
- **Returns:** bool
    True if the hole should be skipped (i.e., it fully coincides with a face and meets projection criteria),
    False otherwise.
- **Comments:**
  > Function:
  > Process a hole to determine if it should be skipped based on geometric conditions.
  > Parameters:
  > hole : numpy.ndarray
  >     A 2D array of shape (n, 3) representing the 3D coordinates of the hole polygon.
  > faces : list of numpy.ndarray
  >     A list of 2D arrays, each representing a 3D face polygon with shape (m, 3).
  > check_projection : bool, optional
  >     If True, checks whether the projection of the hole overlaps with projections of other faces.
  >     Default is True.
  > 
  > Returns
  > bool
  >     True if the hole should be skipped (i.e., it fully coincides with a face and meets projection criteria),
  >     False otherwise.
  > Returns:
  > bool
  >     True if the hole should be skipped (i.e., it fully coincides with a face and meets projection criteria),
  >     False otherwise.

---

###### <a id='encoding_convexify_py_class_Geometry_Option_method_merge_holes'></a>`merge_holes`
- **Type:** Instance Method
- **Parameters:** verts_poly: np.ndarray, verts_holes: dict[int, np.ndarray]
- **Returns:** tuple[np.ndarray, list[np.ndarray]]
    A tuple containing:
    - indices_all: Array of merged vertices including both polygon and hole vertices in traversal order.
    - diagonals: List of connection line segments represented as arrays of two points, 
      each connecting a polygon vertex to a hole vertex.
- **Comments:**
  > Function:
  > Merge holes into a polygon by finding the shortest valid connection lines.
  > Parameters:
  > verts_poly : np.ndarray
  >     Array of vertices representing the outer polygon boundary.
  > verts_holes : dict[int, np.ndarray]
  >     Dictionary mapping hole indices to their respective vertex arrays; each key is an integer 
  >     identifying a hole, and the corresponding value is a NumPy array of its vertices.
  > 
  > Returns
  > tuple[np.ndarray, list[np.ndarray]]
  >     A tuple containing:
  >     - indices_all: Array of merged vertices including both polygon and hole vertices in traversal order.
  >     - diagonals: List of connection line segments represented as arrays of two points, 
  >       each connecting a polygon vertex to a hole vertex.
  > Returns:
  > tuple[np.ndarray, list[np.ndarray]]
  >     A tuple containing:
  >     - indices_all: Array of merged vertices including both polygon and hole vertices in traversal order.
  >     - diagonals: List of connection line segments represented as arrays of two points, 
  >       each connecting a polygon vertex to a hole vertex.

---

###### <a id='encoding_convexify_py_class_Geometry_Option_method_split_poly'></a>`split_poly`
- **Type:** Instance Method
- **Parameters:** verts: np.ndarray, indices: np.ndarray
- **Returns:** list of np.ndarray, list of tuple of int
    A tuple containing two elements:
    - A list of arrays, each array containing indices of `verts` that form a convex polygon.
    - A list of tuples, each tuple representing a diagonal (split edge) by vertex indices 
      used to partition the original polygon.
- **Comments:**
  > Function:
  > Split a simple polygon into convex polygons using a divide-and-conquer approach.
  > Parameters:
  > verts : np.ndarray
  >     Array of shape (#verts, 2) containing the 2D coordinates of vertices.
  > indices : np.ndarray
  >     Array of shape (#verts,) containing the indices of vertices forming the polygon, 
  >     referencing rows in `verts`.
  > 
  > Returns
  > list of np.ndarray, list of tuple of int
  >     A tuple containing two elements:
  >     - A list of arrays, each array containing indices of `verts` that form a convex polygon.
  >     - A list of tuples, each tuple representing a diagonal (split edge) by vertex indices 
  >       used to partition the original polygon.
  > Returns:
  > list of np.ndarray, list of tuple of int
  >     A tuple containing two elements:
  >     - A list of arrays, each array containing indices of `verts` that form a convex polygon.
  >     - A list of tuples, each tuple representing a diagonal (split edge) by vertex indices 
  >       used to partition the original polygon.

---

###### <a id='encoding_convexify_py_class_Geometry_Option_method_split_quad'></a>`split_quad`
- **Type:** Instance Method
- **Parameters:** verts: np.ndarray, indices: np.ndarray
- **Returns:** list of np.ndarray or list of tuple of int
    List of sub-polygons, each represented as an array (or tuple) of vertex indices;
    each sub-polygon is either a triangle or a convex quadrilateral.
- **Comments:**
  > Function:
  > Split a convex polygon into triangles or convex quadrilaterals without obtuse angles.
  > Parameters:
  > verts : np.ndarray, shape (N, 2)
  >     Array of 2D vertex positions, where N is the number of vertices.
  > indices : np.ndarray, shape (M,)
  >     Array of indices referring to vertices in `verts` that form the convex polygon.
  > 
  > Returns
  > list of np.ndarray or list of tuple of int
  >     List of sub-polygons, each represented as an array (or tuple) of vertex indices;
  >     each sub-polygon is either a triangle or a convex quadrilateral.
  > Returns:
  > list of np.ndarray or list of tuple of int
  >     List of sub-polygons, each represented as an array (or tuple) of vertex indices;
  >     each sub-polygon is either a triangle or a convex quadrilateral.

---

### 📦 Class: MoosasConvexify
<a id='encoding_convexify_py_class_MoosasConvexify'></a>
**Description:** No class documentation.

#### Methods
###### <a id='encoding_convexify_py_class_MoosasConvexify_method_convexify_faces'></a>`convexify_faces`
- **Type:** Instance Method
- **Parameters:** idd: Any, normal: Any, faces: Any, holes: Any
- **Returns:** convex_idd : list of str
    Updated identifiers for the resulting convex faces, with new labels assigned for split subfaces.
convex_normal : list of array-like of shape (3,)
    Normal vectors corresponding to each output convex face, preserving input normals.
convex_faces : list of list of array-like of shape (3,)
    List of convex polygons generated from the input faces, with holes merged and non-convex regions split.
divide_lines : list of numpy.ndarray of shape (2, 3)
    List of line segments (pairs of 3D points) representing internal diagonals or merge lines introduced during convexification.
- **Comments:**
  > Function:
  > Convexify polygonal faces with holes by reordering vertices, merging holes, and applying a divide-and-conquer convex decomposition.
  > Parameters:
  > idd : list of str
  >     List of identifiers for each face. These are preserved or modified when splitting faces.
  > normal : list of array-like of shape (3,)
  >     List of normal vectors for each face, used to determine orientation (e.g., upward direction).
  > faces : list of list of array-like of shape (3,)
  >     List of outer boundary vertices for each face, where each face is represented as a list of 3D points.
  > holes : list of list of list of array-like of shape (3,)
  >     List containing hole definitions for each face; each element is a list of holes, and each hole is a list of 3D points.
  > 
  > Returns
  > convex_idd : list of str
  >     Updated identifiers for the resulting convex faces, with new labels assigned for split subfaces.
  > convex_normal : list of array-like of shape (3,)
  >     Normal vectors corresponding to each output convex face, preserving input normals.
  > convex_faces : list of list of array-like of shape (3,)
  >     List of convex polygons generated from the input faces, with holes merged and non-convex regions split.
  > divide_lines : list of numpy.ndarray of shape (2, 3)
  >     List of line segments (pairs of 3D points) representing internal diagonals or merge lines introduced during convexification.
  > Returns:
  > convex_idd : list of str
  >     Updated identifiers for the resulting convex faces, with new labels assigned for split subfaces.
  > convex_normal : list of array-like of shape (3,)
  >     Normal vectors corresponding to each output convex face, preserving input normals.
  > convex_faces : list of list of array-like of shape (3,)
  >     List of convex polygons generated from the input faces, with holes merged and non-convex regions split.
  > divide_lines : list of numpy.ndarray of shape (2, 3)
  >     List of line segments (pairs of 3D points) representing internal diagonals or merge lines introduced during convexification.

---

### 🔧 Functions
###### <a id='encoding_convexify_py_func_triangulate2dFace'></a>`triangulate2dFace`
- **Type:** Function
- **Parameters:** boundary: pygeos.Geometry, holes: np.ndarray[pygeos.Geometry]
- **Returns:** tuple of numpy.ndarray
    A tuple containing two arrays:
    - convexFaces: numpy.ndarray of pygeos.Geometry
      Convex polygonal faces resulting from the decomposition.
    - dividedLines: numpy.ndarray of pygeos.Geometry
      Linestrings representing the internal edges introduced during decomposition.
- **Comments:**
  > Function:
  > Triangulate a 2D face defined by a boundary and optional holes into convex faces and dividing lines.
  > Parameters:
  > boundary : pygeos.Geometry
  >     The outer boundary of the 2D face, represented as a PyGEOS geometry object.
  >     Must be a linear ring or polygon; will be converted to 3D with z=0 if necessary.
  > holes : numpy.ndarray of pygeos.Geometry, optional
  >     Array of PyGEOS geometry objects representing holes within the boundary.
  >     Each hole is expected to be a linear ring or polygon.
  >     If None, no holes are assumed (default is None).
  > 
  > Returns
  > tuple of numpy.ndarray
  >     A tuple containing two arrays:
  >     - convexFaces: numpy.ndarray of pygeos.Geometry
  >       Convex polygonal faces resulting from the decomposition.
  >     - dividedLines: numpy.ndarray of pygeos.Geometry
  >       Linestrings representing the internal edges introduced during decomposition.
  > Returns:
  > tuple of numpy.ndarray
  >     A tuple containing two arrays:
  >     - convexFaces: numpy.ndarray of pygeos.Geometry
  >       Convex polygonal faces resulting from the decomposition.
  >     - dividedLines: numpy.ndarray of pygeos.Geometry
  >       Linestrings representing the internal edges introduced during decomposition.

---

###### <a id='encoding_convexify_py_func_in_cone'></a>`in_cone`
- **Type:** Function
- **Parameters:** verts: np.ndarray, indices: np.ndarray, ia: int, ib: int
- **Returns:** bool
    True if the vertex `ib` lies within the cone defined by `ia` and its adjacent vertices; False otherwise.
- **Comments:**
  > Function:
  > Check whether a given edge is inside the cone formed by a vertex and its neighbors.
  > Parameters:
  > verts : numpy.ndarray
  >     Array of vertex coordinates, where each vertex is represented by its coordinates.
  > indices : numpy.ndarray
  >     Array of indices referencing vertices in `verts`, representing a polygon or cycle.
  > ia : int
  >     Index into `indices` for the central vertex of the cone.
  > ib : int
  >     Index into `indices` for the vertex to check if it lies within the cone.
  > 
  > Returns
  > bool
  >     True if the vertex `ib` lies within the cone defined by `ia` and its adjacent vertices; False otherwise.
  > Returns:
  > bool
  >     True if the vertex `ib` lies within the cone defined by `ia` and its adjacent vertices; False otherwise.

---

###### <a id='encoding_convexify_py_func_diagonalie'></a>`diagonalie`
- **Type:** Function
- **Parameters:** verts: np.ndarray, indices: np.ndarray, ia: int, ib: int
- **Returns:** bool
    True if the diagonal between vertices `ia` and `ib` does not intersect any edge of the polygon 
    (except at endpoints) and lies entirely within the polygon; False otherwise.
- **Comments:**
  > Function:
  > Check if a diagonal between two vertices lies strictly inside a polygon.
  > Parameters:
  > verts : np.ndarray
  >     Array of shape (N, 2) representing the coordinates of the polygon's vertices.
  > indices : np.ndarray
  >     Array of integers representing the indices of vertices forming the polygon boundary.
  > ia : int
  >     Index into `verts` array for the first endpoint of the diagonal.
  > ib : int
  >     Index into `verts` array for the second endpoint of the diagonal.
  > 
  > Returns
  > bool
  >     True if the diagonal between vertices `ia` and `ib` does not intersect any edge of the polygon 
  >     (except at endpoints) and lies entirely within the polygon; False otherwise.
  > Returns:
  > bool
  >     True if the diagonal between vertices `ia` and `ib` does not intersect any edge of the polygon 
  >     (except at endpoints) and lies entirely within the polygon; False otherwise.

---


## 📄 File: encoding\graph.py
<a id='encoding_graph_py'></a>

### Contents
- Classes:
  - [OBB](#encoding_graph_py_class_OBB)
  - [MoosasGraph](#encoding_graph_py_class_MoosasGraph)
- Functions:
  - [assign_vertex_indices()](#encoding_graph_py_func_assign_vertex_indices)
  - [shared_vertices_by_index()](#encoding_graph_py_func_shared_vertices_by_index)

---

### 📦 Class: OBB
<a id='encoding_graph_py_class_OBB'></a>
**Description:** Oriented Bounding Box (OBB) Class

#### Methods
###### <a id='encoding_graph_py_class_OBB_method_create_obb'></a>`create_obb`
- **Type:** Instance Method
- **Parameters:** points: Any, normal: Any, min_scale: Any
- **Returns:** obb_params : dict
    Dictionary containing the OBB parameters with keys:
    - 'center' (numpy.ndarray, shape (3,)): Center point of the OBB.
    - 'scale' (numpy.ndarray, shape (3,)): Dimensions (length, width, height) of the OBB.
    - 'rotation' (numpy.ndarray, shape (3, 3)): Rotation matrix defining the OBB's orientation.
- **Comments:**
  > Function:
  > Create an oriented bounding box (OBB) for a set of 3D points given a normal vector.
  > Parameters:
  > points : numpy.ndarray, shape (N, 3)
  >     Array of N 3D points.
  > normal : numpy.ndarray, shape (3,)
  >     Normal vector defining the orientation of the OBB's z-axis.
  > min_scale : float, optional
  >     Minimum allowable scale for each dimension of the OBB. Default is 0.1.
  > 
  > Returns
  > obb_params : dict
  >     Dictionary containing the OBB parameters with keys:
  >     - 'center' (numpy.ndarray, shape (3,)): Center point of the OBB.
  >     - 'scale' (numpy.ndarray, shape (3,)): Dimensions (length, width, height) of the OBB.
  >     - 'rotation' (numpy.ndarray, shape (3, 3)): Rotation matrix defining the OBB's orientation.
  > Returns:
  > obb_params : dict
  >     Dictionary containing the OBB parameters with keys:
  >     - 'center' (numpy.ndarray, shape (3,)): Center point of the OBB.
  >     - 'scale' (numpy.ndarray, shape (3,)): Dimensions (length, width, height) of the OBB.
  >     - 'rotation' (numpy.ndarray, shape (3, 3)): Rotation matrix defining the OBB's orientation.

---

###### <a id='encoding_graph_py_class_OBB_method_plot_obb_and_points'></a>`plot_obb_and_points`
- **Type:** Instance Method
- **Parameters:** points: Any, obb_params: Any
- **Returns:** fig : matplotlib.figure.Figure
    The generated 3D figure object containing the plotted points and OBB.
ax : mpl_toolkits.mplot3d.Axes3D
    The 3D axes object with the scatter plot of points and OBB edges.
- **Comments:**
  > Function:
  > Plot a 3D oriented bounding box (OBB) and point cloud.
  > Parameters:
  > points : numpy.ndarray
  >     An N x 3 array representing the 3D coordinates of points to be plotted.
  > obb_params : dict
  >     A dictionary containing OBB parameters with the following keys:
  >     - 'center' (numpy.ndarray): 3-element array for the center of the OBB.
  >     - 'scale' (tuple or list): Three elements (l, w, h) representing the length, width, and height of the OBB.
  >     - 'rotation' (numpy.ndarray): A 3x3 rotation matrix (as array) defining the orientation of the OBB.
  > 
  > Returns
  > fig : matplotlib.figure.Figure
  >     The generated 3D figure object containing the plotted points and OBB.
  > ax : mpl_toolkits.mplot3d.Axes3D
  >     The 3D axes object with the scatter plot of points and OBB edges.
  > Returns:
  > fig : matplotlib.figure.Figure
  >     The generated 3D figure object containing the plotted points and OBB.
  > ax : mpl_toolkits.mplot3d.Axes3D
  >     The 3D axes object with the scatter plot of points and OBB edges.

---

### 📦 Class: MoosasGraph
<a id='encoding_graph_py_class_MoosasGraph'></a>
**Description:** 图化模块

#### Methods
###### <a id='encoding_graph_py_class_MoosasGraph_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This constructor does not return any value.
- **Comments:**
  > Function:
  > Initialize an empty directed graph, spaces, faces, and positions.
  > Parameters:
  > self : object
  >     The instance of the class being initialized.
  > 
  > Returns
  > None
  >     This constructor does not return any value.
  > Returns:
  > None
  >     This constructor does not return any value.

---

###### <a id='encoding_graph_py_class_MoosasGraph_method_graph_representation'></a>`graph_representation`
- **Type:** Instance Method
- **Parameters:** self: Any, geo_path: Any, xml_path: Any, _is_cleaned: Any
- **Returns:** graph : networkx.Graph
    A graph structure where nodes represent faces and spaces with associated parameters (e.g., OBB, type, area), 
    and edges represent spatial and semantic relationships (e.g., adjacency, glazing, shading).
- **Comments:**
  > Function:
  > Parse .geo and .xml files to construct an ADSIM graph representation with nodes for faces and spaces, including geometric and topological properties.
  > Parameters:
  > geo_path : str
  >     Path to the *.geo file containing face geometry data (vertices, normals, categories).
  > xml_path : str
  >     Path to the *.xml file containing semantic and topological information about faces, spaces, and their relationships.
  > _is_cleaned : bool, optional
  >     If True, removes isolated nodes (with no edges) from the graph before returning. Default is True.
  > 
  > Returns
  > graph : networkx.Graph
  >     A graph structure where nodes represent faces and spaces with associated parameters (e.g., OBB, type, area), 
  >     and edges represent spatial and semantic relationships (e.g., adjacency, glazing, shading).
  > Returns:
  > graph : networkx.Graph
  >     A graph structure where nodes represent faces and spaces with associated parameters (e.g., OBB, type, area), 
  >     and edges represent spatial and semantic relationships (e.g., adjacency, glazing, shading).

---

###### <a id='encoding_graph_py_class_MoosasGraph_method_draw_graph_3d'></a>`draw_graph_3d`
- **Type:** Instance Method
- **Parameters:** self: Any, file_path: Any, _fig_show: Any
- **Returns:** None
    This function does not return any value. It saves the 3D plot to the specified file path and optionally displays it.
- **Comments:**
  > Function:
  > Draw a 3D visualization of the graph structure and save it to a file.
  > Parameters:
  > file_path : str
  >     Path to save the generated 3D graph image.
  > _fig_show : bool, optional
  >     If True, display the figure using plt.show(). Default is False.
  > 
  > Returns
  > None
  >     This function does not return any value. It saves the 3D plot to the specified file path and optionally displays it.
  > Returns:
  > None
  >     This function does not return any value. It saves the 3D plot to the specified file path and optionally displays it.

---

###### <a id='encoding_graph_py_class_MoosasGraph_method_nodes'></a>`nodes`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a view of all nodes in the graph, including their associated data.

Parameters
self : object
    The instance of the class containing the graph attribute.

Returns
dict_keyiterator or dict
    A dictionary-like object containing all nodes with their data. Each node is returned 
    as a key-value pair where the key is the node identifier and the value is a dictionary 
    of node attributes.
- **Comments:**
  > Function:
  > Get all nodes in the graph.
  > Parameters:
  > self : object
  >     The instance of the class containing the graph attribute.
  > 
  > Returns
  > dict_keyiterator or dict
  >     A dictionary-like object containing all nodes with their data. Each node is returned 
  >     as a key-value pair where the key is the node identifier and the value is a dictionary 
  >     of node attributes.
  > Returns:
  > a view of all nodes in the graph, including their associated data.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the graph attribute.
  > 
  > Returns
  > dict_keyiterator or dict
  >     A dictionary-like object containing all nodes with their data. Each node is returned 
  >     as a key-value pair where the key is the node identifier and the value is a dictionary 
  >     of node attributes.

---

###### <a id='encoding_graph_py_class_MoosasGraph_method_edges'></a>`edges`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** edges : networkx.classes.coreviews.EdgeView
    A view of all edges in the graph, each represented as a tuple 
    (u, v, data_dict), where u and v are nodes and data_dict contains 
    edge attributes.
- **Comments:**
  > Function:
  > Return all edges in the graph with their associated data.
  > Parameters:
  > self : object
  >     The instance of the class containing the graph attribute.
  > 
  > Returns
  > edges : networkx.classes.coreviews.EdgeView
  >     A view of all edges in the graph, each represented as a tuple 
  >     (u, v, data_dict), where u and v are nodes and data_dict contains 
  >     edge attributes.
  > Returns:
  > edges : networkx.classes.coreviews.EdgeView
  >     A view of all edges in the graph, each represented as a tuple 
  >     (u, v, data_dict), where u and v are nodes and data_dict contains 
  >     edge attributes.

---

###### <a id='encoding_graph_py_class_MoosasGraph_method_graph_representation_legacy'></a>`graph_representation_legacy`
- **Type:** Instance Method
- **Parameters:** self: Any, geo_path: Any
- **Returns:** dict
    A dictionary representing the graph, where keys are node identifiers
    and values are lists of connected nodes (adjacency list format).
- **Comments:**
  > Function:
  > Generate a graph representation from a geographic path using legacy method.
  > 
  > This function processes a geographic path and generates a graph representation
  > by assigning unique indices to shared vertices.
  > Parameters:
  > geo_path : str or pathlib.Path
  >     Path to the geographic data file used for generating the graph representation.
  > 
  > Returns
  > dict
  >     A dictionary representing the graph, where keys are node identifiers
  >     and values are lists of connected nodes (adjacency list format).
  > Returns:
  > dict
  >     A dictionary representing the graph, where keys are node identifiers
  >     and values are lists of connected nodes (adjacency list format).

---

### 🔧 Functions
###### <a id='encoding_graph_py_func_assign_vertex_indices'></a>`assign_vertex_indices`
- **Type:** Function
- **Parameters:** faces_vertices: Any
- **Returns:** tuple
    A tuple containing:
    - faces_with_indices (list of list of int): Faces with each vertex replaced by its unique index.
    - vertex_dict (dict): A dictionary mapping each vertex tuple to its assigned index.
- **Comments:**
  > Function:
  > Assign unique indices to vertices and return indexed faces and a vertex dictionary.
  > Parameters:
  > faces_vertices : list of list of array-like
  >     A list of faces, where each face is represented as a list of vertices.
  >     Each vertex is an array-like structure (e.g., list or tuple) of coordinates.
  > 
  > Returns
  > tuple
  >     A tuple containing:
  >     - faces_with_indices (list of list of int): Faces with each vertex replaced by its unique index.
  >     - vertex_dict (dict): A dictionary mapping each vertex tuple to its assigned index.
  > Returns:
  > tuple
  >     A tuple containing:
  >     - faces_with_indices (list of list of int): Faces with each vertex replaced by its unique index.
  >     - vertex_dict (dict): A dictionary mapping each vertex tuple to its assigned index.

---

###### <a id='encoding_graph_py_func_shared_vertices_by_index'></a>`shared_vertices_by_index`
- **Type:** Function
- **Parameters:** face1: Any, face2: Any
- **Returns:** bool
    True if the two faces share at least two vertices, False otherwise.
- **Comments:**
  > Function:
  > Determine if two faces share at least two vertices by comparing their vertex indices.
  > Parameters:
  > face1 : dict
  >     Dictionary containing face data, must include 'vertex_indices' as a list or array of integers.
  > face2 : dict
  >     Dictionary containing face data, must include 'vertex_indices' as a list or array of integers.
  > 
  > Returns
  > bool
  >     True if the two faces share at least two vertices, False otherwise.
  > Returns:
  > bool
  >     True if the two faces share at least two vertices, False otherwise.

---


## 📄 File: encoding\graphIO.py
<a id='encoding_graphIO_py'></a>

### Contents
- Classes:
  - [NumpyEncoder](#encoding_graphIO_py_class_NumpyEncoder)
- Functions:
  - [read_geo()](#encoding_graphIO_py_func_read_geo)
  - [write_geo()](#encoding_graphIO_py_func_write_geo)
  - [read_xml()](#encoding_graphIO_py_func_read_xml)
  - [write_adjson()](#encoding_graphIO_py_func_write_adjson)
  - [read_adjson()](#encoding_graphIO_py_func_read_adjson)
  - [graph_to_json()](#encoding_graphIO_py_func_graph_to_json)
  - [json_to_graph()](#encoding_graphIO_py_func_json_to_graph)

---

### 📦 Class: NumpyEncoder
<a id='encoding_graphIO_py_class_NumpyEncoder'></a>
**Description:** 处理 numpy 数组的 JSON 编码器

#### Methods
###### <a id='encoding_graphIO_py_class_NumpyEncoder_method_default'></a>`default`
- **Type:** Instance Method
- **Parameters:** self: Any, obj: Any
- **Returns:** Any
        The converted object in a native Python type: list for np.ndarray,
        float for np.float32, int for np.int64, or the result of the parent class's
        default method for other types.
- **Comments:**
  > Function:
  > Convert NumPy data types to native Python types for serialization.
  > Parameters:
  > obj : Any
  >         The object to convert. Supported types include np.ndarray, np.float32, and np.int64.
  > 
  >     Returns
  >     Any
  >         The converted object in a native Python type: list for np.ndarray,
  >         float for np.float32, int for np.int64, or the result of the parent class's
  >         default method for other types.
  > Returns:
  > Any
  >         The converted object in a native Python type: list for np.ndarray,
  >         float for np.float32, int for np.int64, or the result of the parent class's
  >         default method for other types.

---

### 🔧 Functions
###### <a id='encoding_graphIO_py_func_read_geo'></a>`read_geo`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** :
    tuple: 包含分类、编号、法向量和多边形面的信息.
- **Comments:**
  > Function:
  > 读取.geo文件，返回分类、编号、法向量和多边形面的坐标数组.
  > Parameters:
  > :
  >     file_path (str): 文件路径.
  > Returns:
  > :
  >     tuple: 包含分类、编号、法向量和多边形面的信息.

---

###### <a id='encoding_graphIO_py_func_write_geo'></a>`write_geo`
- **Type:** Function
- **Parameters:** file_path: Any, cat: Any, idd: Any, normal: Any, faces: Any
- **Returns:** :
    None
- **Comments:**
  > Function:
  > Write classification, ID, normal vectors, and polygon face data to a .geo file.
  > Parameters:
  > :
  >     file_path (str): Path to the output .geo file.
  >     cat (list): List of categories for each face.
  >     idd (list): List of IDs corresponding to each face.
  >     normal (list): List of normal vectors, where each normal is a list or tuple of three floats.
  >     faces (list): List of faces, where each face is a list of vertices, and each vertex is a list or tuple of three coordinates.
  > Returns:
  > :
  >     None

---

###### <a id='encoding_graphIO_py_func_read_xml'></a>`read_xml`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** xml.etree.ElementTree.Element
    Root element of the parsed XML tree.
- **Comments:**
  > Function:
  > Parse an XML file and return the root element.
  > Parameters:
  > file_path : str
  >     Path to the XML file to be parsed.
  > 
  > Returns
  > xml.etree.ElementTree.Element
  >     Root element of the parsed XML tree.
  > Returns:
  > xml.etree.ElementTree.Element
  >     Root element of the parsed XML tree.

---

###### <a id='encoding_graphIO_py_func_write_adjson'></a>`write_adjson`
- **Type:** Function
- **Parameters:** file_path: Any, data: Any
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Write data to a file in ADJSON format.
  > Parameters:
  > file_path : str
  >     The path to the file where data will be written.
  > data : str
  >     The data to write to the file, expected to be in ADJSON format.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='encoding_graphIO_py_func_read_adjson'></a>`read_adjson`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** it as a string.

Parameters
file_path : str
    Path to the file to be read. Should be a valid file path accessible by the system.

Returns
str or None
    The content of the file as a string if successful, otherwise None if an error occurs.
- **Comments:**
  > Function:
  > Reads the content of a file and
  > Parameters:
  > file_path : str
  >     Path to the file to be read. Should be a valid file path accessible by the system.
  > 
  > Returns
  > str or None
  >     The content of the file as a string if successful, otherwise None if an error occurs.
  > Returns:
  > it as a string.
  > 
  > Parameters
  > file_path : str
  >     Path to the file to be read. Should be a valid file path accessible by the system.
  > 
  > Returns
  > str or None
  >     The content of the file as a string if successful, otherwise None if an error occurs.

---

###### <a id='encoding_graphIO_py_func_graph_to_json'></a>`graph_to_json`
- **Type:** Function
- **Parameters:** graph: Any, output_dir: Any
- **Returns:** None
    This function does not return any value. It writes two JSON files, 'nodes.json' and 'edges.json',
    to the specified output directory.
- **Comments:**
  > Function:
  > Export graph data to JSON files.
  > Parameters:
  > graph : object
  >     A graph object with a `graph` attribute that contains nodes and edges with attributes.
  >     The graph should have `nodes(data=True)` and `edges(data=True)` methods returning 
  >     node/edge attributes as dictionaries. Node and edge attributes may contain numpy arrays.
  > output_dir : str or pathlib.Path
  >     Directory path where the JSON files will be saved. If the directory does not exist,
  >     it will be created along with any necessary parent directories.
  > 
  > Returns
  > None
  >     This function does not return any value. It writes two JSON files, 'nodes.json' and 'edges.json',
  >     to the specified output directory.
  > Returns:
  > None
  >     This function does not return any value. It writes two JSON files, 'nodes.json' and 'edges.json',
  >     to the specified output directory.

---

###### <a id='encoding_graphIO_py_func_json_to_graph'></a>`json_to_graph`
- **Type:** Function
- **Parameters:** input_dir: Any
- **Returns:** :
    nx.Graph: 重建的NetworkX图对象
- **Comments:**
  > Function:
  > 从JSON文件读取并重建图数据
  > Parameters:
  > :
  >     input_dir (str): JSON文件所在的目录路径
  > Returns:
  > :
  >     nx.Graph: 重建的NetworkX图对象

---


## 📄 File: encoding\main.py
<a id='encoding_main_py'></a>

### Contents
- Functions:
  - [convex_temp()](#encoding_main_py_func_convex_temp)
  - [graph_temp()](#encoding_main_py_func_graph_temp)

---

### 🔧 Functions
###### <a id='encoding_main_py_func_convex_temp'></a>`convex_temp`
- **Type:** Function
- **Parameters:** None
- **Returns:** None
    This function does not return any value. It performs file reading, convexification of faces, and file writing as side effects.
- **Comments:**
  > Function:
  > Apply convexification to geometric data read from a file and write the result to another file.
  > Returns:
  > None
  >     This function does not return any value. It performs file reading, convexification of faces, and file writing as side effects.

---

###### <a id='encoding_main_py_func_graph_temp'></a>`graph_temp`
- **Type:** Function
- **Parameters:** None
- **Returns:** None
    This function does not return any value. It generates and displays a 3D graph as a side effect.
- **Comments:**
  > Function:
  > Create and visualize a 3D graph from XML representation.
  > Returns:
  > None
  >     This function does not return any value. It generates and displays a 3D graph as a side effect.

---


## 📄 File: encoding\quad.py
<a id='encoding_quad_py'></a>

### Contents
- Functions:
  - [create_quadrilaterals()](#encoding_quad_py_func_create_quadrilaterals)

---

### 🔧 Functions
###### <a id='encoding_quad_py_func_create_quadrilaterals'></a>`create_quadrilaterals`
- **Type:** Function
- **Parameters:** divide_lines: Any
- **Returns:** quad_faces : list of numpy.ndarray
    A list of quadrilateral faces, each represented as a 4x3 numpy array containing 
    the four corner points in 3D space.
quad_normals : list of numpy.ndarray
    A list of unit normal vectors (3D) corresponding to each quadrilateral face, 
    normalized to unit length.
- **Comments:**
  > Function:
  > Create quadrilateral faces and their corresponding normals from grouped 3D lines.
  > Parameters:
  > divide_lines : list of numpy.ndarray
  >     A list of line segments, where each line is a 2x3 numpy array representing 
  >     two 3D points (shape: [2, 3]). Each line segment is used to generate quadrilaterals 
  >     when paired with overlapping lines at different heights.
  > 
  > Returns
  > quad_faces : list of numpy.ndarray
  >     A list of quadrilateral faces, each represented as a 4x3 numpy array containing 
  >     the four corner points in 3D space.
  > quad_normals : list of numpy.ndarray
  >     A list of unit normal vectors (3D) corresponding to each quadrilateral face, 
  >     normalized to unit length.
  > Returns:
  > quad_faces : list of numpy.ndarray
  >     A list of quadrilateral faces, each represented as a 4x3 numpy array containing 
  >     the four corner points in 3D space.
  > quad_normals : list of numpy.ndarray
  >     A list of unit normal vectors (3D) corresponding to each quadrilateral face, 
  >     normalized to unit length.

---


## 📄 File: geometry\cleanse.py
<a id='geometry_cleanse_py'></a>

### Contents
- Functions:
  - [_groupByNormal()](#geometry_cleanse_py_func__groupByNormal)
  - [_groupRelateArray()](#geometry_cleanse_py_func__groupRelateArray)
  - [_groupByCollinear()](#geometry_cleanse_py_func__groupByCollinear)
  - [partitionWall()](#geometry_cleanse_py_func_partitionWall)
  - [_fastOverlap()](#geometry_cleanse_py_func__fastOverlap)
  - [cleanseDuplicatedLevel()](#geometry_cleanse_py_func_cleanseDuplicatedLevel)
  - [cleanseOverlapFace()](#geometry_cleanse_py_func_cleanseOverlapFace)
  - [cleanseDuplicatedWall()](#geometry_cleanse_py_func_cleanseDuplicatedWall)
  - [cleanseOverlapWall()](#geometry_cleanse_py_func_cleanseOverlapWall)
  - [cleanseInvalidWall()](#geometry_cleanse_py_func_cleanseInvalidWall)
  - [cleanseInvalidFace()](#geometry_cleanse_py_func_cleanseInvalidFace)
  - [cleanseCoplannerLine()](#geometry_cleanse_py_func_cleanseCoplannerLine)
  - [_coPlannerCleanse()](#geometry_cleanse_py_func__coPlannerCleanse)
  - [solveIntersectionVertical()](#geometry_cleanse_py_func_solveIntersectionVertical)
  - [solveIntersectionHorizontal()](#geometry_cleanse_py_func_solveIntersectionHorizontal)
  - [splitFaces()](#geometry_cleanse_py_func_splitFaces)
  - [_isValid()](#geometry_cleanse_py_func__isValid)
  - [checkBreakIntersection()](#geometry_cleanse_py_func_checkBreakIntersection)

---

### 🔧 Functions
###### <a id='geometry_cleanse_py_func__groupByNormal'></a>`_groupByNormal`
- **Type:** Function
- **Parameters:** listToGroup: list, listOfNormal: list[pygeos.Geometry | np.ndarray]
- **Returns:** list of list
    A 2-dimensional list where each sublist contains elements from `listToGroup`
    that correspond to the same (or parallel) normal vector. The grouping considers
    both positive and negative parallels.
- **Comments:**
  > Function:
  > Group items in a list based on their corresponding normal vectors.
  > Parameters:
  > listToGroup : list
  >     A list of elements to be grouped. The elements can be of any type.
  > listOfNormal : list of pygeos.Geometry or numpy.ndarray
  >     A list of normal vectors (geometric objects or arrays) used as grouping criteria.
  >     Must have the same length as `listToGroup`.
  > 
  > Returns
  > list of list
  >     A 2-dimensional list where each sublist contains elements from `listToGroup`
  >     that correspond to the same (or parallel) normal vector. The grouping considers
  >     both positive and negative parallels.
  > Returns:
  > list of list
  >     A 2-dimensional list where each sublist contains elements from `listToGroup`
  >     that correspond to the same (or parallel) normal vector. The grouping considers
  >     both positive and negative parallels.

---

###### <a id='geometry_cleanse_py_func__groupRelateArray'></a>`_groupRelateArray`
- **Type:** Function
- **Parameters:** sequences: list
- **Returns:** list of list
    A list of lists where each sublist contains the union of originally connected sequences 
    (i.e., sequences that had overlapping elements are combined).
- **Comments:**
  > Function:
  > Join arrays that have intersecting elements into unified groups.
  > Parameters:
  > sequences : list of list
  >     A list of sequences (lists) containing elements. Sequences that share common elements 
  >     will be merged into a single group.
  > 
  > Returns
  > list of list
  >     A list of lists where each sublist contains the union of originally connected sequences 
  >     (i.e., sequences that had overlapping elements are combined).
  > Returns:
  > list of list
  >     A list of lists where each sublist contains the union of originally connected sequences 
  >     (i.e., sequences that had overlapping elements are combined).

---

###### <a id='geometry_cleanse_py_func__groupByCollinear'></a>`_groupByCollinear`
- **Type:** Function
- **Parameters:** listToGroup: list, listOfNormal: list[pygeos.Geometry | np.ndarray], listOfGeometry: list[pygeos.Geometry]
- **Returns:** list of list
    A 2-dimensional list where each sublist contains elements from `listToGroup` that are determined to be collinear
    based on their normal vectors and spatial alignment (proximity along the direction of the normal).
    The grouping is stricter than `_groupByNormal`, resulting in more refined groups.
- **Comments:**
  > Function:
  > Group elements of a list based on collinearity of corresponding geometries.
  > Parameters:
  > listToGroup : list
  >     A list of elements to be grouped. Can be any type, but typically corresponds to geometric objects or identifiers.
  > listOfNormal : list of pygeos.Geometry or numpy.ndarray
  >     A list of normal vectors (as geometries or coordinate arrays) associated with each element in `listToGroup`.
  >     Used to determine directional alignment (collinearity). Must have the same length as `listToGroup`.
  > listOfGeometry : list of pygeos.Geometry
  >     A list of LineString geometries used to test spatial relationships (e.g., intersections and point alignments).
  >     Must have the same length as `listToGroup`.
  > 
  > Returns
  > list of list
  >     A 2-dimensional list where each sublist contains elements from `listToGroup` that are determined to be collinear
  >     based on their normal vectors and spatial alignment (proximity along the direction of the normal).
  >     The grouping is stricter than `_groupByNormal`, resulting in more refined groups.
  > Returns:
  > list of list
  >     A 2-dimensional list where each sublist contains elements from `listToGroup` that are determined to be collinear
  >     based on their normal vectors and spatial alignment (proximity along the direction of the normal).
  >     The grouping is stricter than `_groupByNormal`, resulting in more refined groups.

---

###### <a id='geometry_cleanse_py_func_partitionWall'></a>`partitionWall`
- **Type:** Function
- **Parameters:** walls: list[MoosasWall], model: MoosasContainer, bottom: Any, top: Any
- **Returns:** list[MoosasWall]
    A list of new MoosasWall objects created from sorted unique coordinates and assigned glazing elements, bounded by the specified or inferred top and bottom levels.
- **Comments:**
  > Function:
  > Partition a list of walls by sorting their coordinates and creating new polygonal walls using specified top and bottom boundaries.
  > Parameters:
  > walls : list[MoosasWall]
  >     List of MoosasWall objects to be partitioned. The function processes their 2D coordinates and glazing elements.
  > model : MoosasContainer
  >     The container model to which the new walls will be associated.
  > bottom : float, optional
  >     The bottom elevation level for the new walls. If not provided, it is calculated as the minimum of (wall.level + wall.offset) across all walls.
  > top : float, optional
  >     The top elevation level for the new walls. If not provided, it is calculated as the maximum of (wall.toplevel + wall.topoffset) across all walls.
  > 
  > Returns
  > list[MoosasWall]
  >     A list of new MoosasWall objects created from sorted unique coordinates and assigned glazing elements, bounded by the specified or inferred top and bottom levels.
  > Returns:
  > list[MoosasWall]
  >     A list of new MoosasWall objects created from sorted unique coordinates and assigned glazing elements, bounded by the specified or inferred top and bottom levels.

---

###### <a id='geometry_cleanse_py_func__fastOverlap'></a>`_fastOverlap`
- **Type:** Function
- **Parameters:** wall1: pygeos.Geometry, wall2: pygeos.Geometry
- **Returns:** bool
    True if the walls overlap based on coordinate ordering and spatial proximity, False otherwise.
- **Comments:**
  > Function:
  > Very fast check whether two walls overlap based on coordinate sequence.
  > Parameters:
  > wall1 : pygeos.Geometry
  >     First wall geometry to compare.
  > wall2 : pygeos.Geometry
  >     Second wall geometry to compare.
  > 
  > Returns
  > bool
  >     True if the walls overlap based on coordinate ordering and spatial proximity, False otherwise.
  > Returns:
  > bool
  >     True if the walls overlap based on coordinate ordering and spatial proximity, False otherwise.

---

###### <a id='geometry_cleanse_py_func_cleanseDuplicatedLevel'></a>`cleanseDuplicatedLevel`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The modified model with duplicated levels removed. Faces that were on removed levels 
    are offset and assigned to the nearest lower level. The levelList is updated accordingly.
- **Comments:**
  > Function:
  > Remove duplicated levels and reassign geometries to the bottom level.
  > Parameters:
  > model : MoosasContainer
  >     The input model containing a list of levels and faces. The levels are evaluated 
  >     for duplication based on the total area of associated faces, and redundant levels 
  >     are removed. Faces from removed levels are reassigned to the preceding level.
  > 
  > Returns
  > MoosasContainer
  >     The modified model with duplicated levels removed. Faces that were on removed levels 
  >     are offset and assigned to the nearest lower level. The levelList is updated accordingly.
  > Returns:
  > MoosasContainer
  >     The modified model with duplicated levels removed. Faces that were on removed levels 
  >     are offset and assigned to the nearest lower level. The levelList is updated accordingly.

---

###### <a id='geometry_cleanse_py_func_cleanseOverlapFace'></a>`cleanseOverlapFace`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The modified model with duplicated faces removed or split to resolve overlaps. 
    The operation is performed level by level, and face containment is addressed 
    during the process.
- **Comments:**
  > Function:
  > Identify and remove duplicated faces in the model using geometric overlap analysis.
  > Parameters:
  > model : MoosasContainer
  >     The input model container containing levels, faces, and walls. The function modifies 
  >     `model.faceList` in place by removing or splitting overlapping faces. One of each pair 
  >     of duplicated faces is removed, and differences are added as new faces.
  > 
  > Returns
  > MoosasContainer
  >     The modified model with duplicated faces removed or split to resolve overlaps. 
  >     The operation is performed level by level, and face containment is addressed 
  >     during the process.
  > Returns:
  > MoosasContainer
  >     The modified model with duplicated faces removed or split to resolve overlaps. 
  >     The operation is performed level by level, and face containment is addressed 
  >     during the process.

---

###### <a id='geometry_cleanse_py_func_cleanseDuplicatedWall'></a>`cleanseDuplicatedWall`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The updated model container with duplicated walls removed. One of each pair of duplicated walls
    is dissolved into another and then removed from the wallList.
- **Comments:**
  > Function:
  > Identify and remove duplicated walls based on geometric duplication in 2D.
  > Parameters:
  > model : MoosasContainer
  >     The input model container containing wall and level lists. Walls are checked for duplication
  >     within each level, and duplicated walls are removed from the wallList.
  > 
  > Returns
  > MoosasContainer
  >     The updated model container with duplicated walls removed. One of each pair of duplicated walls
  >     is dissolved into another and then removed from the wallList.
  > Returns:
  > MoosasContainer
  >     The updated model container with duplicated walls removed. One of each pair of duplicated walls
  >     is dissolved into another and then removed from the wallList.

---

###### <a id='geometry_cleanse_py_func_cleanseOverlapWall'></a>`cleanseOverlapWall`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The modified model with overlapping walls removed and replaced by partitioned 
    non-overlapping wall segments. The `wallList` is updated in place to reflect 
    the changes.
- **Comments:**
  > Function:
  > Solve overlapping walls by identifying and partitioning intersecting wall segments.
  > Parameters:
  > model : MoosasContainer
  >     The container object holding the wall and level data. The `wallList` attribute 
  >     contains the walls to be processed, and `levelList` is used to group walls by level.
  > 
  > Returns
  > MoosasContainer
  >     The modified model with overlapping walls removed and replaced by partitioned 
  >     non-overlapping wall segments. The `wallList` is updated in place to reflect 
  >     the changes.
  > Returns:
  > MoosasContainer
  >     The modified model with overlapping walls removed and replaced by partitioned 
  >     non-overlapping wall segments. The `wallList` is updated in place to reflect 
  >     the changes.

---

###### <a id='geometry_cleanse_py_func_cleanseInvalidWall'></a>`cleanseInvalidWall`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The updated MoosasContainer object with invalid walls removed and appropriate walls merged.
- **Comments:**
  > Function:
  > Cleanse invalid walls from the model by removing walls with invalid geometry or zero dimensions and dissolving them into adjacent valid walls.
  > Parameters:
  > model : MoosasContainer
  >     The container object holding the wall list to be cleansed. Walls that are invalid due to zero height, zero length, or invalid pygeos.Geometry 
  >     will be removed. Invalid walls that are geometrically coincident with valid walls below them will be dissolved into those walls.
  > 
  > Returns
  > MoosasContainer
  >     The updated MoosasContainer object with invalid walls removed and appropriate walls merged.
  > Returns:
  > MoosasContainer
  >     The updated MoosasContainer object with invalid walls removed and appropriate walls merged.

---

###### <a id='geometry_cleanse_py_func_cleanseInvalidFace'></a>`cleanseInvalidFace`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The updated model with invalid faces removed from the faceList.
- **Comments:**
  > Function:
  > Check and remove invalid 2D faces from a MoosasContainer.
  > Parameters:
  > model : MoosasContainer
  >     The input model containing a list of faces to be validated. Faces are tested for valid 2D geometry
  >     after triangulation and conversion via force_2d().
  > 
  > Returns
  > MoosasContainer
  >     The updated model with invalid faces removed from the faceList.
  > Returns:
  > MoosasContainer
  >     The updated model with invalid faces removed from the faceList.

---

###### <a id='geometry_cleanse_py_func_cleanseCoplannerLine'></a>`cleanseCoplannerLine`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The modified model with co-planar walls merged. The `wallList` is updated by removing redundant co-planar faces
    and retaining the merged faces.
- **Comments:**
  > Function:
  > Check and remove co-planar faces, merging them into single faces within a MoosasContainer.
  > Parameters:
  > model : MoosasContainer
  >     The input model container containing wall and level data. The `wallList` attribute holds the list of wall faces,
  >     and `levelList` contains the different building levels to process. Co-planar walls in each level are identified
  >     and merged; original walls are removed and merged versions are added.
  > 
  > Returns
  > MoosasContainer
  >     The modified model with co-planar walls merged. The `wallList` is updated by removing redundant co-planar faces
  >     and retaining the merged faces.
  > Returns:
  > MoosasContainer
  >     The modified model with co-planar walls merged. The `wallList` is updated by removing redundant co-planar faces
  >     and retaining the merged faces.

---

###### <a id='geometry_cleanse_py_func__coPlannerCleanse'></a>`_coPlannerCleanse`
- **Type:** Function
- **Parameters:** elements: np.ndarray[MoosasElement]
- **Returns:** tuple of (np.ndarray[MoosasElement], np.ndarray[MoosasElement])
    A tuple containing two arrays:
    - The first array contains the merged, non-redundant MoosasElement objects after coplanar faces have been dissolved.
    - The second array contains the redundant MoosasElement objects that were removed during the merging process.
- **Comments:**
  > Function:
  > Delete coplanar lines by merging adjacent faces that are coplanar.
  > Parameters:
  > elements : np.ndarray[MoosasElement]
  >     Array of MoosasElement objects representing 3D geometric faces. Each element must provide
  >     methods `getEdgeStr()` to retrieve edge strings and `dissolve()` to merge with other faces.
  >     The normal vector of each face is accessed via the `normal` attribute.
  > 
  > Returns
  > tuple of (np.ndarray[MoosasElement], np.ndarray[MoosasElement])
  >     A tuple containing two arrays:
  >     - The first array contains the merged, non-redundant MoosasElement objects after coplanar faces have been dissolved.
  >     - The second array contains the redundant MoosasElement objects that were removed during the merging process.
  > Returns:
  > tuple of (np.ndarray[MoosasElement], np.ndarray[MoosasElement])
  >     A tuple containing two arrays:
  >     - The first array contains the merged, non-redundant MoosasElement objects after coplanar faces have been dissolved.
  >     - The second array contains the redundant MoosasElement objects that were removed during the merging process.

---

###### <a id='geometry_cleanse_py_func_solveIntersectionVertical'></a>`solveIntersectionVertical`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    A new MoosasContainer instance containing the original walls broken into minimal segments
    resulting from intersection calculations. The segmentation is performed recursively and
    may result in a significantly increased number of wall elements.
- **Comments:**
  > Function:
  > Calculate the intersection of wall projections in 2D for each floor and split walls accordingly.
  > 
  > This function computes pairwise intersections between vertical wall faces projected onto 2D space,
  > then subdivides the walls into smaller segments based on these intersections. It operates only
  > on vertical faces (walls) and ignores 3D spatial relationships such as multi-level overlaps.
  > The calculation is optimized by grouping walls by their normal directions using `_groupByNormal`.
  > Parameters:
  > model : MoosasContainer
  >     A container object holding wall data structured per floor. Walls are assumed to be vertical
  >     and represented in 2D projection. The container will be modified in place as walls are split.
  > 
  > Returns
  > MoosasContainer
  >     A new MoosasContainer instance containing the original walls broken into minimal segments
  >     resulting from intersection calculations. The segmentation is performed recursively and
  >     may result in a significantly increased number of wall elements.
  > Returns:
  > MoosasContainer
  >     A new MoosasContainer instance containing the original walls broken into minimal segments
  >     resulting from intersection calculations. The segmentation is performed recursively and
  >     may result in a significantly increased number of wall elements.

---

###### <a id='geometry_cleanse_py_func_solveIntersectionHorizontal'></a>`solveIntersectionHorizontal`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The input model with updated face divisions where overlapping faces have been split into minimal faces
    to resolve horizontal intersections. The modification is done in place, and the same model object is returned.
- **Comments:**
  > Function:
  > Calculate the intersection between faces and edges on each level by recursively dividing overlapping faces.
  > Parameters:
  > model : MoosasContainer
  >     The container object containing levels, faces, and edges. It holds the geometric data to be processed,
  >     including `levelList`, `faceList`, and `edgeList`. Faces are divided based on their overlap with edges
  >     from the same or adjacent levels.
  > 
  > Returns
  > MoosasContainer
  >     The input model with updated face divisions where overlapping faces have been split into minimal faces
  >     to resolve horizontal intersections. The modification is done in place, and the same model object is returned.
  > Returns:
  > MoosasContainer
  >     The input model with updated face divisions where overlapping faces have been split into minimal faces
  >     to resolve horizontal intersections. The modification is done in place, and the same model object is returned.

---

###### <a id='geometry_cleanse_py_func_splitFaces'></a>`splitFaces`
- **Type:** Function
- **Parameters:** face: MoosasFace, edge: MoosasEdge
- **Returns:** tuple
    A tuple containing:
    - innerFace (MoosasFace): The part of the face intersecting with the edge.
    - outerFaces (list[MoosasFace]): List of remaining face parts after subtraction of the intersection.
    Returns None if no valid split is possible due to area precision or geometric validity issues.
- **Comments:**
  > Function:
  > Split a face into inner and outer parts based on intersection with an edge.
  > Parameters:
  > face : MoosasFace
  >     The input face to be split. Must be planar and aligned with the XY plane.
  > edge : MoosasEdge
  >     The edge used as a splitter; defines the boundary for splitting the face.
  > 
  > Returns
  > tuple
  >     A tuple containing:
  >     - innerFace (MoosasFace): The part of the face intersecting with the edge.
  >     - outerFaces (list[MoosasFace]): List of remaining face parts after subtraction of the intersection.
  >     Returns None if no valid split is possible due to area precision or geometric validity issues.
  > Returns:
  > tuple
  >     A tuple containing:
  >     - innerFace (MoosasFace): The part of the face intersecting with the edge.
  >     - outerFaces (list[MoosasFace]): List of remaining face parts after subtraction of the intersection.
  >     Returns None if no valid split is possible due to area precision or geometric validity issues.

---

###### <a id='geometry_cleanse_py_func__isValid'></a>`_isValid`
- **Type:** Function
- **Parameters:** _wall: MoosasWall
- **Returns:** model : object
    The modified model object with invalid walls removed or dissolved into neighboring walls.
    Walls that fail validation are either deleted or merged, and the updated wallList is returned within the model.
- **Comments:**
  > Function:
  > Check and validate walls in the model, removing invalid ones and dissolving them into adjacent valid walls.
  > Parameters:
  > model : object
  >     The model object containing the wallList, levelList, and associated methods such as searchBy and overlapEdge.
  >     Must have attributes `wallList` (list of MoosasWall objects), `levelList` (list of levels), and methods
  >     `searchBy` (for querying walls by property) and `overlapEdge` (for checking geometric edge overlap).
  > 
  > Returns
  > model : object
  >     The modified model object with invalid walls removed or dissolved into neighboring walls.
  >     Walls that fail validation are either deleted or merged, and the updated wallList is returned within the model.
  > Returns:
  > model : object
  >     The modified model object with invalid walls removed or dissolved into neighboring walls.
  >     Walls that fail validation are either deleted or merged, and the updated wallList is returned within the model.

---

###### <a id='geometry_cleanse_py_func_checkBreakIntersection'></a>`checkBreakIntersection`
- **Type:** Function
- **Parameters:** walls: Any, otherWall2d: Any
- **Returns:** list
    A list of wall objects resulting from breaking the input walls at detected intersection points.
    If no intersections are found, returns the original walls. If breaks occur, recursively processes
    the new set of walls until no further intersections remain.
- **Comments:**
  > Function:
  > Recursively checks and resolves intersections between walls by breaking them at intersection points.
  > Parameters:
  > walls : list or object
  >     A single wall object or a list of wall objects. If not a list, it will be converted to a list.
  > otherWall2d : list of geometric objects
  >     A list of 2D geometric representations of walls (typically linestrings) used for intersection testing.
  > 
  > Returns
  > list
  >     A list of wall objects resulting from breaking the input walls at detected intersection points.
  >     If no intersections are found, returns the original walls. If breaks occur, recursively processes
  >     the new set of walls until no further intersections remain.
  > Returns:
  > list
  >     A list of wall objects resulting from breaking the input walls at detected intersection points.
  >     If no intersections are found, returns the original walls. If breaks occur, recursively processes
  >     the new set of walls until no further intersections remain.

---


## 📄 File: geometry\contour.py
<a id='geometry_contour_py'></a>

### Contents
- Functions:
  - [_findPathDepth()](#geometry_contour_py_func__findPathDepth)
  - [_divideBoundaryByNode()](#geometry_contour_py_func__divideBoundaryByNode)
  - [_divideBoundaryByEdge()](#geometry_contour_py_func__divideBoundaryByEdge)
  - [_divideBoundary()](#geometry_contour_py_func__divideBoundary)
  - [outerBoundary()](#geometry_contour_py_func_outerBoundary)
  - [closed_contour_calculation()](#geometry_contour_py_func_closed_contour_calculation)
  - [_documentBoundary()](#geometry_contour_py_func__documentBoundary)
  - [packing_edges()](#geometry_contour_py_func_packing_edges)
  - [plot_TopoObject()](#geometry_contour_py_func_plot_TopoObject)

---

### 🔧 Functions
###### <a id='geometry_contour_py_func__findPathDepth'></a>`_findPathDepth`
- **Type:** Function
- **Parameters:** node: TopoNode, exitPoint: list[TopoNode], avoidPoint: list[TopoNode], avoidEdge: list[TopoBound], max_depth: Any
- **Returns:** list of TopoNode
    A list of nodes representing the path from the input node to an exit point, including both ends. Returns empty list if no path is found.
- **Comments:**
  > Function:
  > Recursive Depth-first search to find a valid path from node to exit points.
  > Parameters:
  > node : TopoNode
  >     The starting node for the search.
  > exitPoint : list of TopoNode
  >     List of target exit nodes to reach.
  > avoidPoint : list of TopoNode, optional
  >     Nodes to exclude from the search (default is None, treated as empty list).
  > avoidEdge : list of TopoBound, optional
  >     Edges to avoid traversing; if a connection between two nodes lies on one of these edges, it will be skipped (default is None, treated as empty list).
  > max_depth : int, default=geom.PATH_MAX_DEPTH
  >     Maximum recursion depth allowed to prevent infinite traversal.
  > 
  > Returns
  > list of TopoNode
  >     A list of nodes representing the path from the input node to an exit point, including both ends. Returns empty list if no path is found.
  > Returns:
  > list of TopoNode
  >     A list of nodes representing the path from the input node to an exit point, including both ends. Returns empty list if no path is found.

---

###### <a id='geometry_contour_py_func__divideBoundaryByNode'></a>`_divideBoundaryByNode`
- **Type:** Function
- **Parameters:** boundaries: list[TopoBound], nodeList: list[TopoNode]
- **Returns:** list of TopoBound
    A list of simplified, non-overlapping boundary objects resulting from recursive subdivision by internal nodes.
- **Comments:**
  > Function:
  > Recursively divide boundaries by internal nodes to decompose complex regions into simpler ones.
  > Parameters:
  > boundaries : list of TopoBound
  >     List of boundary objects to be subdivided. Each boundary represents a closed loop of nodes.
  > nodeList : list of TopoNode
  >     List of nodes not yet assigned to any boundary. These nodes are candidates for splitting existing boundaries.
  > 
  > Returns
  > list of TopoBound
  >     A list of simplified, non-overlapping boundary objects resulting from recursive subdivision by internal nodes.
  > Returns:
  > list of TopoBound
  >     A list of simplified, non-overlapping boundary objects resulting from recursive subdivision by internal nodes.

---

###### <a id='geometry_contour_py_func__divideBoundaryByEdge'></a>`_divideBoundaryByEdge`
- **Type:** Function
- **Parameters:** boundaries: list[TopoBound], edgeList: list[TopoBound] | list[TopoEdge]
- **Returns:** list of TopoBound
    A list of refined boundary objects resulting from recursive subdivision by eligible edges.
- **Comments:**
  > Function:
  > Recursively divide boundary polygons using internal edges.
  > Parameters:
  > boundaries : list of TopoBound
  >     List of boundary objects to be subdivided. Each boundary represents a polygonal region.
  > edgeList : list of TopoBound or list of TopoEdge
  >     List of edges that may lie inside the boundaries and are used for subdivision. 
  >     These edges are not part of any existing boundary. If TopoEdge objects are provided, 
  >     they are converted internally to TopoBound objects.
  > 
  > Returns
  > list of TopoBound
  >     A list of refined boundary objects resulting from recursive subdivision by eligible edges.
  > Returns:
  > list of TopoBound
  >     A list of refined boundary objects resulting from recursive subdivision by eligible edges.

---

###### <a id='geometry_contour_py_func__divideBoundary'></a>`_divideBoundary`
- **Type:** Function
- **Parameters:** boundaries: list[TopoBound], edgeList: list[TopoBound] | list[TopoEdge]
- **Returns:** list[TopoBound]
    A list of decomposed boundary objects resulting from recursive subdivision. 
    The output contains only minimal boundaries (i.e., those without any internal edges) and any newly detected inner rings.
- **Comments:**
  > Function:
  > Recursively divide boundaries using internal edges to decompose complex regions into minimal boundaries.
  > Parameters:
  > boundaries : list[TopoBound]
  >     List of boundary objects to be subdivided. Each boundary is expected to define a closed loop.
  > edgeList : list[TopoBound] or list[TopoEdge]
  >     List of edge-like objects (either `TopoBound` or `TopoEdge`) that may lie inside the boundaries and are used for splitting.
  >     These edges are typically not yet part of any boundary and represent internal connections or potential splits.
  > 
  > Returns
  > list[TopoBound]
  >     A list of decomposed boundary objects resulting from recursive subdivision. 
  >     The output contains only minimal boundaries (i.e., those without any internal edges) and any newly detected inner rings.
  > Returns:
  > list[TopoBound]
  >     A list of decomposed boundary objects resulting from recursive subdivision. 
  >     The output contains only minimal boundaries (i.e., those without any internal edges) and any newly detected inner rings.

---

###### <a id='geometry_contour_py_func_outerBoundary'></a>`outerBoundary`
- **Type:** Function
- **Parameters:** model: MoosasContainer, bld_level: float
- **Returns:** list[pygeos.Geometry]
    A list of pygeos Geometry objects representing the outer boundaries of each network component.
- **Comments:**
  > Function:
  > Calculate the outer boundary of a network at a specified building level.
  > Parameters:
  > model : MoosasContainer
  >     The model containing topological edges to retrieve the network from.
  > bld_level : float
  >     The building level at which to retrieve the network.
  > 
  > Returns
  > list[pygeos.Geometry]
  >     A list of pygeos Geometry objects representing the outer boundaries of each network component.
  > Returns:
  > list[pygeos.Geometry]
  >     A list of pygeos Geometry objects representing the outer boundaries of each network component.

---

###### <a id='geometry_contour_py_func_closed_contour_calculation'></a>`closed_contour_calculation`
- **Type:** Function
- **Parameters:** model: MoosasContainer, bld_level: float
- **Returns:** MoosasContainer
    The updated model with recorded boundary information from the contour calculation.
- **Comments:**
  > Function:
  > Calculate closed contours at a specified building level and update the model with boundary information.
  > Parameters:
  > model : MoosasContainer
  >     The input model containing topological edges to be processed.
  > bld_level : float
  >     The building level at which to compute the closed contours.
  > 
  > Returns
  > MoosasContainer
  >     The updated model with recorded boundary information from the contour calculation.
  > Returns:
  > MoosasContainer
  >     The updated model with recorded boundary information from the contour calculation.

---

###### <a id='geometry_contour_py_func__documentBoundary'></a>`_documentBoundary`
- **Type:** Function
- **Parameters:** boundaries: Iterable[TopoBound], model: MoosasContainer
- **Returns:** MoosasContainer
    The updated model with boundary edge lists appended to its boundaryList attribute.
- **Comments:**
  > Function:
  > Reverse boundary orientation if necessary and append boundary edges to model.
  > Parameters:
  > boundaries : Iterable[TopoBound]
  >     An iterable of TopoBound objects representing boundaries, each containing a geometry and edge loop.
  > model : MoosasContainer
  >     The container model to which boundary edge lists will be added.
  > 
  > Returns
  > MoosasContainer
  >     The updated model with boundary edge lists appended to its boundaryList attribute.
  > Returns:
  > MoosasContainer
  >     The updated model with boundary edge lists appended to its boundaryList attribute.

---

###### <a id='geometry_contour_py_func_packing_edges'></a>`packing_edges`
- **Type:** Function
- **Parameters:** model: MoosasContainer, divided_zones: Any
- **Returns:** MoosasContainer
    The updated model with validated and potentially subdivided edges, newly added air walls (if applicable),
    and remaining unassigned walls marked in `wall_remain`.
- **Comments:**
  > Function:
  > Packs edges into a MoosasContainer by validating and processing boundary lists, and optionally subdividing complex faces into simpler polygons.
  > Parameters:
  > model : MoosasContainer
  >     The container object holding wall, edge, boundary, and level lists to be processed.
  >     Modified in place by appending valid edges and walls, and removing processed ones.
  > divided_zones : bool
  >     If True, enables the subdivision of complex 2D faces into simpler polygons using triangulation.
  >     Air walls are added to represent internal divisions, and original edges are replaced with new constructed edges.
  > 
  > Returns
  > MoosasContainer
  >     The updated model with validated and potentially subdivided edges, newly added air walls (if applicable),
  >     and remaining unassigned walls marked in `wall_remain`.
  > Returns:
  > MoosasContainer
  >     The updated model with validated and potentially subdivided edges, newly added air walls (if applicable),
  >     and remaining unassigned walls marked in `wall_remain`.

---

###### <a id='geometry_contour_py_func_plot_TopoObject'></a>`plot_TopoObject`
- **Type:** Function
- **Parameters:** *collection: TopoNode | TopoNetwork | TopoEdge | TopoBound
- **Returns:** None
    This function does not return any value. It generates a matplotlib plot as a side effect.
- **Comments:**
  > Function:
  > Plot TopoObject instances such as TopoNode, TopoEdge, TopoBound, or TopoNetwork.
  > Parameters:
  > *collection : TopoNode or TopoNetwork or TopoEdge or TopoBound
  >     Variable number of topology objects to plot. Supported types include TopoNode (points),
  >     TopoEdge (lines), TopoBound (areas), and TopoNetwork (collections of nodes and edges).
  > color : str, optional
  >     Color string to use for plotting the objects (e.g., 'r', 'b', '#FF5733'). If empty string (''),
  >     default color is used. Default is ''.
  > show : bool, optional
  >     If True, display the plot immediately using plt.show(). Default is True.
  > filled : bool, optional
  >     If True and the object is a TopoBound (area), fill the area with the same color. Default is False.
  > 
  > Returns
  > None
  >     This function does not return any value. It generates a matplotlib plot as a side effect.
  > Returns:
  > None
  >     This function does not return any value. It generates a matplotlib plot as a side effect.

---


## 📄 File: geometry\contour_lagacy.py
<a id='geometry_contour_lagacy_py'></a>

### Contents
- Functions:
  - [closed_contour_calculation()](#geometry_contour_lagacy_py_func_closed_contour_calculation)
  - [findpath_depth()](#geometry_contour_lagacy_py_func_findpath_depth)
  - [split()](#geometry_contour_lagacy_py_func_split)
  - [polygon_from_node()](#geometry_contour_lagacy_py_func_polygon_from_node)
  - [useful_wall()](#geometry_contour_lagacy_py_func_useful_wall)
  - [construct_node_network()](#geometry_contour_lagacy_py_func_construct_node_network)
  - [node_Groupping()](#geometry_contour_lagacy_py_func_node_Groupping)
  - [nodegroup_outerboundary()](#geometry_contour_lagacy_py_func_nodegroup_outerboundary)
  - [divide_boundary_node()](#geometry_contour_lagacy_py_func_divide_boundary_node)
  - [divide_boundary_edge()](#geometry_contour_lagacy_py_func_divide_boundary_edge)
  - [document_boundary()](#geometry_contour_lagacy_py_func_document_boundary)
  - [remove_wall()](#geometry_contour_lagacy_py_func_remove_wall)
  - [overlaps_in_node()](#geometry_contour_lagacy_py_func_overlaps_in_node)
  - [findpath_breadth()](#geometry_contour_lagacy_py_func_findpath_breadth)

---

### 🔧 Functions
###### <a id='geometry_contour_lagacy_py_func_closed_contour_calculation'></a>`closed_contour_calculation`
- **Type:** Function
- **Parameters:** model: MoosasModel, bld_level: float
- **Returns:** MoosasModel
    The input model updated with detected boundary information at the specified level.
- **Comments:**
  > Function:
  > Perform closed contour calculation for a given building level in a model.
  > Parameters:
  > model : MoosasModel
  >     The building model containing walls and other structural elements.
  > bld_level : float
  >     The building level (elevation) at which to perform the closed contour calculation.
  > 
  > Returns
  > MoosasModel
  >     The input model updated with detected boundary information at the specified level.
  > Returns:
  > MoosasModel
  >     The input model updated with detected boundary information at the specified level.

---

###### <a id='geometry_contour_lagacy_py_func_findpath_depth'></a>`findpath_depth`
- **Type:** Function
- **Parameters:** node: Any, end: list, node_list: list, block_list: list, last: Any, max_depth: Any
- **Returns:** list
    A list of nodes representing the path from `node` to a node in `end`, 
    in reverse order (from end to start). Returns empty list if no path is found 
    within the depth limit or due to blocking.
- **Comments:**
  > Function:
  > Find a path from the current node to any node in the end list using depth-limited DFS.
  > Parameters:
  > node : int or hashable
  >     The current node to start searching from.
  > end : list
  >     List of target nodes; the search stops if any of these nodes are reached.
  > node_list : list of lists or dict of lists
  >     Adjacency list representing the graph; node_list[node] contains neighbors of node.
  > block_list : list
  >     List of nodes that cannot be traversed; paths through these nodes are blocked.
  > last : int or hashable, optional
  >     The previous node in the path to avoid going backwards. Default is None.
  > max_depth : int, optional
  >     Maximum depth to search from the current node. Default is geom.PATH_MAX_DEPTH.
  > 
  > Returns
  > list
  >     A list of nodes representing the path from `node` to a node in `end`, 
  >     in reverse order (from end to start). Returns empty list if no path is found 
  >     within the depth limit or due to blocking.
  > Returns:
  > list
  >     A list of nodes representing the path from `node` to a node in `end`, 
  >     in reverse order (from end to start). Returns empty list if no path is found 
  >     within the depth limit or due to blocking.

---

###### <a id='geometry_contour_lagacy_py_func_split'></a>`split`
- **Type:** Function
- **Parameters:** linerring: list, splitline: list
- **Returns:** tuple of list
    A tuple containing two lists: linerring1 and linerring2. These represent the two resulting 
    rings after splitting the original linerring along the splitline. The splitline is included 
    in both output rings in forward order in linerring1 and reverse order in linerring2.
- **Comments:**
  > Function:
  > Split a linear ring by a given split line.
  > Parameters:
  > linerring : list
  >     List of nodes representing a linear ring. If the first and last elements are identical, 
  >     the last element is removed before processing.
  > splitline : list
  >     List of nodes defining the split line. The split starts at the first node of splitline 
  >     and ends at the last node. This line is used to divide the linerring into two parts.
  > 
  > Returns
  > tuple of list
  >     A tuple containing two lists: linerring1 and linerring2. These represent the two resulting 
  >     rings after splitting the original linerring along the splitline. The splitline is included 
  >     in both output rings in forward order in linerring1 and reverse order in linerring2.
  > Returns:
  > tuple of list
  >     A tuple containing two lists: linerring1 and linerring2. These represent the two resulting 
  >     rings after splitting the original linerring along the splitline. The splitline is included 
  >     in both output rings in forward order in linerring1 and reverse order in linerring2.

---

###### <a id='geometry_contour_lagacy_py_func_polygon_from_node'></a>`polygon_from_node`
- **Type:** Function
- **Parameters:** nodelist: list, location: list
- **Returns:** pygeos.Geometry
    A polygon geometry constructed from the ordered sequence of points.
- **Comments:**
  > Function:
  > Construct a polygon from a list of node indices and their corresponding locations.
  > Parameters:
  > nodelist : list
  >     List of indices referring to positions in the location list.
  > location : list
  >     List of point geometries (e.g., PyGEOS points) corresponding to node locations.
  > 
  > Returns
  > pygeos.Geometry
  >     A polygon geometry constructed from the ordered sequence of points.
  > Returns:
  > pygeos.Geometry
  >     A polygon geometry constructed from the ordered sequence of points.

---

###### <a id='geometry_contour_lagacy_py_func_useful_wall'></a>`useful_wall`
- **Type:** Function
- **Parameters:** wall_list: Any, model: Any
- **Returns:** list of int
    Filtered list of wall indices with invalid, zero-length, duplicate, and 
    isolated walls removed.
- **Comments:**
  > Function:
  > Filter out invalid, zero-length, duplicate, and isolated walls from a wall list.
  > Parameters:
  > wall_list : list of int
  >     List of wall indices to be filtered.
  > model : object
  >     Model object containing a `wallList` attribute, where each element is a wall 
  >     with methods `force_2d()` and attributes `height` representing geometric and 
  >     dimensional properties.
  > 
  > Returns
  > list of int
  >     Filtered list of wall indices with invalid, zero-length, duplicate, and 
  >     isolated walls removed.
  > Returns:
  > list of int
  >     Filtered list of wall indices with invalid, zero-length, duplicate, and 
  >     isolated walls removed.

---

###### <a id='geometry_contour_lagacy_py_func_construct_node_network'></a>`construct_node_network`
- **Type:** Function
- **Parameters:** vec_list: Any
- **Returns:** location_list : list
    List of unique points (nodes) extracted from the second element of each tuple in vec_list.
node_list : list of numpy.ndarray
    List where each element is an array of indices representing connected nodes 
    to the corresponding node in location_list, sorted by angular order.
angle_list : list of numpy.ndarray
    List where each element is an array of angles corresponding to the direction 
    of connected vectors from the node, sorted in ascending order.
- **Comments:**
  > Function:
  > Construct a node network from a list of vectors.
  > Parameters:
  > vec_list : list of tuple
  >     A list where each element is a tuple containing vector information.
  >     Each tuple is expected to have at least three elements: 
  >     (ignored, source_point, target_point), where source_point and target_point 
  >     are points (e.g., coordinates or identifiers) representing connections.
  > 
  > Returns
  > location_list : list
  >     List of unique points (nodes) extracted from the second element of each tuple in vec_list.
  > node_list : list of numpy.ndarray
  >     List where each element is an array of indices representing connected nodes 
  >     to the corresponding node in location_list, sorted by angular order.
  > angle_list : list of numpy.ndarray
  >     List where each element is an array of angles corresponding to the direction 
  >     of connected vectors from the node, sorted in ascending order.
  > Returns:
  > location_list : list
  >     List of unique points (nodes) extracted from the second element of each tuple in vec_list.
  > node_list : list of numpy.ndarray
  >     List where each element is an array of indices representing connected nodes 
  >     to the corresponding node in location_list, sorted by angular order.
  > angle_list : list of numpy.ndarray
  >     List where each element is an array of angles corresponding to the direction 
  >     of connected vectors from the node, sorted in ascending order.

---

###### <a id='geometry_contour_lagacy_py_func_node_Groupping'></a>`node_Groupping`
- **Type:** Function
- **Parameters:** node_list: Any
- **Returns:** list of list
    A list of groups, where each group is a list of indices representing connected nodes.
- **Comments:**
  > Function:
  > Group nodes based on their connectivity.
  > Parameters:
  > node_list : list of list
  >     A list where each element is a list representing connections or edges from a node.
  >     Nodes with more than one connection are considered eligible for grouping.
  > 
  > Returns
  > list of list
  >     A list of groups, where each group is a list of indices representing connected nodes.
  > Returns:
  > list of list
  >     A list of groups, where each group is a list of indices representing connected nodes.

---

###### <a id='geometry_contour_lagacy_py_func_nodegroup_outerboundary'></a>`nodegroup_outerboundary`
- **Type:** Function
- **Parameters:** node_groups: Any, node_list: Any, location_list: Any, angle_list: Any
- **Returns:** list of list of list of int
    A list corresponding to each node group. Each element is a list of closed loops (sub-boundaries),
    where each loop is represented as a list of node indices forming an outer or inner boundary.
- **Comments:**
  > Function:
  > Compute the outer boundary of each node group based on geometric and angular relationships.
  > Parameters:
  > node_groups : list of list of int
  >     A list of node groups, where each group is a list of node indices.
  > node_list : list of list of int
  >     Adjacency list representation of the graph; node_list[i] contains the neighbors of node i.
  > location_list : list of object
  >     List of point objects representing the spatial location of each node; supports coordinate extraction via pygeos.
  > angle_list : list of list of float
  >     For each node, a list of angles (in radians) to its neighboring nodes, aligned with node_list.
  > 
  > Returns
  > list of list of list of int
  >     A list corresponding to each node group. Each element is a list of closed loops (sub-boundaries),
  >     where each loop is represented as a list of node indices forming an outer or inner boundary.
  > Returns:
  > list of list of list of int
  >     A list corresponding to each node group. Each element is a list of closed loops (sub-boundaries),
  >     where each loop is represented as a list of node indices forming an outer or inner boundary.

---

###### <a id='geometry_contour_lagacy_py_func_divide_boundary_node'></a>`divide_boundary_node`
- **Type:** Function
- **Parameters:** boundary_iteration: Any, node_list: Any, location_list: Any, eligible: Any
- **Returns:** list of list of int
    Refined list of boundary node sequences after iterative splitting; each inner list is a 
    resulting polygon boundary with inserted nodes, ensuring no eligible interior nodes remain.
- **Comments:**
  > Function:
  > Iteratively splits boundary nodes by inserting eligible interior nodes to refine polygonal regions.
  > Parameters:
  > boundary_iteration : list of list of int
  >     A list of boundary node sequences, where each inner list represents a polygonal boundary 
  >     defined by node indices.
  > node_list : dict or list of lists
  >     Graph-like structure representing connections between nodes; used during depth-first search 
  >     to find paths between nodes.
  > location_list : array-like of shapely.Point or similar geometric points
  >     List of point coordinates corresponding to each node, indexed by node ID; used for spatial 
  >     containment checks.
  > eligible : list of int
  >     List of node indices that are candidates for insertion into boundaries if they lie inside 
  >     a given region.
  > 
  > Returns
  > list of list of int
  >     Refined list of boundary node sequences after iterative splitting; each inner list is a 
  >     resulting polygon boundary with inserted nodes, ensuring no eligible interior nodes remain.
  > Returns:
  > list of list of int
  >     Refined list of boundary node sequences after iterative splitting; each inner list is a 
  >     resulting polygon boundary with inserted nodes, ensuring no eligible interior nodes remain.

---

###### <a id='geometry_contour_lagacy_py_func_divide_boundary_edge'></a>`divide_boundary_edge`
- **Type:** Function
- **Parameters:** boundary_iteration: Any, vec_list: Any, node_groups: Any
- **Returns:** list of array_like
    A list of divided boundary edge vectors resulting from the grouping and iteration.
- **Comments:**
  > Function:
  > Divide boundary edges based on given node groups and vector list.
  > Parameters:
  > boundary_iteration : int
  >     The current iteration index for the boundary processing.
  > vec_list : list of array_like
  >     List of vectors representing line segments or edges in the boundary.
  > node_groups : list of tuple
  >     List of tuples, each containing node indices that define a group of connected nodes.
  > 
  > Returns
  > list of array_like
  >     A list of divided boundary edge vectors resulting from the grouping and iteration.
  > Returns:
  > list of array_like
  >     A list of divided boundary edge vectors resulting from the grouping and iteration.

---

###### <a id='geometry_contour_lagacy_py_func_document_boundary'></a>`document_boundary`
- **Type:** Function
- **Parameters:** boundary_coordinates: Any, location_list: Any, vec_list: Any, model: Any
- **Returns:** model : object
    The input model object with updated `boundaryList` containing lists of wall elements 
    representing each detected boundary.
- **Comments:**
  > Function:
  > Constructs and appends boundary edges to the model based on boundary coordinates.
  > Parameters:
  > boundary_coordinates : list of list of int
  >     A nested list where each sublist contains node indices defining a polygonal boundary.
  > location_list : list
  >     List of node locations; used to construct polygons for orientation checking.
  > vec_list : list of tuples
  >     List of vectors, each represented as a tuple (index, node1, node2), 
  >     used to find corresponding wall elements between nodes.
  > model : object
  >     A model object containing a `wallList` attribute (list of wall elements) 
  >     and a `boundaryList` attribute (list to which constructed boundaries are appended).
  > 
  > Returns
  > model : object
  >     The input model object with updated `boundaryList` containing lists of wall elements 
  >     representing each detected boundary.
  > Returns:
  > model : object
  >     The input model object with updated `boundaryList` containing lists of wall elements 
  >     representing each detected boundary.

---

###### <a id='geometry_contour_lagacy_py_func_remove_wall'></a>`remove_wall`
- **Type:** Function
- **Parameters:** wall_list: Any
- **Returns:** tuple of (numpy.ndarray, list of int)
    A tuple containing:
    - vec_list: A numpy array of shape (N, 3) where each row contains 
      [wall_index, start_point, end_point] for each directed segment of the remaining walls.
    - wall_list: Modified list of wall indices that satisfy the connectivity condition 
      (both endpoints shared by at least two other points in the simplified point set).
- **Comments:**
  > Function:
  > Remove walls that do not meet connectivity criteria and generate a list of wall vectors.
  > Parameters:
  > wall_list : list of int
  >     List of indices referring to walls in `model.wallList`. Each wall is processed 
  >     to extract its 2D geometric representation using `force_2d()`.
  > 
  > Returns
  > tuple of (numpy.ndarray, list of int)
  >     A tuple containing:
  >     - vec_list: A numpy array of shape (N, 3) where each row contains 
  >       [wall_index, start_point, end_point] for each directed segment of the remaining walls.
  >     - wall_list: Modified list of wall indices that satisfy the connectivity condition 
  >       (both endpoints shared by at least two other points in the simplified point set).
  > Returns:
  > tuple of (numpy.ndarray, list of int)
  >     A tuple containing:
  >     - vec_list: A numpy array of shape (N, 3) where each row contains 
  >       [wall_index, start_point, end_point] for each directed segment of the remaining walls.
  >     - wall_list: Modified list of wall indices that satisfy the connectivity condition 
  >       (both endpoints shared by at least two other points in the simplified point set).

---

###### <a id='geometry_contour_lagacy_py_func_overlaps_in_node'></a>`overlaps_in_node`
- **Type:** Function
- **Parameters:** geo1_node: list, geo2_node: list
- **Returns:** bool
    True if the two nodes are adjacent in geo1_node, False otherwise.
- **Comments:**
  > Function:
  > Check if two nodes overlap in a geometric sequence and process boundary edges accordingly.
  > Parameters:
  > geo1_node : list
  >     List representing the first geometric node sequence.
  > geo2_node : list
  >     List of two elements representing the second geometric node to check for overlap in geo1_node.
  > 
  > Returns
  > bool
  >     True if the two nodes are adjacent in geo1_node, False otherwise.
  > Returns:
  > bool
  >     True if the two nodes are adjacent in geo1_node, False otherwise.

---

###### <a id='geometry_contour_lagacy_py_func_findpath_breadth'></a>`findpath_breadth`
- **Type:** Function
- **Parameters:** node: Any
- **Returns:** list
    Updated list of node groups, where each group is a list of connected nodes.
- **Comments:**
  > Function:
  > Perform a breadth-first search to find a path from the start node and group connected nodes.
  > Parameters:
  > node : object
  >     The current node being processed in the graph. Expected to be a hashable type.
  > start : object
  >     The starting node for the breadth-first traversal. Must be present in the graph.
  > node_list : dict
  >     A dictionary mapping each node to a list of its neighboring nodes.
  > eligible : set
  >     A set of nodes that are eligible to be visited during traversal.
  > node_groups : list
  >     A list that accumulates groups of connected nodes; updated in-place.
  > group : list
  >     A temporary list storing the current group of connected nodes during traversal.
  > 
  > Returns
  > list
  >     Updated list of node groups, where each group is a list of connected nodes.
  > Returns:
  > list
  >     Updated list of node groups, where each group is a list of connected nodes.

---


## 📄 File: geometry\element.py
<a id='geometry_element_py'></a>

### Contents
- Classes:
  - [MoosasGeometry](#geometry_element_py_class_MoosasGeometry)
  - [MoosasElement](#geometry_element_py_class_MoosasElement)
  - [MoosasFace](#geometry_element_py_class_MoosasFace)
  - [MoosasSkylight](#geometry_element_py_class_MoosasSkylight)
  - [MoosasWall](#geometry_element_py_class_MoosasWall)
  - [MoosasGlazing](#geometry_element_py_class_MoosasGlazing)
  - [MoosasFloor](#geometry_element_py_class_MoosasFloor)
  - [MoosasEdge](#geometry_element_py_class_MoosasEdge)
  - [MoosasSpace](#geometry_element_py_class_MoosasSpace)
  - [MoosasContainer](#geometry_element_py_class_MoosasContainer)
- Functions:
  - [_getElement()](#geometry_element_py_func__getElement)
  - [reverseTwin()](#geometry_element_py_func_reverseTwin)

---

### 📦 Class: MoosasGeometry
<a id='geometry_element_py_class_MoosasGeometry'></a>
**Description:** protection for original geometry.

#### Methods
###### <a id='geometry_element_py_class_MoosasGeometry_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, face: pygeos.Geometry | np.ndarray, faceId: Any, normal: pygeos.Geometry | Vector | np.ndarray, category: Any, holes: list[pygeos.Geometry | np.ndarray], errors: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a polygon object with face geometry, identifier, normal vector, and optional holes.
  > Parameters:
  > face : pygeos.Geometry or np.ndarray
  >     The outer boundary of the polygon as a geometry object or coordinate array.
  > faceId : hashable
  >     Identifier for the face, converted to string internally.
  > normal : pygeos.Geometry or Vector or np.ndarray, optional
  >     Normal vector of the face; if None, computed automatically using faceNormal.
  > category : int, default 0
  >     Category label associated with the face.
  > holes : list of pygeos.Geometry or np.ndarray, optional
  >     List of inner boundaries (holes) within the face; defaults to empty list.
  > errors : {'ignore', 'raise'}, default 'ignore'
  >     Specifies behavior when invalid geometry is detected: 'ignore' prints a warning,
  >     'raise' throws a GeometryError.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasGeometry_method__treatFace'></a>`_treatFace`
- **Type:** Instance Method
- **Parameters:** face: Any
- **Returns:** numpy.ndarray
    A 2D NumPy array of shape (N, 3) containing the processed (x, y, z) coordinates of the face,
    with duplicate consecutive points removed and missing Z-coordinates filled with 0.
    Raises `GeometryError` if the resulting coordinate list has fewer than 3 unique non-collinear points.
- **Comments:**
  > Function:
  > Preprocess a face or hole by converting and validating its coordinates.
  > Parameters:
  > face : array-like or pygeos.Geometry
  >     The input face or hole, either as a PyGEOS geometry object or a sequence of coordinate points.
  >     If it is a PyGEOS geometry, coordinates are extracted using `pygeos.get_coordinates` with Z included.
  > 
  > Returns
  > numpy.ndarray
  >     A 2D NumPy array of shape (N, 3) containing the processed (x, y, z) coordinates of the face,
  >     with duplicate consecutive points removed and missing Z-coordinates filled with 0.
  >     Raises `GeometryError` if the resulting coordinate list has fewer than 3 unique non-collinear points.
  > Returns:
  > numpy.ndarray
  >     A 2D NumPy array of shape (N, 3) containing the processed (x, y, z) coordinates of the face,
  >     with duplicate consecutive points removed and missing Z-coordinates filled with 0.
  >     Raises `GeometryError` if the resulting coordinate list has fewer than 3 unique non-collinear points.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_invalid'></a>`invalid`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str or None
    Returns a string describing the validation error if an invalid condition 
    (e.g., self-intersection) is found; otherwise, returns None if the geometry is valid.
- **Comments:**
  > Function:
  > Check for invalid polygon geometries such as self-intersections.
  > Parameters:
  > self : object
  >     The instance containing the geometry data. Must have `__face` and `__holes` 
  >     attributes, where `__face` is the outer boundary and `__holes` is a list 
  >     of inner hole coordinates.
  > 
  > Returns
  > str or None
  >     Returns a string describing the validation error if an invalid condition 
  >     (e.g., self-intersection) is found; otherwise, returns None if the geometry is valid.
  > Returns:
  > str or None
  >     Returns a string describing the validation error if an invalid condition 
  >     (e.g., self-intersection) is found; otherwise, returns None if the geometry is valid.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_face'></a>`face`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** pygeos.Geometry
    A PyGEOS geometry representing the polygon formed by the boundary and optional holes.
- **Comments:**
  > Function:
  > Return the face geometry of the object as a polygon.
  > Parameters:
  > self : object
  >     The instance of the class containing the boundary and holes attributes.
  > 
  > Returns
  > pygeos.Geometry
  >     A PyGEOS geometry representing the polygon formed by the boundary and optional holes.
  > Returns:
  > pygeos.Geometry
  >     A PyGEOS geometry representing the polygon formed by the boundary and optional holes.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_boundary'></a>`boundary`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a LinearRing geometry representing the boundary of the face
using the pygeos.linearrings function applied to the internal face data.

Parameters
self : object
    The instance of the class containing the `__face` attribute.

Returns
pygeos.Geometry
    A LinearRing geometry representing the boundary of the face.
- **Comments:**
  > Function:
  > Boundary of the face as a LinearRing.
  > Parameters:
  > self : object
  >     The instance of the class containing the `__face` attribute.
  > 
  > Returns
  > pygeos.Geometry
  >     A LinearRing geometry representing the boundary of the face.
  > Returns:
  > a LinearRing geometry representing the boundary of the face
  > using the pygeos.linearrings function applied to the internal face data.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the `__face` attribute.
  > 
  > Returns
  > pygeos.Geometry
  >     A LinearRing geometry representing the boundary of the face.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_normal'></a>`normal`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** pygeos.Geometry
    The geometry of the normal vector. If `self.flip` is True, returns the negated
    normal's geometry; otherwise, returns the original normal's geometry.
- **Comments:**
  > Function:
  > Geometry of the normal vector, optionally flipped.
  > Parameters:
  > self : object
  >     The instance of the class containing this property. It is expected to have
  >     attributes `__normal` (with a `geometry` attribute) and `flip` (boolean).
  > 
  > Returns
  > pygeos.Geometry
  >     The geometry of the normal vector. If `self.flip` is True, returns the negated
  >     normal's geometry; otherwise, returns the original normal's geometry.
  > Returns:
  > pygeos.Geometry
  >     The geometry of the normal vector. If `self.flip` is True, returns the negated
  >     normal's geometry; otherwise, returns the original normal's geometry.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_faceId'></a>`faceId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    The face ID.
- **Comments:**
  > Function:
  > Get the face ID as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > str
  >     The face ID.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_category'></a>`category`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the category of the surface as an integer, where each value represents 
a specific type of surface or element (e.g., opaque, translucent, shading, etc.).

Returns
int
    The category code:
    - -2: Ignore faces (excluded from calculations)
    - -1: Shading faces (included as shading elements)
    -  0: Opaque surface
    -  1: Translucent surface
    -  2: Air wall
    -  3: Wall element (MoosasWall)
    -  4: Plane element (MoosasFace)
    -  5: Glazing element (MoosasGlazing)
    -  6: Skylight element (MoosasSkylight)
- **Comments:**
  > Function:
  > Category identifier for the surface element.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > the category of the surface as an integer, where each value represents 
  > a specific type of surface or element (e.g., opaque, translucent, shading, etc.).
  > 
  > Returns
  > int
  >     The category code:
  >     - -2: Ignore faces (excluded from calculations)
  >     - -1: Shading faces (included as shading elements)
  >     -  0: Opaque surface
  >     -  1: Translucent surface
  >     -  2: Air wall
  >     -  3: Wall element (MoosasWall)
  >     -  4: Plane element (MoosasFace)
  >     -  5: Glazing element (MoosasGlazing)
  >     -  6: Skylight element (MoosasSkylight)

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_setCategory'></a>`setCategory`
- **Type:** Instance Method
- **Parameters:** self: Any, cat: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Set the category attribute based on input or predefined conditions.
  > Parameters:
  > cat : int, optional
  >     The category value to set. If not provided, the category is determined
  >     based on the current value of `self.category` using internal rules:
  >     - If `self.category` is 3, 4, or -1, sets `self.__category` to 0.
  >     - If `self.category` is greater than or equal to 5, sets `self.__category` to 1.
  >     Default is None.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_holes'></a>`holes`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a list of hole geometries in the object, converted to linearrings using pygeos.

Parameters
self : object
    The instance of the class containing the private attribute __holes.

Returns
list of pygeos.Geometry
    A list of pygeos Geometry objects representing the holes as linearrings.
- **Comments:**
  > Function:
  > List of hole geometries as linearrings.
  > Parameters:
  > self : object
  >     The instance of the class containing the private attribute __holes.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list of pygeos Geometry objects representing the holes as linearrings.
  > Returns:
  > a list of hole geometries in the object, converted to linearrings using pygeos.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the private attribute __holes.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list of pygeos Geometry objects representing the holes as linearrings.

---

###### <a id='geometry_element_py_class_MoosasGeometry_method_getEdgeStr'></a>`getEdgeStr`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get a unique edge string of the boundary, ignore the direction of the edge.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

### 📦 Class: MoosasElement
<a id='geometry_element_py_class_MoosasElement'></a>
**Description:** Base class, which expresses all geometry, loads basic methods & basic members

#### Methods
###### <a id='geometry_element_py_class_MoosasElement_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str] | MoosasGeometry | list[MoosasGeometry] | np.ndarray[MoosasGeometry], level: float, offset: float, glazingId: str | list[str] | np.ndarray[str], glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement], space: Any, uid: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a new instance with model, geometry, and optional
  > Parameters:
  > for shading and glazing.
  > 
  > Parameters
  > model : MoosasContainer
  >     The container model that holds the geometry and other elements.
  > faceId : str or list of str or numpy.ndarray of str or MoosasGeometry or list of MoosasGeometry or numpy.ndarray of MoosasGeometry
  >     Identifier(s) or geometry object(s) representing faces; if string, must exist in model's geoId.
  > level : float, optional
  >     Elevation level of the face(s), by default None.
  > offset : float, optional
  >     Offset distance from the face(s), by default None.
  > glazingId : str or list of str or numpy.ndarray of str, optional
  >     Identifier(s) for glazing elements to be associated, by default None.
  > glazingElement : MoosasElement or list of MoosasElement or numpy.ndarray of MoosasElement, optional
  >     Predefined glazing element(s) to be associated, by default None.
  > space : list of str, optional
  >     List of space identifiers this object belongs to, by default None.
  > uid : str, optional
  >     Unique identifier for the instance; if not provided, a 6-character code is generated.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_glazingElement'></a>`glazingElement`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > protect the __glazingElement attribute
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_glazingId'></a>`glazingId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get glazingId from glazingElement
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_face'></a>`face`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > if the element only contains one face, a pygoes.Geometry will be return
  > if you want to get a list anyway,
  > you can call mixItemListToList() func in utils.tools.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_mergedFace'></a>`mergedFace`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > return a single face merging all faces contained in this element
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_holes'></a>`holes`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a flattened list of hole geometries extracted from each polygon 
in the internal geometries array. Each hole is represented as a pygeos Geometry object.

Returns
pygeos.Geometry or numpy.ndarray of pygeos.Geometry
    A list or array containing the hole geometries from all polygons.
- **Comments:**
  > Function:
  > List of hole geometries from all polygons in the collection.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > a flattened list of hole geometries extracted from each polygon 
  > in the internal geometries array. Each hole is represented as a pygeos Geometry object.
  > 
  > Returns
  > pygeos.Geometry or numpy.ndarray of pygeos.Geometry
  >     A list or array containing the hole geometries from all polygons.

---

###### <a id='geometry_element_py_class_MoosasElement_method_normal'></a>`normal`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > if the element contains multi faces,
  > the normal has the best description of the faces will be returned
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_faceId'></a>`faceId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > if the element only contains one face, a str will be return
  > if you want to get a list anyway,
  > you can call mixItemListToList() func in utils.tools.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_category'></a>`category`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > if the element only contains one face, a int will be return
  > if you want to get a list anyway,
  > you can call mixItemListToList() func in utils.tools.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_area'></a>`area`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > quick link to self.area3d
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_elevation'></a>`elevation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > correct elevation of the object
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_wwr'></a>`wwr`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The Window-to-Wall Ratio (WWR), defined as the ratio of projected glazing area 
    to the total projected wall surface area.
- **Comments:**
  > Function:
  > Calculate the Window-to-Wall Ratio (WWR) based on projected areas.
  > 
  > The WWR is computed as the ratio of glazing area to the total wall surface area,
  > using 3D projections onto wall surfaces. The calculation does not use the exact
  > surface area of window objects, but rather their projection on the wall.
  > Parameters:
  > self : object
  >     The instance of the class containing the method. Expected to have:
  >     - `glazingElement`: iterable of objects with a `face` attribute representing glazing geometry.
  >     - `face`: geometric representation of wall faces, possibly nested.
  >     - `area3d(faces)` method: computes the 3D area of given faces.
  > 
  > Returns
  > float
  >     The Window-to-Wall Ratio (WWR), defined as the ratio of projected glazing area 
  >     to the total projected wall surface area.
  > Returns:
  > float
  >     The Window-to-Wall Ratio (WWR), defined as the ratio of projected glazing area 
  >     to the total projected wall surface area.

---

###### <a id='geometry_element_py_class_MoosasElement_method_firstFaceId'></a>`firstFaceId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the first face ID from the object, which can accelerate calculations 
and prevent errors in contexts where only a single face ID is expected. 
This is particularly useful for objects containing only one face, such as 
MoosasGlazing, MoosasSkylight, or MoosasFace, and ensures compatibility 
with functions like `searchBy` in `utils.tools` that expect a single attribute.

Parameters
self : object
    The instance of the class containing the `faceId` attribute. 
    It is expected to have a `faceId` attribute which is either 
    a scalar value or a numpy ndarray.

Returns
scalar or int or any
    The first face ID. If `faceId` is not a numpy array, returns `self.faceId`. 
    Otherwise, returns the first element of `self.faceId` (i.e., `self.faceId[0]`).
- **Comments:**
  > Function:
  > First face ID from the object.
  > Parameters:
  > self : object
  >     The instance of the class containing the `faceId` attribute. 
  >     It is expected to have a `faceId` attribute which is either 
  >     a scalar value or a numpy ndarray.
  > 
  > Returns
  > scalar or int or any
  >     The first face ID. If `faceId` is not a numpy array, returns `self.faceId`. 
  >     Otherwise, returns the first element of `self.faceId` (i.e., `self.faceId[0]`).
  > Returns:
  > the first face ID from the object, which can accelerate calculations 
  > and prevent errors in contexts where only a single face ID is expected. 
  > This is particularly useful for objects containing only one face, such as 
  > MoosasGlazing, MoosasSkylight, or MoosasFace, and ensures compatibility 
  > with functions like `searchBy` in `utils.tools` that expect a single attribute.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the `faceId` attribute. 
  >     It is expected to have a `faceId` attribute which is either 
  >     a scalar value or a numpy ndarray.
  > 
  > Returns
  > scalar or int or any
  >     The first face ID. If `faceId` is not a numpy array, returns `self.faceId`. 
  >     Otherwise, returns the first element of `self.faceId` (i.e., `self.faceId[0]`).

---

###### <a id='geometry_element_py_class_MoosasElement_method_glazingElementFromId'></a>`glazingElementFromId`
- **Type:** Instance Method
- **Parameters:** self: Any, glazingIds: Any
- **Returns:** list of MoosasGlazing or MoosasSkylight
    A list of glazing objects (either MoosasGlazing or MoosasSkylight instances) matching the provided IDs.
- **Comments:**
  > Function:
  > Get glazing elements by their IDs.
  > Parameters:
  > glazingIds : list or array-like
  >     List of glazing element IDs (Uid) to search for. Can be a mix of types that is converted to a flat list.
  > 
  > Returns
  > list of MoosasGlazing or MoosasSkylight
  >     A list of glazing objects (either MoosasGlazing or MoosasSkylight instances) matching the provided IDs.
  > Returns:
  > list of MoosasGlazing or MoosasSkylight
  >     A list of glazing objects (either MoosasGlazing or MoosasSkylight instances) matching the provided IDs.

---

###### <a id='geometry_element_py_class_MoosasElement_method_replaceGeo'></a>`replaceGeo`
- **Type:** Instance Method
- **Parameters:** self: Any, geoId: Any
- **Returns:** None
    This function does not return any value. It modifies the internal `__geometries` attribute in place.
- **Comments:**
  > Function:
  > Replace the current geometries with new ones based on provided geometry IDs.
  > Parameters:
  > geoId : int or list of int
  >     Geometry ID(s) to be used for replacing the current geometries. 
  >     If a single integer is provided, it will be treated as a list with one element.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the internal `__geometries` attribute in place.
  > Returns:
  > None
  >     This function does not return any value. It modifies the internal `__geometries` attribute in place.

---

###### <a id='geometry_element_py_class_MoosasElement_method_delete'></a>`delete`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Delete all geometries in the object by setting their delete flag to True.
  > Parameters:
  > self : object
  >     The instance of the class containing the geometries to be marked for deletion.
  >     It is expected to have a private attribute `__geometries` which is an iterable
  >     of geometry objects that each support assignment to a `delete` attribute.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasElement_method_area3d'></a>`area3d`
- **Type:** Instance Method
- **Parameters:** self: Any, faces: Any, project: Any
- **Returns:** None
- **Comments:**
  > Function:
  > use projection to get the correct area of the object
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_faceUV'></a>`faceUV`
- **Type:** Instance Method
- **Parameters:** self: Any, uniform: Any
- **Returns:** list of pygeos.Geometry
    A list of 2D geometries representing the UV-projected faces. If `uniform` is True,
    the coordinates are scaled to the unit square; otherwise, they are in raw UV space.
- **Comments:**
  > Function:
  > Get the UV-projected faces of a surface, optionally normalized to a unit square.
  > Parameters:
  > uniform : bool, optional
  >     If True, the UV coordinates are normalized to fit within the unit square [0, 1] 
  >     based on the bounding box of all faces. Default is False.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list of 2D geometries representing the UV-projected faces. If `uniform` is True,
  >     the coordinates are scaled to the unit square; otherwise, they are in raw UV space.
  > Returns:
  > list of pygeos.Geometry
  >     A list of 2D geometries representing the UV-projected faces. If `uniform` is True,
  >     the coordinates are scaled to the unit square; otherwise, they are in raw UV space.

---

###### <a id='geometry_element_py_class_MoosasElement_method_glazingUV'></a>`glazingUV`
- **Type:** Instance Method
- **Parameters:** self: Any, uniform: Any
- **Returns:** list of pygeos.Geometry
    A list of geometries representing the UV-projected glazing faces. If `uniform` is True, 
    the coordinates are normalized; otherwise, they are in raw UV space.
- **Comments:**
  > Function:
  > Get UV-projected glazing faces from the surface.
  > Parameters:
  > self : object
  >     The instance of the class containing glazing elements and geometric data.
  > uniform : bool, optional
  >     If True, normalizes the UV coordinates to the unit square [0, 1] based on the bounding box 
  >     of the input faces. Default is False.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list of geometries representing the UV-projected glazing faces. If `uniform` is True, 
  >     the coordinates are normalized; otherwise, they are in raw UV space.
  > Returns:
  > list of pygeos.Geometry
  >     A list of geometries representing the UV-projected glazing faces. If `uniform` is True, 
  >     the coordinates are normalized; otherwise, they are in raw UV space.

---

###### <a id='geometry_element_py_class_MoosasElement_method_getEdgeStr'></a>`getEdgeStr`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get a unique edge string of the boundary, ignore the direction of the edge.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_getWeightCenter'></a>`getWeightCenter`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** np.ndarray
    A 1D numpy array of shape (3,) containing the x, y, and z coordinates of the centroid, 
    computed as the mean of the face's vertex coordinates.
- **Comments:**
  > Function:
  > Compute the weight center (centroid) of a 3D face.
  > Parameters:
  > self : object
  >     The instance of the class containing the `face` attribute, which is a geometric object 
  >     supported by pygeos representing a 2D or 3D polygonal face.
  > 
  > Returns
  > np.ndarray
  >     A 1D numpy array of shape (3,) containing the x, y, and z coordinates of the centroid, 
  >     computed as the mean of the face's vertex coordinates.
  > Returns:
  > np.ndarray
  >     A 1D numpy array of shape (3,) containing the x, y, and z coordinates of the centroid, 
  >     computed as the mean of the face's vertex coordinates.

---

###### <a id='geometry_element_py_class_MoosasElement_method_add_glazing'></a>`add_glazing`
- **Type:** Instance Method
- **Parameters:** self: Any, glazingObject: MoosasGlazing | MoosasSkylight
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Add a glazing object to the current element.
  > Parameters:
  > glazingObject : MoosasGlazing or MoosasSkylight
  >     The glazing object to be added. This object will be appended to the 
  >     internal list of glazing elements and its parentFace attribute will 
  >     be set to the current instance.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasElement_method_dissolve'></a>`dissolve`
- **Type:** Instance Method
- **Parameters:** self: Any, others: Any
- **Returns:** None
- **Comments:**
  > Function:
  > method to merge multiple elements
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method__merge'></a>`_merge`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** None
    This function modifies the current instance in place by merging geometries, 
    adjusting offset and level, flipping normals if necessary, and adding 
    glazing elements from the other object.
- **Comments:**
  > Function:
  > Merge another object into this one by aligning face normals and combining geometries.
  > Parameters:
  > other : object
  >     Another object to merge with this one. Must have methods `getEdgeStr`, 
  >     `getWeightCenter`, and attributes `__geometries`, `normal`, `offset`, 
  >     `level`, and `glazingElement`. The `getEdgeStr` method should return a 
  >     list of edge strings, and `getWeightCenter` should return the center point.
  > 
  > Returns
  > None
  >     This function modifies the current instance in place by merging geometries, 
  >     adjusting offset and level, flipping normals if necessary, and adding 
  >     glazing elements from the other object.
  > Returns:
  > None
  >     This function modifies the current instance in place by merging geometries, 
  >     adjusting offset and level, flipping normals if necessary, and adding 
  >     glazing elements from the other object.

---

###### <a id='geometry_element_py_class_MoosasElement_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > return a linestring formatted in pygeos,or an array vector object
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_representation'></a>`representation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > return a simplified representation for the geometry
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, elementDict: Any, model: MoosasContainer
- **Returns:** None
- **Comments:**
  > Function:
  > construct an element from a dictionary
  > if the faceId record in the dictionary is already occurred in the model,
  > the MoosasElement contains that faceId will be returned directly.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasElement_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, element_tag: Any, writeGeometry: Any
- **Returns:** xml.etree.ElementTree.Element
    An XML Element representing the MoosasFace object with attributes such as Uid, faceId,
    level, offset, area, glazingId, height, normal, external, space, and neighbor edges.
    Optionally includes geometric point data if writeGeometry is True.
- **Comments:**
  > Function:
  > Convert the MoosasFace object to an XML element representation.
  > Parameters:
  > model : MoosasContainer
  >     The container model associated with the geometry.
  > element_tag : str, optional
  >     The tag name for the root XML element (default is 'geometry').
  > writeGeometry : bool, optional
  >     If True, includes the detailed geometric coordinates in the XML output (default is False).
  > 
  > Returns
  > xml.etree.ElementTree.Element
  >     An XML Element representing the MoosasFace object with attributes such as Uid, faceId,
  >     level, offset, area, glazingId, height, normal, external, space, and neighbor edges.
  >     Optionally includes geometric point data if writeGeometry is True.
  > Returns:
  > xml.etree.ElementTree.Element
  >     An XML Element representing the MoosasFace object with attributes such as Uid, faceId,
  >     level, offset, area, glazingId, height, normal, external, space, and neighbor edges.
  >     Optionally includes geometric point data if writeGeometry is True.

---

### 📦 Class: MoosasFace
<a id='geometry_element_py_class_MoosasFace'></a>
**Description:** The base class, which records the horizontal face

#### Methods
###### <a id='geometry_element_py_class_MoosasFace_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, faceId: str | MoosasGeometry, level: float, offset: float, glazingId: Any, glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement], space: Any, uid: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a MoosasFace object with geometric and structural properties.
  > Parameters:
  > model : MoosasContainer
  >     The container model to which the face belongs.
  > faceId : str or MoosasGeometry
  >     Identifier or geometry object representing the face. Must not be a list or array.
  > level : float, optional
  >     The level (elevation) of the face. If not provided, inferred from geometry.
  > offset : float, optional
  >     Vertical offset of the face relative to its level. Calculated if not provided.
  > glazingId : Any, optional
  >     Identifier for glazing associated with the face. Default is None.
  > glazingElement : MoosasElement or list[MoosasElement] or np.ndarray[MoosasElement], optional
  >     Glazing element(s) attached to the face. Default is None.
  > space : Any, optional
  >     Spatial context or zone to which the face belongs. Default is None.
  > uid : str, optional
  >     Unique identifier for the face. Generated if not provided.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='geometry_element_py_class_MoosasFace_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, elementDict: Any, model: MoosasContainer
- **Returns:** MoosasFace
    An instance of MoosasFace initialized with data from elementDict and associated with the given model.
- **Comments:**
  > Function:
  > Create a MoosasFace instance from a dictionary representation.
  > Parameters:
  > elementDict : dict
  >     Dictionary containing the element data.
  > model : MoosasContainer
  >     Model container that holds the built data and manages elements.
  > 
  > Returns
  > MoosasFace
  >     An instance of MoosasFace initialized with data from elementDict and associated with the given model.
  > Returns:
  > MoosasFace
  >     An instance of MoosasFace initialized with data from elementDict and associated with the given model.

---

###### <a id='geometry_element_py_class_MoosasFace_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any, region: Any
- **Returns:** pygeos.Geometry
    The input geometry converted to 2D.
- **Comments:**
  > Function:
  > Force the geometry into 2 dimensions.
  > Parameters:
  > region : bool, optional
  >     Placeholder argument for consistency; has no effect on the operation.
  > 
  > Returns
  > pygeos.Geometry
  >     The input geometry converted to 2D.
  > Returns:
  > pygeos.Geometry
  >     The input geometry converted to 2D.

---

###### <a id='geometry_element_py_class_MoosasFace_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, Element_tag: Any, writeGeometry: Any
- **Returns:** face_xml : Element
    The XML element representing the face, possibly including geometry based on writeGeometry flag.
- **Comments:**
  > Function:
  > Convert the MoosasFace object to an XML representation.
  > Parameters:
  > model : MoosasContainer
  >     The container model containing the face data to be converted.
  > Element_tag : str, optional
  >     The XML tag name for the element, default is 'face'.
  > writeGeometry : bool, optional
  >     If True, includes geometry information in the XML output; default is False.
  > 
  > Returns
  > face_xml : Element
  >     The XML element representing the face, possibly including geometry based on writeGeometry flag.
  > Returns:
  > face_xml : Element
  >     The XML element representing the face, possibly including geometry based on writeGeometry flag.

---

###### <a id='geometry_element_py_class_MoosasFace_method_dissolve'></a>`dissolve`
- **Type:** Instance Method
- **Parameters:** self: Any, wall: Any
- **Returns:** None
    This function does not return any value but raises an exception when called.
- **Comments:**
  > Function:
  > Dissolves the specified wall from the structure.
  > Parameters:
  > self : object
  >     The instance of the class calling this method.
  > wall : str or int
  >     Identifier for the wall to be dissolved. Can be a name (string) or index (integer).
  > 
  > Returns
  > None
  >     This function does not return any value but raises an exception when called.
  > Returns:
  > None
  >     This function does not return any value but raises an exception when called.

---

###### <a id='geometry_element_py_class_MoosasFace_method_representation'></a>`representation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** pygeos.Geometry
    A 3D geometry created by converting the 2D forced geometry to 3D using the given elevation.
- **Comments:**
  > Function:
  > Return a 3D geometric representation of the object with specified elevation.
  > Parameters:
  > self : object
  >     The instance of the class containing `force_2d` and `elevation` attributes.
  >     Must have methods `force_2d()` and attribute `elevation` defined.
  > 
  > Returns
  > pygeos.Geometry
  >     A 3D geometry created by converting the 2D forced geometry to 3D using the given elevation.
  > Returns:
  > pygeos.Geometry
  >     A 3D geometry created by converting the 2D forced geometry to 3D using the given elevation.

---

### 📦 Class: MoosasSkylight
<a id='geometry_element_py_class_MoosasSkylight'></a>
**Description:** 一个特别简单的glazing类，只为与Moosasface区分开

#### Methods
###### <a id='geometry_element_py_class_MoosasSkylight_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, faceId: str | MoosasGeometry, level: float, offset: float, glazingId: Any, glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement], space: Any, uid: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a MoosasSkylight object.
  > Parameters:
  > model : MoosasContainer
  >     The container model to which the skylight belongs.
  > faceId : str or MoosasGeometry
  >     Identifier or geometry object representing the skylight's face. Must not be a list.
  > level : float, optional
  >     Elevation level of the skylight. Default is None.
  > offset : float, optional
  >     Vertical offset from the base level. Default is None.
  > glazingId : object, optional
  >     Identifier for the glazing material or component. Default is None.
  > glazingElement : MoosasElement or list of MoosasElement or np.ndarray of MoosasElement, optional
  >     Glazing element(s) associated with the skylight. Default is None.
  > space : object, optional
  >     Space to which the skylight belongs. Default is None.
  > uid : str, optional
  >     Unique identifier for the skylight. If not provided, it is generated based on `faceId`.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasSkylight_method_orientation'></a>`orientation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** Vector
    A Vector object created from the `normal` attribute of the instance.
- **Comments:**
  > Function:
  > Return the orientation vector based on the normal.
  > Parameters:
  > self : object
  >     The instance of the class containing the `normal` attribute.
  > 
  > Returns
  > Vector
  >     A Vector object created from the `normal` attribute of the instance.
  > Returns:
  > Vector
  >     A Vector object created from the `normal` attribute of the instance.

---

###### <a id='geometry_element_py_class_MoosasSkylight_method_apply_to_face'></a>`apply_to_face`
- **Type:** Instance Method
- **Parameters:** self: Any, face: MoosasFace
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Apply the glazing to a given face.
  > Parameters:
  > face : MoosasFace
  >     The face object to which the glazing will be added.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasSkylight_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, Element_tag: Any, writeGeometry: Any
- **Returns:** xml_element : xml.etree.ElementTree.Element
    The XML element representing the skylight, with parent face UID and shading ID as sub-elements.
- **Comments:**
  > Function:
  > Convert the MoosasSkylight object to an XML element representation.
  > Parameters:
  > model : MoosasContainer
  >     The container model to which the skylight belongs.
  > Element_tag : str, optional
  >     The tag name for the XML element, default is 'skylight'.
  > writeGeometry : bool, optional
  >     If True, geometry information will be included in the XML output, default is False.
  > 
  > Returns
  > xml_element : xml.etree.ElementTree.Element
  >     The XML element representing the skylight, with parent face UID and shading ID as sub-elements.
  > Returns:
  > xml_element : xml.etree.ElementTree.Element
  >     The XML element representing the skylight, with parent face UID and shading ID as sub-elements.

---

### 📦 Class: MoosasWall
<a id='geometry_element_py_class_MoosasWall'></a>
**Description:** The basic class, which expresses the read vertical face, has the following new members:

#### Methods
###### <a id='geometry_element_py_class_MoosasWall_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float, offset: float, glazingId: Any, glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement], space: Any, uid: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a MoosasWall instance with geometric and spatial properties.
  > Parameters:
  > model : MoosasContainer
  >     The container model that holds the wall and associated level information.
  > faceId : str or list of str or numpy.ndarray of str
  >     Identifier(s) for the face(s) representing the wall geometry.
  > level : float, optional
  >     The base level (elevation) of the wall. If not provided, inferred from geometry and model levels.
  > offset : float, optional
  >     Vertical offset from the base level. If not provided, calculated from geometry.
  > glazingId : object, optional
  >     Identifier for glazing elements associated with the wall. Default is None.
  > glazingElement : MoosasElement or list of MoosasElement or numpy.ndarray of MoosasElement, optional
  >     Glazing element(s) attached to the wall. Default is None.
  > space : object, optional
  >     Spatial context or enclosure to which the wall belongs. Default is None.
  > uid : str, optional
  >     Unique identifier for the wall. If not provided, generated based on faceId.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasWall_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, elementDict: Any, model: MoosasContainer
- **Returns:** MoosasWall
    A new MoosasWall instance initialized from the provided dictionary and model.
- **Comments:**
  > Function:
  > Create a MoosasWall instance from a dictionary representation.
  > Parameters:
  > elementDict : dict
  >     Dictionary containing the element's data.
  > model : MoosasContainer
  >     Model container to which the element belongs.
  > 
  > Returns
  > MoosasWall
  >     A new MoosasWall instance initialized from the provided dictionary and model.
  > Returns:
  > MoosasWall
  >     A new MoosasWall instance initialized from the provided dictionary and model.

---

###### <a id='geometry_element_py_class_MoosasWall_method_fromProjection'></a>`fromProjection`
- **Type:** Class Method
- **Parameters:** cls: Any, prjLine: pygeos.Geometry, bottom: float, top: float, model: MoosasContainer, airBoundary: Any
- **Returns:** wall : cls
    An instance of the class (e.g., Wall) created from the projected geometry and added to the model.
- **Comments:**
  > Function:
  > Create a wall or glazing object from a 2D projection line and elevation bounds.
  > Parameters:
  > prjLine : pygeos.Geometry
  >     A 2D line geometry representing the projection of the wall.
  > bottom : float
  >     The bottom elevation (z-coordinate) of the wall.
  > top : float
  >     The top elevation (z-coordinate) of the wall.
  > model : MoosasContainer
  >     The model container to which the geometry will be added.
  > airBoundary : bool, optional
  >     If True, creates an air boundary with glazing; if False, creates a standard wall. Default is False.
  > 
  > Returns
  > wall : cls
  >     An instance of the class (e.g., Wall) created from the projected geometry and added to the model.
  > Returns:
  > wall : cls
  >     An instance of the class (e.g., Wall) created from the projected geometry and added to the model.

---

###### <a id='geometry_element_py_class_MoosasWall_method_break_'></a>`break_`
- **Type:** Class Method
- **Parameters:** cls: Any, wall: MoosasWall, breakPoints: list[pygeos.Geometry] | pygeos.Geometry
- **Returns:** list
    A list of new wall objects (type determined by `cls`) created by breaking the original wall at the specified points.
    If insufficient break points are provided, returns a list containing the original unbroken wall.
- **Comments:**
  > Function:
  > Break a wall into multiple segments at specified break points.
  > Parameters:
  > cls : type
  >     The class instance (used as part of a classmethod).
  > wall : MoosasWall
  >     The wall object to be broken into segments. Must have 2D geometry and level/top-level attributes.
  > breakPoints : list[pygeos.Geometry] or pygeos.Geometry
  >     A single point or a list of pygeos geometry points where the wall should be broken.
  > 
  > Returns
  > list
  >     A list of new wall objects (type determined by `cls`) created by breaking the original wall at the specified points.
  >     If insufficient break points are provided, returns a list containing the original unbroken wall.
  > Returns:
  > list
  >     A list of new wall objects (type determined by `cls`) created by breaking the original wall at the specified points.
  >     If insufficient break points are provided, returns a list containing the original unbroken wall.

---

###### <a id='geometry_element_py_class_MoosasWall_method_fromSeriesPoint'></a>`fromSeriesPoint`
- **Type:** Class Method
- **Parameters:** cls: Any, breakPoints: list[pygeos.Geometry] | pygeos.Geometry, bottom: float, top: float, gls: list[MoosasGlazing], model: MoosasContainer
- **Returns:** list[MoosasWall]
    A list of newly created wall segments formed by partitioning at the given break points,
    with glazing elements appropriately reassigned based on spatial containment.
- **Comments:**
  > Function:
  > Partition walls based on break points and reassign glazing elements.
  > Parameters:
  > breakPoints : list[pygeos.Geometry] or pygeos.Geometry
  >     A geometry or list of geometries representing the points where walls are to be split.
  > bottom : float
  >     The bottom elevation for the generated wall segments.
  > top : float
  >     The top elevation for the generated wall segments.
  > gls : list[MoosasGlazing]
  >     List of glazing elements to be reassigned to the new wall segments after partitioning.
  > model : MoosasContainer
  >     The model container that holds the glazing list and other contextual data.
  > 
  > Returns
  > list[MoosasWall]
  >     A list of newly created wall segments formed by partitioning at the given break points,
  >     with glazing elements appropriately reassigned based on spatial containment.
  > Returns:
  > list[MoosasWall]
  >     A list of newly created wall segments formed by partitioning at the given break points,
  >     with glazing elements appropriately reassigned based on spatial containment.

---

###### <a id='geometry_element_py_class_MoosasWall_method_height'></a>`height`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float or int
    The calculated height as the difference between the highest top and lowest bottom position.
- **Comments:**
  > Function:
  > Height of the element including glazing elements.
  > 
  > Calculates the total height by finding the difference between the maximum top level 
  > (including top offset and toplevel) and the minimum bottom level (including offset and level) 
  > across the main element and all associated glazing elements.
  > Parameters:
  > self : object
  >     The instance of the class containing the height property. Must have attributes
  >     `toplevel`, `topoffset`, `level`, `offset`, and `glazingElement`. The `glazingElement`
  >     attribute should be an iterable of objects with `toplevel`, `topoffset`, `level`, and `offset` attributes.
  > 
  > Returns
  > float or int
  >     The calculated height as the difference between the highest top and lowest bottom position.
  > Returns:
  > float or int
  >     The calculated height as the difference between the highest top and lowest bottom position.

---

###### <a id='geometry_element_py_class_MoosasWall_method_prepareProjection'></a>`prepareProjection`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return any value. It modifies the instance attributes
    `__botProjection` and `__topProjection` by setting them to lists of projected
    2D points (with Z-coordinate filtered) at specified precision.
- **Comments:**
  > Function:
  > Prepare top and bottom projections of the face geometry.
  > Parameters:
  > self : object
  >     The instance of the class containing the face attribute and methods.
  >     Must have a `face` attribute accessible via `self.face` that represents
  >     a geometry object compatible with pygeos, and a `geom.POINT_PRECISION`
  >     constant for precision control.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the instance attributes
  >     `__botProjection` and `__topProjection` by setting them to lists of projected
  >     2D points (with Z-coordinate filtered) at specified precision.
  > Returns:
  > None
  >     This function does not return any value. It modifies the instance attributes
  >     `__botProjection` and `__topProjection` by setting them to lists of projected
  >     2D points (with Z-coordinate filtered) at specified precision.

---

###### <a id='geometry_element_py_class_MoosasWall_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any, top: Any, region: Any
- **Returns:** pygeos.Geometry or None
    A 2D geometric object representing the projected line, point, or polygon;
    returns None if the projection cannot be computed.
- **Comments:**
  > Function:
  > Project the 3D geometry into a 2D representation based on top or bottom projections.
  > Parameters:
  > top : bool
  >     If True, use the top projection of the geometry; otherwise, use the bottom projection.
  > region : bool
  >     If True, combine top and bottom projections to form a 2D region (e.g., polygon or closed line);
  >     if False, return the 2D representation of the specified projection (top or bottom).
  > 
  > Returns
  > pygeos.Geometry or None
  >     A 2D geometric object representing the projected line, point, or polygon;
  >     returns None if the projection cannot be computed.
  > Returns:
  > pygeos.Geometry or None
  >     A 2D geometric object representing the projected line, point, or polygon;
  >     returns None if the projection cannot be computed.

---

###### <a id='geometry_element_py_class_MoosasWall_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, Element_tag: Any, writeGeometry: Any
- **Returns:** xml.etree.ElementTree.Element
    The XML element representing the wall, with attributes such as length, 
    force2d coordinates, toplevel, and topoffset converted to inches.
- **Comments:**
  > Function:
  > Convert the MoosasWall object to an XML element representation.
  > Parameters:
  > model : MoosasContainer
  >     The container model to which the XML element will be added.
  > Element_tag : str, optional
  >     The tag name for the XML element (default is 'wall').
  > writeGeometry : bool, optional
  >     If True, geometry information is included in the XML (default is False).
  > 
  > Returns
  > xml.etree.ElementTree.Element
  >     The XML element representing the wall, with attributes such as length, 
  >     force2d coordinates, toplevel, and topoffset converted to inches.
  > Returns:
  > xml.etree.ElementTree.Element
  >     The XML element representing the wall, with attributes such as length, 
  >     force2d coordinates, toplevel, and topoffset converted to inches.

---

###### <a id='geometry_element_py_class_MoosasWall_method_dissolve'></a>`dissolve`
- **Type:** Instance Method
- **Parameters:** self: Any, wall: MoosasWall | list[MoosasWall]
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Merge the current MoosasWall with one or more other MoosasWall objects into a single entity.
  > Parameters:
  > wall : MoosasWall or list of MoosasWall
  >     The wall or walls to be merged with the current instance. If a single MoosasWall is provided,
  >     it is converted into a list for uniform processing.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasWall_method_representation'></a>`representation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** pygeos.Geometry
    A 3D pygeos polygon representing the vertical extrusion of the glazing element,
    constructed from bottom and top boundary coordinates.
- **Comments:**
  > Function:
  > Return a 3D polygon representation of the glazing element.
  > Parameters:
  > self : MoosasGlazing
  >     The instance of MoosasGlazing containing geometric and level data for generating the 3D polygon.
  >     Must have methods `force_2d`, `level`, `offset`, `toplevel`, and `topoffset`.
  > 
  > Returns
  > pygeos.Geometry
  >     A 3D pygeos polygon representing the vertical extrusion of the glazing element,
  >     constructed from bottom and top boundary coordinates.
  > Returns:
  > pygeos.Geometry
  >     A 3D pygeos polygon representing the vertical extrusion of the glazing element,
  >     constructed from bottom and top boundary coordinates.

---

### 📦 Class: MoosasGlazing
<a id='geometry_element_py_class_MoosasGlazing'></a>
**Description:** glazing element based on MoosasWall.

#### Methods
###### <a id='geometry_element_py_class_MoosasGlazing_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, faceId: str | list[str] | np.ndarray[str], level: float, offset: float, glazingId: Any, glazingElement: MoosasElement | list[MoosasElement] | np.ndarray[MoosasElement], space: Any, uid: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a MoosasGlazing object with geometric and structural properties.
  > Parameters:
  > model : MoosasContainer
  >     The container model to which the glazing belongs.
  > faceId : str or list of str or numpy.ndarray of str
  >     Identifier(s) for the associated face(s). If a MoosasGeometry object is passed,
  >     its faceId is used.
  > level : float, optional
  >     Elevation level of the bottom of the glazing. If not provided, defaults to None.
  > offset : float, optional
  >     Vertical offset from the base level. If not provided, defaults to None.
  > glazingId : any, optional
  >     User-defined identifier for the glazing element. Defaults to None.
  > glazingElement : MoosasElement or list of MoosasElement or numpy.ndarray of MoosasElement, optional
  >     The glazing element(s) defining the geometry and properties. Defaults to None.
  > space : any, optional
  >     Associated space for the glazing. Defaults to None.
  > uid : str, optional
  >     Unique identifier for the glazing. If not provided, it is generated based on faceId.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='geometry_element_py_class_MoosasGlazing_method_fromProjection'></a>`fromProjection`
- **Type:** Class Method
- **Parameters:** cls: Any, prjLine: pygeos.Geometry, bottom: float, top: float, model: MoosasContainer, airBoundary: Any
- **Returns:** gls : cls or None
    An instance of the class created from the projection, or None if the input line is too short.
- **Comments:**
  > Function:
  > Create an instance from a projection line with defined bottom and top elevations.
  > Parameters:
  > prjLine : pygeos.Geometry
  >     A linestring geometry representing the projection; must have sufficient length.
  > bottom : float
  >     The bottom elevation (z-coordinate) of the generated geometry.
  > top : float
  >     The top elevation (z-coordinate) of the generated geometry.
  > model : MoosasContainer
  >     The model container used to include the generated geometry.
  > airBoundary : bool, optional
  >     If True, includes an air boundary; defaults to False.
  > 
  > Returns
  > gls : cls or None
  >     An instance of the class created from the projection, or None if the input line is too short.
  > Returns:
  > gls : cls or None
  >     An instance of the class created from the projection, or None if the input line is too short.

---

###### <a id='geometry_element_py_class_MoosasGlazing_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any, top: Any, region: Any
- **Returns:** object
    A 2D representation of the geometry, type depends on implementation in parent class.
- **Comments:**
  > Function:
  > Force the geometry into a 2D representation.
  > Parameters:
  > top : bool, optional
  >     If True, project to the top view. Default is False.
  > region : bool, optional
  >     If True, return as a 2D region. Default is False.
  > 
  > Returns
  > object
  >     A 2D representation of the geometry, type depends on implementation in parent class.
  > Returns:
  > object
  >     A 2D representation of the geometry, type depends on implementation in parent class.

---

###### <a id='geometry_element_py_class_MoosasGlazing_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: Any, Element_tag: Any, writeGeometry: Any
- **Returns:** xml_element : xml.etree.ElementTree.Element
    The XML element representing the glazing, with additional subelements for 'parentFace' and 'shadingid'.
- **Comments:**
  > Function:
  > Convert the MoosasGlazing object to an XML representation.
  > Parameters:
  > model : object
  >     The model context in which the XML is generated; passed to the parent class method.
  > Element_tag : str, optional
  >     The tag name for the XML element representing the glazing. Default is 'glazing'.
  > writeGeometry : bool, optional
  >     If True, geometry information will be included in the XML output. Default is False.
  > 
  > Returns
  > xml_element : xml.etree.ElementTree.Element
  >     The XML element representing the glazing, with additional subelements for 'parentFace' and 'shadingid'.
  > Returns:
  > xml_element : xml.etree.ElementTree.Element
  >     The XML element representing the glazing, with additional subelements for 'parentFace' and 'shadingid'.

---

### 📦 Class: MoosasFloor
<a id='geometry_element_py_class_MoosasFloor'></a>
**Description:** this class define a floor contains multi horizontal/incline face elements.

#### Methods
###### <a id='geometry_element_py_class_MoosasFloor_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, faces: list[MoosasFace]
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a new instance with a list of MoosasFace objects.
  > Parameters:
  > faces : list of MoosasFace
  >     A list of MoosasFace instances to be associated with this object. 
  >     The input may be a nested list, which will be flattened using mixItemListToList.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, floorDict: Any, model: MoosasContainer
- **Returns:** cls
    A new instance of the class initialized with MoosasFace objects created from the input dictionary.
- **Comments:**
  > Function:
  > Create a new instance from a dictionary representation of a floor.
  > Parameters:
  > floorDict : dict
  >     Dictionary containing floor data, must include 'face' key with list of face data.
  > model : MoosasContainer
  >     Model container used for creating MoosasFace instances.
  > 
  > Returns
  > cls
  >     A new instance of the class initialized with MoosasFace objects created from the input dictionary.
  > Returns:
  > cls
  >     A new instance of the class initialized with MoosasFace objects created from the input dictionary.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_area'></a>`area`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The sum of the areas of all faces in the object.
- **Comments:**
  > Function:
  > Compute the total area of all faces in the object.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > float
  >     The sum of the areas of all faces in the object.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_level'></a>`level`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The level value of the first face in the face list.
- **Comments:**
  > Function:
  > Level of the face.
  > Parameters:
  > self : object
  >     The instance of the class containing the face attribute.
  > 
  > Returns
  > float
  >     The level value of the first face in the face list.
  > Returns:
  > float
  >     The level value of the first face in the face list.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_offset'></a>`offset`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The mean value of the `offset` attribute from all faces, converted to a Python float.
- **Comments:**
  > Function:
  > Mean offset value across all faces in the object.
  > Parameters:
  > self : object
  >     The instance of the class containing the `face` attribute, which is expected to be 
  >     a collection of objects each having an `offset` property.
  > 
  > Returns
  > float
  >     The mean value of the `offset` attribute from all faces, converted to a Python float.
  > Returns:
  > float
  >     The mean value of the `offset` attribute from all faces, converted to a Python float.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_glazingId'></a>`glazingId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a concatenated list of glazing IDs by iterating over each face in the object's `face` attribute and collecting their `glazingId` values.

Parameters
self : object
    The instance of the class containing the `face` attribute, which is expected to be an iterable of objects each having a `glazingId` property.

Returns
list of str
    A list of glazing IDs extracted from each face.
- **Comments:**
  > Function:
  > Get the list of glazing IDs from all faces.
  > Parameters:
  > self : object
  >     The instance of the class containing the `face` attribute, which is expected to be an iterable of objects each having a `glazingId` property.
  > 
  > Returns
  > list of str
  >     A list of glazing IDs extracted from each face.
  > Returns:
  > a concatenated list of glazing IDs by iterating over each face in the object's `face` attribute and collecting their `glazingId` values.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the `face` attribute, which is expected to be an iterable of objects each having a `glazingId` property.
  > 
  > Returns
  > list of str
  >     A list of glazing IDs extracted from each face.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_glazingElement'></a>`glazingElement`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** list of MoosasSkylight
    A list containing all glazing elements extracted from each face in `self.face`.
- **Comments:**
  > Function:
  > Get all glazing elements from the faces.
  > Parameters:
  > self : object
  >     The instance of the class containing the `face` attribute, which is expected to be an iterable 
  >     of objects each having a `glazingElement` property.
  > 
  > Returns
  > list of MoosasSkylight
  >     A list containing all glazing elements extracted from each face in `self.face`.
  > Returns:
  > list of MoosasSkylight
  >     A list containing all glazing elements extracted from each face in `self.face`.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_getWeightCenter'></a>`getWeightCenter`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** np.ndarray
    A 1D numpy array representing the mean coordinates (center) across all face centers.
- **Comments:**
  > Function:
  > Compute the weighted center of all faces in the object.
  > Parameters:
  > self : object
  >     The instance of the class containing a list of face objects, each with a `getWeightCenter` method.
  > 
  > Returns
  > np.ndarray
  >     A 1D numpy array representing the mean coordinates (center) across all face centers.
  > Returns:
  > np.ndarray
  >     A 1D numpy array representing the mean coordinates (center) across all face centers.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a 2D geometry.

Returns
pygeos.Geometry
    A single 2D geometry representing the union of all faces. If the union fails,
    a multipolygon composed of the individual 2D faces is returned instead.
- **Comments:**
  > Function:
  > Force the geometry into a 2D representation and return the union of all faces.
  > Parameters:
  > self : object
  >     The object containing a `face` attribute, which is a collection of geometric faces.
  >     Each face must have a `force_2d` method that returns a 2D geometry.
  > 
  > Returns
  > pygeos.Geometry
  >     A single 2D geometry representing the union of all faces. If the union fails,
  >     a multipolygon composed of the individual 2D faces is returned instead.
  > Returns:
  > a 2D geometry.
  > 
  > Returns
  > pygeos.Geometry
  >     A single 2D geometry representing the union of all faces. If the union fails,
  >     a multipolygon composed of the individual 2D faces is returned instead.

---

###### <a id='geometry_element_py_class_MoosasFloor_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, Element_tag: Any, writeGeometry: Any
- **Returns:** ET.Element
    An XML element with the specified tag containing face UIDs as text subelements.
- **Comments:**
  > Function:
  > Construct an XML element representing the floor with face UIDs as subelements.
  > Parameters:
  > model : MoosasContainer
  >     The container model containing the data to be represented in XML.
  > Element_tag : str, optional
  >     The tag name for the root XML element (default is 'floor').
  > writeGeometry : bool, optional
  >     If True, includes geometric data in the XML output (default is False).
  > 
  > Returns
  > ET.Element
  >     An XML element with the specified tag containing face UIDs as text subelements.
  > Returns:
  > ET.Element
  >     An XML element with the specified tag containing face UIDs as text subelements.

---

### 📦 Class: MoosasEdge
<a id='geometry_element_py_class_MoosasEdge'></a>
**Description:** This class specifies a closed envelope

#### Methods
###### <a id='geometry_element_py_class_MoosasEdge_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, walls: list[MoosasWall]
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a boundary object composed of walls.
  > Parameters:
  > walls : list of MoosasWall
  >     List of MoosasWall objects that form the boundary. Must contain at least 3 walls.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasEdge_method_prepareBoundary'></a>`prepareBoundary`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return any value. It modifies the instance's
    `__botBound` and `__topBound` attributes in place and updates the orientation
    of walls and their glazing elements.
- **Comments:**
  > Function:
  > Prepare boundary polygons for walls and glazings.
  > 
  > This method processes wall elements to generate bottom and top boundary polygons
  > using 2D force representations, and assigns orientation factors to walls and their glazing elements.
  > If top boundary generation fails, it defaults to the bottom boundary.
  > Parameters:
  > self : object
  >     The instance of the class containing the method. Expected attributes include:
  >     - wall (list): List of wall objects, each having `force_2d`, `glazingElement`, and `orientation` attributes.
  >     - FactorOfWall (list): List of orientation factors corresponding to each wall.
  >     - __botBound (list): Internal list to store bottom boundary points.
  >     - __topBound (list): Internal list to store top boundary points.
  >     - get_polygon (callable): Method to convert a list of points into a polygon.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the instance's
  >     `__botBound` and `__topBound` attributes in place and updates the orientation
  >     of walls and their glazing elements.
  > Returns:
  > None
  >     This function does not return any value. It modifies the instance's
  >     `__botBound` and `__topBound` attributes in place and updates the orientation
  >     of walls and their glazing elements.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, floorDict: Any, model: Any
- **Returns:** cls
    A new instance of the class, initialized with a list of MoosasWall objects created from the input dictionary.
- **Comments:**
  > Function:
  > Create a class instance from a dictionary representation of a floor.
  > Parameters:
  > floorDict : dict
  >     Dictionary containing floor data, expected to include a 'face' key.
  > model : object
  >     Model object passed to the creation of individual MoosasWall instances.
  > 
  > Returns
  > cls
  >     A new instance of the class, initialized with a list of MoosasWall objects created from the input dictionary.
  > Returns:
  > cls
  >     A new instance of the class, initialized with a list of MoosasWall objects created from the input dictionary.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_difference'></a>`difference`
- **Type:** Class Method
- **Parameters:** cls: Any, mainEdge: MoosasEdge, subBoundary: pygeos.Geometry
- **Returns:** pygeos.Geometry
    The resulting geometry after subtracting subBoundary from mainEdge.
- **Comments:**
  > Function:
  > Compute the geometric difference between a main edge and a sub-boundary.
  > Parameters:
  > mainEdge : MoosasEdge
  >     The primary edge geometry to be processed. Must be valid.
  > subBoundary : pygeos.Geometry
  >     The sub-boundary geometry to subtract from the main edge. Must fully overlap with the 2D projection of mainEdge.
  > 
  > Returns
  > pygeos.Geometry
  >     The resulting geometry after subtracting subBoundary from mainEdge.
  > Returns:
  > pygeos.Geometry
  >     The resulting geometry after subtracting subBoundary from mainEdge.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_selectWall'></a>`selectWall`
- **Type:** Class Method
- **Parameters:** cls: Any, boundary: pygeos.Geometry, walls: list[MoosasWall]
- **Returns:** cls
    An instance of the class (typically a collection of walls) constructed from the valid walls 
    that match the boundary edges or newly created walls where no match was found.
- **Comments:**
  > Function:
  > Select walls that match the edges of a given boundary or create new ones if no match is found.
  > Parameters:
  > boundary : pygeos.Geometry
  >     A geometry object representing the boundary whose edges are used to select or create walls.
  > walls : list of MoosasWall
  >     A list of wall objects to be matched against the boundary edges. Must not be empty.
  > 
  > Returns
  > cls
  >     An instance of the class (typically a collection of walls) constructed from the valid walls 
  >     that match the boundary edges or newly created walls where no match was found.
  > Returns:
  > cls
  >     An instance of the class (typically a collection of walls) constructed from the valid walls 
  >     that match the boundary edges or newly created walls where no match was found.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_parent'></a>`parent`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** object
    The parent object of the first element in the wall list.
- **Comments:**
  > Function:
  > The parent object of the wall associated with this instance.
  > Parameters:
  > None
  > 
  > Returns
  > object
  >     The parent object of the first element in the wall list.
  > Returns:
  > object
  >     The parent object of the first element in the wall list.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_level'></a>`level`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the minimum level value computed across all wall objects 
contained in the instance's `wall` attribute.

Parameters
self : object
    The instance of the class containing the `wall` attribute, which 
    is expected to be an iterable of objects each having a `level` 
    attribute.

Returns
float
    The minimum level value from the `level` attributes of all walls.
- **Comments:**
  > Function:
  > Minimum level value among all walls.
  > Parameters:
  > self : object
  >     The instance of the class containing the `wall` attribute, which 
  >     is expected to be an iterable of objects each having a `level` 
  >     attribute.
  > 
  > Returns
  > float
  >     The minimum level value from the `level` attributes of all walls.
  > Returns:
  > the minimum level value computed across all wall objects 
  > contained in the instance's `wall` attribute.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the `wall` attribute, which 
  >     is expected to be an iterable of objects each having a `level` 
  >     attribute.
  > 
  > Returns
  > float
  >     The minimum level value from the `level` attributes of all walls.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_toplevel'></a>`toplevel`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The maximum value of the `toplevel` property across all walls in `self.wall`.
- **Comments:**
  > Function:
  > Maximum top level among all walls.
  > Parameters:
  > self : object
  >     The instance of the class containing the `wall` attribute, which is a collection 
  >     of wall objects each having a `toplevel` property.
  > 
  > Returns
  > float
  >     The maximum value of the `toplevel` property across all walls in `self.wall`.
  > Returns:
  > float
  >     The maximum value of the `toplevel` property across all walls in `self.wall`.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_elevation'></a>`elevation`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the average elevation value computed from the `elevation` 
attribute of each wall in the `self.wall` collection.

Parameters
self : object
    The instance of the class containing the `wall` attribute, which is 
    expected to be a collection of objects each having an `elevation` property.

Returns
float
    The mean elevation of all walls in the collection.
- **Comments:**
  > Function:
  > Mean elevation of all walls.
  > Parameters:
  > self : object
  >     The instance of the class containing the `wall` attribute, which is 
  >     expected to be a collection of objects each having an `elevation` property.
  > 
  > Returns
  > float
  >     The mean elevation of all walls in the collection.
  > Returns:
  > the average elevation value computed from the `elevation` 
  > attribute of each wall in the `self.wall` collection.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing the `wall` attribute, which is 
  >     expected to be a collection of objects each having an `elevation` property.
  > 
  > Returns
  > float
  >     The mean elevation of all walls in the collection.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_FactorOfWall'></a>`FactorOfWall`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** np.ndarray[Vector]
    An array of Vector objects representing the cross product of the orientation 
    factor (determined by clockwise or counter-clockwise polygon winding) and 
    each edge vector of the polygon boundary.
- **Comments:**
  > Function:
  > Compute the normal factor vectors for wall edges based on polygon orientation.
  > Parameters:
  > self : object
  >     The instance of the class containing the boundary and orientation methods.
  >     Must have a `__botBound` attribute accessible via `self.__botBound` and an `is_ccw()` method.
  > 
  > Returns
  > np.ndarray[Vector]
  >     An array of Vector objects representing the cross product of the orientation 
  >     factor (determined by clockwise or counter-clockwise polygon winding) and 
  >     each edge vector of the polygon boundary.
  > Returns:
  > np.ndarray[Vector]
  >     An array of Vector objects representing the cross product of the orientation 
  >     factor (determined by clockwise or counter-clockwise polygon winding) and 
  >     each edge vector of the polygon boundary.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_area'></a>`area`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the area of the 2D projection of the geometry.

Parameters
self : object
    The geometry object on which the property is accessed. Must have `force_2d` method.

Returns
float
    The area of the geometry in 2D.
- **Comments:**
  > Function:
  > Area of the geometry.
  > Parameters:
  > self : object
  >     The geometry object on which the property is accessed. Must have `force_2d` method.
  > 
  > Returns
  > float
  >     The area of the geometry in 2D.
  > Returns:
  > the area of the 2D projection of the geometry.
  > 
  > Parameters
  > self : object
  >     The geometry object on which the property is accessed. Must have `force_2d` method.
  > 
  > Returns
  > float
  >     The area of the geometry in 2D.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_getWeightCenter'></a>`getWeightCenter`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** np.ndarray
    A 1D NumPy array containing the mean (center) coordinates along axis 0 
    of the 2D force coordinates extracted from all walls.
- **Comments:**
  > Function:
  > Compute the weight center of wall force coordinates.
  > Parameters:
  > self : object
  >     The instance of the class containing the `wall` attribute, which is a collection 
  >     of wall objects that have a `force_2d` method returning 2D coordinate data.
  > 
  > Returns
  > np.ndarray
  >     A 1D NumPy array containing the mean (center) coordinates along axis 0 
  >     of the 2D force coordinates extracted from all walls.
  > Returns:
  > np.ndarray
  >     A 1D NumPy array containing the mean (center) coordinates along axis 0 
  >     of the 2D force coordinates extracted from all walls.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_is_ccw'></a>`is_ccw`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** bool
    True if the polygon is oriented counter-clockwise, False otherwise.
- **Comments:**
  > Function:
  > Determine if the polygon boundary is oriented counter-clockwise (CCW).
  > Parameters:
  > self : object
  >     The instance of the class containing the polygon boundary.
  >     It must have a private attribute `__botBound` that represents
  >     the boundary geometry compatible with pygeos.
  > 
  > Returns
  > bool
  >     True if the polygon is oriented counter-clockwise, False otherwise.
  > Returns:
  > bool
  >     True if the polygon is oriented counter-clockwise, False otherwise.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_get_polygon'></a>`get_polygon`
- **Type:** Instance Method
- **Parameters:** self: Any, target: Any
- **Returns:** pygeos.Geometry
    A PyGEOS geometry object representing the requested polygon.
- **Comments:**
  > Function:
  > Get the polygon geometry for a given target.
  > Parameters:
  > target : str or int
  >     The identifier or name of the target polygon to retrieve.
  > 
  > Returns
  > pygeos.Geometry
  >     A PyGEOS geometry object representing the requested polygon.
  > Returns:
  > pygeos.Geometry
  >     A PyGEOS geometry object representing the requested polygon.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any, top: Any
- **Returns:** the top boundary; otherwise, returns the bottom boundary.

Returns
pygeos.Geometry
    The 2D geometry representing either the top or bottom boundary.
- **Comments:**
  > Function:
  > Force the geometry into a 2D representation.
  > Parameters:
  > top : bool
  >     If True, returns the top boundary; otherwise, returns the bottom boundary.
  > 
  > Returns
  > pygeos.Geometry
  >     The 2D geometry representing either the top or bottom boundary.
  > Returns:
  > the top boundary; otherwise, returns the bottom boundary.
  > 
  > Returns
  > pygeos.Geometry
  >     The 2D geometry representing either the top or bottom boundary.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_is_valid'></a>`is_valid`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** bool
    True if the geometry meets minimum area and dimension requirements and has no self-intersections; 
    False otherwise.
- **Comments:**
  > Function:
  > Check if the geometry is valid based on area, dimensions, and self-intersection.
  > Parameters:
  > self : object
  >     The instance of the class containing geometric data. Must have attributes `area`, `level`, 
  >     and method `force_2d()`. The `force_2d()` method should return a geometry object compatible with pygeos.
  > 
  > Returns
  > bool
  >     True if the geometry meets minimum area and dimension requirements and has no self-intersections; 
  >     False otherwise.
  > Returns:
  > bool
  >     True if the geometry meets minimum area and dimension requirements and has no self-intersections; 
  >     False otherwise.

---

###### <a id='geometry_element_py_class_MoosasEdge_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, Element_tag: Any, writeGeometry: Any
- **Returns:** xml.etree.ElementTree.Element
    An XML element representing the edge and its walls with associated properties.
- **Comments:**
  > Function:
  > Convert the MoosasSpace object's edge and wall data into an XML element representation.
  > Parameters:
  > model : MoosasContainer
  >     The container model providing context for the XML conversion.
  > Element_tag : str, optional
  >     The tag name for the root XML element (default is 'edge').
  > writeGeometry : bool, optional
  >     If True, includes geometric data in the XML output (default is False).
  > 
  > Returns
  > xml.etree.ElementTree.Element
  >     An XML element representing the edge and its walls with associated properties.
  > Returns:
  > xml.etree.ElementTree.Element
  >     An XML element representing the edge and its walls with associated properties.

---

### 📦 Class: MoosasSpace
<a id='geometry_element_py_class_MoosasSpace'></a>
**Description:** define a space with topology and related data.

#### Methods
###### <a id='geometry_element_py_class_MoosasSpace_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, _floor: MoosasFloor | None, _edge: MoosasEdge, _ceiling: MoosasFloor | None, void: list[MoosasSpace]
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a new instance with floor, edge, ceiling, and optional void spaces.
  > Parameters:
  > _floor : MoosasFloor or None
  >     The floor object associated with the space, or None if not present.
  > _edge : MoosasEdge
  >     The edge object defining the boundary and internal mass of the space.
  > _ceiling : MoosasFloor or None
  >     The ceiling object associated with the space, or None if not present.
  > void : list of MoosasSpace, optional
  >     A list of void spaces within the zone. Defaults to an empty list if None.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasSpace_method_fromDict'></a>`fromDict`
- **Type:** Class Method
- **Parameters:** cls: Any, spaceDict: Any, model: MoosasContainer
- **Returns:** Space
    A new Space instance constructed from the provided dictionary and model.
- **Comments:**
  > Function:
  > Construct a Space object from a dictionary representation.
  > Parameters:
  > spaceDict : dict
  >     Dictionary containing space elements such as 'edge', 'ceiling', 'floor', 
  >     'internalMass', and 'void'.
  > model : MoosasContainer
  >     Model container providing context for constructing associated objects.
  > 
  > Returns
  > Space
  >     A new Space instance constructed from the provided dictionary and model.
  > Returns:
  > Space
  >     A new Space instance constructed from the provided dictionary and model.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_neighbor'></a>`neighbor`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** dict
    A dictionary representing the neighbors.
- **Comments:**
  > Function:
  > Dictionary of neighbors associated with the object.
  > Parameters:
  > self : object
  >     The instance of the class containing the neighbor property.
  > 
  > Returns
  > dict
  >     A dictionary representing the neighbors.
  > Returns:
  > dict
  >     A dictionary representing the neighbors.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_void'></a>`void`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** list[MoosasSpace]
    A list of MoosasSpace objects stored in the private __void attribute.
- **Comments:**
  > Function:
  > List of MoosasSpace objects representing the void.
  > Parameters:
  > self : object
  >     The instance of the class containing the void property.
  > 
  > Returns
  > list[MoosasSpace]
  >     A list of MoosasSpace objects stored in the private __void attribute.
  > Returns:
  > list[MoosasSpace]
  >     A list of MoosasSpace objects stored in the private __void attribute.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_parent'></a>`parent`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the parent node associated with the edge of this instance.

Returns
object
    The parent node of the edge.
- **Comments:**
  > Function:
  > Parent property of the edge.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > the parent node associated with the edge of this instance.
  > 
  > Returns
  > object
  >     The parent node of the edge.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_id'></a>`id`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    The private attribute `__id` representing the object's ID.
- **Comments:**
  > Function:
  > Return the ID of the object as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > str
  >     The private attribute `__id` representing the object's ID.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_area'></a>`area`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The effective area, calculated as the area of the edge minus the sum of the areas of all voids.
- **Comments:**
  > Function:
  > Compute the effective area of the object, accounting for any voids.
  > Parameters:
  > self : object
  >     The instance of the class containing the `edge` and `void` attributes.
  >     It is expected to have an `edge` attribute with an `area` property,
  >     and a `void` attribute which is a collection of objects each having an `area` property.
  > 
  > Returns
  > float
  >     The effective area, calculated as the area of the edge minus the sum of the areas of all voids.
  > Returns:
  > float
  >     The effective area, calculated as the area of the edge minus the sum of the areas of all voids.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_level'></a>`level`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The level value from the associated edge.
- **Comments:**
  > Function:
  > Level of the edge.
  > Parameters:
  > self : object
  >     The instance of the class containing the `edge` attribute.
  > 
  > Returns
  > float
  >     The level value from the associated edge.
  > Returns:
  > float
  >     The level value from the associated edge.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_topLevel'></a>`topLevel`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the top-level elevation based on the object's state: if the object is void,
returns the toplevel from the edge; otherwise, returns the ceiling level.

Parameters
self : object
    The instance of the class containing this property. Assumes the presence
    of `is_void()`, `edge.toplevel`, and `ceiling.level` attributes/methods.

Returns
float
    The top-level elevation value, either from `edge.toplevel` (if void) or `ceiling.level`.
- **Comments:**
  > Function:
  > Top-level elevation of the structure, depending on whether it is void or not.
  > Parameters:
  > self : object
  >     The instance of the class containing this property. Assumes the presence
  >     of `is_void()`, `edge.toplevel`, and `ceiling.level` attributes/methods.
  > 
  > Returns
  > float
  >     The top-level elevation value, either from `edge.toplevel` (if void) or `ceiling.level`.
  > Returns:
  > the top-level elevation based on the object's state: if the object is void,
  > returns the toplevel from the edge; otherwise, returns the ceiling level.
  > 
  > Parameters
  > self : object
  >     The instance of the class containing this property. Assumes the presence
  >     of `is_void()`, `edge.toplevel`, and `ceiling.level` attributes/methods.
  > 
  > Returns
  > float
  >     The top-level elevation value, either from `edge.toplevel` (if void) or `ceiling.level`.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_height'></a>`height`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** float
    The computed height. If the instance is void (determined by `is_void()`), returns
    the difference between `toplevel` and `level` of the edge. Otherwise, returns the
    difference between the adjusted ceiling level and the adjusted floor level.
- **Comments:**
  > Function:
  > Height of the object calculated based on edge, ceiling, and floor levels and offsets.
  > Parameters:
  > self : object
  >     The instance of the class containing the height property. It is expected to have
  >     methods `is_void()` and attributes `edge`, `ceiling`, and `floor`. The `edge`
  >     attribute should have `toplevel` and `level` properties. The `ceiling` and `floor`
  >     attributes should each have `level` and `offset` properties.
  > 
  > Returns
  > float
  >     The computed height. If the instance is void (determined by `is_void()`), returns
  >     the difference between `toplevel` and `level` of the edge. Otherwise, returns the
  >     difference between the adjusted ceiling level and the adjusted floor level.
  > Returns:
  > float
  >     The computed height. If the instance is void (determined by `is_void()`), returns
  >     the difference between `toplevel` and `level` of the edge. Otherwise, returns the
  >     difference between the adjusted ceiling level and the adjusted floor level.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_spaceType'></a>`spaceType`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a 2D geometric representation,
    and that `pygeos` and `bBox` utilities are available for area and bounding box computations.

Returns
str
    The classified space type, one of 'Corridor', 'MainSpace', or 'privateSpace',
    based on area, aspect ratio, and dimensional thresholds of decomposed convex faces.
- **Comments:**
  > Function:
  > Determine the type of space based on geometric properties of 2D faces.
  > Parameters:
  > self : object
  >     The instance of the class containing the `force_2d` method and geometric data.
  >     It is assumed that `self` has a method `force_2d()` which returns a 2D geometric representation,
  >     and that `pygeos` and `bBox` utilities are available for area and bounding box computations.
  > 
  > Returns
  > str
  >     The classified space type, one of 'Corridor', 'MainSpace', or 'privateSpace',
  >     based on area, aspect ratio, and dimensional thresholds of decomposed convex faces.
  > Returns:
  > a 2D geometric representation,
  >     and that `pygeos` and `bBox` utilities are available for area and bounding box computations.
  > 
  > Returns
  > str
  >     The classified space type, one of 'Corridor', 'MainSpace', or 'privateSpace',
  >     based on area, aspect ratio, and dimensional thresholds of decomposed convex faces.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_regenerateId'></a>`regenerateId`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** :
    str: self.id
- **Comments:**
  > Function:
  > calculate the id for the space
  > the id comes from 7 params,each params space two indent('0'to'9' & 'a'to'j')
  > so the id will be encoded like this:
  >     0x 1a 2b 3c 4d 5e 6f 7g
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     str: self.id

---

###### <a id='geometry_element_py_class_MoosasSpace_method_add_void'></a>`add_void`
- **Type:** Instance Method
- **Parameters:** self: Any, void: MoosasSpace
- **Returns:** None
- **Comments:**
  > Function:
  > Add a void space to the collection of voids and update space attributes in all faces.
  > Parameters:
  > void : MoosasSpace
  >     The void space object to be added to the internal void list.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasSpace_method_force_2d'></a>`force_2d`
- **Type:** Instance Method
- **Parameters:** self: Any, top: Any
- **Returns:** pygeos.Geometry
    A 2D polygon geometry. If the object has voids, a polygon with holes is constructed;
    otherwise, the 2D version of the edge is returned directly.
- **Comments:**
  > Function:
  > Project the geometry to 2D and return a 2D polygon.
  > Parameters:
  > top : bool, optional
  >     If True, project to the top plane; otherwise, use default 2D projection.
  >     Default is False.
  > 
  > Returns
  > pygeos.Geometry
  >     A 2D polygon geometry. If the object has voids, a polygon with holes is constructed;
  >     otherwise, the 2D version of the edge is returned directly.
  > Returns:
  > pygeos.Geometry
  >     A 2D polygon geometry. If the object has voids, a polygon with holes is constructed;
  >     otherwise, the 2D version of the edge is returned directly.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_is_void'></a>`is_void`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** bool
    True if the space is considered void (i.e., either floor or ceiling is missing, 
    or their area is less than the space's area within the given precision), 
    False otherwise.
- **Comments:**
  > Function:
  > Check if the space is considered void based on floor and ceiling area conditions.
  > Parameters:
  > self : object
  >     The instance of the class containing the attributes `floor`, `ceiling`, `area`, 
  >     where `floor` and `ceiling` are objects with an `area` attribute, and `area` 
  >     represents the reference area of the space. It is assumed that `geom.AREA_PRECISION` 
  >     is a predefined constant used for numerical precision tolerance.
  > 
  > Returns
  > bool
  >     True if the space is considered void (i.e., either floor or ceiling is missing, 
  >     or their area is less than the space's area within the given precision), 
  >     False otherwise.
  > Returns:
  > bool
  >     True if the space is considered void (i.e., either floor or ceiling is missing, 
  >     or their area is less than the space's area within the given precision), 
  >     False otherwise.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_boundBox'></a>`boundBox`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a list of face objects.
    Each face object must have a `face` attribute compatible with `pygeos.get_coordinates`.

Returns
numpy.ndarray
    A 2x3 array containing the minimum and maximum coordinates of the bounding box.
    The first row is the minimum (x, y, z) corner, and the second row is the maximum (x, y, z) corner.
- **Comments:**
  > Function:
  > Compute the axis-aligned bounding box of all faces in the object.
  > Parameters:
  > self : object
  >     The instance of the class containing the `getAllFaces` method, which returns a list of face objects.
  >     Each face object must have a `face` attribute compatible with `pygeos.get_coordinates`.
  > 
  > Returns
  > numpy.ndarray
  >     A 2x3 array containing the minimum and maximum coordinates of the bounding box.
  >     The first row is the minimum (x, y, z) corner, and the second row is the maximum (x, y, z) corner.
  > Returns:
  > a list of face objects.
  >     Each face object must have a `face` attribute compatible with `pygeos.get_coordinates`.
  > 
  > Returns
  > numpy.ndarray
  >     A 2x3 array containing the minimum and maximum coordinates of the bounding box.
  >     The first row is the minimum (x, y, z) corner, and the second row is the maximum (x, y, z) corner.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_applySettings'></a>`applySettings`
- **Type:** Instance Method
- **Parameters:** self: Any, buildingTemplateHint: Any
- **Returns:** None
    This function does not return any value. It updates `self.settings` 
    with the zone template and other settings from the matched template.
- **Comments:**
  > Function:
  > Apply settings based on a building template hint.
  > Parameters:
  > buildingTemplateHint : str or dict
  >     The hint used to locate the appropriate building template. If a string, 
  >     it can be an exact key or a regex pattern matching a key in 
  >     `self.parent.buildingTemplate`. If a dictionary, it is treated as 
  >     the template itself, and the corresponding key is inferred.
  > 
  > Returns
  > None
  >     This function does not return any value. It updates `self.settings` 
  >     with the zone template and other settings from the matched template.
  > Returns:
  > None
  >     This function does not return any value. It updates `self.settings` 
  >     with the zone template and other settings from the matched template.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_add_neighbor'></a>`add_neighbor`
- **Type:** Instance Method
- **Parameters:** self: Any, neighbor_id: Any, element: MoosasElement
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Add a neighbor element to the specified neighbor ID.
  > Parameters:
  > neighbor_id : hashable
  >     The identifier for the neighbor group to which the element will be added.
  > element : MoosasElement
  >     The element to be added to the neighbor list associated with neighbor_id.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_addInternalMass'></a>`addInternalMass`
- **Type:** Instance Method
- **Parameters:** self: Any, wall: MoosasWall
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Add an internal mass wall to the current object.
  > Parameters:
  > wall : MoosasWall
  >     The wall object representing internal mass to be added.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_getAllFaces'></a>`getAllFaces`
- **Type:** Instance Method
- **Parameters:** self: Any, to_dict: Any
- **Returns:** :
    list[MoosasElement]: all faces in the space.
    dict:
    {
        MoosasFloor: list[MoosasFloor],
        MoosasCeiling:list[MoosasCeiling],
        MoosasWall:list[MoosasWall],
        MoosasSkylight:list[MoosasSkylight],
        MoosasGlazing:list[MoosasGlazing],
        Shading:list[MoosasElement],
        InternalMass:list[MoosasElement],
    }
- **Comments:**
  > Function:
  > get all faces in the space.
  > 
  > Args:
  >     to_dict (bool, optional): whether to return a dictionary or a list. Defaults to False.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     list[MoosasElement]: all faces in the space.
  >     dict:
  >     {
  >         MoosasFloor: list[MoosasFloor],
  >         MoosasCeiling:list[MoosasCeiling],
  >         MoosasWall:list[MoosasWall],
  >         MoosasSkylight:list[MoosasSkylight],
  >         MoosasGlazing:list[MoosasGlazing],
  >         Shading:list[MoosasElement],
  >         InternalMass:list[MoosasElement],
  >     }

---

###### <a id='geometry_element_py_class_MoosasSpace_method_open_edges'></a>`open_edges`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** dict
    A dictionary where keys are edge strings and values are the corresponding
    geometry objects (`moGeometry`) that are not shared (i.e., open edges).
- **Comments:**
  > Function:
  > Return a dictionary of open edges from the geometry faces.
  > Parameters:
  > self : object
  >     The instance of the class containing the method. It is expected to have
  >     methods `getAllFaces` and access to face geometry objects with `getEdgeStr`.
  > 
  > Returns
  > dict
  >     A dictionary where keys are edge strings and values are the corresponding
  >     geometry objects (`moGeometry`) that are not shared (i.e., open edges).
  > Returns:
  > dict
  >     A dictionary where keys are edge strings and values are the corresponding
  >     geometry objects (`moGeometry`) that are not shared (i.e., open edges).

---

###### <a id='geometry_element_py_class_MoosasSpace_method_to_string'></a>`to_string`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer
- **Returns:** None
- **Comments:**
  > Function:
  > lagacy method to print the space info
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasSpace_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    The string value of the instance's 'id' attribute.
- **Comments:**
  > Function:
  > Return a string representation of the object using its 'id' attribute.
  > Parameters:
  > self : object
  >     The instance of the class containing the 'id' attribute.
  > 
  > Returns
  > str
  >     The string value of the instance's 'id' attribute.
  > Returns:
  > str
  >     The string value of the instance's 'id' attribute.

---

###### <a id='geometry_element_py_class_MoosasSpace_method_to_xml'></a>`to_xml`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasContainer, xml_tag: Any, writeGeometry: Any
- **Returns:** xml.etree.ElementTree.Element
    The XML element representing the object, containing attributes such as id, area, height, boundary coordinates,
    settings, topology (floor, ceiling, edge), neighbors, and internal mass elements.
- **Comments:**
  > Function:
  > Convert the object to an XML element representation.
  > Parameters:
  > model : MoosasContainer, optional
  >     The container model holding global variables and geometry lists. If not provided, uses the parent attribute of the object.
  > xml_tag : str, default="space"
  >     The tag name for the root XML element.
  > writeGeometry : bool, default=False
  >     If True, includes geometric data in the XML output.
  > 
  > Returns
  > xml.etree.ElementTree.Element
  >     The XML element representing the object, containing attributes such as id, area, height, boundary coordinates,
  >     settings, topology (floor, ceiling, edge), neighbors, and internal mass elements.
  > Returns:
  > xml.etree.ElementTree.Element
  >     The XML element representing the object, containing attributes such as id, area, height, boundary coordinates,
  >     settings, topology (floor, ceiling, edge), neighbors, and internal mass elements.

---

### 📦 Class: MoosasContainer
<a id='geometry_element_py_class_MoosasContainer'></a>
**Description:** Define all the global variables needed for Moosas+.

#### Methods
###### <a id='geometry_element_py_class_MoosasContainer_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This method does not return any value.
- **Comments:**
  > Function:
  > Initialize the MoosasModel with default lists and assign appropriate types to these lists.
  > Parameters:
  > self : object
  >     The instance of the MoosasModel class being initialized. This method sets up all the 
  >     internal list attributes used to store geometric and structural components of the model.
  > 
  > Returns
  > None
  >     This method does not return any value.
  > Returns:
  > None
  >     This method does not return any value.

---

###### <a id='geometry_element_py_class_MoosasContainer_method_spaceIdDict'></a>`spaceIdDict`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** :
    dict: {spaceId:MoosasSpace}
- **Comments:**
  > Function:
  > space id dictionary for all spaces in self.spaceList
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     dict: {spaceId:MoosasSpace}

---

###### <a id='geometry_element_py_class_MoosasContainer_method_fromDict'></a>`fromDict`
- **Type:** Instance Method
- **Parameters:** self: Any, spaceDict: dict
- **Returns:** :
    MoosasSpace: created MoosasSpace object.
- **Comments:**
  > Function:
  > construct a space from a dictionary
  > the space will be added to self.spaceList automatically,
  > and the space topology will be automatically recalculate.
  > for more information please refer to MoosasSpace.fromDict()
  > 
  > Args:
  >     spaceDict (dict): Dictionary to construct space from.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     MoosasSpace: created MoosasSpace object.

---

###### <a id='geometry_element_py_class_MoosasContainer_method_update'></a>`update`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Update the builtData attribute to reflect current elements and glazing.
  > 
  > This method initializes the element and glazing dictionaries in builtData if they do not exist,
  > then populates them with face and glazing data from the instance's glazingList, skylightList,
  > and all faces obtained via getAllFaces.
  > Parameters:
  > self : object
  >     The instance of the class containing the method. It is expected to have the following attributes:
  >     - builtData: an object that will be updated with 'element' and 'glazing' dictionaries.
  >     - glazingList: a list of objects, each having a 'glazingId' attribute.
  >     - skylightList: a list of objects, each having a 'glazingId' attribute.
  >     - getAllFaces(): a method returning a collection of face objects, each with a 'faceId' attribute.
  >     - mixItemListToList: a function used to convert faceId items into a flat list.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasContainer_method_getAllFaces'></a>`getAllFaces`
- **Type:** Instance Method
- **Parameters:** self: Any, dumpUseless: Any
- **Returns:** :
    list[MoosasElement]: all MoosasElement in the model
- **Comments:**
  > Function:
  > get all MoosasElement in the model as a list
  > the elements in the list will not change their type hence you can test which element it is by isinstance()
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     list[MoosasElement]: all MoosasElement in the model

---

###### <a id='geometry_element_py_class_MoosasContainer_method_includeGeo'></a>`includeGeo`
- **Type:** Instance Method
- **Parameters:** self: Any, geo: pygeos.Geometry, normal: pygeos.Geometry | Vector | np.ndarray, cat: int, holes: Any
- **Returns:** :
    str: GeoId of the geometry, can be used to construct faces.
- **Comments:**
  > Function:
  > Include a geometry into the geometry library.
  > 
  > Args:
  >     geo (pygeos.Geometry): The polygon to include.
  >     normal (pygeos.Geometry, optional): The normal vector of the polygon. Defaults to None.
  >     cat (int, optional): Category of the geometry (opaque == 0, transparent == 1, aperture == 2). Defaults to 0.
  >     holes (List[pygeos.Geometry], optional): The inner holes of the geometry. Defaults to None.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     str: GeoId of the geometry, can be used to construct faces.

---

###### <a id='geometry_element_py_class_MoosasContainer_method_removeGeo'></a>`removeGeo`
- **Type:** Instance Method
- **Parameters:** self: Any, geo: MoosasGeometry | pygeos.Geometry | str
- **Returns:** None
- **Comments:**
  > Function:
  > Remove a geometry from the internal geometry list.
  > Parameters:
  > geo : MoosasGeometry or pygeos.Geometry or str
  >     The geometry to be removed. Can be a MoosasGeometry object, a pygeos.Geometry object, 
  >     or a string representing the face ID of the geometry.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_element_py_class_MoosasContainer_method_findFace'></a>`findFace`
- **Type:** Instance Method
- **Parameters:** self: Any, faceId: str | list[str]
- **Returns:** :
    list[MoosasGeometry]: a list of MoosasGeometry object of the face
- **Comments:**
  > Function:
  > find a geometry in the library
  > it will test the validation of the identification automatically, and skip invalid geometry
  > 
  > Args:
  >     faceId (str|list[str]): The id of the face in the geo file or library
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     list[MoosasGeometry]: a list of MoosasGeometry object of the face

---

### 🔧 Functions
###### <a id='geometry_element_py_func__getElement'></a>`_getElement`
- **Type:** Function
- **Parameters:** *key: str
- **Returns:** an array with None if any key is missing. Default is True.

Returns
np.ndarray
    A numpy array containing the values from the dictionary corresponding to the input keys. If `strict` is False and a key is missing, returns an array with a single None value.
- **Comments:**
  > Function:
  > Get values from a dictionary corresponding to given keys and return as a numpy array.
  > Parameters:
  > *key : str
  >     Variable length argument list of keys to look up in the dictionary.
  > dictionary : dict
  >     The dictionary from which to retrieve values using the provided keys.
  > strict : bool, optional
  >     If True, raises an error when a key is not found. If False, returns an array with None if any key is missing. Default is True.
  > 
  > Returns
  > np.ndarray
  >     A numpy array containing the values from the dictionary corresponding to the input keys. If `strict` is False and a key is missing, returns an array with a single None value.
  > Returns:
  > an array with None if any key is missing. Default is True.
  > 
  > Returns
  > np.ndarray
  >     A numpy array containing the values from the dictionary corresponding to the input keys. If `strict` is False and a key is missing, returns an array with a single None value.

---

###### <a id='geometry_element_py_func_reverseTwin'></a>`reverseTwin`
- **Type:** Function
- **Parameters:** point_twin: Any
- **Returns:** list
    The same list with its two elements swapped.
- **Comments:**
  > Function:
  > Reverse the elements of a two-element list in place.
  > Parameters:
  > point_twin : list
  >     A list with exactly two elements that will be swapped in place.
  > 
  > Returns
  > list
  >     The same list with its two elements swapped.
  > Returns:
  > list
  >     The same list with its two elements swapped.

---


## 📄 File: geometry\geos.py
<a id='geometry_geos_py'></a>

### Contents
- Classes:
  - [Vector](#geometry_geos_py_class_Vector)
  - [Ray](#geometry_geos_py_class_Ray)
  - [Projection](#geometry_geos_py_class_Projection)
  - [Transformation2d](#geometry_geos_py_class_Transformation2d)
- Functions:
  - [bBox()](#geometry_geos_py_func_bBox)
  - [is_ccw()](#geometry_geos_py_func_is_ccw)
  - [selfIntersect()](#geometry_geos_py_func_selfIntersect)
  - [overlapEdge()](#geometry_geos_py_func_overlapEdge)
  - [overlapArea()](#geometry_geos_py_func_overlapArea)
  - [makeValid()](#geometry_geos_py_func_makeValid)
  - [contains()](#geometry_geos_py_func_contains)
  - [equals()](#geometry_geos_py_func_equals)
  - [faceNormal()](#geometry_geos_py_func_faceNormal)
  - [difference()](#geometry_geos_py_func_difference)
  - [intersection()](#geometry_geos_py_func_intersection)
  - [rayFaceIntersect()](#geometry_geos_py_func_rayFaceIntersect)
  - [simplify()](#geometry_geos_py_func_simplify)
  - [split()](#geometry_geos_py_func_split)
  - [section()](#geometry_geos_py_func_section)
  - [distance()](#geometry_geos_py_func_distance)
  - [splitByCurveLagacy()](#geometry_geos_py_func_splitByCurveLagacy)
  - [splitByCurve()](#geometry_geos_py_func_splitByCurve)
  - [lineIntersection()](#geometry_geos_py_func_lineIntersection)
  - [closeTheCurve()](#geometry_geos_py_func_closeTheCurve)

---

### 📦 Class: Vector
<a id='geometry_geos_py_class_Vector'></a>
**Description:** The geometric operations of points and vectors and related 2D and 3D are defined, and the data formats of pygeos

#### Methods
###### <a id='geometry_geos_py_class_Vector_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, *vec: Vector | Iterable | pygeos.Geometry | float | int
- **Returns:** None
    This constructor initializes the instance attributes x, y, z, and style.
- **Comments:**
  > Function:
  > Initialize a Vector object from various input types.
  > Parameters:
  > vec : Vector or Iterable or pygeos.Geometry or float or int
  >     Input representing a vector, which can be provided as:
  >     - A Vector instance
  >     - A pygeos.Geometry (point, line, etc.)
  >     - An Iterable (list, tuple, numpy array) of coordinates
  >     - Individual float or int values (as variable arguments)
  > 
  > Returns
  > None
  >     This constructor initializes the instance attributes x, y, z, and style.
  > Returns:
  > None
  >     This constructor initializes the instance attributes x, y, z, and style.

---

###### <a id='geometry_geos_py_class_Vector_method_dump'></a>`dump`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** numpy.ndarray or pygeos.Geometry
    If `self.style` is `pygeos.Geometry`, returns `self.geometry`; otherwise, returns `self.array`.
- **Comments:**
  > Function:
  > Return the underlying geometry or array representation based on the current style.
  > Parameters:
  > self : object
  >     The instance of the class containing the `dump` property, with attributes `style`, `geometry`, and `array`.
  > 
  > Returns
  > numpy.ndarray or pygeos.Geometry
  >     If `self.style` is `pygeos.Geometry`, returns `self.geometry`; otherwise, returns `self.array`.
  > Returns:
  > numpy.ndarray or pygeos.Geometry
  >     If `self.style` is `pygeos.Geometry`, returns `self.geometry`; otherwise, returns `self.array`.

---

###### <a id='geometry_geos_py_class_Vector_method_geometry'></a>`geometry`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get geometry representation of the vector
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_array'></a>`array`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get array representation of the vector
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_string'></a>`string`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string representation of the vector with components separated by underscores. Components smaller than 
    `geom.POINT_PRECISION` are replaced with '0.00', others are rounded to 2 decimal places. This format allows 
    forward and reverse vectors (e.g., [0,0,1] and [0,0,-1]) to have the same string representation when symmetry 
    in direction comparison is desired.
- **Comments:**
  > Function:
  > Return a string representation of the vector for comparing direction, where small values are zeroed and components are rounded.
  > Parameters:
  > self : Vector
  >     The Vector instance whose direction string is to be generated. The vector is normalized and its components are processed
  >     to allow comparison of direction, treating opposite vectors as equivalent in certain contexts.
  > 
  > Returns
  > str
  >     A string representation of the vector with components separated by underscores. Components smaller than 
  >     `geom.POINT_PRECISION` are replaced with '0.00', others are rounded to 2 decimal places. This format allows 
  >     forward and reverse vectors (e.g., [0,0,1] and [0,0,-1]) to have the same string representation when symmetry 
  >     in direction comparison is desired.
  > Returns:
  > str
  >     A string representation of the vector with components separated by underscores. Components smaller than 
  >     `geom.POINT_PRECISION` are replaced with '0.00', others are rounded to 2 decimal places. This format allows 
  >     forward and reverse vectors (e.g., [0,0,1] and [0,0,-1]) to have the same string representation when symmetry 
  >     in direction comparison is desired.

---

###### <a id='geometry_geos_py_class_Vector_method_uniform'></a>`uniform`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a unit vector in a consistent direction based on the
lexicographic sign convention, ensuring that antipodal vectors (like `vec` and `-vec`)
map to the same uniform vector. Specifically, the signs are flipped if the first
non-zero component is negative.

Parameters
self : Vector
    The vector instance for which the uniform representation is computed.

Returns
Vector
    A new Vector instance representing the uniform unit vector. The direction
    is adjusted so that the first non-zero component is non-negative, ensuring
    consistency across opposite vectors.
- **Comments:**
  > Function:
  > Get a normalized uniform representation of the vector.
  > 
  > This property
  > Parameters:
  > self : Vector
  >     The vector instance for which the uniform representation is computed.
  > 
  > Returns
  > Vector
  >     A new Vector instance representing the uniform unit vector. The direction
  >     is adjusted so that the first non-zero component is non-negative, ensuring
  >     consistency across opposite vectors.
  > Returns:
  > a unit vector in a consistent direction based on the
  > lexicographic sign convention, ensuring that antipodal vectors (like `vec` and `-vec`)
  > map to the same uniform vector. Specifically, the signs are flipped if the first
  > non-zero component is negative.
  > 
  > Parameters
  > self : Vector
  >     The vector instance for which the uniform representation is computed.
  > 
  > Returns
  > Vector
  >     A new Vector instance representing the uniform unit vector. The direction
  >     is adjusted so that the first non-zero component is non-negative, ensuring
  >     consistency across opposite vectors.

---

###### <a id='geometry_geos_py_class_Vector_method_azimuthToVector'></a>`azimuthToVector`
- **Type:** Class Method
- **Parameters:** cls: Any, azimuth: Any
- **Returns:** Vector
    A unit vector in the xy-plane corresponding to the given azimuth, with z-component zero.
- **Comments:**
  > Function:
  > Convert an azimuth angle to a unit direction vector.
  > Parameters:
  > azimuth : float
  >     The azimuth angle in degrees, measured clockwise from the positive y-axis.
  >     Negative angles are normalized to the range [0, 360).
  > 
  > Returns
  > Vector
  >     A unit vector in the xy-plane corresponding to the given azimuth, with z-component zero.
  > Returns:
  > Vector
  >     A unit vector in the xy-plane corresponding to the given azimuth, with z-component zero.

---

###### <a id='geometry_geos_py_class_Vector_method_altitude'></a>`altitude`
- **Type:** Instance Method
- **Parameters:** self: Any, to_degree: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get the angle to Vector([0,0,1])
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_azimuth'></a>`azimuth`
- **Type:** Instance Method
- **Parameters:** self: Any, to_degree: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get the angle to Vector(0,1,0) in clockwise
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_length'></a>`length`
- **Type:** Instance Method
- **Parameters:** self: Any, power: Any
- **Returns:** float
    The length of the vector. If `power` is True, returns the squared length;
    otherwise, returns the Euclidean norm.
- **Comments:**
  > Function:
  > Compute the length (magnitude) of the vector.
  > Parameters:
  > power : bool, optional
  >     If True, return the squared length (sum of squares) without taking the square root,
  >     which can accelerate the calculation. Default is False.
  > 
  > Returns
  > float
  >     The length of the vector. If `power` is True, returns the squared length;
  >     otherwise, returns the Euclidean norm.
  > Returns:
  > float
  >     The length of the vector. If `power` is True, returns the squared length;
  >     otherwise, returns the Euclidean norm.

---

###### <a id='geometry_geos_py_class_Vector_method_unit'></a>`unit`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a normalized vector. The original vector will be modified and returned to itself
If you don't want to change the vector, you can do like this:
unitVec = Vector(vec).unit()
- **Comments:**
  > Function:
  > No function description.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > a normalized vector. The original vector will be modified and returned to itself
  > If you don't want to change the vector, you can do like this:
  > unitVec = Vector(vec).unit()

---

###### <a id='geometry_geos_py_class_Vector_method_quickAngle'></a>`quickAngle`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > a quick calculation for angle to Vector(1,0,0)
  > if the self.y>=0: get Vector.dot([1,0],vec) in [-1,1]
  > if the self.y<0: get -vector.dot([1,0],vec)-2 in [-3,-1]
  > the return result is in [-3,1] and is positive correlation to the angle.
  > for example:
  > [1,0]==1,[0,1]==0,[-1,0]1
  > [.99,-.01]3,[0,-1]2,[-.99,-.01]1
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_dot'></a>`dot`
- **Type:** Instance Method
- **Parameters:** vec1: Any, vec2: Any
- **Returns:** None
- **Comments:**
  > Function:
  > call np.dot
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_cross'></a>`cross`
- **Type:** Instance Method
- **Parameters:** vec1: Any, vec2: Any, style: Any
- **Returns:** None
- **Comments:**
  > Function:
  > call np.cross
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_parallel'></a>`parallel`
- **Type:** Instance Method
- **Parameters:** vec1: Any, vec2: Any
- **Returns:** None
- **Comments:**
  > Function:
  > test if two vector is parallel, based on their dot value
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method_equal'></a>`equal`
- **Type:** Instance Method
- **Parameters:** vec1: Any, vec2: Any
- **Returns:** bool
    True if the vectors are approximately equal within POINT_PRECISION, False otherwise.
- **Comments:**
  > Function:
  > Check if two vectors are approximately equal within a given precision.
  > Parameters:
  > vec1 : array-like
  >     First vector to compare. Can be a list, tuple, or array.
  > vec2 : array-like
  >     Second vector to compare. Can be a list, tuple, or array.
  > 
  > Returns
  > bool
  >     True if the vectors are approximately equal within POINT_PRECISION, False otherwise.
  > Returns:
  > bool
  >     True if the vectors are approximately equal within POINT_PRECISION, False otherwise.

---

###### <a id='geometry_geos_py_class_Vector_method___add__'></a>`__add__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** Vector
    A new Vector object containing the element-wise sum of the two vectors.
- **Comments:**
  > Function:
  > Add two Vector objects element-wise.
  > Parameters:
  > other : Vector
  >     Another Vector object whose array elements will be added to this vector's array.
  > 
  > Returns
  > Vector
  >     A new Vector object containing the element-wise sum of the two vectors.
  > Returns:
  > Vector
  >     A new Vector object containing the element-wise sum of the two vectors.

---

###### <a id='geometry_geos_py_class_Vector_method___sub__'></a>`__sub__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** Vector
    A new Vector instance containing the result of element-wise subtraction 
    of `other.array` from `self.array`.
- **Comments:**
  > Function:
  > Subtracts another vector from this vector element-wise.
  > Parameters:
  > other : Vector
  >     The vector to be subtracted from this vector. Must have an `array` attribute 
  >     compatible with numpy-style subtraction.
  > 
  > Returns
  > Vector
  >     A new Vector instance containing the result of element-wise subtraction 
  >     of `other.array` from `self.array`.
  > Returns:
  > Vector
  >     A new Vector instance containing the result of element-wise subtraction 
  >     of `other.array` from `self.array`.

---

###### <a id='geometry_geos_py_class_Vector_method___abs__'></a>`__abs__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** Vector
    A new Vector instance with the absolute values of the original components.
- **Comments:**
  > Function:
  > Return the absolute value of each component in the vector.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > Vector
  >     A new Vector instance with the absolute values of the original components.

---

###### <a id='geometry_geos_py_class_Vector_method___neg__'></a>`__neg__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** Any
    A new object that is the negation of `self`, obtained by multiplying by -1.
- **Comments:**
  > Function:
  > Return the negation of the object by multiplying by -1.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > Any
  >     A new object that is the negation of `self`, obtained by multiplying by -1.

---

###### <a id='geometry_geos_py_class_Vector_method___getitem__'></a>`__getitem__`
- **Type:** Instance Method
- **Parameters:** self: Any, item: Any
- **Returns:** Any
    The element or subarray at the specified index or slice.
- **Comments:**
  > Function:
  > Get item from the array using indexing.
  > Parameters:
  > item : int or slice
  >     Index or slice object specifying the position(s) to retrieve from the array.
  > 
  > Returns
  > Any
  >     The element or subarray at the specified index or slice.
  > Returns:
  > Any
  >     The element or subarray at the specified index or slice.

---

###### <a id='geometry_geos_py_class_Vector_method___mul__'></a>`__mul__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** a new Vector.

Returns
float or Vector
    If `other` is a Vector, returns the dot product as a float. 
    If `other` is a scalar, returns a new Vector with components scaled by the scalar.
- **Comments:**
  > Function:
  > Scalar multiplication or dot product of two vectors.
  > Parameters:
  > other : Vector or float or int
  >     The other vector or scalar to multiply with. If `other` is a Vector, 
  >     computes the dot product. If `other` is a scalar (int or float), 
  >     performs scalar multiplication and returns a new Vector.
  > 
  > Returns
  > float or Vector
  >     If `other` is a Vector, returns the dot product as a float. 
  >     If `other` is a scalar, returns a new Vector with components scaled by the scalar.
  > Returns:
  > a new Vector.
  > 
  > Returns
  > float or Vector
  >     If `other` is a Vector, returns the dot product as a float. 
  >     If `other` is a scalar, returns a new Vector with components scaled by the scalar.

---

###### <a id='geometry_geos_py_class_Vector_method___truediv__'></a>`__truediv__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** a new Vector instance.

Parameters
other : scalar or array-like
    The value(s) to divide the vector's components by. Can be a scalar or an array-like 
    object compatible with numpy broadcasting rules.

Returns
Vector
    A new Vector instance containing the result of element-wise division.
- **Comments:**
  > Function:
  > Divides the vector by a scalar or array and
  > Parameters:
  > other : scalar or array-like
  >     The value(s) to divide the vector's components by. Can be a scalar or an array-like 
  >     object compatible with numpy broadcasting rules.
  > 
  > Returns
  > Vector
  >     A new Vector instance containing the result of element-wise division.
  > Returns:
  > a new Vector instance.
  > 
  > Parameters
  > other : scalar or array-like
  >     The value(s) to divide the vector's components by. Can be a scalar or an array-like 
  >     object compatible with numpy broadcasting rules.
  > 
  > Returns
  > Vector
  >     A new Vector instance containing the result of element-wise division.

---

###### <a id='geometry_geos_py_class_Vector_method___xor__'></a>`__xor__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** Vector
    A new Vector instance containing the result of the cross product (if `other` is a Vector) 
    or element-wise power operation (if `other` is a scalar or array_like).
- **Comments:**
  > Function:
  > Element-wise XOR or cross product operation between two Vectors or a Vector and a scalar.
  > Parameters:
  > other : Vector or array_like
  >     The second operand for the operation. If `other` is a Vector, computes the cross 
  >     product of the two vectors using their underlying arrays. If `other` is a scalar 
  >     or array_like, performs element-wise power (np.pow) of the vector's array with `other`.
  > 
  > Returns
  > Vector
  >     A new Vector instance containing the result of the cross product (if `other` is a Vector) 
  >     or element-wise power operation (if `other` is a scalar or array_like).
  > Returns:
  > Vector
  >     A new Vector instance containing the result of the cross product (if `other` is a Vector) 
  >     or element-wise power operation (if `other` is a scalar or array_like).

---

###### <a id='geometry_geos_py_class_Vector_method___key'></a>`__key`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > A tuple based on the object properties, useful for hashing.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Vector_method___hash__'></a>`__hash__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** int
    The hash value of the object, computed from its key.
- **Comments:**
  > Function:
  > Compute the hash value of the object based on its key.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > int
  >     The hash value of the object, computed from its key.

---

###### <a id='geometry_geos_py_class_Vector_method___eq__'></a>`__eq__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** bool
    True if the two vectors are equal, False otherwise.
- **Comments:**
  > Function:
  > Check equality between this Vector and another object.
  > Parameters:
  > self : Vector
  >     The first vector operand.
  > other : object
  >     The second operand to compare against, typically a Vector or compatible object.
  > 
  > Returns
  > bool
  >     True if the two vectors are equal, False otherwise.
  > Returns:
  > bool
  >     True if the two vectors are equal, False otherwise.

---

###### <a id='geometry_geos_py_class_Vector_method___ne__'></a>`__ne__`
- **Type:** Instance Method
- **Parameters:** self: Any, other: Any
- **Returns:** bool
    True if the objects are not equal, False otherwise.
- **Comments:**
  > Function:
  > Check inequality between this object and another.
  > Parameters:
  > other : object
  >     The object to compare with this instance.
  > 
  > Returns
  > bool
  >     True if the objects are not equal, False otherwise.
  > Returns:
  > bool
  >     True if the objects are not equal, False otherwise.

---

###### <a id='geometry_geos_py_class_Vector_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string in the format "Vector(x, y, z)" where x, y, and z are formatted to two decimal places.
- **Comments:**
  > Function:
  > Return a string representation of the Vector instance with formatted coordinates.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > str
  >     A string in the format "Vector(x, y, z)" where x, y, and z are formatted to two decimal places.

---

### 📦 Class: Ray
<a id='geometry_geos_py_class_Ray'></a>
**Description:** Defines a ray with a direction and can also be used to express an infinite plane

#### Methods
###### <a id='geometry_geos_py_class_Ray_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, origin: Any, direction: Any, value: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a Ray object with an origin, direction, and optional value.
  > Parameters:
  > origin : array-like or Vector
  >     The starting point of the ray. If not a Vector, it will be converted to one.
  > direction : array-like or Vector
  >     The direction vector of the ray. If not a Vector, it will be converted to one.
  >     It will be normalized to a unit vector.
  > value : float, optional
  >     An associated scalar value with the ray (default is 0).
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Ray_method_reverse'></a>`reverse`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** Ray
    A new Ray instance with the same origin and value, but with the direction reversed.
- **Comments:**
  > Function:
  > Reverse the direction of the ray.
  > Parameters:
  > self : Ray
  >     The Ray instance whose direction is to be reversed.
  > 
  > Returns
  > Ray
  >     A new Ray instance with the same origin and value, but with the direction reversed.
  > Returns:
  > Ray
  >     A new Ray instance with the same origin and value, but with the direction reversed.

---

###### <a id='geometry_geos_py_class_Ray_method_mirror'></a>`mirror`
- **Type:** Instance Method
- **Parameters:** self: Any, mir: Any
- **Returns:** Ray
    A new Ray instance representing the mirrored (reflected) ray. The returned ray
    is reversed such that it represents the correct propagation direction after reflection.
- **Comments:**
  > Function:
  > Compute a mirror image of the ray based on a given normal vector.
  > Parameters:
  > mir : Vector
  >     The normal vector defining the plane of reflection. The direction of this vector
  >     is used to compute the reflection; its head and tail positions are ignored.
  > 
  > Returns
  > Ray
  >     A new Ray instance representing the mirrored (reflected) ray. The returned ray
  >     is reversed such that it represents the correct propagation direction after reflection.
  > Returns:
  > Ray
  >     A new Ray instance representing the mirrored (reflected) ray. The returned ray
  >     is reversed such that it represents the correct propagation direction after reflection.

---

###### <a id='geometry_geos_py_class_Ray_method_dump'></a>`dump`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A comma-separated string representation of the ray's origin and direction coordinates.
- **Comments:**
  > Function:
  > Get the standard ray export string for MoosasRad.exe.
  > Parameters:
  > self : object
  >     The instance of the class containing `origin` and `direction` attributes,
  >     each having an `array` property with numeric values.
  > 
  > Returns
  > str
  >     A comma-separated string representation of the ray's origin and direction coordinates.
  > Returns:
  > str
  >     A comma-separated string representation of the ray's origin and direction coordinates.

---

###### <a id='geometry_geos_py_class_Ray_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A formatted string showing the origin and direction of the Ray.
- **Comments:**
  > Function:
  > Return a string representation of the Ray object with origin and direction.
  > Parameters:
  > self : Ray
  >     The instance of the Ray object to represent as a string.
  > 
  > Returns
  > str
  >     A formatted string showing the origin and direction of the Ray.
  > Returns:
  > str
  >     A formatted string showing the origin and direction of the Ray.

---

### 📦 Class: Projection
<a id='geometry_geos_py_class_Projection'></a>
**Description:** Establish a three-dimensional coordinate system based on the infinite plane input and realize the conversion with

#### Methods
###### <a id='geometry_geos_py_class_Projection_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, origin: Any, unitZ: Any, unitX: Any
- **Returns:** None
    This method initializes the object and does not return a value.
- **Comments:**
  > Function:
  > Initialize a Projection object with an origin and coordinate axes.
  > Parameters:
  > origin : array-like
  >     The origin point of the projection, converted to a Vector.
  > unitZ : array-like
  >     The unit vector defining the Z-axis direction of the projection.
  > unitX : array-like, optional
  >     The unit vector defining the X-axis direction. If not provided, it is 
  >     computed automatically based on the Z-axis and a default reference direction.
  > 
  > Returns
  > None
  >     This method initializes the object and does not return a value.
  > Returns:
  > None
  >     This method initializes the object and does not return a value.

---

###### <a id='geometry_geos_py_class_Projection_method_fromRay'></a>`fromRay`
- **Type:** Class Method
- **Parameters:** cls: Any, plane: Ray
- **Returns:** cls
    A new instance of the class initialized with the origin and direction from the Ray.
- **Comments:**
  > Function:
  > Create a new instance from a Ray object.
  > Parameters:
  > plane : Ray
  >     The Ray object containing origin and direction used to create the new instance.
  > 
  > Returns
  > cls
  >     A new instance of the class initialized with the origin and direction from the Ray.
  > Returns:
  > cls
  >     A new instance of the class initialized with the origin and direction from the Ray.

---

###### <a id='geometry_geos_py_class_Projection_method_fromPolygon'></a>`fromPolygon`
- **Type:** Class Method
- **Parameters:** cls: Any, polygon: pygeos.Geometry
- **Returns:** cls
    An instance of the class representing the coordinate system defined by the polygon's 
    normal vector, center point, and an orthogonal basis vector derived from a cross-section.
- **Comments:**
  > Function:
  > Construct a coordinate system from a given polygon.
  > Parameters:
  > polygon : pygeos.Geometry
  >     A polygon geometry used to define the coordinate system. Must be a valid 3D polygon.
  > 
  > Returns
  > cls
  >     An instance of the class representing the coordinate system defined by the polygon's 
  >     normal vector, center point, and an orthogonal basis vector derived from a cross-section.
  > Returns:
  > cls
  >     An instance of the class representing the coordinate system defined by the polygon's 
  >     normal vector, center point, and an orthogonal basis vector derived from a cross-section.

---

###### <a id='geometry_geos_py_class_Projection_method_findOrthogonalBasis'></a>`findOrthogonalBasis`
- **Type:** Class Method
- **Parameters:** cls: Any, polygons: Any
- **Returns:** proj : object
    An instance of the class (likely a coordinate system or projection object) 
    representing the orthogonal basis, with `unitX` aligned to the most frequent 
    edge direction and `unitZ` set to [0, 0, 1]. The basis is centered at the 
    mean coordinates of all input polygons.
- **Comments:**
  > Function:
  > Find an orthogonal basis from the most frequent edge directions in given polygons.
  > Parameters:
  > polygons : pygeos.Geometry or list of pygeos.Geometry
  >     A single polygon or a list of polygons from which edge vectors are extracted 
  >     to determine the dominant orthogonal axes.
  > 
  > Returns
  > proj : object
  >     An instance of the class (likely a coordinate system or projection object) 
  >     representing the orthogonal basis, with `unitX` aligned to the most frequent 
  >     edge direction and `unitZ` set to [0, 0, 1]. The basis is centered at the 
  >     mean coordinates of all input polygons.
  > Returns:
  > proj : object
  >     An instance of the class (likely a coordinate system or projection object) 
  >     representing the orthogonal basis, with `unitX` aligned to the most frequent 
  >     edge direction and `unitZ` set to [0, 0, 1]. The basis is centered at the 
  >     mean coordinates of all input polygons.

---

###### <a id='geometry_geos_py_class_Projection_method_rotateMatrix'></a>`rotateMatrix`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** numpy.matrix
    A 3x3 matrix where each column is one of the local axes (axisX, axisY, axisZ),
    representing the rotation from the local coordinate system to the global coordinate system.
- **Comments:**
  > Function:
  > Rotation matrix representing the orientation axes.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > numpy.matrix
  >     A 3x3 matrix where each column is one of the local axes (axisX, axisY, axisZ),
  >     representing the rotation from the local coordinate system to the global coordinate system.

---

###### <a id='geometry_geos_py_class_Projection_method_axisZ'></a>`axisZ`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** numpy.ndarray
    The array associated with the instance.
- **Comments:**
  > Function:
  > Return the array attribute as a property.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > numpy.ndarray
  >     The array associated with the instance.

---

###### <a id='geometry_geos_py_class_Projection_method_axisY'></a>`axisY`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** numpy.ndarray
    A 3D vector representing the Y-axis, computed as the cross product of axisX and axisZ.
- **Comments:**
  > Function:
  > Return the Y-axis vector computed as the cross product of X-axis and Z-axis vectors.
  > Parameters:
  > self : object
  >     The instance of the class containing axisX and axisZ attributes, which are 3D vectors.
  > 
  > Returns
  > numpy.ndarray
  >     A 3D vector representing the Y-axis, computed as the cross product of axisX and axisZ.
  > Returns:
  > numpy.ndarray
  >     A 3D vector representing the Y-axis, computed as the cross product of axisX and axisZ.

---

###### <a id='geometry_geos_py_class_Projection_method_toUV'></a>`toUV`
- **Type:** Instance Method
- **Parameters:** self: Any, worldGeometry: pygeos.Geometry
- **Returns:** pygeos.Geometry
    The geometry transformed into UV coordinates on the specified plane. The 
    output retains the type (point, linestring, polygon, etc.) of the input 
    geometry but is represented in the 2D UV coordinate system of the plane.
- **Comments:**
  > Function:
  > Converts a geometry from world coordinates to UV coordinates on a specified plane.
  > Parameters:
  > worldGeometry : pygeos.Geometry
  >     The input geometry in world coordinates to be transformed. Can be a point, 
  >     line, or polygon. Must be a valid 2D or 3D geometry.
  > 
  > Returns
  > pygeos.Geometry
  >     The geometry transformed into UV coordinates on the specified plane. The 
  >     output retains the type (point, linestring, polygon, etc.) of the input 
  >     geometry but is represented in the 2D UV coordinate system of the plane.
  > Returns:
  > pygeos.Geometry
  >     The geometry transformed into UV coordinates on the specified plane. The 
  >     output retains the type (point, linestring, polygon, etc.) of the input 
  >     geometry but is represented in the 2D UV coordinate system of the plane.

---

###### <a id='geometry_geos_py_class_Projection_method_toWorld'></a>`toWorld`
- **Type:** Instance Method
- **Parameters:** self: Any, UVGeometry: pygeos.Geometry
- **Returns:** pygeos.Geometry
    The transformed geometry in the world coordinate system. The type of geometry (point, linestring, polygon) 
    is preserved after transformation.
- **Comments:**
  > Function:
  > Converts a geometry from UV coordinate system to world coordinate system.
  > Parameters:
  > UVGeometry : pygeos.Geometry
  >     The input geometry in UV coordinates to be transformed. Must be a valid 2D or 3D geometry.
  > 
  > Returns
  > pygeos.Geometry
  >     The transformed geometry in the world coordinate system. The type of geometry (point, linestring, polygon) 
  >     is preserved after transformation.
  > Returns:
  > pygeos.Geometry
  >     The transformed geometry in the world coordinate system. The type of geometry (point, linestring, polygon) 
  >     is preserved after transformation.

---

### 📦 Class: Transformation2d
<a id='geometry_geos_py_class_Transformation2d'></a>
**Description:** Realize two-dimensional transformation, including movement and rotation, and define the rotation angle in clockwise

#### Methods
###### <a id='geometry_geos_py_class_Transformation2d_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, moveVec: Any, rotateRadius: float, rotateOrigin: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize transformation
  > Parameters:
  > for movement and rotation.
  > 
  > Parameters
  > moveVec : array-like or pygeos.Geometry, optional
  >     Vector representing the translation to apply. If a pygeos Geometry is provided,
  >     its coordinates are extracted. Default is numpy array [0, 0].
  > rotateRadius : float, optional
  >     Angular distance (in radians) to rotate. Default is 0.
  > rotateOrigin : array-like or pygeos.Geometry, optional
  >     Point around which rotation occurs. If a pygeos Geometry is provided,
  >     its coordinates are extracted. If None, no rotation origin is set. Default is None.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_geos_py_class_Transformation2d_method_rotateMatrix'></a>`rotateMatrix`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** the inverse of the 2D rotation matrix corresponding to the `rotateRadius` attribute,
where the rotation angle is given in radians. The returned matrix can be used to reverse
the rotation transformation.

Parameters
self : object
    The instance having the `rotateRadius` attribute, which specifies the rotation
    angle in radians.

Returns
numpy.matrix
    A 2x2 inverse rotation matrix represented as a NumPy matrix object.
- **Comments:**
  > Function:
  > Rotation matrix property based on the object's rotation angle.
  > Parameters:
  > self : object
  >     The instance having the `rotateRadius` attribute, which specifies the rotation
  >     angle in radians.
  > 
  > Returns
  > numpy.matrix
  >     A 2x2 inverse rotation matrix represented as a NumPy matrix object.
  > Returns:
  > the inverse of the 2D rotation matrix corresponding to the `rotateRadius` attribute,
  > where the rotation angle is given in radians. The returned matrix can be used to reverse
  > the rotation transformation.
  > 
  > Parameters
  > self : object
  >     The instance having the `rotateRadius` attribute, which specifies the rotation
  >     angle in radians.
  > 
  > Returns
  > numpy.matrix
  >     A 2x2 inverse rotation matrix represented as a NumPy matrix object.

---

###### <a id='geometry_geos_py_class_Transformation2d_method_opposite'></a>`opposite`
- **Type:** Class Method
- **Parameters:** cls: Any, transformation: Any
- **Returns:** object
    A new instance of the class (same type as `cls`) representing the opposite transformation, with reversed 
    translation (`-moveVec`), reversed rotation angle (`-rotateAngle`), and adjusted rotation origin if applicable.
- **Comments:**
  > Function:
  > Get the inverse of a given transformation.
  > Parameters:
  > transformation : object
  >     An object representing a transformation, which must have attributes `moveVec` (numpy.ndarray or similar),
  >     `rotateAngle` (float), and `rotateOrigin` (numpy.ndarray or None). The `moveVec` represents the translation 
  >     vector, `rotateAngle` the rotation angle in radians, and `rotateOrigin` the origin point for rotation, if any.
  > 
  > Returns
  > object
  >     A new instance of the class (same type as `cls`) representing the opposite transformation, with reversed 
  >     translation (`-moveVec`), reversed rotation angle (`-rotateAngle`), and adjusted rotation origin if applicable.
  > Returns:
  > object
  >     A new instance of the class (same type as `cls`) representing the opposite transformation, with reversed 
  >     translation (`-moveVec`), reversed rotation angle (`-rotateAngle`), and adjusted rotation origin if applicable.

---

###### <a id='geometry_geos_py_class_Transformation2d_method_transfrom'></a>`transfrom`
- **Type:** Instance Method
- **Parameters:** self: Any, geo: pygeos.Geometry
- **Returns:** pygeos.Geometry
    The transformed geometry after applying translation and optional rotation.
    The output type matches the input geometry type (point, linestring, or polygon).
- **Comments:**
  > Function:
  > Transform a geometry by applying translation followed by rotation.
  > Parameters:
  > geo : pygeos.Geometry
  >     The input geometry to be transformed. Can be a point, linestring, or polygon.
  > 
  > Returns
  > pygeos.Geometry
  >     The transformed geometry after applying translation and optional rotation.
  >     The output type matches the input geometry type (point, linestring, or polygon).
  > Returns:
  > pygeos.Geometry
  >     The transformed geometry after applying translation and optional rotation.
  >     The output type matches the input geometry type (point, linestring, or polygon).

---

### 🔧 Functions
###### <a id='geometry_geos_py_func_bBox'></a>`bBox`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry
- **Returns:** : dict() include:
- **Comments:**
  > Function:
  > calculate the bounding box of the geometry with direction(calculating by OrthogonalBasis):
  > two projection will be done:
  > 1. project the geo to 2d faces geoProj as projection 1
  > 2.1 in the projection 1, find the Orthogonal Basis of geoProj as projection 2
  > 2.2 reversed project.axisX the projection 2 to the world
  > 3. construct bBoxProjection using the projection2World.axisX and projection1.axisZ
  > 
  > geo (pygeos.Geometry) : input 3d geometry
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > : dict() include:

---

###### <a id='geometry_geos_py_func_is_ccw'></a>`is_ccw`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry
- **Returns:** bool
    True if the ring is oriented counter-clockwise, False otherwise.
- **Comments:**
  > Function:
  > Determine if a polygon's ring is oriented counter-clockwise.
  > Parameters:
  > geo : pygeos.Geometry
  >     A geometry object representing a polygon or line string. Must have at least 3 points to form a ring.
  > 
  > Returns
  > bool
  >     True if the ring is oriented counter-clockwise, False otherwise.
  > Returns:
  > bool
  >     True if the ring is oriented counter-clockwise, False otherwise.

---

###### <a id='geometry_geos_py_func_selfIntersect'></a>`selfIntersect`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry
- **Returns:** bool
    True if the geometry is self-intersecting, False otherwise.
- **Comments:**
  > Function:
  > Test whether a geometry is self-intersecting.
  > Parameters:
  > geo : pygeos.Geometry
  >     A PyGEOS geometry object to be tested for self-intersection.
  > 
  > Returns
  > bool
  >     True if the geometry is self-intersecting, False otherwise.
  > Returns:
  > bool
  >     True if the geometry is self-intersecting, False otherwise.

---

###### <a id='geometry_geos_py_func_overlapEdge'></a>`overlapEdge`
- **Type:** Function
- **Parameters:** geo1: pygeos.Geometry, geo2: pygeos.Geometry
- **Returns:** bool
    True if the two geometries share at least two endpoints (i.e., overlap on an edge), False otherwise.
- **Comments:**
  > Function:
  > Determine if two geometries share at least two endpoints, indicating a common edge.
  > Parameters:
  > geo1 : pygeos.Geometry
  >     First geometry object to compare.
  > geo2 : pygeos.Geometry
  >     Second geometry object to compare.
  > 
  > Returns
  > bool
  >     True if the two geometries share at least two endpoints (i.e., overlap on an edge), False otherwise.
  > Returns:
  > bool
  >     True if the two geometries share at least two endpoints (i.e., overlap on an edge), False otherwise.

---

###### <a id='geometry_geos_py_func_overlapArea'></a>`overlapArea`
- **Type:** Function
- **Parameters:** geo1: pygeos.Geometry, geo2: pygeos.Geometry
- **Returns:** float
    The area of the intersection between geo1 and geo2. Returns 0.0 if there is no overlap, 
    if either geometry is empty, or if an error occurs during computation.
- **Comments:**
  > Function:
  > Calculate the overlapping area between two geometries.
  > Parameters:
  > geo1 : pygeos.Geometry
  >     The first input geometry.
  > geo2 : pygeos.Geometry
  >     The second input geometry.
  > 
  > Returns
  > float
  >     The area of the intersection between geo1 and geo2. Returns 0.0 if there is no overlap, 
  >     if either geometry is empty, or if an error occurs during computation.
  > Returns:
  > float
  >     The area of the intersection between geo1 and geo2. Returns 0.0 if there is no overlap, 
  >     if either geometry is empty, or if an error occurs during computation.

---

###### <a id='geometry_geos_py_func_makeValid'></a>`makeValid`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry, error: Any
- **Returns:** None
- **Comments:**
  > Function:
  > revise method of pygeos.make_valid()
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_func_contains'></a>`contains`
- **Type:** Function
- **Parameters:** child: pygeos.Geometry, parent: pygeos.Geometry
- **Returns:** bool
    True if all points of the child geometry are within twice the POINT_PRECISION distance 
    from the parent geometry, False otherwise. Returns False if an error occurs during processing.
- **Comments:**
  > Function:
  > Check if all points of a child geometry are within a specified distance from a parent geometry.
  > Parameters:
  > child : pygeos.Geometry
  >     The geometry whose points are to be checked for proximity to the parent.
  > parent : pygeos.Geometry
  >     The geometry used as reference for proximity checking.
  > 
  > Returns
  > bool
  >     True if all points of the child geometry are within twice the POINT_PRECISION distance 
  >     from the parent geometry, False otherwise. Returns False if an error occurs during processing.
  > Returns:
  > bool
  >     True if all points of the child geometry are within twice the POINT_PRECISION distance 
  >     from the parent geometry, False otherwise. Returns False if an error occurs during processing.

---

###### <a id='geometry_geos_py_func_equals'></a>`equals`
- **Type:** Function
- **Parameters:** geo1: pygeos.Geometry, geo2: pygeos.Geometry
- **Returns:** bool
    True if the geometries have the same number of points and all corresponding points 
    (in forward or reverse order) are within 1.2 * geom.POINT_PRECISION distance; otherwise False.
- **Comments:**
  > Function:
  > Check if two geometries are approximately equal by comparing their points within a tolerance.
  > Parameters:
  > geo1 : pygeos.Geometry
  >     First geometry to compare.
  > geo2 : pygeos.Geometry
  >     Second geometry to compare.
  > 
  > Returns
  > bool
  >     True if the geometries have the same number of points and all corresponding points 
  >     (in forward or reverse order) are within 1.2 * geom.POINT_PRECISION distance; otherwise False.
  > Returns:
  > bool
  >     True if the geometries have the same number of points and all corresponding points 
  >     (in forward or reverse order) are within 1.2 * geom.POINT_PRECISION distance; otherwise False.

---

###### <a id='geometry_geos_py_func_faceNormal'></a>`faceNormal`
- **Type:** Function
- **Parameters:** face: pygeos.Geometry
- **Returns:** Vector
    A unit vector representing the normal to the face, computed via the cross product of two non-parallel edges.
    If no such pair is found, returns a Vector constructed directly from the face.
- **Comments:**
  > Function:
  > Calculate the normal vector of a face using cross product of non-parallel edges.
  > Parameters:
  > face : pygeos.Geometry
  >     A geometry object representing a face or linestring. Coordinates are extracted to compute edge vectors.
  > 
  > Returns
  > Vector
  >     A unit vector representing the normal to the face, computed via the cross product of two non-parallel edges.
  >     If no such pair is found, returns a Vector constructed directly from the face.
  > Returns:
  > Vector
  >     A unit vector representing the normal to the face, computed via the cross product of two non-parallel edges.
  >     If no such pair is found, returns a Vector constructed directly from the face.

---

###### <a id='geometry_geos_py_func_difference'></a>`difference`
- **Type:** Function
- **Parameters:** geoBase: pygeos.Geometry, geoDifference: pygeos.Geometry
- **Returns:** list of pygeos.Geometry
    A list of geometries representing the result of the 3D difference operation.
- **Comments:**
  > Function:
  > 3D difference operation between two polygons.
  > 
  > Performs a 3D boolean difference between a base geometry and a differencing geometry by projecting 
  > them into a 2D UV plane, computing the difference, and transforming the result back to 3D space.
  > Parameters:
  > geoBase : pygeos.Geometry
  >     The base geometry from which parts will be subtracted. Must be a valid polygon.
  > geoDifference : pygeos.Geometry
  >     The geometry to subtract from the base. Must be a valid polygon.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list of geometries representing the result of the 3D difference operation.
  > Returns:
  > list of pygeos.Geometry
  >     A list of geometries representing the result of the 3D difference operation.

---

###### <a id='geometry_geos_py_func_intersection'></a>`intersection`
- **Type:** Function
- **Parameters:** geoBase: pygeos.Geometry, geoDifference: pygeos.Geometry
- **Returns:** list of pygeos.Geometry
    A list containing the resulting geometry or geometries from the intersection operation in 3D space.
- **Comments:**
  > Function:
  > Compute the 3D intersection of two geometric polygons by projecting them into 2D, performing the intersection, and transforming back.
  > Parameters:
  > geoBase : pygeos.Geometry
  >     The base geometry (polygon) involved in the intersection.
  > geoDifference : pygeos.Geometry
  >     The geometry to intersect with the base geometry.
  > 
  > Returns
  > list of pygeos.Geometry
  >     A list containing the resulting geometry or geometries from the intersection operation in 3D space.
  > Returns:
  > list of pygeos.Geometry
  >     A list containing the resulting geometry or geometries from the intersection operation in 3D space.

---

###### <a id='geometry_geos_py_func_rayFaceIntersect'></a>`rayFaceIntersect`
- **Type:** Function
- **Parameters:** ray: Ray, face: pygeos.Geometry, normal: Vector, infinity_face: Any, limit_distance: Any
- **Returns:** None
- **Comments:**
  > Function:
  > func to calculate the intersection for face and ray in many circumstances.
  > 
  > ray: input ray as Ray object
  > face: input face as pygeos.Geometry
  > normal: faceNormal(face), you can provide one to accelerate the calculation
  > infinity_face: do not test the containment of the face and the intersection
  > limit_distance: the "ray" is a line and have limit length
  > 
  > return: point as pygeos.points, None if no intersection
  > 
  > plan expression: (P - p0).n = 0
  >     ray expression: P(t) = p1 + tu
  >     cross them: (P(t) - p0).n = (p1 + tu - p0).n = 0
  >     as result: P(t) = p1 + t*u = p1 + ((p0 - p1).n/u.n) * u
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_func_simplify'></a>`simplify`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry, include_z: Any
- **Returns:** None
- **Comments:**
  > Function:
  > simplified the geometry to remove redundant points where the last and next directions are parallel
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_func_split'></a>`split`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry, spliter: Ray | pygeos.Geometry, normal: Any
- **Returns:** list[list[pygeos.Geometry]]
    A list containing one or more lists of geometric components resulting from the split.
    Each inner list represents a connected part of the split result, composed of pygeos.Geometry objects.
- **Comments:**
  > Function:
  > Split a polygon geometry using a curve or plane.
  > Parameters:
  > geo : pygeos.Geometry
  >     The input polygon geometry to be split. Only polygon geometries are supported.
  > spliter : Ray or pygeos.Geometry
  >     The splitting element, which can be a Ray object representing a plane, or a pygeos.Geometry
  >     (e.g., line or polygon) used to define the split. If a Ray is provided, it defines both the
  >     splitting plane and its normal direction.
  > normal : array-like or None, optional
  >     The normal vector of the splitting plane. If not provided and `spliter` is a Ray, the normal
  >     is taken from the Ray's direction. If `spliter` is a geometry, the normal is computed using
  >     the face normal of the geometry.
  > 
  > Returns
  > list[list[pygeos.Geometry]]
  >     A list containing one or more lists of geometric components resulting from the split.
  >     Each inner list represents a connected part of the split result, composed of pygeos.Geometry objects.
  > Returns:
  > list[list[pygeos.Geometry]]
  >     A list containing one or more lists of geometric components resulting from the split.
  >     Each inner list represents a connected part of the split result, composed of pygeos.Geometry objects.

---

###### <a id='geometry_geos_py_func_section'></a>`section`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry, elevation: float, segment: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate the section for a geometry on given elevation(z value), which can be used to do a section on z
  > Return all parts of the section if segment==True
  > Otherwise, only the biggest line will be return, it can be used to split the geometry by split() method
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_geos_py_func_distance'></a>`distance`
- **Type:** Function
- **Parameters:** point: Any, polygon: pygeos.Geometry, normal: Any
- **Returns:** float
    The absolute distance from the point to the polygon or plane, computed
    as the absolute dot product between the vector from a point on the polygon
    to the input point and the normal vector.
- **Comments:**
  > Function:
  > Get the distance from a point to a polygon or plane.
  > Parameters:
  > point : array-like
  >     The point for which the distance to the polygon or plane is calculated.
  >     It will be converted to a numpy array internally.
  > polygon : pygeos.Geometry
  >     A geometric object representing the polygon. Coordinates of the polygon
  >     are used to compute the distance.
  > normal : array-like, optional
  >     The normal vector of the plane. If not provided, it is computed using
  >     the `faceNormal` function based on the polygon. If provided, it will be
  >     converted to a Vector and normalized.
  > 
  > Returns
  > float
  >     The absolute distance from the point to the polygon or plane, computed
  >     as the absolute dot product between the vector from a point on the polygon
  >     to the input point and the normal vector.
  > Returns:
  > float
  >     The absolute distance from the point to the polygon or plane, computed
  >     as the absolute dot product between the vector from a point on the polygon
  >     to the input point and the normal vector.

---

###### <a id='geometry_geos_py_func_splitByCurveLagacy'></a>`splitByCurveLagacy`
- **Type:** Function
- **Parameters:** geoBase: pygeos.Geometry, curve: pygeos.Geometry
- **Returns:** list[list[pygeos.Geometry]]
    A list containing two lists of geometries: the first sublist represents geometries on one side of the split curve,
    and the second sublist represents geometries on the other side. Each sublist contains reconstructed curve segments
    after splitting and re-projection back to world coordinates.
- **Comments:**
  > Function:
  > Split a geometry into two parts based on intersection with a dividing curve using legacy projection-based method.
  > 
  > This function is part of the split function. It should not be used directly.
  > Parameters:
  > geoBase : pygeos.Geometry
  >     The base geometry to be split, typically a linestring or polygon.
  > curve : pygeos.Geometry
  >     The curve geometry used as the splitting divider; intersections with `geoBase` determine split locations.
  > 
  > Returns
  > list[list[pygeos.Geometry]]
  >     A list containing two lists of geometries: the first sublist represents geometries on one side of the split curve,
  >     and the second sublist represents geometries on the other side. Each sublist contains reconstructed curve segments
  >     after splitting and re-projection back to world coordinates.
  > Returns:
  > list[list[pygeos.Geometry]]
  >     A list containing two lists of geometries: the first sublist represents geometries on one side of the split curve,
  >     and the second sublist represents geometries on the other side. Each sublist contains reconstructed curve segments
  >     after splitting and re-projection back to world coordinates.

---

###### <a id='geometry_geos_py_func_splitByCurve'></a>`splitByCurve`
- **Type:** Function
- **Parameters:** geoBase: pygeos.Geometry, curve: pygeos.Geometry
- **Returns:** list of list of pygeos.Geometry
    A list containing two groups of geometries resulting from the split operation.
    Each group is a list of pygeos.Geometry objects representing polygons.
    The first sublist typically represents one side of the split, and the second sublist
    the other side, with holes properly subtracted based on containment relationships.
- **Comments:**
  > Function:
  > Split a geometric object by a curve using projection and intersection analysis.
  > Parameters:
  > geoBase : pygeos.Geometry
  >     The base geometry to be split, typically a polygon or linestring in 3D space.
  >     It serves as the input shape that will be divided based on its intersection with the curve.
  > curve : pygeos.Geometry
  >     A curve (linestring) used to split the geoBase. This curve is projected into the same
  >     plane as geoBase for intersection calculations.
  > 
  > Returns
  > list of list of pygeos.Geometry
  >     A list containing two groups of geometries resulting from the split operation.
  >     Each group is a list of pygeos.Geometry objects representing polygons.
  >     The first sublist typically represents one side of the split, and the second sublist
  >     the other side, with holes properly subtracted based on containment relationships.
  > Returns:
  > list of list of pygeos.Geometry
  >     A list containing two groups of geometries resulting from the split operation.
  >     Each group is a list of pygeos.Geometry objects representing polygons.
  >     The first sublist typically represents one side of the split, and the second sublist
  >     the other side, with holes properly subtracted based on containment relationships.

---

###### <a id='geometry_geos_py_func_lineIntersection'></a>`lineIntersection`
- **Type:** Function
- **Parameters:** l1: pygeos.Geometry, l2: pygeos.Geometry
- **Returns:** pygeos.Geometry
    A Point geometry representing the intersection point of the two lines,
    or None if the lines are parallel or nearly collinear.
- **Comments:**
  > Function:
  > Compute the intersection point of two line segments using vector mathematics.
  > Parameters:
  > l1 : pygeos.Geometry
  >     A LineString geometry representing the first line segment.
  > l2 : pygeos.Geometry
  >     A LineString geometry representing the second line segment.
  > 
  > Returns
  > pygeos.Geometry
  >     A Point geometry representing the intersection point of the two lines,
  >     or None if the lines are parallel or nearly collinear.
  > Returns:
  > pygeos.Geometry
  >     A Point geometry representing the intersection point of the two lines,
  >     or None if the lines are parallel or nearly collinear.

---

###### <a id='geometry_geos_py_func_closeTheCurve'></a>`closeTheCurve`
- **Type:** Function
- **Parameters:** geo: pygeos.Geometry
- **Returns:** pygeos.Geometry
    A new geometry where the input curve is closed by connecting the last point to the first.
    If the input was already closed, the original geometry is returned.
- **Comments:**
  > Function:
  > Close an open geometric curve by adding the first coordinate to the end if not already closed.
  > Parameters:
  > geo : pygeos.Geometry
  >     A geometric object (e.g., LineString) that may be open or closed. If the geometry is already closed,
  >     it is returned as-is.
  > 
  > Returns
  > pygeos.Geometry
  >     A new geometry where the input curve is closed by connecting the last point to the first.
  >     If the input was already closed, the original geometry is returned.
  > Returns:
  > pygeos.Geometry
  >     A new geometry where the input curve is closed by connecting the last point to the first.
  >     If the input was already closed, the original geometry is returned.

---


## 📄 File: geometry\grid.py
<a id='geometry_grid_py'></a>

### Contents
- Classes:
  - [MoosasGrid](#geometry_grid_py_class_MoosasGrid)
  - [MoosasGridCell](#geometry_grid_py_class_MoosasGridCell)

---

### 📦 Class: MoosasGrid
<a id='geometry_grid_py_class_MoosasGrid'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_grid_py_class_MoosasGrid_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, element: MoosasElement, gird_size: Any, grid_offset: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a MoosasGrid instance with element properties and apply grid configuration.
  > Parameters:
  > element : MoosasElement
  >     The element object containing parent, faceId, level, offset, glazingId, space attributes.
  > gird_size : float or None, optional
  >     Size of the grid cells. If None, a default or internal logic is used. Default is None.
  > grid_offset : float, optional
  >     Offset value for grid positioning. Default is 0.78.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_grid_py_class_MoosasGrid_method_griding'></a>`griding`
- **Type:** Instance Method
- **Parameters:** self: Any, grid_size: Any, grid_offset: Any
- **Returns:** None
    This function does not return a value. It modifies the instance attributes:
    `proj`, `UVFace`, `gridSize`, `gridOffset`, and `gridCell`, where `gridCell` 
    is a 2D numpy array of `MoosasGridCell` objects representing the generated grid.
- **Comments:**
  > Function:
  > Create grid points and grid polygons based on specified grid size and offset.
  > Parameters:
  > grid_size : float, optional
  >     The size of each grid cell. If None, it is automatically calculated as one-fifth 
  >     of the maximum bounding box dimension of the UV-projected face. Default is None.
  > grid_offset : float, default=0.78
  >     The offset value added to the z-coordinate (level + offset + grid_offset) 
  >     to position the grid in 3D space. Default is 0.78.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the instance attributes:
  >     `proj`, `UVFace`, `gridSize`, `gridOffset`, and `gridCell`, where `gridCell` 
  >     is a 2D numpy array of `MoosasGridCell` objects representing the generated grid.
  > Returns:
  > None
  >     This function does not return a value. It modifies the instance attributes:
  >     `proj`, `UVFace`, `gridSize`, `gridOffset`, and `gridCell`, where `gridCell` 
  >     is a 2D numpy array of `MoosasGridCell` objects representing the generated grid.

---

###### <a id='geometry_grid_py_class_MoosasGrid_method_gridPoints'></a>`gridPoints`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** numpy.ndarray
    An array of valid grid points transformed to world coordinates,
    filtered by the `valid` mask.
- **Comments:**
  > Function:
  > Return valid grid points in world coordinates as a NumPy array.
  > Parameters:
  > self : object
  >     The instance of the class containing the grid structure and projection.
  >     Must have a `gridCell` attribute (list of lists of cells) where each cell
  >     has an `origin.geometry` and a `valid` attribute, and a `proj` attribute
  >     with a `toWorld` method to transform coordinates.
  > 
  > Returns
  > numpy.ndarray
  >     An array of valid grid points transformed to world coordinates,
  >     filtered by the `valid` mask.
  > Returns:
  > numpy.ndarray
  >     An array of valid grid points transformed to world coordinates,
  >     filtered by the `valid` mask.

---

###### <a id='geometry_grid_py_class_MoosasGrid_method_mask'></a>`mask`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** list of list of bool
    A 2D list with the same dimensions as `self.gridCell`, where each element is a boolean 
    indicating whether the corresponding cell is valid (`True`) or not (`False`).
- **Comments:**
  > Function:
  > Return a 2D mask of boolean values indicating the validity of each cell in the grid.
  > Parameters:
  > self : object
  >     The instance of the class containing the `gridCell` attribute. This should be an object 
  >     with a `gridCell` property that is a 2D list (or similar structure) of cell objects, 
  >     where each cell has a `valid` attribute.
  > 
  > Returns
  > list of list of bool
  >     A 2D list with the same dimensions as `self.gridCell`, where each element is a boolean 
  >     indicating whether the corresponding cell is valid (`True`) or not (`False`).
  > Returns:
  > list of list of bool
  >     A 2D list with the same dimensions as `self.gridCell`, where each element is a boolean 
  >     indicating whether the corresponding cell is valid (`True`) or not (`False`).

---

###### <a id='geometry_grid_py_class_MoosasGrid_method_gridPolygon'></a>`gridPolygon`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** gridCell : numpy.ndarray
    A 2D array of `MoosasGridCell` objects with updated `polygon` attributes, where each 
    valid cell contains a 3D polygon (shapely geometry) in world coordinates, generated 
    from the cell's origin and trimmed by the UVFace if on the boundary.
- **Comments:**
  > Function:
  > Generate grid polygons from valid grid cells and assign them to the gridCell array.
  > Parameters:
  > self : object
  >     The instance of the class containing the gridCell attribute, gridSize, UVFace, 
  >     proj, and other related properties. It is assumed that `gridCell` is a 2D array 
  >     of `MoosasGridCell` objects, each having `valid`, `origin`, and `polygon` attributes.
  > 
  > Returns
  > gridCell : numpy.ndarray
  >     A 2D array of `MoosasGridCell` objects with updated `polygon` attributes, where each 
  >     valid cell contains a 3D polygon (shapely geometry) in world coordinates, generated 
  >     from the cell's origin and trimmed by the UVFace if on the boundary.
  > Returns:
  > gridCell : numpy.ndarray
  >     A 2D array of `MoosasGridCell` objects with updated `polygon` attributes, where each 
  >     valid cell contains a 3D polygon (shapely geometry) in world coordinates, generated 
  >     from the cell's origin and trimmed by the UVFace if on the boundary.

---

### 📦 Class: MoosasGridCell
<a id='geometry_grid_py_class_MoosasGridCell'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_grid_py_class_MoosasGridCell_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, origin: Any, direction: Any, value: Any, valid: Any, polygon: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a MoosasGridCell instance.
  > Parameters:
  > origin : array-like
  >     The origin point of the grid cell.
  > direction : array-like
  >     The direction vector associated with the grid cell.
  > value : float or None, optional
  >     The value assigned to the grid cell. Default is None.
  > valid : bool, optional
  >     Flag indicating whether the grid cell is valid. Default is False.
  > polygon : Polygon or None, optional
  >     Geometric polygon representing the grid cell's shape. Default is None.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='geometry_grid_py_class_MoosasGridCell_method_flipPolygon'></a>`flipPolygon`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return a value; it modifies the polygon in place.
- **Comments:**
  > Function:
  > Flip the orientation of the polygon if its normal is opposite to the given direction.
  > Parameters:
  > self : object
  >     The instance containing the polygon and direction attributes.
  >     self.polygon : shapely geometry or None
  >         The polygon to be flipped; modified in place if conditions are met.
  >     self.direction : numpy.ndarray or similar vector-like
  >         Direction vector used for comparison with the polygon's normal.
  >     self.ANGLE_TOLERANCE : float
  >         Tolerance value for angle comparison, typically defined in Vector class.
  > 
  > Returns
  > None
  >     This function does not return a value; it modifies the polygon in place.
  > Returns:
  > None
  >     This function does not return a value; it modifies the polygon in place.

---


## 📄 File: geometry\spaceGen.py
<a id='geometry_spaceGen_py'></a>

### Contents
- Functions:
  - [BTGSpaceGeneration()](#geometry_spaceGen_py_func_BTGSpaceGeneration)
  - [CCRSpaceGeneration()](#geometry_spaceGen_py_func_CCRSpaceGeneration)
  - [VFGSpaceGeneration()](#geometry_spaceGen_py_func_VFGSpaceGeneration)

---

### 🔧 Functions
###### <a id='geometry_spaceGen_py_func_BTGSpaceGeneration'></a>`BTGSpaceGeneration`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The input model with updated boundaryList containing walls identified as valid boundaries for each level.
- **Comments:**
  > Function:
  > Generate boundary space from model elements grouped by level.
  > Parameters:
  > model : MoosasContainer
  >     The container object holding building levels, faces, walls, and to which generated boundaries will be assigned.
  > 
  > Returns
  > MoosasContainer
  >     The input model with updated boundaryList containing walls identified as valid boundaries for each level.
  > Returns:
  > MoosasContainer
  >     The input model with updated boundaryList containing walls identified as valid boundaries for each level.

---

###### <a id='geometry_spaceGen_py_func_CCRSpaceGeneration'></a>`CCRSpaceGeneration`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** MoosasContainer
    The updated model container after applying closed contour calculations for each level.
- **Comments:**
  > Function:
  > Perform closed contour calculation for each building level in the model.
  > Parameters:
  > model : MoosasContainer
  >     The input model container containing building levels and associated data.
  >     This object is updated in place with closed contour calculations.
  > 
  > Returns
  > MoosasContainer
  >     The updated model container after applying closed contour calculations for each level.
  > Returns:
  > MoosasContainer
  >     The updated model container after applying closed contour calculations for each level.

---

###### <a id='geometry_spaceGen_py_func_VFGSpaceGeneration'></a>`VFGSpaceGeneration`
- **Type:** Function
- **Parameters:** model: MoosasContainer
- **Returns:** None
- **Comments:**
  > Function:
  > calculate view factor to get the topology of the walls
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---


## 📄 File: geometry\topology.py
<a id='geometry_topology_py'></a>

### Contents
- Classes:
  - [TopoEdge](#geometry_topology_py_class_TopoEdge)
  - [TopoNode](#geometry_topology_py_class_TopoNode)
  - [TopoNetwork](#geometry_topology_py_class_TopoNetwork)
  - [TopoBound](#geometry_topology_py_class_TopoBound)
- Functions:
  - [_findItemBreadth()](#geometry_topology_py_func__findItemBreadth)

---

### 📦 Class: TopoEdge
<a id='geometry_topology_py_class_TopoEdge'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_topology_py_class_TopoEdge_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, idd: Any, edge: MoosasWall
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a new instance with model ID and edge geometry.
  > Parameters:
  > idd : Any
  >     The model identifier.
  > edge : MoosasWall
  >     The edge object representing a wall, used to extract 2D geometry and UID.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoEdge_method_valid'></a>`valid`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** bool
    True if both locations are not None and are separated by more than
    POINT_PRECISION; False otherwise.
- **Comments:**
  > Function:
  > Check if the fromLocation and toLocation are valid and sufficiently distant.
  > Parameters:
  > self : object
  >     The instance of the class containing this property. It is expected to have
  >     `fromLocation` and `toLocation` attributes, which are geometric points,
  >     and access to `pygeos` and `geom.POINT_PRECISION` for distance evaluation.
  > 
  > Returns
  > bool
  >     True if both locations are not None and are separated by more than
  >     POINT_PRECISION; False otherwise.
  > Returns:
  > bool
  >     True if both locations are not None and are separated by more than
  >     POINT_PRECISION; False otherwise.

---

###### <a id='geometry_topology_py_class_TopoEdge_method_fromPStr'></a>`fromPStr`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string formed by joining the coordinates of `fromLocation` with underscores, where each coordinate value 
    is converted to its string representation.
- **Comments:**
  > Function:
  > Get a string representation of the coordinates of the fromLocation attribute.
  > Parameters:
  > self : object
  >     The instance of the class containing the `fromLocation` attribute. It is expected to have a `fromLocation` 
  >     property accessible, which can be processed by `pygeos.get_coordinates`.
  > 
  > Returns
  > str
  >     A string formed by joining the coordinates of `fromLocation` with underscores, where each coordinate value 
  >     is converted to its string representation.
  > Returns:
  > str
  >     A string formed by joining the coordinates of `fromLocation` with underscores, where each coordinate value 
  >     is converted to its string representation.

---

###### <a id='geometry_topology_py_class_TopoEdge_method_toPStr'></a>`toPStr`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** a geometry object compatible with `pygeos.get_coordinates`.

Returns
str
    A string formed by converting the first coordinate point (x, y) to strings and joining them with an underscore.
- **Comments:**
  > Function:
  > Return a string representation of the first coordinate of the location, joined by underscores.
  > Parameters:
  > self : object
  >     The instance of the class containing the `toLocation` attribute. It is expected to have a `toLocation` 
  >     property or attribute that returns a geometry object compatible with `pygeos.get_coordinates`.
  > 
  > Returns
  > str
  >     A string formed by converting the first coordinate point (x, y) to strings and joining them with an underscore.
  > Returns:
  > a geometry object compatible with `pygeos.get_coordinates`.
  > 
  > Returns
  > str
  >     A string formed by converting the first coordinate point (x, y) to strings and joining them with an underscore.

---

###### <a id='geometry_topology_py_class_TopoEdge_method_overlap'></a>`overlap`
- **Type:** Instance Method
- **Parameters:** this: TopoEdge, other: TopoEdge
- **Returns:** bool
    True if the endpoints of the two edges are within POINT_PRECISION distance 
    of each other, indicating overlap; False otherwise.
- **Comments:**
  > Function:
  > Check if two TopoEdge objects overlap based on their endpoint proximity.
  > Parameters:
  > this : TopoEdge
  >     The first edge to compare.
  > other : TopoEdge
  >     The second edge to compare.
  > 
  > Returns
  > bool
  >     True if the endpoints of the two edges are within POINT_PRECISION distance 
  >     of each other, indicating overlap; False otherwise.
  > Returns:
  > bool
  >     True if the endpoints of the two edges are within POINT_PRECISION distance 
  >     of each other, indicating overlap; False otherwise.

---

###### <a id='geometry_topology_py_class_TopoEdge_method_isolateEdge'></a>`isolateEdge`
- **Type:** Instance Method
- **Parameters:** edge_list: Iterable[TopoEdge]
- **Returns:** list of int
    A list of indices corresponding to edges in edge_list that are isolated, meaning at least 
    one of their connecting nodes has a degree less than 2.
- **Comments:**
  > Function:
  > Identify indices of edges that are isolated, i.e., connected to nodes with degree less than 2.
  > Parameters:
  > edge_list : Iterable[TopoEdge]
  >     An iterable of TopoEdge objects, each representing an edge with 'fromPStr' and 'toPStr' 
  >     attributes indicating the start and end node strings.
  > 
  > Returns
  > list of int
  >     A list of indices corresponding to edges in edge_list that are isolated, meaning at least 
  >     one of their connecting nodes has a degree less than 2.
  > Returns:
  > list of int
  >     A list of indices corresponding to edges in edge_list that are isolated, meaning at least 
  >     one of their connecting nodes has a degree less than 2.

---

###### <a id='geometry_topology_py_class_TopoEdge_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string describing the TopoNode, including its idd and location.
- **Comments:**
  > Function:
  > Return a string representation of the TopoNode instance.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > str
  >     A string describing the TopoNode, including its idd and location.

---

### 📦 Class: TopoNode
<a id='geometry_topology_py_class_TopoNode'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_topology_py_class_TopoNode_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, idd: Any, location: pygeos.Geometry
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a TopoNode instance with an identifier, location, and empty lists for neighbors, angles, and connected edges.
  > Parameters:
  > idd : hashable
  >     Unique identifier for the node.
  > location : pygeos.Geometry
  >     Geometric representation of the node's location.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoNode_method_sortNeighbor'></a>`sortNeighbor`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function modifies the object's attributes in place and does not return any value.
- **Comments:**
  > Function:
  > Sort the neighbors according to their angle to the x-axis.
  > Parameters:
  > self : object
  >     The instance of the class containing the attributes to be sorted.
  >     Must have the following attributes:
  >     - neighbor : list
  >         List of neighbor elements to be sorted.
  >     - neiAngle : list of float
  >         List of angles corresponding to each neighbor, used as the sorting key.
  >     - connectedEdges : list
  >         List of edge connections associated with each neighbor, sorted to match the new order.
  > 
  > Returns
  > None
  >     This function modifies the object's attributes in place and does not return any value.
  > Returns:
  > None
  >     This function modifies the object's attributes in place and does not return any value.

---

###### <a id='geometry_topology_py_class_TopoNode_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string representation of the TopoNetwork in the format "N" followed by the string representation of its `idd` attribute.
- **Comments:**
  > Function:
  > String representation of the TopoNetwork object.
  > Parameters:
  > self : TopoNetwork
  >     The instance of TopoNetwork to represent as a string.
  > 
  > Returns
  > str
  >     A string representation of the TopoNetwork in the format "N" followed by the string representation of its `idd` attribute.
  > Returns:
  > str
  >     A string representation of the TopoNetwork in the format "N" followed by the string representation of its `idd` attribute.

---

### 📦 Class: TopoNetwork
<a id='geometry_topology_py_class_TopoNetwork'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_topology_py_class_TopoNetwork_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, edges: Any, nodes: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize the network topology from given edges or nodes.
  > Parameters:
  > edges : list[TopoEdge], optional
  >     List of TopoEdge objects representing the edges in the network. Each edge contains information about its endpoints.
  >     If provided, the nodes will be derived from these edges using `_nodeFromEdge`.
  > nodes : list[TopoNode], optional
  >     List of TopoNode objects representing the unique nodes in the network. Each node contains:
  >     - a unique ID,
  >     - a list of neighboring TopoNode objects,
  >     - a list of edge IDs connecting to those neighbors (in corresponding order),
  >     - a list of dot products representing angles between the node and its neighbors relative to the x-axis.
  >     If provided and edges are not, the edges will be derived using `_edgeFromNode`.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoNetwork_method__nodeFromEdge'></a>`_nodeFromEdge`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return any value. It modifies the object's state by updating
    the `edges` and `nodes` attributes to reflect the cleaned edge list and constructed
    topological node network.
- **Comments:**
  > Function:
  > Construct the node list from valid and processed topological edges.
  > 
  > This method processes the topological edges by removing invalid and duplicate edges,
  > merges spatially close nodes, removes isolated edges, and constructs a node network
  > with neighbor relationships and angular information relative to the x-axis.
  > Parameters:
  > self : object
  >     The instance of the class containing the `edges` attribute (list of TopoEdge objects)
  >     and `nodes` attribute (to be populated with TopoNode objects). The method modifies
  >     `self.edges` and `self.nodes` in place.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the object's state by updating
  >     the `edges` and `nodes` attributes to reflect the cleaned edge list and constructed
  >     topological node network.
  > Returns:
  > None
  >     This function does not return any value. It modifies the object's state by updating
  >     the `edges` and `nodes` attributes to reflect the cleaned edge list and constructed
  >     topological node network.

---

###### <a id='geometry_topology_py_class_TopoNetwork_method__edgeFromNode'></a>`_edgeFromNode`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return a value. It modifies the instance by setting
    the `edges` attribute to a list of unique TopoEdge objects.
- **Comments:**
  > Function:
  > Extract unique edge list from node.edgeId.
  > Parameters:
  > self : object
  >     The instance of the class containing nodes and edges attributes.
  >     It is expected to have a `nodes` attribute which is an iterable of objects,
  >     each having a `connectedEdges` attribute that yields TopoEdge instances.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the instance by setting
  >     the `edges` attribute to a list of unique TopoEdge objects.
  > Returns:
  > None
  >     This function does not return a value. It modifies the instance by setting
  >     the `edges` attribute to a list of unique TopoEdge objects.

---

###### <a id='geometry_topology_py_class_TopoNetwork_method_inLevel'></a>`inLevel`
- **Type:** Class Method
- **Parameters:** cls: Any, bld_level: float, model: Any
- **Returns:** None
- **Comments:**
  > Function:
  > clean zero, duplicate and isolated edge in the edge list,
  > then build a list[TopoEdge] to record these edge for next step.
  > This list will construct a TopoNetwork.
  > 
  > bld_level: building level to retrieve in float
  > model: get topoEdge from this model
  > 
  > return: TopoNetwork with select edges
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoNetwork_method_splitNetwork'></a>`splitNetwork`
- **Type:** Class Method
- **Parameters:** cls: Any, oriNetwork: TopoNetwork
- **Returns:** list of TopoNetwork
    A list of isolated subnetworks derived from the original network.
- **Comments:**
  > Function:
  > Split the network into several isolated subnetworks.
  > Parameters:
  > oriNetwork : TopoNetwork
  >     The original network to be split into isolated parts.
  > 
  > Returns
  > list of TopoNetwork
  >     A list of isolated subnetworks derived from the original network.
  > Returns:
  > list of TopoNetwork
  >     A list of isolated subnetworks derived from the original network.

---

###### <a id='geometry_topology_py_class_TopoNetwork_method_outerBoundary'></a>`outerBoundary`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** list[TopoBound]
    A list of TopoBound objects representing the outer boundary or boundaries of the network.
    Returns an empty list if there are fewer than 3 nodes.
- **Comments:**
  > Function:
  > Calculate the outer boundary(s) of the network.
  > 
  > This method computes the outer boundary of the network by traversing nodes in a clockwise manner,
  > starting from the node with maximum x and minimum y among those with maximum x. It handles cases
  > where the boundary may self-intersect, potentially resulting in multiple boundary loops.
  > Parameters:
  > self : object
  >     The instance of the class containing the network topology, with attributes:
  >     - nodes (list): A list of TopoNode objects representing the network nodes.
  >     - Other attributes used during traversal (e.g., neighbor relationships, angles).
  > 
  > Returns
  > list[TopoBound]
  >     A list of TopoBound objects representing the outer boundary or boundaries of the network.
  >     Returns an empty list if there are fewer than 3 nodes.
  > Returns:
  > list[TopoBound]
  >     A list of TopoBound objects representing the outer boundary or boundaries of the network.
  >     Returns an empty list if there are fewer than 3 nodes.

---

### 📦 Class: TopoBound
<a id='geometry_topology_py_class_TopoBound'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_topology_py_class_TopoBound_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, nodes: list[TopoNode], edges: list[TopoEdge]
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize a new instance with optional lists of nodes and edges.
  > Parameters:
  > nodes : list of TopoNode, optional
  >     List of TopoNode objects to initialize the node loop. If not provided, nodeLoop is set to None.
  > edges : list of TopoEdge, optional
  >     List of TopoEdge objects to initialize the edge loop. If not provided, edgeLoop is set to None.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method_initEdgeLoop'></a>`initEdgeLoop`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return a value. It modifies the `edgeLoop` attribute
    of the instance in place, populating it with TopoEdge objects extracted
    based on connectivity between consecutive nodes in `nodeLoop`.
- **Comments:**
  > Function:
  > Extract edges from the node loop to form an edge loop.
  > Parameters:
  > self : object
  >     The instance of the class containing the nodeLoop and edgeLoop attributes.
  >     It is expected to have a `nodeLoop` attribute which is a list of nodes,
  >     each having `neighbor` and `connectedEdges` properties.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the `edgeLoop` attribute
  >     of the instance in place, populating it with TopoEdge objects extracted
  >     based on connectivity between consecutive nodes in `nodeLoop`.
  > Returns:
  > None
  >     This function does not return a value. It modifies the `edgeLoop` attribute
  >     of the instance in place, populating it with TopoEdge objects extracted
  >     based on connectivity between consecutive nodes in `nodeLoop`.

---

###### <a id='geometry_topology_py_class_TopoBound_method_initNodeLoop'></a>`initNodeLoop`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return a value. It modifies the `nodeLoop` attribute of the instance in place.
- **Comments:**
  > Function:
  > Initialize and construct the node loop from the edge loop.
  > 
  > This method constructs a list of unique nodes (`nodeLoop`) by iterating over the edges 
  > in `edgeLoop`, adding both the start (`fromP`) and end (`toP`) points of each edge. 
  > It then adjusts the order of the first two nodes based on connectivity with the second edge, 
  > and if the edge loop is closed (i.e., first and last edges share a common node), 
  > it appends the first node to the end of the node loop to close it.
  > Parameters:
  > self : object
  >     The instance of the class containing this method. Expected to have the following attributes:
  >     - edgeLoop : list of edge objects, each with 'fromP' and 'toP' attributes representing connected points.
  >     - nodeLoop : list, will be initialized as an empty list and populated with node points.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the `nodeLoop` attribute of the instance in place.
  > Returns:
  > None
  >     This function does not return a value. It modifies the `nodeLoop` attribute of the instance in place.

---

###### <a id='geometry_topology_py_class_TopoBound_method_reverse'></a>`reverse`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function modifies the object in place and does not return a value.
- **Comments:**
  > Function:
  > Reverse the boundary by reversing the order of nodes and edges in the loops.
  > Parameters:
  > self : object
  >     The instance of the class containing the nodeLoop and edgeLoop attributes.
  >     It is expected to have `nodeLoop` and `edgeLoop` as list-like attributes that support reverse().
  > 
  > Returns
  > None
  >     This function modifies the object in place and does not return a value.
  > Returns:
  > None
  >     This function modifies the object in place and does not return a value.

---

###### <a id='geometry_topology_py_class_TopoBound_method_fromTopoEdge'></a>`fromTopoEdge`
- **Type:** Class Method
- **Parameters:** cls: Any, edge: TopoEdge
- **Returns:** cls
    A new instance of the class initialized with nodes [edge.fromP, edge.toP] and edges [edge].
- **Comments:**
  > Function:
  > Create an instance from a TopoEdge.
  > Parameters:
  > edge : TopoEdge
  >     The TopoEdge object to create the instance from. Contains fromP and toP node attributes.
  > 
  > Returns
  > cls
  >     A new instance of the class initialized with nodes [edge.fromP, edge.toP] and edges [edge].
  > Returns:
  > cls
  >     A new instance of the class initialized with nodes [edge.fromP, edge.toP] and edges [edge].

---

###### <a id='geometry_topology_py_class_TopoBound_method_isClose'></a>`isClose`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > whether the loop is close?
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method_coveredBy'></a>`coveredBy`
- **Type:** Instance Method
- **Parameters:** self: Any, other: TopoBound
- **Returns:** None
- **Comments:**
  > Function:
  > test if this boundary share same topology with others
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method_connect'></a>`connect`
- **Type:** Instance Method
- **Parameters:** self: Any, other: TopoBound
- **Returns:** None
- **Comments:**
  > Function:
  > test if this boundary connected to others
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method_geometry'></a>`geometry`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > get the polygon or linestring from the nodeLoop
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string formed by joining the string representations of each node in `nodeLoop` with spaces.
- **Comments:**
  > Function:
  > Return a string representation of the object by joining string representations of nodes in the loop.
  > Parameters:
  > self : object
  >     The instance of the class containing the `nodeLoop` attribute, which is an iterable of nodes.
  > 
  > Returns
  > str
  >     A string formed by joining the string representations of each node in `nodeLoop` with spaces.
  > Returns:
  > str
  >     A string formed by joining the string representations of each node in `nodeLoop` with spaces.

---

###### <a id='geometry_topology_py_class_TopoBound_method_split'></a>`split`
- **Type:** Class Method
- **Parameters:** cls: Any, oriBoundary: TopoBound, splitLinestring: TopoBound
- **Returns:** None
- **Comments:**
  > Function:
  > split the boundary by another spliter
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='geometry_topology_py_class_TopoBound_method_selfIntersect'></a>`selfIntersect`
- **Type:** Class Method
- **Parameters:** cls: Any, oriBoundary: Any
- **Returns:** list of TopoBound
    A list of `TopoBound` instances created from the split segments of the original boundary. 
    The main segment starting with `oriBoundary.nodeLoop[0]` is located at `validBound[-1]`.
- **Comments:**
  > Function:
  > Check if a boundary self-intersects and split it at intersection points.
  > Parameters:
  > cls : type
  >     The class instance, used to create new instances of the boundary.
  > oriBoundary : object
  >     An object with a `nodeLoop` attribute containing a sequence of `TopoNode` objects representing the boundary.
  > 
  > Returns
  > list of TopoBound
  >     A list of `TopoBound` instances created from the split segments of the original boundary. 
  >     The main segment starting with `oriBoundary.nodeLoop[0]` is located at `validBound[-1]`.
  > Returns:
  > list of TopoBound
  >     A list of `TopoBound` instances created from the split segments of the original boundary. 
  >     The main segment starting with `oriBoundary.nodeLoop[0]` is located at `validBound[-1]`.

---

### 🔧 Functions
###### <a id='geometry_topology_py_func__findItemBreadth'></a>`_findItemBreadth`
- **Type:** Function
- **Parameters:** node: TopoNode
- **Returns:** None
- **Comments:**
  > Function:
  > Recursive Breadth-first search method to find all connected node to the target node
  > 
  > node: target node
  > avoidPoint: optional nodes that don't want to add in the group
  > nodeInGroup: please leave blank for this argument
  > max_depth: maximum iteration to avoid collapse
  > 
  > return: list[TopoNode] target nodes which are connected together
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---


## 📄 File: geometry\viewFactor.py
<a id='geometry_viewFactor_py'></a>

### Contents
- Classes:
  - [ViewFactorFace](#geometry_viewFactor_py_class_ViewFactorFace)
- Functions:
  - [viewFactorTopology()](#geometry_viewFactor_py_func_viewFactorTopology)

---

### 📦 Class: ViewFactorFace
<a id='geometry_viewFactor_py_class_ViewFactorFace'></a>
**Description:** No class documentation.

#### Methods
###### <a id='geometry_viewFactor_py_class_ViewFactorFace_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, element: MoosasElement, normal: Any, value: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a ViewFactorFace instance.
  > Parameters:
  > element : MoosasElement
  >     The MoosasElement associated with this face, containing geometry and normal information.
  > normal : array-like, optional
  >     The normal vector of the face. If None, defaults to the element's normal.
  > value : float, optional
  >     An optional scalar value associated with the face, passed to the parent class.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='geometry_viewFactor_py_class_ViewFactorFace_method_fromElement'></a>`fromElement`
- **Type:** Class Method
- **Parameters:** cls: Any, element: MoosasElement
- **Returns:** tuple
    A tuple containing two instances of the class initialized with opposite normal vectors and modified Uids.
- **Comments:**
  > Function:
  > Create two instances of the class from a MoosasElement.
  > Parameters:
  > element : MoosasElement
  >     The element used to create the instances, providing normal vector and Uid.
  > 
  > Returns
  > tuple
  >     A tuple containing two instances of the class initialized with opposite normal vectors and modified Uids.
  > Returns:
  > tuple
  >     A tuple containing two instances of the class initialized with opposite normal vectors and modified Uids.

---

###### <a id='geometry_viewFactor_py_class_ViewFactorFace_method_branchTest'></a>`branchTest`
- **Type:** Instance Method
- **Parameters:** self: Any, faces: list[ViewFactorFace], number: Any
- **Returns:** None
    This function does not return a value. It updates the `objects` attribute of the instance by adding the closest visible faces based on ray intersection tests.
- **Comments:**
  > Function:
  > Perform a ray-casting test to determine visible faces from a source ray using multiple sample directions.
  > Parameters:
  > faces : list of ViewFactorFace
  >     List of face objects to test for visibility. Each face must have an origin, direction, and associated geometric representation.
  > number : int, optional
  >     Number of azimuthal rays to cast per elevation band. Default is 100.
  > 
  > Returns
  > None
  >     This function does not return a value. It updates the `objects` attribute of the instance by adding the closest visible faces based on ray intersection tests.
  > Returns:
  > None
  >     This function does not return a value. It updates the `objects` attribute of the instance by adding the closest visible faces based on ray intersection tests.

---

### 🔧 Functions
###### <a id='geometry_viewFactor_py_func_viewFactorTopology'></a>`viewFactorTopology`
- **Type:** Function
- **Parameters:** model: Any, elementList: Any, vfNumber: Any
- **Returns:** list
    A list of boundary objects (e.g., TopoNetwork boundaries) representing outer boundaries after shading analysis and topological grouping.
- **Comments:**
  > Function:
  > Calculate view factor topology for a given model and element list.
  > Parameters:
  > model : object
  >     The model containing wall and geometric information; expected to have `wallList` attribute with geometric representations.
  > elementList : list
  >     List of elements from which ViewFactorFace instances are generated; each element should support `ViewFactorFace.fromElement`.
  > vfNumber : int, optional
  >     Number of view factors to compute during branch testing. Default is 64.
  > 
  > Returns
  > list
  >     A list of boundary objects (e.g., TopoNetwork boundaries) representing outer boundaries after shading analysis and topological grouping.
  > Returns:
  > list
  >     A list of boundary objects (e.g., TopoNetwork boundaries) representing outer boundaries after shading analysis and topological grouping.

---


## 📄 File: geometry\visualization.py
<a id='geometry_visualization_py'></a>

### Contents
- Functions:
  - [plot_plan_in_node()](#geometry_visualization_py_func_plot_plan_in_node)
  - [plot_object()](#geometry_visualization_py_func_plot_object)
  - [plot()](#geometry_visualization_py_func_plot)
  - [patch()](#geometry_visualization_py_func_patch)

---

### 🔧 Functions
###### <a id='geometry_visualization_py_func_plot_plan_in_node'></a>`plot_plan_in_node`
- **Type:** Function
- **Parameters:** node_list: Any, boundary_list: Any, location_list: Any, save: Any, show: Any
- **Returns:** myfig : matplotlib.figure.Figure
    The current figure object containing the plot.
- **Comments:**
  > Function:
  > Plot a plan in a node with given boundaries and locations.
  > Parameters:
  > node_list : list
  >     List of nodes to be plotted.
  > boundary_list : list
  >     List of boundary coordinates defining the regions.
  > location_list : list
  >     List of location coordinates to be marked on the plot.
  > save : bool, optional
  >     If True, saves the plot to a file. Default is False.
  > show : bool, optional
  >     If True, displays the plot. Default is True.
  > 
  > Returns
  > myfig : matplotlib.figure.Figure
  >     The current figure object containing the plot.
  > Returns:
  > myfig : matplotlib.figure.Figure
  >     The current figure object containing the plot.

---

###### <a id='geometry_visualization_py_func_plot_object'></a>`plot_object`
- **Type:** Function
- **Parameters:** *geoCollection: Any
- **Returns:** None
    This function does not return a value. It renders a plot using matplotlib.
- **Comments:**
  > Function:
  > Plot geometric objects using matplotlib.
  > Parameters:
  > geoCollection : iterable of array-like or pygeos.Geometry objects
  >     Variable number of geometric collections or individual geometries to plot.
  >     Each can be a pygeos geometry, an iterable of coordinates, or an object with a `force_2d` method.
  > colors : str or list of str, optional
  >     Color(s) to use for plotting the geometries. If a single string is provided,
  >     it is applied to all collections. If a list, must have length matching `geoCollection`,
  >     otherwise the last color is repeated as needed. Default is 'black'.
  > show : bool, optional
  >     If True, display the plot immediately. Default is True.
  > filled : bool, optional
  >     If True, fill the interior of the plotted shapes. Default is False.
  > 
  > Returns
  > None
  >     This function does not return a value. It renders a plot using matplotlib.
  > Returns:
  > None
  >     This function does not return a value. It renders a plot using matplotlib.

---

###### <a id='geometry_visualization_py_func_plot'></a>`plot`
- **Type:** Function
- **Parameters:** i: Any, j: Any, color: Any
- **Returns:** None
    This function does not return any value. It modifies the current matplotlib plot.
- **Comments:**
  > Function:
  > Plot a line between two points defined by indices in a location list.
  > Parameters:
  > i : int
  >     Index of the first point in the location_list.
  > j : int
  >     Index of the second point in the location_list.
  > color : str, optional
  >     Color of the line to be plotted. Default is 'black'.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the current matplotlib plot.
  > Returns:
  > None
  >     This function does not return any value. It modifies the current matplotlib plot.

---

###### <a id='geometry_visualization_py_func_patch'></a>`patch`
- **Type:** Function
- **Parameters:** boundary: Any, color: Any
- **Returns:** None
    This function does not return a value. It modifies the current matplotlib plot by adding a filled polygon and optionally a text annotation.
- **Comments:**
  > Function:
  > Create a filled polygon patch from boundary coordinates and optionally color it.
  > Parameters:
  > boundary : list of int
  >     List of indices referring to points in `location_list` that form the boundary of the polygon.
  > color : array-like of float, optional
  >     RGB color triplet (e.g., [r, g, b]) used to fill the polygon. If provided, also annotates 
  >     the patch with the rounded red channel value at the centroid. Default is None, resulting in a fill without a specified color.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the current matplotlib plot by adding a filled polygon and optionally a text annotation.
  > Returns:
  > None
  >     This function does not return a value. It modifies the current matplotlib plot by adding a filled polygon and optionally a text annotation.

---


## 📄 File: IO\transIO.py
<a id='IO_transIO_py'></a>

### Contents
- Functions:
  - [modelFromFile()](#IO_transIO_py_func_modelFromFile)
  - [preClassified()](#IO_transIO_py_func_preClassified)
  - [modelToFile()](#IO_transIO_py_func_modelToFile)
  - [writeSpc()](#IO_transIO_py_func_writeSpc)

---

### 🔧 Functions
###### <a id='IO_transIO_py_func_modelFromFile'></a>`modelFromFile`
- **Type:** Function
- **Parameters:** inputPath: str, inputType: Any
- **Returns:** :
    model(MoosasModel): the MoosasModel contain the geometry data.
- **Comments:**
  > Function:
  > Get a MoosasModel from geometry file *.geo,*.xml,*.obj,*.json(geoJson)
  > 
  > please check the file requirement in each function:
  > _readGeo,_readXml,_readObj,readGeoJson
  > this can be used to generate a model to test whether your geometries are read corectly.
  > 
  > Args:
  >     inputPath(str): input geometry file.
  >     inputType(str): input file type. If None the type will be interpreted from the file directly (default: None)
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     model(MoosasModel): the MoosasModel contain the geometry data.

---

###### <a id='IO_transIO_py_func_preClassified'></a>`preClassified`
- **Type:** Function
- **Parameters:** model: Any
- **Returns:** object
    The modified model object with added `geoId` (list of face IDs) and `newIndex` (integer representing 
    the length of the geometry list).
- **Comments:**
  > Function:
  > Preprocesses a model by assigning face IDs to geoId and setting a new index based on geometry list length.
  > Parameters:
  > model : object
  >     The model object containing a `geometryList` attribute, where each element has a `faceId` attribute.
  >     This object is modified in place by adding `geoId` and `newIndex` attributes.
  > 
  > Returns
  > object
  >     The modified model object with added `geoId` (list of face IDs) and `newIndex` (integer representing 
  >     the length of the geometry list).
  > Returns:
  > object
  >     The modified model object with added `geoId` (list of face IDs) and `newIndex` (integer representing 
  >     the length of the geometry list).

---

###### <a id='IO_transIO_py_func_modelToFile'></a>`modelToFile`
- **Type:** Function
- **Parameters:** model: Any, outputPath: Any, outputType: Any, geoPath: Any, geoType: Any
- **Returns:** :
    None
- **Comments:**
  > Function:
  > write the space topology data or geometry data to the file
  > 
  > please check the file description in each function:
  > _readGeo,_readXml,_readObj,readGeoJson
  > 
  > Args:
  >     model(MoosasModel): model to write the space data and geometries data
  >     outputPath(str): input geometry file.
  >     geoPath(str): output geometry file.
  >     outputType(str): input file type. If None the type will be interpreted from the file directly (default: None)
  >     geoType(str): output geometry file.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     None

---

###### <a id='IO_transIO_py_func_writeSpc'></a>`writeSpc`
- **Type:** Function
- **Parameters:** file_path: Any, model: Any
- **Returns:** :
    None
- **Comments:**
  > Function:
  > write the string of each space.
  > 
  > we get the string from space.to_string method instead of __str__() method
  > since the string output is too long.
  > 
  > Args:
  >     file_path(str): output space string file path
  >     model(MoosasModel): model to export
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     None

---


## 📄 File: IO\_geo.py
<a id='IO__geo_py'></a>

### Contents
- Functions:
  - [writeGeo()](#IO__geo_py_func_writeGeo)
  - [objToGeo()](#IO__geo_py_func_objToGeo)
  - [geoLegacyToGeo()](#IO__geo_py_func_geoLegacyToGeo)
  - [_readGeo()](#IO__geo_py_func__readGeo)
  - [_roundPolygons()](#IO__geo_py_func__roundPolygons)
  - [_readGeoLegacy()](#IO__geo_py_func__readGeoLegacy)

---

### 🔧 Functions
###### <a id='IO__geo_py_func_writeGeo'></a>`writeGeo`
- **Type:** Function
- **Parameters:** file_path: Any, model: Any, geoList: Any, mask: Any
- **Returns:** :
    geo file string
- **Comments:**
  > Function:
  > Get a *.geo file for the geometry library in the model
  > 
  > .geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
  > cateories of the surface (polygon type cat):
  > -2 == ignore faces (would not be included in calculation)
  > -1 == shading faces (included as shading element)
  > 0 == opaque surface
  > 1 == translucent surface
  > 2 == the air wall
  > 3 == wall element.MoosasWall
  > 4 == plane element.MoosasFace
  > 5 == glazing element.MoosasGlazing
  > 6 == skylight element.MoosasSkylight
  > 
  > The .geo file format is:
  > f,{polygon type cat},{polygon number idd}
  > fn, {normal x}, {normal y}, {normal z}
  > fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
  > ...
  > fv,{vertex nx},{vertex ny},{vertex nz}
  > fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
  > fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
  > ;
  > A face should end with ';'
  > 
  > For example, there are two vertical faces with two openings with a positive x-axis normal vector:
  > f,1,0
  > fn,1.0,0.0,0.0
  > fv,15.5,10.0,2.2
  > fv,15.5,10.0,0.0
  > fv,15.5,10.8,0.0
  > fv,15.5,10.8,2.2
  > fh,0,15.5,10.1,1.8
  > fh,0,15.5,10.1,0.9
  > fh,0,15.5,10.3,0.9
  > fh,0,15.5,10.3,1.8
  > fh,1,15.5,10.5,1.8
  > fh,1,15.5,10.5,0.9
  > fh,1,15.5,10.7,0.9
  > fh,1,15.5,10.7,1.8
  > ;
  > f,1,0
  > fn,1.0,0.0,0.0
  > fv,12.5,10.0,2.2
  > fv,12.5,10.0,0.0
  > fv,12.5,10.8,0.0
  > fv,12.5,10.8,2.2
  > fh,0,12.5,10.1,1.8
  > fh,0,12.5,10.1,0.9
  > fh,0,12.5,10.3,0.9
  > fh,0,12.5,10.3,1.8
  > fh,1,12.5,10.5,1.8
  > fh,1,12.5,10.5,0.9
  > fh,1,12.5,10.7,0.9
  > fh,1,12.5,10.7,1.8
  > ;
  > ...
  > 
  > Args:
  >     file_path(str): output geo file path
  >     model(MoosasModel): model to export
  >     geoList(list(MoosasGeometry)): list of geometry objects to export
  >     mask(list[int]): mask for the geometry index in the geometry library. default is None
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     geo file string

---

###### <a id='IO__geo_py_func_objToGeo'></a>`objToGeo`
- **Type:** Function
- **Parameters:** file_path: Any, geo_path: Any
- **Returns:** :
    None
- **Comments:**
  > Function:
  > Transform an *.obj file to *.geo file.
  > 
  > Args:
  >     file_path(str): *.obj file path
  >     geo_path(str): *.geo file path
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     None

---

###### <a id='IO__geo_py_func_geoLegacyToGeo'></a>`geoLegacyToGeo`
- **Type:** Function
- **Parameters:** file_path: Any, geo_path: Any
- **Returns:** :
    None
- **Comments:**
  > Function:
  > Transform a legacy *.geo file to new *.geo file.
  > 
  > Args:
  >     file_path(str): legacy *.geo file path
  >     geo_path(str): *.geo file path. if None we will overwrite the original file.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     None

---

###### <a id='IO__geo_py_func__readGeo'></a>`_readGeo`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** list of MoosasGeometry
    A list of MoosasGeometry instances constructed from the parsed faces in the .geo file. 
    Each geometry includes vertex data, normal vectors, category, ID, and optional holes. 
    Invalid geometries are skipped with a warning printed to stdout.

.geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
The .geo file format is:
f,{polygon type cat},{polygon number idd}
fn, {normal x}, {normal y}, {normal z}
fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
...
fv,{vertex nx},{vertex ny},{vertex nz}
fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
;
A face should end with ';'

For example, there are two vertical faces with two openings with a positive x-axis normal vector:
f,1,0
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
f,-1,0
fn,1.0,0.0,0.0
fv,12.5,10.0,2.2
fv,12.5,10.0,0.0
fv,12.5,10.8,0.0
fv,12.5,10.8,2.2
fh,0,12.5,10.1,1.8
fh,0,12.5,10.1,0.9
fh,0,12.5,10.3,0.9
fh,0,12.5,10.3,1.8
fh,1,12.5,10.5,1.8
fh,1,12.5,10.5,0.9
fh,1,12.5,10.7,0.9
fh,1,12.5,10.7,1.8
;
...
- **Comments:**
  > Function:
  > Read a .geo file and return a list of MoosasGeometry objects representing the geometric data.
  > Parameters:
  > file_path : str
  >     Path to the .geo file to be read. The .geo format is a custom simplified format used by moosasPy 
  >     for efficient I/O, containing polygon definitions, normals, vertices, and apertures.
  > 
  > Returns
  > list of MoosasGeometry
  >     A list of MoosasGeometry instances constructed from the parsed faces in the .geo file. 
  >     Each geometry includes vertex data, normal vectors, category, ID, and optional holes. 
  >     Invalid geometries are skipped with a warning printed to stdout.
  > 
  > .geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
  > The .geo file format is:
  > f,{polygon type cat},{polygon number idd}
  > fn, {normal x}, {normal y}, {normal z}
  > fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
  > ...
  > fv,{vertex nx},{vertex ny},{vertex nz}
  > fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
  > fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
  > ;
  > A face should end with ';'
  > 
  > For example, there are two vertical faces with two openings with a positive x-axis normal vector:
  > f,1,0
  > fn,1.0,0.0,0.0
  > fv,15.5,10.0,2.2
  > fv,15.5,10.0,0.0
  > fv,15.5,10.8,0.0
  > fv,15.5,10.8,2.2
  > fh,0,15.5,10.1,1.8
  > fh,0,15.5,10.1,0.9
  > fh,0,15.5,10.3,0.9
  > fh,0,15.5,10.3,1.8
  > fh,1,15.5,10.5,1.8
  > fh,1,15.5,10.5,0.9
  > fh,1,15.5,10.7,0.9
  > fh,1,15.5,10.7,1.8
  > ;
  > f,-1,0
  > fn,1.0,0.0,0.0
  > fv,12.5,10.0,2.2
  > fv,12.5,10.0,0.0
  > fv,12.5,10.8,0.0
  > fv,12.5,10.8,2.2
  > fh,0,12.5,10.1,1.8
  > fh,0,12.5,10.1,0.9
  > fh,0,12.5,10.3,0.9
  > fh,0,12.5,10.3,1.8
  > fh,1,12.5,10.5,1.8
  > fh,1,12.5,10.5,0.9
  > fh,1,12.5,10.7,0.9
  > fh,1,12.5,10.7,1.8
  > ;
  > ...
  > Returns:
  > list of MoosasGeometry
  >     A list of MoosasGeometry instances constructed from the parsed faces in the .geo file. 
  >     Each geometry includes vertex data, normal vectors, category, ID, and optional holes. 
  >     Invalid geometries are skipped with a warning printed to stdout.
  > 
  > .geo is a moosasPy dedicated file format, which uses a simplified file structure to increase I/O speed......
  > The .geo file format is:
  > f,{polygon type cat},{polygon number idd}
  > fn, {normal x}, {normal y}, {normal z}
  > fv, {vertex 1x}, {vertex 1y}, {vertex 1z}
  > ...
  > fv,{vertex nx},{vertex ny},{vertex nz}
  > fh,{aperture number},{vertex 1x},{vertex 1y},{vertex 1z}
  > fh,{aperture number},{vertex nx},{vertex ny},{vertex nz}
  > ;
  > A face should end with ';'
  > 
  > For example, there are two vertical faces with two openings with a positive x-axis normal vector:
  > f,1,0
  > fn,1.0,0.0,0.0
  > fv,15.5,10.0,2.2
  > fv,15.5,10.0,0.0
  > fv,15.5,10.8,0.0
  > fv,15.5,10.8,2.2
  > fh,0,15.5,10.1,1.8
  > fh,0,15.5,10.1,0.9
  > fh,0,15.5,10.3,0.9
  > fh,0,15.5,10.3,1.8
  > fh,1,15.5,10.5,1.8
  > fh,1,15.5,10.5,0.9
  > fh,1,15.5,10.7,0.9
  > fh,1,15.5,10.7,1.8
  > ;
  > f,-1,0
  > fn,1.0,0.0,0.0
  > fv,12.5,10.0,2.2
  > fv,12.5,10.0,0.0
  > fv,12.5,10.8,0.0
  > fv,12.5,10.8,2.2
  > fh,0,12.5,10.1,1.8
  > fh,0,12.5,10.1,0.9
  > fh,0,12.5,10.3,0.9
  > fh,0,12.5,10.3,1.8
  > fh,1,12.5,10.5,1.8
  > fh,1,12.5,10.5,0.9
  > fh,1,12.5,10.7,0.9
  > fh,1,12.5,10.7,1.8
  > ;
  > ...

---

###### <a id='IO__geo_py_func__roundPolygons'></a>`_roundPolygons`
- **Type:** Function
- **Parameters:** polygons: np.ndarray[pygeos.Geometry], precision: float
- **Returns:** :
        np.ndarray rounded polygons
- **Comments:**
  > Function:
  > round the coordinates of polygons according to precision.
  > graping the next near coordinates (x,y,z) to the past if their distance is less than precision.
  > 
  >     Args:
  >         polygons(np.ndarray[pygeos.Geometry]): polygons in np.ndarray format
  >         precision(float): round precision, usually would be geom.POINT_PRECISION
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >         np.ndarray rounded polygons

---

###### <a id='IO__geo_py_func__readGeoLegacy'></a>`_readGeoLegacy`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** a list of MoosasGeometry objects.

Parameters
file_path : str
    Path to the .geo file to be read. The file contains geometric data in a custom plain text format,
    with face type (cat), ID, normal vector, and vertices defined per face.

Returns
list[MoosasGeometry]
    A list of MoosasGeometry instances constructed from the parsed faces, each containing
    geometry, identifier, normal vector, and category as specified in the input file.
- **Comments:**
  > Function:
  > Reads a legacy .geo file format used by moosasPy and
  > Parameters:
  > file_path : str
  >     Path to the .geo file to be read. The file contains geometric data in a custom plain text format,
  >     with face type (cat), ID, normal vector, and vertices defined per face.
  > 
  > Returns
  > list[MoosasGeometry]
  >     A list of MoosasGeometry instances constructed from the parsed faces, each containing
  >     geometry, identifier, normal vector, and category as specified in the input file.
  > Returns:
  > a list of MoosasGeometry objects.
  > 
  > Parameters
  > file_path : str
  >     Path to the .geo file to be read. The file contains geometric data in a custom plain text format,
  >     with face type (cat), ID, normal vector, and vertices defined per face.
  > 
  > Returns
  > list[MoosasGeometry]
  >     A list of MoosasGeometry instances constructed from the parsed faces, each containing
  >     geometry, identifier, normal vector, and category as specified in the input file.

---


## 📄 File: IO\_idf.py
<a id='IO__idf_py'></a>

### Contents
- Functions:
  - [writeIDF()](#IO__idf_py_func_writeIDF)
  - [encodeURI()](#IO__idf_py_func_encodeURI)
  - [IDFtoOWL()](#IO__idf_py_func_IDFtoOWL)
  - [OWLtoIDF()](#IO__idf_py_func_OWLtoIDF)

---

### 🔧 Functions
###### <a id='IO__idf_py_func_writeIDF'></a>`writeIDF`
- **Type:** Function
- **Parameters:** outputPath: str, model: Any
- **Returns:** None
    This function does not return any value. It writes the IDF file to the specified path and prints progress information.
- **Comments:**
  > Function:
  > Write an EnergyPlus Input Data File (IDF) based on a MoosasModel.
  > Parameters:
  > outputPath : str
  >     Path to save the generated IDF file. The directory must be writable.
  > model : MoosasModel
  >     A model instance containing building geometry and settings to be converted into IDF format.
  >     Must provide methods `getAllFaces`, `spaceIdDict`, and `spaceList`, and associated attributes
  >     for space and surface properties.
  > 
  > Returns
  > None
  >     This function does not return any value. It writes the IDF file to the specified path and prints progress information.
  > Returns:
  > None
  >     This function does not return any value. It writes the IDF file to the specified path and prints progress information.

---

###### <a id='IO__idf_py_func_encodeURI'></a>`encodeURI`
- **Type:** Function
- **Parameters:** hint: Any
- **Returns:** rdflib.term.URIRef
    A URIRef object created from the processed hint string.

Raises
Exception
    If the input string contains an exclamation mark ('!').
- **Comments:**
  > Function:
  > Encode a string into a URI by replacing spaces with underscores and converting to a URIRef object.
  > Parameters:
  > hint : str
  >     The input string to be encoded into a URI. It will be stripped of leading/trailing whitespace 
  >     and have spaces replaced with underscores.
  > 
  > Returns
  > rdflib.term.URIRef
  >     A URIRef object created from the processed hint string.
  > 
  > Raises
  > Exception
  >     If the input string contains an exclamation mark ('!').
  > Returns:
  > rdflib.term.URIRef
  >     A URIRef object created from the processed hint string.
  > 
  > Raises
  > Exception
  >     If the input string contains an exclamation mark ('!').

---

###### <a id='IO__idf_py_func_IDFtoOWL'></a>`IDFtoOWL`
- **Type:** Function
- **Parameters:** idfTemplatePath: Any
- **Returns:** Graph
        An RDFlib Graph object representing the IDF data as an OWL ontology. The graph includes classes,
        properties, and instances derived from the IDF file, with semantics aligned to the EnergyPlus
        InputOutputReference documentation. Subjects are defined under the 'idf' namespace.
- **Comments:**
  > Function:
  > Translate an IDF (Input Data File) knowledge base into an OWL (Web Ontology Language) RDF graph.
  > Parameters:
  > idfTemplatePath : str
  >         Path to the IDF template file to be converted. The file contains building energy model input data
  >         structured according to EnergyPlus Input/Output Reference definitions.
  > 
  >     Returns
  >     Graph
  >         An RDFlib Graph object representing the IDF data as an OWL ontology. The graph includes classes,
  >         properties, and instances derived from the IDF file, with semantics aligned to the EnergyPlus
  >         InputOutputReference documentation. Subjects are defined under the 'idf' namespace.
  > Returns:
  > Graph
  >         An RDFlib Graph object representing the IDF data as an OWL ontology. The graph includes classes,
  >         properties, and instances derived from the IDF file, with semantics aligned to the EnergyPlus
  >         InputOutputReference documentation. Subjects are defined under the 'idf' namespace.

---

###### <a id='IO__idf_py_func_OWLtoIDF'></a>`OWLtoIDF`
- **Type:** Function
- **Parameters:** owl: Graph, outFile: Any
- **Returns:** IDF
    An IDF object representing the EnergyPlus input data file, populated with objects 
    derived from the input OWL graph and saved to the specified output path.
- **Comments:**
  > Function:
  > Convert an OWL ontology graph to an IDF (Input Data File) format used by EnergyPlus.
  > Parameters:
  > owl : Graph or str
  >     An RDFlib Graph object containing the OWL ontology data, or a string path to an OWL file.
  > outFile : str
  >     Path to the output file where the generated IDF will be saved.
  > 
  > Returns
  > IDF
  >     An IDF object representing the EnergyPlus input data file, populated with objects 
  >     derived from the input OWL graph and saved to the specified output path.
  > Returns:
  > IDF
  >     An IDF object representing the EnergyPlus input data file, populated with objects 
  >     derived from the input OWL graph and saved to the specified output path.

---


## 📄 File: IO\_json.py
<a id='IO__json_py'></a>

### Contents
- Functions:
  - [writeJson()](#IO__json_py_func_writeJson)
  - [writeGeojson()](#IO__json_py_func_writeGeojson)
  - [_readGeojson()](#IO__json_py_func__readGeojson)

---

### 🔧 Functions
###### <a id='IO__json_py_func_writeJson'></a>`writeJson`
- **Type:** Function
- **Parameters:** file_path: Any, model: Any
- **Returns:** :
    json string of the file
- **Comments:**
  > Function:
  > Get a json file describe the space topology.
  > we have 3 different level of data:
  > 
  > faces:{
  >     Uid: unique id, which is random generated.
  >     faceId: the faceId of the faces in the geo data or file.
  >     level: building level where the element locates.
  >     offset: the element's offset from the building level.
  >     area: the total surface area.
  >     glazingId: glazing faceId in the geo data or file.
  >     height: level + offset
  >     normal: element's normal, point to exterior.
  >     external: whether the element is connected to exterior.
  >     space: the space id which this element belongs to.
  >     }
  > 
  > topology:{
  >     floor:{faces:[{faces}..]}
  >     edge:{faces:[{faces}..]}
  >     ceiling:{faces:[{faces}..]}
  > }
  > 
  > space:{
  >     id: unique space id, which is calculated based on the shape & location of the space. It is the same in each we call transfrom()
  >     area: space area
  >     height: space height
  >     boundary: space 1 level space boundary (1LSB){pt:[[x,y,z]...]}
  >     internalMass: the internalMass in the space {faces:[{faces}..]}
  >     topology:{topology}
  >     neighbor: the neighborhood space share the same 2 level space boundary (2LSB)
  >         [{
  >             faceId: the faceId of the 2LSB in the geo file,
  >             id: the neighbor space id
  >         }]
  >     settings: thermal settings of the space in dictionary, you can find their names in .thermal.settings
  >     void: the void inside the space, also formatted in space[{space}..]
  > }
  > 
  > Args:
  >     file_path(str): output space json file path
  >     model(MoosasModel): model to export
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     json string of the file

---

###### <a id='IO__json_py_func_writeGeojson'></a>`writeGeojson`
- **Type:** Function
- **Parameters:** file_path: Any, model: Any
- **Returns:** :
    json file string
- **Comments:**
  > Function:
  > Get a geojson file for the geometry library in the model
  > 
  > features = [
  >     {
  >         "type": "Feature",
  >         "properties": {
  >             "normal": geometries' normal,
  >             "id": geometries' faceId,
  >             "is_glazing": geo.category
  >         },
  > 
  >         "geometries": {
  >             "type": "Polygon",
  >             "coordinates": coordinates for each polygon
  >         }
  >     }
  > ]
  > 
  > Args:
  >     file_path(str): output geojson file path
  >     model(MoosasModel): model to export
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     json file string

---

###### <a id='IO__json_py_func__readGeojson'></a>`_readGeojson`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** list[MoosasGeometry]
    A list of MoosasGeometry objects parsed from the GeoJSON file.
- **Comments:**
  > Function:
  > Read a GeoJSON file and return a list of MoosasGeometry objects.
  > Parameters:
  > file_path : str
  >     Path to the GeoJSON file to be read.
  > 
  > Returns
  > list[MoosasGeometry]
  >     A list of MoosasGeometry objects parsed from the GeoJSON file.
  > Returns:
  > list[MoosasGeometry]
  >     A list of MoosasGeometry objects parsed from the GeoJSON file.

---


## 📄 File: IO\_obj.py
<a id='IO__obj_py'></a>

### Contents
- Functions:
  - [_readObj()](#IO__obj_py_func__readObj)
  - [_roundPolygons()](#IO__obj_py_func__roundPolygons)

---

### 🔧 Functions
###### <a id='IO__obj_py_func__readObj'></a>`_readObj`
- **Type:** Function
- **Parameters:** file_path: Any
- **Returns:** list[MoosasGeometry]
    A list of MoosasGeometry instances constructed from the geometry, material properties,
    and face data parsed from the OBJ and MTL files. Each MoosasGeometry object contains
    polygonal face data, identifier, normal vector, and category based on material transparency.
- **Comments:**
  > Function:
  > Reads an OBJ file and its associated MTL file to construct a list of MoosasGeometry objects.
  > Parameters:
  > file_path : str
  >     Path to the input .obj file. The corresponding .mtl file is expected to be referenced 
  >     within the OBJ file and located in the same directory.
  > 
  > Returns
  > list[MoosasGeometry]
  >     A list of MoosasGeometry instances constructed from the geometry, material properties,
  >     and face data parsed from the OBJ and MTL files. Each MoosasGeometry object contains
  >     polygonal face data, identifier, normal vector, and category based on material transparency.
  > Returns:
  > list[MoosasGeometry]
  >     A list of MoosasGeometry instances constructed from the geometry, material properties,
  >     and face data parsed from the OBJ and MTL files. Each MoosasGeometry object contains
  >     polygonal face data, identifier, normal vector, and category based on material transparency.

---

###### <a id='IO__obj_py_func__roundPolygons'></a>`_roundPolygons`
- **Type:** Function
- **Parameters:** polygons: np.ndarray[pygeos.Geometry], precision: float
- **Returns:** :
        np.ndarray rounded polygons
- **Comments:**
  > Function:
  > round the coordinates of polygons according to precision.
  > graping the next near coordinates (x,y,z) to the past if their distance is less than precision.
  > 
  >     Args:
  >         polygons(np.ndarray[pygeos.Geometry]): polygons in np.ndarray format
  >         precision(float): round precision, usually would be geom.POINT_PRECISION
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >         np.ndarray rounded polygons

---


## 📄 File: IO\_rdf.py
<a id='IO__rdf_py'></a>

### Contents
- Classes:
  - [MoosasGraph](#IO__rdf_py_class_MoosasGraph)
- Functions:
  - [writeRDF()](#IO__rdf_py_func_writeRDF)
  - [loadRDF()](#IO__rdf_py_func_loadRDF)

---

### 📦 Class: MoosasGraph
<a id='IO__rdf_py_class_MoosasGraph'></a>
**Description:** No class documentation.

#### Methods
###### <a id='IO__rdf_py_class_MoosasGraph_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasModel, dumpUseless: Any, ExportIFC: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize the MoosasGraph instance with optional model encoding and namespace bindings.
  > Parameters:
  > model : MoosasModel, optional
  >     The model to encode into the graph. If provided, the model is encoded using the `encodeModel` method.
  >     Default is None.
  > dumpUseless : bool, default True
  >     If True, useless or redundant information is excluded during model encoding. 
  >     This parameter is passed to the `encodeModel` method.
  > ExportIFC : bool, default False
  >     If True, enables IFC-specific export features during model encoding.
  >     This parameter is passed to the `encodeModel` method.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_load'></a>`load`
- **Type:** Class Method
- **Parameters:** cls: Any, filePath: Any, fileFormat: Any
- **Returns:** rdflib.Graph
    A new instance of the class populated with the parsed data.
- **Comments:**
  > Function:
  > Load a graph from a file.
  > Parameters:
  > filePath : str
  >     Path to the file containing the serialized graph.
  > fileFormat : str, optional
  >     Serialization format of the file (e.g., 'turtle', 'xml', 'n3'). Default is 'turtle'.
  > 
  > Returns
  > rdflib.Graph
  >     A new instance of the class populated with the parsed data.
  > Returns:
  > rdflib.Graph
  >     A new instance of the class populated with the parsed data.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeModel'></a>`encodeModel`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasModel, dumpUseless: Any, ExportIFC: Any
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Encode a MoosasModel into the ontology representation.
  > Parameters:
  > model : MoosasModel
  >     The model to be encoded, containing building elements, geometry, spaces, and other data.
  > dumpUseless : bool, optional
  >     If True, retrieves all faces including those marked as useless; otherwise, uses only specific element lists.
  >     Default is True.
  > ExportIFC : bool, optional
  >     If True, enables IFC-specific export logic during encoding. Default is False.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_buildOntology'></a>`buildOntology`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasModel
- **Returns:** None
    This function modifies the internal state of the object by adding RDF triples to represent 
    the ontology but does not return any value.
- **Comments:**
  > Function:
  > Constructs an ontology hierarchy for classes in Moosas based on the provided model.
  > Parameters:
  > model : MoosasModel
  >     The input model containing building templates and other information used to construct 
  >     the ontology. The model's `buildingTemplate` attribute is accessed to extract zone 
  >     information, which is used to define properties and relationships in the ontology.
  > 
  > Returns
  > None
  >     This function modifies the internal state of the object by adding RDF triples to represent 
  >     the ontology but does not return any value.
  > Returns:
  > None
  >     This function modifies the internal state of the object by adding RDF triples to represent 
  >     the ontology but does not return any value.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_ifcOntology'></a>`ifcOntology`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
    This function does not return any value. It modifies the state of the instance by adding 
    RDF triples representing IFC4.0 ontology elements and their relationships.
- **Comments:**
  > Function:
  > Add IFC4.0 ontology definitions to the current graph for data coupling and semantic interoperability.
  > Parameters:
  > self : object
  >     The instance of the class containing namespaces (ifc, rdfs, moosas) and an `add` method 
  >     for adding RDF triples. It is assumed that this object has attributes `ifc`, `rdfs`, 
  >     `moosas`, and a method `add(triple)` that accepts an RDF triple.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the state of the instance by adding 
  >     RDF triples representing IFC4.0 ontology elements and their relationships.
  > Returns:
  > None
  >     This function does not return any value. It modifies the state of the instance by adding 
  >     RDF triples representing IFC4.0 ontology elements and their relationships.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeWeather'></a>`encodeWeather`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasModel
- **Returns:** None
    This function does not return any value. It modifies the internal RDF graph by adding weather-related triples.
- **Comments:**
  > Function:
  > Encode weather data from a MoosasModel into RDF triples.
  > Parameters:
  > self : object
  >     The instance of the class containing this method, providing access to RDF graph and namespaces.
  > model : MoosasModel
  >     An instance of MoosasModel containing weather data to be encoded, including location and file information.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the internal RDF graph by adding weather-related triples.
  > Returns:
  > None
  >     This function does not return any value. It modifies the internal RDF graph by adding weather-related triples.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeProgram'></a>`encodeProgram`
- **Type:** Instance Method
- **Parameters:** self: Any, pgName: str, pgDict: dict
- **Returns:** None
    This function modifies the instance's RDF graph in place and does not return a value.
- **Comments:**
  > Function:
  > Encode a program into the RDF graph with associated metadata.
  > Parameters:
  > pgName : str
  >     The name of the program, used as a term and UID in the RDF graph.
  > pgDict : dict
  >     A dictionary containing metadata or properties of the program, where keys are 
  >     predicate names and values are corresponding literals to be added as triples.
  > 
  > Returns
  > None
  >     This function modifies the instance's RDF graph in place and does not return a value.
  > Returns:
  > None
  >     This function modifies the instance's RDF graph in place and does not return a value.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeGeo'></a>`encodeGeo`
- **Type:** Instance Method
- **Parameters:** self: Any, geo: MoosasGeometry
- **Returns:** None
    This function does not return a value. It modifies the internal state by adding 
    RDF triples to the instance.
- **Comments:**
  > Function:
  > Encode a geometric object into RDF triples.
  > Parameters:
  > geo : MoosasGeometry
  >     The geometric object to encode, containing attributes such as faceId, category, 
  >     boundary, and holes. The object is converted into RDF triples representing 
  >     its properties and geometry in WKT format.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the internal state by adding 
  >     RDF triples to the instance.
  > Returns:
  > None
  >     This function does not return a value. It modifies the internal state by adding 
  >     RDF triples to the instance.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeElement'></a>`encodeElement`
- **Type:** Instance Method
- **Parameters:** self: Any, Element: MoosasElement, typeName: str, mask: Any, ExportIFC: Any
- **Returns:** None
    This function does not return a value. It modifies the internal RDF graph by adding triples.
- **Comments:**
  > Function:
  > Encode a MoosasElement into RDF triples within the graph.
  > Parameters:
  > Element : MoosasElement
  >     The element to be encoded, containing properties such as Uid, offset, area, normal, etc.
  > typeName : str, optional
  >     The type name of the element (e.g., 'rawElement', 'Wall', 'Glazing'), used to assign semantic type. Default is "rawElement".
  > mask : set or list, optional
  >     A collection of neighbor element identifiers to filter which neighbors are added. If provided, only neighbors in the mask are included. Default is None.
  > ExportIFC : bool, optional
  >     If True, generates IFC-compliant RDF triples for the element, including GlobalID and corresponding IFC types. Default is False.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the internal RDF graph by adding triples.
  > Returns:
  > None
  >     This function does not return a value. It modifies the internal RDF graph by adding triples.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeStorey'></a>`encodeStorey`
- **Type:** Instance Method
- **Parameters:** self: Any, model: MoosasModel
- **Returns:** None
    This function modifies the RDF graph in place and does not return any value.
- **Comments:**
  > Function:
  > Encode building storeys and their associated spaces into the RDF graph.
  > Parameters:
  > self : object
  >     The instance of the class containing the method. Holds the RDF graph and namespaces.
  > model : MoosasModel
  >     The model containing level and space information to be encoded. Must have `levelList` 
  >     and `spaceList` attributes, where `levelList` contains elevation levels and `spaceList` 
  >     contains space objects with 'level' and 'id' properties.
  > 
  > Returns
  > None
  >     This function modifies the RDF graph in place and does not return any value.
  > Returns:
  > None
  >     This function modifies the RDF graph in place and does not return any value.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encode2LSB'></a>`encode2LSB`
- **Type:** Instance Method
- **Parameters:** self: Any, spaceId: str, element: MoosasElement
- **Returns:** None
    This function does not return a value. It modifies the internal state by adding RDF triples
    representing the IfcRelSpaceBoundary2ndLevel relationship.
- **Comments:**
  > Function:
  > Encode a building element into a second-level space boundary representation using RDF triples.
  > Parameters:
  > spaceId : str
  >     Identifier for the space, used to construct URIs and determine spatial relationships.
  >     Special value 'outer' indicates an external spatial element.
  > element : MoosasElement
  >     The building element to encode, containing properties such as Uid, category, level,
  >     normal vector, space membership, and glazing elements.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the internal state by adding RDF triples
  >     representing the IfcRelSpaceBoundary2ndLevel relationship.
  > Returns:
  > None
  >     This function does not return a value. It modifies the internal state by adding RDF triples
  >     representing the IfcRelSpaceBoundary2ndLevel relationship.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_encodeSpace'></a>`encodeSpace`
- **Type:** Instance Method
- **Parameters:** self: Any, space: MoosasSpace, ExportIFC: Any
- **Returns:** None
    This function does not return any value. It modifies the graph state by adding RDF triples.
- **Comments:**
  > Function:
  > Encode a MoosasSpace object into RDF triples within the graph, optionally exporting to IFC format.
  > Parameters:
  > space : MoosasSpace
  >     The space object to be encoded, containing properties such as id, area, height, ceiling, floor, edge, and voids.
  > ExportIFC : bool, optional
  >     If True, exports the space and associated elements to IFC-compatible RDF triples. Default is False.
  > 
  > Returns
  > None
  >     This function does not return any value. It modifies the graph state by adding RDF triples.
  > Returns:
  > None
  >     This function does not return any value. It modifies the graph state by adding RDF triples.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_decodeGeo'></a>`decodeGeo`
- **Type:** Instance Method
- **Parameters:** self: Any, geoUri: Any, model: MoosasModel
- **Returns:** MoosasGeometry
    A MoosasGeometry object representing the decoded geometry, including face, face ID, category, and any holes.
- **Comments:**
  > Function:
  > Decode a geographic URI into a MoosasGeometry object.
  > Parameters:
  > geoUri : str or rdflib.term.URIRef
  >     The geographic URI to decode. If a string is provided, it will be converted to a URIRef.
  > model : MoosasModel, optional
  >     An optional model used to look up the face by face ID. If provided and a matching geometry is found, it will be returned directly.
  > 
  > Returns
  > MoosasGeometry
  >     A MoosasGeometry object representing the decoded geometry, including face, face ID, category, and any holes.
  > Returns:
  > MoosasGeometry
  >     A MoosasGeometry object representing the decoded geometry, including face, face ID, category, and any holes.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_decodeElement'></a>`decodeElement`
- **Type:** Instance Method
- **Parameters:** self: Any, elementUri: Any, model: MoosasModel
- **Returns:** MoosasElement or None
    The decoded MoosasElement instance if found or successfully created; otherwise, None.
- **Comments:**
  > Function:
  > Decode an element from its URI by retrieving and interpreting semantic information.
  > Parameters:
  > elementUri : str or rdflib.term.URIRef
  >     The URI reference of the element to decode. If a string is provided, it will be converted to a URIRef.
  > model : MoosasModel, optional
  >     The model instance containing element lists (e.g., faceList, wallList). Used to search for existing elements. 
  >     If not provided, a new element will be constructed based on retrieved properties.
  > 
  > Returns
  > MoosasElement or None
  >     The decoded MoosasElement instance if found or successfully created; otherwise, None.
  > Returns:
  > MoosasElement or None
  >     The decoded MoosasElement instance if found or successfully created; otherwise, None.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_isClass'></a>`isClass`
- **Type:** Instance Method
- **Parameters:** self: Any, _from: str, _class: URIRef
- **Returns:** bool
    True if the subject has the specified class as its type, False otherwise.
- **Comments:**
  > Function:
  > Check if the given subject is an instance of the specified class.
  > Parameters:
  > _from : str
  >     The subject URI as a string.
  > _class : rdflib.term.URIRef
  >     The class URI to check against, represented as a URIRef.
  > 
  > Returns
  > bool
  >     True if the subject has the specified class as its type, False otherwise.
  > Returns:
  > bool
  >     True if the subject has the specified class as its type, False otherwise.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_getObject'></a>`getObject`
- **Type:** Instance Method
- **Parameters:** self: Any, _from: Any, _property: Any
- **Returns:** list
    A list of objects obtained by collecting unique values from the `objects` generator and converting them using `mixItemListToObject`.
- **Comments:**
  > Function:
  > Get a list of objects associated with a given subject and property.
  > Parameters:
  > self : object
  >     The instance of the class containing the `objects` method and `mixItemListToObject` function.
  > _from : hashable
  >     The subject or source entity from which to retrieve associated objects.
  > _property : hashable
  >     The property or predicate used to filter the relationships.
  > 
  > Returns
  > list
  >     A list of objects obtained by collecting unique values from the `objects` generator and converting them using `mixItemListToObject`.
  > Returns:
  > list
  >     A list of objects obtained by collecting unique values from the `objects` generator and converting them using `mixItemListToObject`.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_getSubject'></a>`getSubject`
- **Type:** Instance Method
- **Parameters:** self: Any, _property: Any, _to: Any
- **Returns:** list
    A list of subject objects obtained from matching triples, with mixed items converted into objects.
- **Comments:**
  > Function:
  > Get a list of subjects for a given property and object, returned as a mixed item list converted to objects.
  > Parameters:
  > _property : str or rdflib.term.URIRef
  >     The property (predicate) to match in the RDF triples.
  > _to : str or rdflib.term.Identifier
  >     The object value to match in the RDF triples.
  > 
  > Returns
  > list
  >     A list of subject objects obtained from matching triples, with mixed items converted into objects.
  > Returns:
  > list
  >     A list of subject objects obtained from matching triples, with mixed items converted into objects.

---

###### <a id='IO__rdf_py_class_MoosasGraph_method_getRelate'></a>`getRelate`
- **Type:** Instance Method
- **Parameters:** self: Any, node: Any
- **Returns:** list
    A list of nodes that are related to the input node, either as objects in subject-predicate-node triples or as subjects in node-predicate-object triples. Duplicates are removed using a set.
- **Comments:**
  > Function:
  > Get all nodes related to the given node through outgoing or incoming triples.
  > Parameters:
  > node : hashable
  >     The node for which related nodes are to be retrieved. Can be any hashable type representing a subject or object in the triples.
  > 
  > Returns
  > list
  >     A list of nodes that are related to the input node, either as objects in subject-predicate-node triples or as subjects in node-predicate-object triples. Duplicates are removed using a set.
  > Returns:
  > list
  >     A list of nodes that are related to the input node, either as objects in subject-predicate-node triples or as subjects in node-predicate-object triples. Duplicates are removed using a set.

---

### 🔧 Functions
###### <a id='IO__rdf_py_func_writeRDF'></a>`writeRDF`
- **Type:** Function
- **Parameters:** model: MoosasModel, out_path: str, fileFormat: Any, dumpUseless: Any, ExportIFC: Any
- **Returns:** MoosasGraph
    The generated MoosasGraph object that was serialized to the file.
- **Comments:**
  > Function:
  > Serialize a MoosasModel to an RDF file in the specified format.
  > Parameters:
  > model : MoosasModel
  >     The MoosasModel instance to be serialized into RDF.
  > out_path : str
  >     The file path where the RDF output will be written.
  > fileFormat : str, optional
  >     The serialization format for the RDF output (e.g., 'turtle', 'xml'). Default is "turtle".
  > dumpUseless : bool, optional
  >     If True, includes unnecessary or auxiliary information in the output. Default is True.
  > ExportIFC : bool, optional
  >     If True, exports IFC-related data in the RDF output. Default is False.
  > 
  > Returns
  > MoosasGraph
  >     The generated MoosasGraph object that was serialized to the file.
  > Returns:
  > MoosasGraph
  >     The generated MoosasGraph object that was serialized to the file.

---

###### <a id='IO__rdf_py_func_loadRDF'></a>`loadRDF`
- **Type:** Function
- **Parameters:** input_path: str, fileFormat: Any
- **Returns:** MoosasModel
    A constructed MoosasModel instance populated with data from the RDF file.
- **Comments:**
  > Function:
  > Load RDF data from a file and construct a MoosasModel instance.
  > Parameters:
  > input_path : str
  >     Path to the input RDF file.
  > fileFormat : str, optional
  >     Format of the RDF file (default is "turtle").
  > 
  > Returns
  > MoosasModel
  >     A constructed MoosasModel instance populated with data from the RDF file.
  > Returns:
  > MoosasModel
  >     A constructed MoosasModel instance populated with data from the RDF file.

---


## 📄 File: IO\_xml.py
<a id='IO__xml_py'></a>

### Contents
- Functions:
  - [writeXml()](#IO__xml_py_func_writeXml)

---

### 🔧 Functions
###### <a id='IO__xml_py_func_writeXml'></a>`writeXml`
- **Type:** Function
- **Parameters:** file_path: Any, model: Any, writeGeometry: Any
- **Returns:** :
    ElementTree
- **Comments:**
  > Function:
  > Get a xml file describe the space topology.
  > we have 3 different level of data:
  > 
  > <face>
  >     <Uid> unique id, which is random generated. </Uid>
  >     <faceId> the faceId of the faces in the geo data or file. </faceId>
  >     <level> the faceId of the faces in the geo data or file. </level>
  >     <offset> the element's offset from the building level. </offset>
  >     <area> the total surface area. </area>
  >     <glazingId> glazing faceId in the geo data or file. </glazingId>
  >     <height> level + offset </height>
  >     <normal> element's normal, point to exterior. (x y z) </normal>
  >     <external> whether the element is connected to exterior. </external>
  >     <space> the space id which this element belongs to. </space>
  > </face>
  > 
  > <topology>
  >     <floor>
  >         <face>...</face>
  >     </floor>
  >     <ceiling>
  >         <face>...</face>
  >     </ceiling>
  >     <edge>
  >         <face>...</face>
  >     </edge>
  > </topology>
  > 
  > <space>
  >     <id>
  >         unique space id, which is calculated based on the shape & location of the space.
  >         It is the same in each we call transfrom()
  >     </id>
  >     <area> space area </area>
  >     <height> space height </height>
  >     <boundary> space 1 level space boundary (1LSB) {pt:[[x,y,z]...]}
  >         <pt>216.53 393.70 0.0</pt>
  >         <pt>... ... ...</pt>
  >         <pt>216.53 177.16 0.0</pt>
  >     </boundary>
  > 
  >     <internal_wall> the internalMass in the space
  >         <face>...</face>
  >     </internal_wall>
  >     <topology>
  >         <floor>...</floor>
  >         <ceiling>...</ceiling>
  >         <edge>...</edge>
  >     </topology>
  >     <neighbor> the neighborhood space share the same 2 level space boundary (2LSB)
  >         <faceId> the faceId of the 2LSB in the geo file, </faceId>
  >         <id> the neighbor space id </id>
  >     </neighbor>
  >     <setting> thermal settings of the space in dictionary, you can find their names in .thermal.settings
  >         ...
  >     </setting>
  >     <void> the void inside the space, also formatted in space[{space}..]
  >         ...
  >     </void>
  > </space>
  > 
  > Args:
  >     file_path(str): output space xml file path
  >     model(MoosasModel): model to export
  >     writeGeometry(bool): whether write geometry in the file
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > :
  >     ElementTree

---


## 📄 File: rad\radiance.py
<a id='rad_radiance_py'></a>

### Contents
- Functions:
  - [_meshToRadObject()](#rad_radiance_py_func__meshToRadObject)
  - [_materialLib()](#rad_radiance_py_func__materialLib)
  - [_getSky()](#rad_radiance_py_func__getSky)

---

### 🔧 Functions
###### <a id='rad_radiance_py_func__meshToRadObject'></a>`_meshToRadObject`
- **Type:** Function
- **Parameters:** geos: Any, material: Any, id: Any
- **Returns:** str
    Radiance-formatted string representation of the mesh geometry, including material,
    polygon identifiers, and vertex coordinates. Returns an empty string if no valid
    triangles are generated.
- **Comments:**
  > Function:
  > Convert a mesh geometry to a Radiance object string representation.
  > Parameters:
  > geos : pygeos.Geometry or list of pygeos.Geometry
  >     Input geometry or list of geometries to convert.
  > material : str
  >     Material name to assign to the Radiance object.
  > id : str
  >     Identifier prefix for the generated polygons.
  > 
  > Returns
  > str
  >     Radiance-formatted string representation of the mesh geometry, including material,
  >     polygon identifiers, and vertex coordinates. Returns an empty string if no valid
  >     triangles are generated.
  > Returns:
  > str
  >     Radiance-formatted string representation of the mesh geometry, including material,
  >     polygon identifiers, and vertex coordinates. Returns an empty string if no valid
  >     triangles are generated.

---

###### <a id='rad_radiance_py_func__materialLib'></a>`_materialLib`
- **Type:** Function
- **Parameters:** None
- **Returns:** str
    A string defining materials (plastic and glass) in Radiance format, including default_floor,
    default_roof, default_wall with specified reflectances, and a base glazing material.
- **Comments:**
  > Function:
  > Return a string containing Radiance material definitions for common building materials.
  > Returns:
  > str
  >     A string defining materials (plastic and glass) in Radiance format, including default_floor,
  >     default_roof, default_wall with specified reflectances, and a base glazing material.

---

###### <a id='rad_radiance_py_func__getSky'></a>`_getSky`
- **Type:** Function
- **Parameters:** date: datetime, skyType: Any, lat: Any, lon: Any, diff: Any
- **Returns:** str
    A formatted string containing the Radiance sky definition commands, including gensky command
    and associated glow and source elements for sky and ground.
- **Comments:**
  > Function:
  > Generate a Radiance sky description string for a given date and location.
  > Parameters:
  > date : datetime
  >     The date and time for which the sky is generated, used to determine month, day, and hour.
  > skyType : str
  >     Type of sky model to generate (e.g., "-c" for cloudy, other values for different sky types).
  > lat : float or str
  >     Latitude of the location in degrees, used in the sky generation command.
  > lon : float or str
  >     Longitude of the location in degrees, used in the sky generation command.
  > diff : float, optional
  >     Diffuse solar irradiance value (in W/m²). Used only if skyType is "-c". Default is 10000.
  > 
  > Returns
  > str
  >     A formatted string containing the Radiance sky definition commands, including gensky command
  >     and associated glow and source elements for sky and ground.
  > Returns:
  > str
  >     A formatted string containing the Radiance sky definition commands, including gensky command
  >     and associated glow and source elements for sky and ground.

---


## 📄 File: rad\radiation.py
<a id='rad_radiation_py'></a>

### Contents
- Functions:
  - [modelRadiation()](#rad_radiation_py_func_modelRadiation)
  - [spaceRadiation()](#rad_radiation_py_func_spaceRadiation)
  - [positionRadiation()](#rad_radiation_py_func_positionRadiation)
  - [rayTest()](#rad_radiation_py_func_rayTest)
  - [WriteRadGeo()](#rad_radiation_py_func_WriteRadGeo)

---

### 🔧 Functions
###### <a id='rad_radiation_py_func_modelRadiation'></a>`modelRadiation`
- **Type:** Function
- **Parameters:** model: Any, reflection: Any
- **Returns:** object
    The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad'
    values representing the total solar radiation for summer and winter periods.
- **Comments:**
  > Function:
  > Calculate radiation for each space in the model using a fast single-call method via MoosasRad.exe.
  > Parameters:
  > model : object
  >     The building model containing spaces, geometry, and sky data. Must have `spaceList`, 
  >     `cumSky['summerCumSky']`, `cumSky['winterCumSky']`, and settings attributes.
  > reflection : int, optional
  >     The number of reflections to consider in the radiation calculation. Default is 1.
  > 
  > Returns
  > object
  >     The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad'
  >     values representing the total solar radiation for summer and winter periods.
  > Returns:
  > object
  >     The input model with updated space settings including 'zone_summerrad' and 'zone_winterrad'
  >     values representing the total solar radiation for summer and winter periods.

---

###### <a id='rad_radiation_py_func_spaceRadiation'></a>`spaceRadiation`
- **Type:** Function
- **Parameters:** space: MoosasSpace, reflection: Any
- **Returns:** dict
    Updated settings dictionary of the space with 'zone_summerrad' and 'zone_winterrad' keys 
    representing total summer and winter radiation values weighted by window areas.
- **Comments:**
  > Function:
  > Calculate seasonal radiation for a space by aggregating aperture-level radiation contributions.
  > Parameters:
  > space : MoosasSpace
  >     The space object containing apertures (skylights or glazing) for which radiation is calculated.
  > reflection : float, optional
  >     Reflection coefficient used in radiation calculation. Default is 1.
  > 
  > Returns
  > dict
  >     Updated settings dictionary of the space with 'zone_summerrad' and 'zone_winterrad' keys 
  >     representing total summer and winter radiation values weighted by window areas.
  > Returns:
  > dict
  >     Updated settings dictionary of the space with 'zone_summerrad' and 'zone_winterrad' keys 
  >     representing total summer and winter radiation values weighted by window areas.

---

###### <a id='rad_radiation_py_func_positionRadiation'></a>`positionRadiation`
- **Type:** Function
- **Parameters:** positionRay: Ray | Iterable[Ray], sky: MoosasCumSky, model: Any, reflection: Any, geo_path: Any
- **Returns:** : Iterable[float]
The return value is unit in kWh/m2
- **Comments:**
  > Function:
  > Cumulative radiation for positions with factors.
  > The position are defined as Ray class with origins and directions.
  > list or ndarry or Ray can be given as positionRay.
  > The return value is unit in kWh/m2
  > Model or geoPath should be provided.
  > 
  > positionRay: Iterable[Ray] position(origin, factor) to test. Put as much as possible in one coll on this func.
  > sky: MoosasCumSky cumulative sky model we use in this func.
  > model: MoosasModel the reflectance test content.
  > reflection: how many reflection will be calculated. default 1
  > geoPath: optional *.geo file input for the test content.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > : Iterable[float]
  > The return value is unit in kWh/m2

---

###### <a id='rad_radiation_py_func_rayTest'></a>`rayTest`
- **Type:** Function
- **Parameters:** rays: Iterable[Ray], model: Any, geo_path: str, ray_path: str
- **Returns:** : Iterable[Ray | None]
if the intersection is valid, the reflection of the ray will be return.
If not, None will be add.
- **Comments:**
  > Function:
  > call MoosasRad.exe to test the ray face intersection and reflection.
  > if the ray hit a face: result ray will be the reflection ray of the input ray.
  > if the ray doesnt hit a face: result==None.
  > Model or geoPath should be provided.
  > 
  > rays: Iterable[Ray] ray to test. Put as much as possible rays in one coll on this func.
  > model: MoosasModel the reflectance test content.
  > geoPath: optional *.geo file input for the test content.
  > ray_path: option temp path for the ray file.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > : Iterable[Ray | None]
  > if the intersection is valid, the reflection of the ray will be return.
  > If not, None will be add.

---

###### <a id='rad_radiation_py_func_WriteRadGeo'></a>`WriteRadGeo`
- **Type:** Function
- **Parameters:** model: Any
- **Returns:** str
    The absolute file path to the generated .geo file.
- **Comments:**
  > Function:
  > Write a geometry file for the given model in Radiance format.
  > Parameters:
  > model : object
  >     The geometric model to be written to the Radiance .geo file. The exact type depends on the expected input of `writeGeo`, typically representing a 3D scene or geometry structure.
  > 
  > Returns
  > str
  >     The absolute file path to the generated .geo file.
  > Returns:
  > str
  >     The absolute file path to the generated .geo file.

---


## 📄 File: thermal\buildingFaces.py
<a id='thermal_buildingFaces_py'></a>

### Contents
- Functions:
  - [createThermalSurface()](#thermal_buildingFaces_py_func_createThermalSurface)
  - [createWindowSurface()](#thermal_buildingFaces_py_func_createWindowSurface)

---

### 🔧 Functions
###### <a id='thermal_buildingFaces_py_func_createThermalSurface'></a>`createThermalSurface`
- **Type:** Function
- **Parameters:** idf: IDF, element: MoosasElement, surfaceType: Any, Construction_Name: Any, Construction_Name_Window: Any
- **Returns:** list
    A list of IDF objects representing the created thermal surfaces, including interior paired surfaces and any associated window surfaces.
- **Comments:**
  > Function:
  > Create thermal surface(s) in an IDF model based on a MoosasElement.
  > Parameters:
  > idf : IDF
  >     The EnergyPlus IDF object to which the thermal surface will be added.
  > element : MoosasElement
  >     The geometric and spatial element used to define the thermal surface.
  > surfaceType : str, optional
  >     Type of the surface (e.g., 'Floor', 'Wall', 'Roof'). Default is 'Floor'.
  > Construction_Name : str, optional
  >     Name of the construction used for the main surface. Default is "Office_External_Wall".
  > Construction_Name_Window : str, optional
  >     Name of the construction used for window surfaces. Default is "Office_External_Window".
  > 
  > Returns
  > list
  >     A list of IDF objects representing the created thermal surfaces, including interior paired surfaces and any associated window surfaces.
  > Returns:
  > list
  >     A list of IDF objects representing the created thermal surfaces, including interior paired surfaces and any associated window surfaces.

---

###### <a id='thermal_buildingFaces_py_func_createWindowSurface'></a>`createWindowSurface`
- **Type:** Function
- **Parameters:** idf: IDF, element: MoosasElement, parentElement: MoosasElement, Construction_Name: Any
- **Returns:** list
    A list containing one or two FenestrationSurface:Detailed objects created in the IDF. 
    Returns two surfaces if the parent element is internal (not outer), otherwise returns one.
- **Comments:**
  > Function:
  > Create one or two FenestrationSurface:Detailed objects in an IDF file based on a given element and its parent.
  > Parameters:
  > idf : IDF
  >     The EnergyPlus IDF object to which the new fenestration surface(s) will be added.
  > element : MoosasElement
  >     The Moosas element representing the window or fenestration geometry.
  > parentElement : MoosasElement
  >     The parent Moosas element, typically a wall, that hosts the fenestration element.
  > Construction_Name : str, optional
  >     The name of the construction used for the fenestration surface. Default is "Office_External_Wall".
  > 
  > Returns
  > list
  >     A list containing one or two FenestrationSurface:Detailed objects created in the IDF. 
  >     Returns two surfaces if the parent element is internal (not outer), otherwise returns one.
  > Returns:
  > list
  >     A list containing one or two FenestrationSurface:Detailed objects created in the IDF. 
  >     Returns two surfaces if the parent element is internal (not outer), otherwise returns one.

---


## 📄 File: thermal\construction.py
<a id='thermal_construction_py'></a>

### Contents
- Classes:
  - [Construction](#thermal_construction_py_class_Construction)

---

### 📦 Class: Construction
<a id='thermal_construction_py_class_Construction'></a>
**Description:** No class documentation.

#### Methods
###### <a id='thermal_construction_py_class_Construction_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, *layers: MoosasSettings
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a new instance with given layers and optional name.
  > Parameters:
  > layers : MoosasSettings
  >     Variable number of MoosasSettings instances representing the layers.
  >     At least one layer must be provided.
  > _name : str, optional
  >     Name to assign to the instance. If not provided, a 4-character 
  >     alphanumeric code is generated automatically.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='thermal_construction_py_class_Construction_method_create'></a>`create`
- **Type:** Class Method
- **Parameters:** cls: Any, _type: Any, UFactor: Any, SHGC: Any
- **Returns:** object
    An instance of cls initialized with the created MoosasSettings layer.
- **Comments:**
  > Function:
  > Create a MoosasSettings instance based on the specified type and U-factor.
  > Parameters:
  > cls : type
  >     The class invoking the method (used for returning an instance of the class).
  > _type : str
  >     The type of element to create; either 'window' or another type for opaque materials.
  > UFactor : float or str
  >     The U-factor value; will be converted to float and rounded to 2 decimal places.
  > SHGC : float, optional
  >     Solar Heat Gain Coefficient, required only for 'window' type. 
  >     Defaults to 0.48 if not provided and _type is 'window'.
  > 
  > Returns
  > object
  >     An instance of cls initialized with the created MoosasSettings layer.
  > Returns:
  > object
  >     An instance of cls initialized with the created MoosasSettings layer.

---

###### <a id='thermal_construction_py_class_Construction_method_fromIDFConstructionList'></a>`fromIDFConstructionList`
- **Type:** Class Method
- **Parameters:** cls: Any, idf: Any, idfObject: Any
- **Returns:** cls or None
    An instance of the class constructed from the provided IDF construction list,
    or None if any layer material cannot be found or is invalid.
- **Comments:**
  > Function:
  > Create a class instance from an IDF construction list.
  > Parameters:
  > idf : IDF
  >     The IDF object containing the building energy model data.
  > idfObject : IDFSurfaceObject
  >     The IDF object representing the construction to be processed.
  > 
  > Returns
  > cls or None
  >     An instance of the class constructed from the provided IDF construction list,
  >     or None if any layer material cannot be found or is invalid.
  > Returns:
  > cls or None
  >     An instance of the class constructed from the provided IDF construction list,
  >     or None if any layer material cannot be found or is invalid.

---

###### <a id='thermal_construction_py_class_Construction_method_applyToIDF'></a>`applyToIDF`
- **Type:** Instance Method
- **Parameters:** self: Any, idf: Any, rename: dict
- **Returns:** None
    This function does not return any value.
- **Comments:**
  > Function:
  > Apply modifications to the IDF object and propagate to all layers.
  > Parameters:
  > idf : IDFSurface
  >     The IDF surface object to which modifications are applied.
  > rename : dict, optional
  >     A dictionary mapping old names to new names for renaming references in the IDF.
  > 
  > Returns
  > None
  >     This function does not return any value.
  > Returns:
  > None
  >     This function does not return any value.

---


## 📄 File: thermal\idfGeometry.py
<a id='thermal_idfGeometry_py'></a>

### Contents
- Classes:
  - [ZoneTemplate](#thermal_idfGeometry_py_class_ZoneTemplate)
- Functions:
  - [createThermalSurface()](#thermal_idfGeometry_py_func_createThermalSurface)
  - [encodeFace()](#thermal_idfGeometry_py_func_encodeFace)
  - [createWindowSurface()](#thermal_idfGeometry_py_func_createWindowSurface)

---

### 📦 Class: ZoneTemplate
<a id='thermal_idfGeometry_py_class_ZoneTemplate'></a>
**Description:** No class documentation.

#### Methods
###### <a id='thermal_idfGeometry_py_class_ZoneTemplate_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, idf: IDF
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize the object by extracting and processing construction and zone-related data from an IDF file.
  > Parameters:
  > idf : IDF
  >     The IDF object containing the building energy model data, used to extract constructions, zones, 
  >     and related objects for further processing.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='thermal_idfGeometry_py_class_ZoneTemplate_method_getConstruction'></a>`getConstruction`
- **Type:** Instance Method
- **Parameters:** self: Any, _type: Any, UFactor: Any, SHGC: Any
- **Returns:** Construction
    The existing construction with closest U-factor match or a newly created 
    and added Construction object.
- **Comments:**
  > Function:
  > Find or create a construction by type and U-factor.
  > Parameters:
  > self : object
  >     The instance of the class containing the construction list and IDF.
  > _type : str
  >     The type of construction to find or create.
  > UFactor : float or str
  >     The U-factor value for the construction; will be converted to float.
  > SHGC : float, optional
  >     The Solar Heat Gain Coefficient (SHGC) for the new construction. Default is None.
  > 
  > Returns
  > Construction
  >     The existing construction with closest U-factor match or a newly created 
  >     and added Construction object.
  > Returns:
  > Construction
  >     The existing construction with closest U-factor match or a newly created 
  >     and added Construction object.

---

###### <a id='thermal_idfGeometry_py_class_ZoneTemplate_method_appliedToZone'></a>`appliedToZone`
- **Type:** Instance Method
- **Parameters:** self: Any, zone: MoosasSpace
- **Returns:** None
    This function does not return a value. It modifies the internal IDF model by applying
    schedules, load definitions, HVAC configurations, and zone control settings based on
    the provided zone data.
- **Comments:**
  > Function:
  > Apply zone-specific settings and schedules to an IDF model.
  > Parameters:
  > zone : MoosasSpace
  >     A zone object containing settings such as work hours, temperature setpoints,
  >     occupancy, equipment, lighting, infiltration, ventilation, and other zone-level
  >     parameters. The settings are used to construct schedules and apply HVAC and load
  >     specifications.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the internal IDF model by applying
  >     schedules, load definitions, HVAC configurations, and zone control settings based on
  >     the provided zone data.
  > Returns:
  > None
  >     This function does not return a value. It modifies the internal IDF model by applying
  >     schedules, load definitions, HVAC configurations, and zone control settings based on
  >     the provided zone data.

---

### 🔧 Functions
###### <a id='thermal_idfGeometry_py_func_createThermalSurface'></a>`createThermalSurface`
- **Type:** Function
- **Parameters:** idf: IDF, element: MoosasElement, surfaceType: Any, Construction_Name: Any, Construction_Name_Window: Any, normal: Any
- **Returns:** list
    A list of IDF objects (surfaces) created, including the main thermal surface and any associated window surfaces. Returns None if the element is invalid or belongs to a void space.
- **Comments:**
  > Function:
  > Create a thermal surface in an EnergyPlus IDF file based on a MoosasElement.
  > Parameters:
  > idf : IDF
  >     The EnergyPlus Input Data File (IDF) object to which the thermal surface will be added.
  > element : MoosasElement
  >     The building element (e.g., wall, floor) used to create the thermal surface. Must have valid space and geometric properties.
  > surfaceType : str, optional
  >     Type of the surface, one of 'Floor', 'Wall', 'Ceiling', or 'Roof'. Default is 'Floor'.
  > Construction_Name : str, optional
  >     Name of the construction used for the main surface. Default is "Office_External_Wall".
  > Construction_Name_Window : str, optional
  >     Name of the construction used for any associated window surfaces. Default is "Office_External_Window".
  > normal : Vector, optional
  >     Normal vector to define the orientation of the surface. If None, it is automatically determined based on geometry and surface type.
  > 
  > Returns
  > list
  >     A list of IDF objects (surfaces) created, including the main thermal surface and any associated window surfaces. Returns None if the element is invalid or belongs to a void space.
  > Returns:
  > list
  >     A list of IDF objects (surfaces) created, including the main thermal surface and any associated window surfaces. Returns None if the element is invalid or belongs to a void space.

---

###### <a id='thermal_idfGeometry_py_func_encodeFace'></a>`encodeFace`
- **Type:** Function
- **Parameters:** obj: MoosasSettings, polygon: pygeos.Geometry, normal: Vector
- **Returns:** None
    This function modifies the `obj` in place and does not return a value.
- **Comments:**
  > Function:
  > Encode face geometry into a given settings object by storing vertex coordinates.
  > Parameters:
  > obj : MoosasSettings
  >     The settings object where face parameters will be stored.
  > polygon : pygeos.Geometry
  >     A polygonal geometry whose coordinates define the face.
  > normal : Vector
  >     A vector used to determine the orientation of the face; 
  >     if the dot product with the face normal is negative, vertex order is reversed.
  > 
  > Returns
  > None
  >     This function modifies the `obj` in place and does not return a value.
  > Returns:
  > None
  >     This function modifies the `obj` in place and does not return a value.

---

###### <a id='thermal_idfGeometry_py_func_createWindowSurface'></a>`createWindowSurface`
- **Type:** Function
- **Parameters:** idf: IDF, element: MoosasElement, parentElement: MoosasElement, Construction_Name: Any, normal: Any
- **Returns:** list of Surface
    A list containing one or two Surface objects added to the IDF:
    - One surface for outer (exterior) parent elements.
    - Two surfaces (with opposite orientations and linked boundary conditions) for inner (interior) parent elements.
- **Comments:**
  > Function:
  > Create window surface(s) in an EnergyPlus IDF file based on element geometry and thermal settings.
  > Parameters:
  > idf : IDF
  >     The EnergyPlus Input Data File (IDF) object to which the surface will be added.
  > element : MoosasElement
  >     The element representing the window geometry to be encoded.
  > parentElement : MoosasElement
  >     The parent building element (e.g., wall) that hosts the window; used to derive space and boundary information.
  > Construction_Name : str, optional
  >     The name of the construction to be assigned to the window surface. Default is "Office_External_Wall".
  > normal : array-like, optional
  >     The normal vector to the surface face; used during geometry encoding. If not provided, inferred from geometry.
  > 
  > Returns
  > list of Surface
  >     A list containing one or two Surface objects added to the IDF:
  >     - One surface for outer (exterior) parent elements.
  >     - Two surfaces (with opposite orientations and linked boundary conditions) for inner (interior) parent elements.
  > Returns:
  > list of Surface
  >     A list containing one or two Surface objects added to the IDF:
  >     - One surface for outer (exterior) parent elements.
  >     - Two surfaces (with opposite orientations and linked boundary conditions) for inner (interior) parent elements.

---


## 📄 File: thermal\schedule.py
<a id='thermal_schedule_py'></a>

### Contents
- Classes:
  - [schType](#thermal_schedule_py_class_schType)
  - [schDesignDay](#thermal_schedule_py_class_schDesignDay)
- Functions:
  - [dailySchedule()](#thermal_schedule_py_func_dailySchedule)

---

### 📦 Class: schType
<a id='thermal_schedule_py_class_schType'></a>
**Description:** No class documentation.

### 📦 Class: schDesignDay
<a id='thermal_schedule_py_class_schDesignDay'></a>
**Description:** No class documentation.

### 🔧 Functions
###### <a id='thermal_schedule_py_func_dailySchedule'></a>`dailySchedule`
- **Type:** Function
- **Parameters:** sch: dict, _type: Any, _name: Any
- **Returns:** MoosasSettings
    An instance of MoosasSettings with updated parameters representing the constructed 
    daily schedule, including proper fields for EnergyPlus-compatible schedule definitions.
- **Comments:**
  > Function:
  > Generate a daily schedule for design days based on input dictionary.
  > Parameters:
  > sch : dict
  >     A dictionary where keys are design day types (e.g., schDesignDay.anything) 
  >     and values are lists of 24 numeric values representing hourly data starting from 1 AM 
  >     (covering the period from 12:00 PM to 1 AM next day).
  > _type : schType, optional
  >     Schedule type limits name, used to define valid value ranges for the schedule. 
  >     Default is schType.AnyNumber.
  > _name : str, optional
  >     Name assigned to the generated schedule. If not provided, a unique name 
  >     in the format 'sch_xxxx' (where xxxx is a random 4-character code) will be generated.
  > 
  > Returns
  > MoosasSettings
  >     An instance of MoosasSettings with updated parameters representing the constructed 
  >     daily schedule, including proper fields for EnergyPlus-compatible schedule definitions.
  > Returns:
  > MoosasSettings
  >     An instance of MoosasSettings with updated parameters representing the constructed 
  >     daily schedule, including proper fields for EnergyPlus-compatible schedule definitions.

---


## 📄 File: thermal\settings.py
<a id='thermal_settings_py'></a>

### Contents
- Classes:
  - [MoosasSettings](#thermal_settings_py_class_MoosasSettings)
  - [ThermalSettings](#thermal_settings_py_class_ThermalSettings)

---

### 📦 Class: MoosasSettings
<a id='thermal_settings_py_class_MoosasSettings'></a>
**Description:** No class documentation.

#### Methods
###### <a id='thermal_settings_py_class_MoosasSettings_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, default: Any, **kwargs: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize the object with default
  > Parameters:
  > and optional keyword arguments.
  > 
  > Parameters
  > default : SpaceDefault, optional
  >     The default parameter set to copy. If None, defaults to SpaceDefault.
  > **kwargs : dict
  >     Additional keyword arguments to update the parameters; may include 'id'.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='thermal_settings_py_class_MoosasSettings_method_fromIdfObject'></a>`fromIdfObject`
- **Type:** Class Method
- **Parameters:** cls: Any, idfObject: Any
- **Returns:** cls
    A new instance of the class initialized with extracted keyword arguments.
- **Comments:**
  > Function:
  > Create a new instance from an IDF object.
  > Parameters:
  > cls : type
  >     The class constructor, used to instantiate the new object.
  > idfObject : object
  >     An object containing IDF data with attributes 'objls' and key-value access 
  >     via indexing. Keys in 'objls' are used to extract non-empty values.
  > 
  > Returns
  > cls
  >     A new instance of the class initialized with extracted keyword arguments.
  > Returns:
  > cls
  >     A new instance of the class initialized with extracted keyword arguments.

---

###### <a id='thermal_settings_py_class_MoosasSettings_method_updateParams'></a>`updateParams`
- **Type:** Instance Method
- **Parameters:** self: Any, **kwargs: Any
- **Returns:** self : object
    Returns the instance of the object with updated parameters, enabling method chaining.
- **Comments:**
  > Function:
  > Update the
  > Parameters:
  > of the object with the provided keyword arguments.
  > 
  > Parameters
  > **kwargs : dict
  >     Arbitrary keyword arguments representing the parameters to be updated.
  >     Each key-value pair will be added or updated in the `self.params` dictionary.
  > 
  > Returns
  > self : object
  >     Returns the instance of the object with updated parameters, enabling method chaining.
  > Returns:
  > self : object
  >     Returns the instance of the object with updated parameters, enabling method chaining.

---

###### <a id='thermal_settings_py_class_MoosasSettings_method_paramToString'></a>`paramToString`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A comma-separated string representation of the parameter values.
- **Comments:**
  > Function:
  > Convert parameter values to a comma-separated string.
  > Parameters:
  > self : object
  >     The instance containing a `params` attribute, which is a dictionary 
  >     mapping parameter names to their values.
  > 
  > Returns
  > str
  >     A comma-separated string representation of the parameter values.
  > Returns:
  > str
  >     A comma-separated string representation of the parameter values.

---

###### <a id='thermal_settings_py_class_MoosasSettings_method_paramTags'></a>`paramTags`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string starting with '!' followed by comma-separated parameter keys.
- **Comments:**
  > Function:
  > Get a string of parameter keys prefixed with an exclamation mark.
  > Parameters:
  > self : object
  >     The instance of the class containing a `params` dictionary attribute.
  > 
  > Returns
  > str
  >     A string starting with '!' followed by comma-separated parameter keys.
  > Returns:
  > str
  >     A string starting with '!' followed by comma-separated parameter keys.

---

###### <a id='thermal_settings_py_class_MoosasSettings_method_applyToIDF'></a>`applyToIDF`
- **Type:** Instance Method
- **Parameters:** self: Any, idf: Any, rename: dict
- **Returns:** None
    This function does not return a value. It modifies the `idf` object in place.
- **Comments:**
  > Function:
  > Apply
  > Parameters:
  > to an IDF object, optionally renaming fields.
  > 
  > Parameters
  > idf : pyenergyplus.idf.IDF
  >     The IDF object to which the parameters will be applied.
  > rename : dict, optional
  >     A dictionary mapping parameter names to new field names in the IDF object.
  >     If not provided, no renaming is performed.
  > 
  > Returns
  > None
  >     This function does not return a value. It modifies the `idf` object in place.
  > Returns:
  > None
  >     This function does not return a value. It modifies the `idf` object in place.

---

###### <a id='thermal_settings_py_class_MoosasSettings_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string representation of the ThermalSettings object, specifically the string representation of its `params` attribute.
- **Comments:**
  > Function:
  > String representation of the ThermalSettings object.
  > Parameters:
  > self : ThermalSettings
  >     The instance of ThermalSettings to represent as a string.
  > 
  > Returns
  > str
  >     A string representation of the ThermalSettings object, specifically the string representation of its `params` attribute.
  > Returns:
  > str
  >     A string representation of the ThermalSettings object, specifically the string representation of its `params` attribute.

---

### 📦 Class: ThermalSettings
<a id='thermal_settings_py_class_ThermalSettings'></a>
**Description:** No class documentation.

#### Methods
###### <a id='thermal_settings_py_class_ThermalSettings_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, **kwargs: Any
- **Returns:** None
    This method does not return any value.
- **Comments:**
  > Function:
  > Initialize the ThermalSettings object with default space settings and load values.
  > Parameters:
  > **kwargs : dict
  >     Additional keyword arguments to be passed to the parent class constructor.
  > 
  > Returns
  > None
  >     This method does not return any value.
  > Returns:
  > None
  >     This method does not return any value.

---

###### <a id='thermal_settings_py_class_ThermalSettings_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    Concatenated string representation of `self.params` and `self.load`.
- **Comments:**
  > Function:
  > Return string representations of the params and load attributes.
  > Parameters:
  > self : object
  >     The instance of the class containing `params` and `load` attributes.
  > 
  > Returns
  > str
  >     Concatenated string representation of `self.params` and `self.load`.
  > Returns:
  > str
  >     Concatenated string representation of `self.params` and `self.load`.

---


## 📄 File: utils\constant.py
<a id='utils_constant_py'></a>

### Contents
- Classes:
  - [buildingType](#utils_constant_py_class_buildingType)
  - [geom](#utils_constant_py_class_geom)
  - [settings](#utils_constant_py_class_settings)
  - [ui](#utils_constant_py_class_ui)
  - [meter](#utils_constant_py_class_meter)
  - [entity](#utils_constant_py_class_entity)
  - [orientation](#utils_constant_py_class_orientation)
  - [dateSetting](#utils_constant_py_class_dateSetting)
  - [rad](#utils_constant_py_class_rad)

---

### 📦 Class: buildingType
<a id='utils_constant_py_class_buildingType'></a>
**Description:** No class documentation.

### 📦 Class: geom
<a id='utils_constant_py_class_geom'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_constant_py_class_geom_method_round'></a>`round`
- **Type:** Instance Method
- **Parameters:** num: Any, precision: Any
- **Returns:** float or numpy.ndarray
    The rounded number or array, where each element is rounded down to the nearest multiple of precision.
- **Comments:**
  > Function:
  > Round the input number or array to the specified precision using floor rounding.
  > Parameters:
  > num : array-like or scalar
  >     The number or array of numbers to be rounded.
  > precision : float
  >     The precision to which the numbers are to be rounded down.
  > 
  > Returns
  > float or numpy.ndarray
  >     The rounded number or array, where each element is rounded down to the nearest multiple of precision.
  > Returns:
  > float or numpy.ndarray
  >     The rounded number or array, where each element is rounded down to the nearest multiple of precision.

---

### 📦 Class: settings
<a id='utils_constant_py_class_settings'></a>
**Description:** No class documentation.

### 📦 Class: ui
<a id='utils_constant_py_class_ui'></a>
**Description:** No class documentation.

### 📦 Class: meter
<a id='utils_constant_py_class_meter'></a>
**Description:** No class documentation.

### 📦 Class: entity
<a id='utils_constant_py_class_entity'></a>
**Description:** No class documentation.

### 📦 Class: orientation
<a id='utils_constant_py_class_orientation'></a>
**Description:** No class documentation.

### 📦 Class: dateSetting
<a id='utils_constant_py_class_dateSetting'></a>
**Description:** No class documentation.

### 📦 Class: rad
<a id='utils_constant_py_class_rad'></a>
**Description:** No class documentation.


## 📄 File: utils\date.py
<a id='utils_date_py'></a>

### Contents
- Classes:
  - [DateTime](#utils_date_py_class_DateTime)
  - [Date](#utils_date_py_class_Date)
  - [Time](#utils_date_py_class_Time)

---

### 📦 Class: DateTime
<a id='utils_date_py_class_DateTime'></a>
**Description:** Create Ladybug Date time.

#### Methods
###### <a id='utils_date_py_class_DateTime_method___new__'></a>`__new__`
- **Type:** Instance Method
- **Parameters:** cls: Any, monthOrDateTime: int | datetime, day: Any, hour: Any, minute: Any, leap_year: Any
- **Returns:** MoosasDateTime
    A new instance of MoosasDateTime with the specified date and time components.
- **Comments:**
  > Function:
  > Create a MoosasDateTime instance from a month or datetime object, with optional day, hour, minute, and leap year settings.
  > Parameters:
  > monthOrDateTime : int or datetime, default 1
  >     If int, represents the month (1-12). If datetime, its month, day, hour, and minute are used.
  > day : int, default 1
  >     Day of the month (1-31), used only if monthOrDateTime is an integer.
  > hour : int or float, default 0
  >     Hour of the day (0-23) or decimal hour. Can be combined with minute.
  > minute : int or float, default 0
  >     Minute of the hour (0-59) or fractional minutes. Combined with hour as total minutes.
  > leap_year : bool, default False
  >     If True, sets the year to 2016 (leap year); otherwise, sets year to 2017.
  > 
  > Returns
  > MoosasDateTime
  >     A new instance of MoosasDateTime with the specified date and time components.
  > Returns:
  > MoosasDateTime
  >     A new instance of MoosasDateTime with the specified date and time components.

---

###### <a id='utils_date_py_class_DateTime_method___reduce_ex__'></a>`__reduce_ex__`
- **Type:** Instance Method
- **Parameters:** self: Any, protocol: Any
- **Returns:** tuple
    A tuple containing the class type and a tuple of arguments (month, day, hour, minute) 
    required to reconstruct the instance during unpickling.
- **Comments:**
  > Function:
  > Call the __new__() constructor when the class instance is unpickled.
  > 
  > This method is necessary for the pickle.loads() call to work.
  > Parameters:
  > self : object
  >     The instance of the class being pickled.
  > protocol : int
  >     The pickle protocol version used for serialization.
  > 
  > Returns
  > tuple
  >     A tuple containing the class type and a tuple of arguments (month, day, hour, minute) 
  >     required to reconstruct the instance during unpickling.
  > Returns:
  > tuple
  >     A tuple containing the class type and a tuple of arguments (month, day, hour, minute) 
  >     required to reconstruct the instance during unpickling.

---

###### <a id='utils_date_py_class_DateTime_method_from_hoy'></a>`from_hoy`
- **Type:** Class Method
- **Parameters:** cls: Any, hoy: Any, leap_year: Any
- **Returns:** Ladybug Datetime
    A DateTime object corresponding to the given hour of the year.
- **Comments:**
  > Function:
  > Create Ladybug Datetime from an hour of the year.
  > Parameters:
  > hoy : float
  >     A float value representing the hour of the year, 0 <= hoy < 8760.
  > leap_year : bool, optional
  >     Boolean to note whether the DateTime is part of a leap year. Default is False.
  > 
  > Returns
  > Ladybug Datetime
  >     A DateTime object corresponding to the given hour of the year.
  > Returns:
  > Ladybug Datetime
  >     A DateTime object corresponding to the given hour of the year.

---

###### <a id='utils_date_py_class_DateTime_method_from_moy'></a>`from_moy`
- **Type:** Class Method
- **Parameters:** cls: Any, moy: Any, leap_year: Any
- **Returns:** LadybugDatetime
    A Ladybug Datetime object corresponding to the given minute of the year.
- **Comments:**
  > Function:
  > Create a Ladybug Datetime object from a minute of the year.
  > Parameters:
  > moy : int
  >     An integer representing the minute of the year, must satisfy 0 <= moy < 525600.
  > leap_year : bool, optional
  >     Boolean indicating whether the datetime is in a leap year. Default is False.
  > 
  > Returns
  > LadybugDatetime
  >     A Ladybug Datetime object corresponding to the given minute of the year.
  > Returns:
  > LadybugDatetime
  >     A Ladybug Datetime object corresponding to the given minute of the year.

---

###### <a id='utils_date_py_class_DateTime_method__calculate_hour_and_minute'></a>`_calculate_hour_and_minute`
- **Type:** Instance Method
- **Parameters:** float_hour: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate hour and minutes as integers from a float hour.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_from_date_and_time'></a>`from_date_and_time`
- **Type:** Class Method
- **Parameters:** cls: Any, date: Any, time: Any
- **Returns:** DateTime
    A new DateTime object created from the given Date and Time.
- **Comments:**
  > Function:
  > Create a DateTime object from a Date and a Time object.
  > Parameters:
  > date : Date
  >     A ladybug Date object.
  > time : Time
  >     A ladybug Time object.
  > 
  > Returns
  > DateTime
  >     A new DateTime object created from the given Date and Time.
  > Returns:
  > DateTime
  >     A new DateTime object created from the given Date and Time.

---

###### <a id='utils_date_py_class_DateTime_method_leap_year'></a>`leap_year`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Boolean to note whether DateTime belongs to a leap year or not.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_doy'></a>`doy`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate day of the year for this date time.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_hoy'></a>`hoy`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate hour of the year for this date time.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_moy'></a>`moy`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate minute of the year for this date time.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_float_hour'></a>`float_hour`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get hour and minute as a float value, e.g. 6.25 for 6:15.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_date'></a>`date`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get a Date object associated with this DateTime.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_time'></a>`time`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get a Time object associated with this DateTime.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return date time as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method_ToString'></a>`ToString`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Overwrite .NET ToString.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_DateTime_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return date time as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

### 📦 Class: Date
<a id='utils_date_py_class_Date'></a>
**Description:** Ladybug Date.

#### Methods
###### <a id='utils_date_py_class_Date_method___new__'></a>`__new__`
- **Type:** Instance Method
- **Parameters:** cls: Any, month: Any, day: Any, leap_year: Any
- **Returns:** date
    A date object representing the specified day in either a leap year (2016) or a common year (2017).
- **Comments:**
  > Function:
  > Create a Ladybug Date object.
  > Parameters:
  > month : int, optional
  >     The month of the year from 1 to 12. Default is 1.
  > day : int, optional
  >     The day of the month from 1 to 31. Default is 1.
  > leap_year : bool, optional
  >     Boolean to indicate whether the date is in a leap year (2016) or not (2017). Default is False.
  > 
  > Returns
  > date
  >     A date object representing the specified day in either a leap year (2016) or a common year (2017).
  > Returns:
  > date
  >     A date object representing the specified day in either a leap year (2016) or a common year (2017).

---

###### <a id='utils_date_py_class_Date_method___reduce_ex__'></a>`__reduce_ex__`
- **Type:** Instance Method
- **Parameters:** self: Any, protocol: Any
- **Returns:** tuple
    A tuple containing the class type and a tuple of arguments (month, day, leap_year) 
    to be passed to __new__ upon unpickling.
- **Comments:**
  > Function:
  > Call the __new__() constructor when the class instance is unpickled.
  > 
  > This method is necessary for the pickle.loads() call to work.
  > Parameters:
  > self : object
  >     The instance of the class being pickled.
  > protocol : int
  >     The pickle protocol used for serialization.
  > 
  > Returns
  > tuple
  >     A tuple containing the class type and a tuple of arguments (month, day, leap_year) 
  >     to be passed to __new__ upon unpickling.
  > Returns:
  > tuple
  >     A tuple containing the class type and a tuple of arguments (month, day, leap_year) 
  >     to be passed to __new__ upon unpickling.

---

###### <a id='utils_date_py_class_Date_method_leap_year'></a>`leap_year`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Boolean to note whether Date belongs to a leap year or not.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Date_method_doy'></a>`doy`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate day of the year for this date.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Date_method_to_array'></a>`to_array`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return date as an array of values.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Date_method_to_dict'></a>`to_dict`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get date as a dictionary.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Date_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return date as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Date_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return date as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

### 📦 Class: Time
<a id='utils_date_py_class_Time'></a>
**Description:** Create Ladybug Time.

#### Methods
###### <a id='utils_date_py_class_Time_method___new__'></a>`__new__`
- **Type:** Instance Method
- **Parameters:** cls: Any, hour: Any, minute: Any
- **Returns:** time
    A new instance of Ladybug Time with the specified hour and minute.
- **Comments:**
  > Function:
  > Create a Ladybug Time object.
  > Parameters:
  > hour : int or float, optional
  >     The hour of the time, which can be an integer or a float. If a float is provided,
  >     it will be converted to hours and minutes. Default is 0.
  > minute : int, optional
  >     The minute of the time. Default is 0.
  > 
  > Returns
  > time
  >     A new instance of Ladybug Time with the specified hour and minute.
  > Returns:
  > time
  >     A new instance of Ladybug Time with the specified hour and minute.

---

###### <a id='utils_date_py_class_Time_method___reduce_ex__'></a>`__reduce_ex__`
- **Type:** Instance Method
- **Parameters:** self: Any, protocol: Any
- **Returns:** tuple
    A tuple containing the class type and a tuple of arguments (hour, minute) 
    to be passed to __new__ upon unpickling.
- **Comments:**
  > Function:
  > Call the __new__() constructor when the class instance is unpickled.
  > 
  > This method is necessary for the pickle.loads() call to work.
  > Parameters:
  > self : object
  >     The instance of the class being pickled.
  > protocol : int
  >     The pickle protocol version used for serialization.
  > 
  > Returns
  > tuple
  >     A tuple containing the class type and a tuple of arguments (hour, minute) 
  >     to be passed to __new__ upon unpickling.
  > Returns:
  > tuple
  >     A tuple containing the class type and a tuple of arguments (hour, minute) 
  >     to be passed to __new__ upon unpickling.

---

###### <a id='utils_date_py_class_Time_method_from_dict'></a>`from_dict`
- **Type:** Class Method
- **Parameters:** cls: Any, data: Any
- **Returns:** cls
    A new instance of the class initialized with the given hour and minute.
- **Comments:**
  > Function:
  > Create a time object from a dictionary.
  > Parameters:
  > data : dict
  >     A dictionary containing time components with the following keys:
  >     - 'hour' (int, optional): Hour value between 0-23. Default is 0.
  >     - 'minute' (int, optional): Minute value between 0-59. Default is 0.
  > 
  > Returns
  > cls
  >     A new instance of the class initialized with the given hour and minute.
  > Returns:
  > cls
  >     A new instance of the class initialized with the given hour and minute.

---

###### <a id='utils_date_py_class_Time_method_from_mod'></a>`from_mod`
- **Type:** Class Method
- **Parameters:** cls: Any, mod: Any
- **Returns:** Ladybug Time
    A Time object corresponding to the given minute of the day.
- **Comments:**
  > Function:
  > Create a Ladybug Time object from a minute of the day.
  > Parameters:
  > mod : int
  >     An integer value representing the minute of the day, in the range 0 <= mod < 1440.
  > 
  > Returns
  > Ladybug Time
  >     A Time object corresponding to the given minute of the day.
  > Returns:
  > Ladybug Time
  >     A Time object corresponding to the given minute of the day.

---

###### <a id='utils_date_py_class_Time_method_from_time_string'></a>`from_time_string`
- **Type:** Class Method
- **Parameters:** cls: Any, time_string: Any, leap_year: Any
- **Returns:** Time
    A Ladybug Time object representing the given time.
- **Comments:**
  > Function:
  > Create a Ladybug Time object from a time string in the format 'HH:MM'.
  > Parameters:
  > time_string : str
  >     A string representing time in 24-hour format 'HH:MM', where HH is hours (00-23)
  >     and MM is minutes (00-59).
  > leap_year : bool, optional
  >     A flag to indicate whether the time is for a leap year. This parameter does not
  >     affect the parsing of the time string but may be used by the class constructor.
  >     Default is False.
  > 
  > Returns
  > Time
  >     A Ladybug Time object representing the given time.
  > Returns:
  > Time
  >     A Ladybug Time object representing the given time.

---

###### <a id='utils_date_py_class_Time_method_from_array'></a>`from_array`
- **Type:** Class Method
- **Parameters:** cls: Any, time_array: Any
- **Returns:** LadybugTime
    A new instance of Ladybug Time initialized with the given hour and minute.
- **Comments:**
  > Function:
  > Create a Ladybug Time object from an array of integers.
  > Parameters:
  > time_array : array-like of int
  >     An array of 2 integers ordered as follows: (hour, minute).
  > 
  > Returns
  > LadybugTime
  >     A new instance of Ladybug Time initialized with the given hour and minute.
  > Returns:
  > LadybugTime
  >     A new instance of Ladybug Time initialized with the given hour and minute.

---

###### <a id='utils_date_py_class_Time_method_mod'></a>`mod`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate minute of the day for this time.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method_float_hour'></a>`float_hour`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get hour and minute as a float value, e.g. 6.25 for 6:15.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method_to_array'></a>`to_array`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return time as an array of values.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method_to_dict'></a>`to_dict`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Get time as a dictionary.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method__calculate_hour_and_minute'></a>`_calculate_hour_and_minute`
- **Type:** Instance Method
- **Parameters:** float_hour: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Calculate hour and minutes as integers from a float hour.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return time as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method_ToString'></a>`ToString`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Overwrite .NET ToString.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---

###### <a id='utils_date_py_class_Time_method___repr__'></a>`__repr__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Return time as a string.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > None

---


## 📄 File: utils\error.py
<a id='utils_error_py'></a>

### Contents
- Classes:
  - [ShellError](#utils_error_py_class_ShellError)
  - [FileError](#utils_error_py_class_FileError)
  - [GeometryError](#utils_error_py_class_GeometryError)
  - [TopologyError](#utils_error_py_class_TopologyError)

---

### 📦 Class: ShellError
<a id='utils_error_py_class_ShellError'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_error_py_class_ShellError_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, execution: Any, message: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a new instance with execution context and message.
  > Parameters:
  > execution : any
  >     The execution context or environment to be stored in the instance.
  > message : str
  >     The message string associated with the instance.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='utils_error_py_class_ShellError_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string in the format '{execution}: {message}', where 'execution' and 'message' 
    are attributes of the FileError instance.
- **Comments:**
  > Function:
  > Return a string representation of the FileError exception.
  > Parameters:
  > self : FileError
  >     The instance of the FileError exception.
  > 
  > Returns
  > str
  >     A string in the format '{execution}: {message}', where 'execution' and 'message' 
  >     are attributes of the FileError instance.
  > Returns:
  > str
  >     A string in the format '{execution}: {message}', where 'execution' and 'message' 
  >     are attributes of the FileError instance.

---

### 📦 Class: FileError
<a id='utils_error_py_class_FileError'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_error_py_class_FileError_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, file: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize the object with a file.
  > Parameters:
  > file : object
  >     The file to be assigned to the instance variable.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='utils_error_py_class_FileError_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A string describing the error, including the name of the invalid file.
- **Comments:**
  > Function:
  > Return a string representation of the FileError indicating the file is not a valid moosas file.
  > Parameters:
  > No parameter descriptions.
  > Returns:
  > str
  >     A string describing the error, including the name of the invalid file.

---

### 📦 Class: GeometryError
<a id='utils_error_py_class_GeometryError'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_error_py_class_GeometryError_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, geometry: Any, reason: Any
- **Returns:** None
    This constructor does not return any value.
- **Comments:**
  > Function:
  > Initialize a new instance with geometry and reason attributes.
  > Parameters:
  > geometry : object
  >     The geometric representation or data associated with the instance.
  > reason : str
  >     A description or explanation indicating the reason for the instance's state or creation.
  > 
  > Returns
  > None
  >     This constructor does not return any value.
  > Returns:
  > None
  >     This constructor does not return any value.

---

###### <a id='utils_error_py_class_GeometryError_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A formatted string describing the error in the form "GeometryError: {geometry} is invalid: {reason}".
- **Comments:**
  > Function:
  > Return a string representation of the TopologyError exception.
  > Parameters:
  > self : TopologyError
  >     The instance of the TopologyError exception to represent as a string.
  >     Contains attributes `geometry` and `reason` that describe the error.
  > 
  > Returns
  > str
  >     A formatted string describing the error in the form "GeometryError: {geometry} is invalid: {reason}".
  > Returns:
  > str
  >     A formatted string describing the error in the form "GeometryError: {geometry} is invalid: {reason}".

---

### 📦 Class: TopologyError
<a id='utils_error_py_class_TopologyError'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_error_py_class_TopologyError_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, func: Any, reason: Any
- **Returns:** None
    This constructor does not return a value.
- **Comments:**
  > Function:
  > Initialize a new instance with a function and a reason.
  > Parameters:
  > func : callable
  >     The function to be stored in the instance.
  > reason : str
  >     A string describing the reason associated with the function.
  > 
  > Returns
  > None
  >     This constructor does not return a value.
  > Returns:
  > None
  >     This constructor does not return a value.

---

###### <a id='utils_error_py_class_TopologyError_method___str__'></a>`__str__`
- **Type:** Instance Method
- **Parameters:** self: Any
- **Returns:** str
    A formatted string describing the error, including the function name and reason.
- **Comments:**
  > Function:
  > Return a string representation of the TopologyError instance.
  > Parameters:
  > self : object
  >     The instance of TopologyError.
  > 
  > Returns
  > str
  >     A formatted string describing the error, including the function name and reason.
  > Returns:
  > str
  >     A formatted string describing the error, including the function name and reason.

---


## 📄 File: utils\standard.py
<a id='utils_standard_py'></a>

### Contents
- Functions:
  - [loadBuildingTemplate()](#utils_standard_py_func_loadBuildingTemplate)
  - [searchTemplate()](#utils_standard_py_func_searchTemplate)

---

### 🔧 Functions
###### <a id='utils_standard_py_func_loadBuildingTemplate'></a>`loadBuildingTemplate`
- **Type:** Function
- **Parameters:** templateFile: Any
- **Returns:** dict
    A nested dictionary where each key is formed by joining non-'zone_' column values 
    with underscores, and each value is a dictionary mapping 'zone_' column names to 
    their respective values for that row.
- **Comments:**
  > Function:
  > Load a building template from a CSV file and return it as a dictionary.
  > Parameters:
  > templateFile : str
  >     Path to the CSV file containing the building template. The file should have 
  >     a header row with column names, where columns prefixed with 'zone_' are treated 
  >     as values, and others are used as keys.
  > 
  > Returns
  > dict
  >     A nested dictionary where each key is formed by joining non-'zone_' column values 
  >     with underscores, and each value is a dictionary mapping 'zone_' column names to 
  >     their respective values for that row.
  > Returns:
  > dict
  >     A nested dictionary where each key is formed by joining non-'zone_' column values 
  >     with underscores, and each value is a dictionary mapping 'zone_' column names to 
  >     their respective values for that row.

---

###### <a id='utils_standard_py_func_searchTemplate'></a>`searchTemplate`
- **Type:** Function
- **Parameters:** str_list: Any, templatelist: Any
- **Returns:** list
    List of template values whose names match any of the provided tags via regex search.
- **Comments:**
  > Function:
  > Search for template names matching any of the given tags using regular expressions.
  > Parameters:
  > str_list : list of str
  >     List of strings (tags) to search for within template names.
  > templatelist : dict, optional
  >     Dictionary of templates where keys are template names (str) and values are associated data.
  >     Default is the global `template` dictionary.
  > 
  > Returns
  > list
  >     List of template values whose names match any of the provided tags via regex search.
  > Returns:
  > list
  >     List of template values whose names match any of the provided tags via regex search.

---


## 📄 File: utils\support.py
<a id='utils_support_py'></a>

### Contents

---


## 📄 File: utils\tools.py
<a id='utils_tools_py'></a>

### Contents
- Classes:
  - [MoosasPath](#utils_tools_py_class_MoosasPath)
- Functions:
  - [isFilePath()](#utils_tools_py_func_isFilePath)
  - [callCmd()](#utils_tools_py_func_callCmd)
  - [mixItemListToObject()](#utils_tools_py_func_mixItemListToObject)
  - [mixItemListToList()](#utils_tools_py_func_mixItemListToList)
  - [generate_code()](#utils_tools_py_func_generate_code)
  - [encodeParams()](#utils_tools_py_func_encodeParams)
  - [searchBy()](#utils_tools_py_func_searchBy)
  - [to_dictionary()](#utils_tools_py_func_to_dictionary)
  - [parseFile()](#utils_tools_py_func_parseFile)

---

### 📦 Class: MoosasPath
<a id='utils_tools_py_class_MoosasPath'></a>
**Description:** No class documentation.

#### Methods
###### <a id='utils_tools_py_class_MoosasPath_method___init__'></a>`__init__`
- **Type:** Instance Method
- **Parameters:** self: Any, MoosasPlusDirectory: Any
- **Returns:** None
- **Comments:**
  > Function:
  > Initialize the MoosasPlus environment with directory paths.
  > Parameters:
  > MoosasPlusDirectory : str, optional
  >     Root directory for MoosasPlus. If None, defaults to the parent directory
  >     of the current file's directory. Will be converted to an absolute path.
  > 
  > Returns
  > None
  > Returns:
  > None

---

###### <a id='utils_tools_py_class_MoosasPath_method_clean'></a>`clean`
- **Type:** Instance Method
- **Parameters:** dir: Any
- **Returns:** list
    A list of None values, one for each file removed (result of os.remove calls).
- **Comments:**
  > Function:
  > Clean all files in the specified directory.
  > Parameters:
  > dir : str
  >     Path to the directory whose files are to be removed.
  > 
  > Returns
  > list
  >     A list of None values, one for each file removed (result of os.remove calls).
  > Returns:
  > list
  >     A list of None values, one for each file removed (result of os.remove calls).

---

###### <a id='utils_tools_py_class_MoosasPath_method_checkBu