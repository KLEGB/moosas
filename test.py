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
f = rf'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\test\dataset3\_7_in.geo'
# stdout = sys.stdout

model = transform(f,
                  output_path=rf'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\test\dataset3\_7_topology.xml',
                  geo_path=rf'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\test\dataset3\_7_out.geo',
                  triangulate_faces=False,
                  solve_duplicated=True,solve_overlap=True, divided_zones=False,break_wall_vertical=True, break_wall_horizontal=True, solve_redundant=True,
                  attach_shading=False, standardize=False)
    # sys.stdout = stdout
    # model.summary()
# saveModel(model,r'C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.owl')
# model = loadModel(r'C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.owl')
# raise Exception
# MoosasPy.weather.includeEpw(r'C:\EnergyPlusV22-2-0\WeatherData\CHN_Shanghai.Shanghai.583620_CSWD.epw','shanghai')
model.loadWeatherData('583620')
model.loadCumSky('583620')

IO.writeIDF(r'test/testIDF.idf',model)
# eng = energyAnalysis(model,core="办公建筑")
# print(eng)
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
# --------------------
# Program finish. Summary:
# LEVEL		WALL		GLS		SKY		FACE		SPACE		AREA
# 0.00		212(0)		52		0		47		45		6685.8
# 4.84		319(-60)		194		2		192		64		5908.3
# 8.15		451(-11)		141		0		118		29		2238.3
# 11.45		451(-11)		141		1		116		99		10362.4
# 14.75		451(-11)		141		0		123		26		2002.4
# 18.05		278(-5)		84		19		314		69		5695.7
# 21.35		278(-5)		84		0		75		69		5695.7
# 24.65		0(0)		0		0		75		0		0.0
#     		2440(-103)		837		22		1060		401		38588.5
# --------------------
# I/O                0.000s	0.0%
# Data Structuring   32.194s	25.5%	 ■■■■■■■■■■■■
# Data Cleansing     30.283s	24.0%	 ■■■■■■■■■■■■
# 1LSB Calculation   16.340s	13.0%	 ■■■■■■
# Space Construction 38.964s	30.9%	 ■■■■■■■■■■■■■■■
# 2LSB Calculation   8.236s	6.5%	 ■■■
# Content attachment 0.000s	0.0%
# Total Duration     126.017s	100%

# --------------------
# Program finish. Summary:
# LEVEL		WALL		GLS		SKY		FACE		SPACE		AREA
# 0.00		214(0)		52		0		46		42		5016.4
# 4.84		465(-2)		141		0		192		110		11723.6
# 8.15		465(-2)		141		0		122		114		12489.1
# 11.45		465(-2)		141		0		120		77		10404.2
# 14.75		465(-2)		141		0		128		62		6150.6
# 18.05		283(0)		84		0		289		61		5657.2
# 21.35		283(0)		84		0		74		50		4602.2
# 24.65		0(0)		0		0		74		0		0.0
#     		2640(-8)		784		0		1045		516		56043.2
# --------------------
# I/O                0.000s	0.0%
# Data Structuring   18.120s	18.2%	 ■■■■■■■■■
# Data Cleansing     12.769s	12.9%	 ■■■■■■
# 1LSB Calculation   23.742s	23.9%	 ■■■■■■■■■■■
# Space Construction 35.333s	35.6%	 ■■■■■■■■■■■■■■■■■
# 2LSB Calculation   9.392s	9.5%	 ■■■■
# Content attachment 0.000s	0.0%
# Total Duration     99.357s	100%
