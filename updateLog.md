-- 0.8.0
# Environment Update 06.19
- 0.8.0.0 create a deployment toSKetchUp.py to auto download embedded python and build the environment.
- 0.8.0.1 fix path issue

--- 0.7.9 
# IDF update 05.08
- 0.7.9.0 create *.idf exporting module, which can extend a template idf file with the geometries in MOOSAS
- 0.7.9.1 documentation works on transform module
- 0.7.9.2 fix VFG method and improve the efficiency
- 0.7.9.3 include more IDF objects and better alignment to the template idf model

--- 0.7.8 
# IO update 04.28
- 0.7.8.0 create IO module to reconstruct all IO related code.
- 0.7.8.1 create _rdf module for *.rdf file supporting (in and out) and realize the out module
- 0.7.8.2 realize the in module
- 0.7.8.3 fix the summary bug
- 0.7.8.4 embedded BTG CCR and VFG methods into the space generation

--- 0.7.7
# convex Update 03.10
- 0.7.7.0 Include the convex module into the transformation after the 1LSB generation
- 0.7.7.1 update convex module
- 0.7.7.4 fix the blur matching in topology calculation
- 0.7.7.6 fix the topology bug
- 0.7.7.7 fix the breaking function in MoosasWall
- 0.7.7.8 fix space topology, dead loop for searching the top void
- 0.7.7.9 fix the overlap area calculation, using grid_size instead of exact intersection, difference and all other set operation
- 0.7.7.10 fix the glazing Uid tag

--- 0.7.6
# Transformation Update 03.10
create preprocess module to transformation: work on cleanse issue directly on input files.
frequently fix the bug in cleanse module

--- 0.7.5 
# Standardize Update 03.02
- 0.7.5.0 Standardize method had been added.
- 0.7.5.1 method for height calculation of walls has been updated.
- 0.7.5.2 compatibility for transformation module in ruby environment had been checked.

--- 0.7.4
# Transformation bug fix 02.20
- 0.7.4.0 big fixing on the force_2d methods detect the co-linear projections and avoid them.
- 0.7.4.1 Temporary exception were add in horizontal face clipping
- 0.7.4.2 big fixing on the normal calculation of faces
- 0.7.4.3 using PCA method instead of simple calculation

--- 0.7.3
# Hole support Update 12.30
- 0.7.3.0 Hole were supported in transformation.
- 0.7.3.1 wwr/area/toUV/toWorld methods were adjusted.

--- 0.7.1
# Transformation Ver 01.30
- 0.7.1.0 Better performance in matching glazing and wall 
- 0.7.1.1 Better performance in generating level series in the model.
- 0.7.1.2 Better performance in outer boundary calculation while the boundaries are self-intersected or isolated.
- 0.7.1.3 Better performance in shading attachment, some faces will be recycled to the wall/floor in this stage.
- 0.7.1.4 Better performance in matching floor/ceiling and boundary.


--- 0.7.0
# Python Environment Update 11.08
- 0.7.0.0 Change the python environment to embedded the moosas+. 
- 0.7.0.1 * to_rbz.bat was embedded into the root folder to create *.rbz automatically


--- 0.6.12
# Thermal Ventilation Analysis 12.28
- 0.6.12.0 Debug for auto_contamx
- 0.6.12.1 Include Thermal Ventilation to MoosasVent
- 0.6.12.2 OS command error in vent/run.bat and vent/view.bat

--- 0.6.11
# English Version 12.22 15:20
English Version update

--- 0.6.10
# Energy 12.06 21:15
- 0.6.10.0 MoosasEnergy update to allow changes in parameters.
- 0.6.10.1 Debug for MoosasRadiance/Sunhour/Daylight/Grid about the deleted grids.
- 0.6.10.2 MoosasEnergy update to allow changes in parameters.

--- 0.6.9
# Transforming_inclinewall 12.04 21:40
-0.6.9.0 Debug MoosasTransforming on pairing the incline windows and walls.
-0.6.9.1 Debug for MMR/Transforming about the redudant lines.

--- 0.6.8
# energy settings and template 11.29
- 0.6.8.0 Setting up the innitial space parameters for different building type in MoosasStandard;
Move the setting data as BuildingTemplate into db/building_template.csv;
Built the innitilization of building template in MoosasStandard, and the method to search the template;
Other iterations in main.html/skp.js/ui.js/MoosasModel/MoosasWebDialog/MoosasMain to be compatible to those changes.
- 0.6.8.4 Built the method in MoosasWeather to calculate Thermal Design Climate Zone by temperature data from weatherfile.
- 0.6.8.5 Settingup the corespondence from java to ruby to change the building type.

--- 0.6.7
# sketchup_Debug 11.25
- 0.6.7.0 Fix the bug of air arrows and MoosasEdge.normals for the visualization of the ventilation.
- 0.6.7.1 Ensure the consistancy parameters between java (UI.space_settings), go(MoosasParam), and ruby(MoosasSpace.settings);
- 0.6.7.2 Optimized the main.html on the geometry_tab;
- 0.6.7.3 Rewritten several function in ui.js about the geometry_tab.
- 0.6.7.4 Debug single/multi objective optimization on the corespondence to java.

--- 0.6.6
# Transformation_obj 11.25
- 0.6.6.0 MoosasTransformer now is avaliable towards *.obj file.
- 0.6.6.1 Debug MoosasTransforming on matpoltlib

