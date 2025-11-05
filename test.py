import pygeos, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,energyAnalysis,saveModel
from MoosasPy import IO,geometry,preprocess,vent

# owl = IO.IDFtoOWL(r'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\MO2IDF\1.idf')
# owl.serialize(r'test\IDF2OWL.ttl', format='ttl')
# idf = IO.OWLtoIDF(owl,r'test\OWL2IDF.idf')
# print(idf)
# raise Exception

# f = rf"\\166.111.40.8\protect\moosasTestModelDataset\_newcleaned\101_01901_01901-01.geo"
# model = transform(f,output_path=f'test\example.xml',
#                   solve_contains=True, divided_zones=False, break_wall_horizontal=True, solve_redundant=True,
#                   attach_shading=False, standardize=True)
#
# model.loadWeatherData()
# model.loadCumSky()
# eng = energyAnalysis(model)
# print(eng)
from MoosasPy import loadModel,vent
from MoosasPy.geometry import Vector
import MoosasPy

f = r'C:\Users\Lenovo\AppData\Roaming\SketchUp\SketchUp 2022\SketchUp\Plugins\pkpm-moosas\data\geometry\selection0.geo'
f = r'\\166.111.40.8\home\2025_MoosasEnergy\zhonghairuzhen.geo'
model = transform(f,solve_duplicated=True,
                  solve_contains=True, divided_zones=False, break_wall_horizontal=True, solve_redundant=True,
                  attach_shading=False, standardize=False)
# saveModel(model,r'C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.owl')
# model = loadModel(r'C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.owl')
# raise Exception
MoosasPy.weather.includeEpw(r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Shanghai.Shanghai.583620_CSWD.epw','shanghai')
model.loadWeatherData('583620')
model.loadCumSky('583620')
eng = energyAnalysis(model,core="办公建筑")
print(eng)
#
#
# Network = vent.afn.AfnNetwork(model)
#
# prjFile = r'E:\PycharmProjects\moosas\test\contamTest\afn_0x8028.prj'
# print(prjFile)
# # afn=vent.runFile(prjFile)
# # print(afn)
# flow = vent.readPathResult(prjFile,prjFile[:-4]+'.net')
# print(flow)
# # 		total horizontal faces: 22 skylights: 3
# # LOADING: Break walls 84/84			add walls:0
# # 		total vertical faces: 42 glazings: 35