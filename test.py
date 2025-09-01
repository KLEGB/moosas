import pygeos, os
import numpy as np
import sys, re, time
os.chdir(r'C:\\')
from datetime import datetime
from MoosasPy import transform,energyAnalysis
from MoosasPy import IO,geometry,preprocess

f = rf"\\166.111.40.8\protect\CUGER_Daylight\evomass\geo"
model = transform(f,output_path=f'test\example.xml',
                  solve_contains=True, divided_zones=False, break_wall_horizontal=True, solve_redundant=True,
                  attach_shading=False, standardize=True)

model.loadWeatherData()
model.loadCumSky()
eng = energyAnalysis(model)
print(eng)
