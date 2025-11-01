import os
from MoosasPy import iterateProjects
prjfiles = [for f in os.listdir(C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/libs/vent/thermal) if f.endswith(.prj)]
zonefiles = [for f in os.listdir(C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/libs/vent/thermal) if f.endswith(.heat)]
iterateProjects(prjfiles,zonefiles,C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm_moosas/data/vent/resultconcatResult.csv,outdoorTemperature=20.0,maxIteration=10)
