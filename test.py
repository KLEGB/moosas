import pygeos, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,energyAnalysis
from MoosasPy import IO,geometry,preprocess

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


f = r'C:\Users\Lenovo\AppData\Roaming\SketchUp\SketchUp 2022\SketchUp\Plugins\pkpm-moosas\data\geometry\selection0.geo'
model = transform(f,solve_duplicated=True,
                  solve_contains=True, divided_zones=False, break_wall_horizontal=True, solve_redundant=True,
                  attach_shading=False, standardize=False)

# 		total horizontal faces: 22 skylights: 3
# LOADING: Break walls 84/84			add walls:0
# 		total vertical faces: 42 glazings: 35