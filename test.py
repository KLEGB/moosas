import pygeos, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,energyAnalysis,saveModel,loadModel
from MoosasPy import IO,geometry,preprocess,vent

# owl = IO.IDFtoOWL(r'E:\PycharmProjects\moosas\MoosasPy\db\in.idf')
# owl.serialize('zoneTemplatebase.rdf')
# sg = IO._idf.extractZoneTemplate(owl)
# sg.serialize('zoneTemplate.rdf')


f = r'C:\Users\Lenovo\AppData\Roaming\SketchUp\SketchUp 2022\SketchUp\Plugins\pkpm-moosas\data\geometry\selection0.geo'
f = r'\\166.111.40.8\home\2025_MoosasEnergy\zhonghairuzhen.geo'
f = rf'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\test\dataset3\_7_in.geo'
f = rf'test\example0_c.geo'
# stdout = sys.stdout

# model = transform(f,
#                   geo_path=rf'test\example0_out.geo',
#                   triangulate_faces=False,
#                   solve_duplicated=True,solve_overlap=True, divided_zones=False,break_wall_vertical=True, break_wall_horizontal=True, solve_redundant=True,
#                   attach_shading=False, standardize=False)
# IO.writeRDF(model,r"test\example0_c.RDF")
geoFile = r'\\166.111.40.8\protect\moosasTestModelDataset\SRT_DATA\new_geo\cyh_25_01101_01101-01.geo'
xmlFile = r'\\166.111.40.8\protect\moosasTestModelDataset\SRT_DATA\new_xml\cyh_25_01101_01101-01.xml'
model = loadModel(xmlFile,geoFile,fileFormat='xml')
# IO.writeIDF(model,'test/test.idf')