--- 0.6.5
# General_update 11.24
- 0.6.5.0 MoosasTransformer is fixed to solve the problem of windows being ignored;
- 0.6.5.1 MoosasModel adds visualization for interior walls;
- 0.6.5.2 MoosasDaylight/MoosasConstant/MoosasModel/MoosasRender add the type representing air wall, in MoosasConstant::ENTITY_IGNORE;
- 0.6.5.3 /view adds the CFD icon, main.html optimizes the page display;
- 0.6.5.4 MoosasWeather.rb/.py interaction performance is improved, stability is increased, and city name input is added;
- 0.6.5.5 Other optimization on MMR, MoosasVent's interactive experience 

--- 0.6.4
# MoosasVent 11.23
MoosasVenXgb is fixed to supplement related dependencies;
Added MoosasMain-visual.exe for cmd debugging

--- 0.6.3
# database update 11.22 19:26 
- 0.6.3.0 space database update, MMR and MoosasModel update spatial numbering
- 0.6.3.1 MMR and MoosasModel update the space numbering logic and bind it to the absolute spatial coordinates
- 0.6.3.2 MMR.rb MMR restores the window binding shading function
- 0.6.3.3 Facade radiation calculations moved from MMR to MoosasEnergy;
- 0.6.3.4 The fast radiation calculation option is added on the front-end, and you can choose whether to call MoosasRadiance to calculate the energy consumption.
- 0.6.3.5 MoosasEnergy iteration, which is linked to MoosasRadiance to calculate the heat gain of solar radiation in winter and summer;
- 0.6.3.6 MoosasRadiance reconstruction, which supports the calculation of single point of radiation;

--- 0.6.2
# Visulize type update 11.21 
The MoosasRender.rb visualization has been updated to show shading transparently

--- 0.6.1
# transformation 11.21
- 0.6.1.0 MoosasMain has been updated to support multiple command lines;
- 0.6.1.1 MMR.rb supports group export of .geo and multi-file reading of .xml
- 0.6.1.2 MoosasMain updates the export of execute.log, which can read py standard output;
- 0.6.1.3 MoosasTransformer updated the invalid space filtering logic to make the recognition more stable

--- 0.6.0
# first commit
Moosas Ver.6.0

--- 0.5.1 
# Transformation Debug
new logic for searching/creating the coplan and the holes on floor/ceiling

--- 0.5.0 
# new environment solution
taking embedded python 3.11 for moosas!
now you should run moosas by python\python.exe [pythonFile.py] or python\pythonw.exe [pythonFile.py]

--- 0.4.10 
# 2LSB improvement and xml reconstruction
extrude the faces topology with the sharing edges
and print the topology to xml
now all ids in xml are the uid of faces

--- 0.4.9 
# 2LSB improvement
fix several bugs in 2LSB calculation for Transformation:
index error for void in MoosasElement.space
rearrange workflow to move the void attachment above the space construction
several geometry error in 2LSB calculation
improve interface and print layout of the whole transformation moudule

--- 0.4.8 
# spcace builder update
the space builder method are added into moosas+.
now users can add space by MoosasSpace.fromDict() or MoosasModel.fromDict()

--- 0.4.7 
# geometry input optimization
now all holes will automatically built as aperture (catgory ==2)

--- 0.4.6 
# Transformation void object iteration
add void space to moosas+ to solve the inner loop problem for some special space, like the loop corridor space.

--- 0.4.5 
# Transformation cleanse method iteration
make the redundant line/invalid wall/overlapped wall checking perform better, and create the groupByCollinear method.

--- 0.4.4 
# Transformation update
iterate the transformation method, using toponode/wall/network/boundary to be more stable

--- 0.4.3 
# Module rearrangement
Arrange all module in new folder to avoid circular import.
**Emergency: Energy analysis result is wrong since 0.3.2

--- 0.4.1 
# File Struecture Consistancy
Ensure all input and output file are in the same structure:<br>
Perfix '!' means following string are annotations until the end of the line;<br>
blocks are split by ';'<br>
data are split by '\n' <br>
empty lines are valid, it will be regraded as an empty data

--- 0.3.0
# 0.3.5 Improve Performance
Ventilation: Residual exit and irregular temperature identified have been added to ventilation.<br>
AFN: Heat load calculation has been improved and faster.<br>
transforming: solve_redundant_line method has been improved to be more stable and save.<br>
radiation: new calculation method on the whole model have been added, but the method is not save and need improvement in the future.<br>
weather: Deviation in simulating the cumulative sky has been fix by the global horizontal radiation in the weather file.

# 0.3.4 MoosasVent Update
Ventilation Analysis has been added to moosas+.
It provides analysis on bouyancy ventilation calculation and pressure driven ventilation.
Main module is ventilation.py, conread.py, afn.py and MoosasAFN.exe
more information you can call:
```console
MoosasAFN.exe -help
```
# 0.3.3 MoosasGrid Update
Griding method has been added to grid.py
The MoosasGrid class is based on MoosasElement and can be innitilized from MoosasElement

#0.3.2 MoosasRad Update
Now radiation calculation has been added into moosas+.
more information you can call:
```console
MoosasRad.exe -help
```
# 0.3.1 MoosasEnergy Update 
Now you can more flexibly call MoosasEnergy+ by command line (cmd). The execution is located in .\libs\energy For more information you can:
```console
MoosasEnergyPublic.exe -help
```
--- 0.2.0
# 0.2.1 Moosas+ Energy Update
Create moudule: standard, utils, energy, weather, constant
Those are which support the energy.analysis() method.
Now Users can call MoosasEnergy totally on python by following command:

```console
model = MoosasPy.transforming.transform(r'geo\selection0.geo',stdout=None)
model.loadWeatherData('545110')
for space in model.Moosasspacelist:
    space.applySettings('climatezone3_GB/T51350-2019_RESIDENTIAL')
eData=MoosasPy.energy.analysis(model)
```