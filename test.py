import shapely, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,saveModel,loadModel,includeEpw



# owl = IO.IDFtoOWL(r'E:\PycharmProjects\moosas\MoosasPy\db\in.idf')
# owl.serialize('zoneTemplatebase.rdf')
# sg = IO._idf.extractZoneTemplate(owl)
# sg.serialize('zoneTemplate.rdf')
# includeEpw(r"//166.111.40.8/home/2026_MoosasAFN/N-building/climate_data/epw543990.epw",city="Beijing-Haidian")
# stdout = sys.stdout
# model = transform(r'\\166.111.40.8\home\2026_MoosasAFN\NBuilding-2018.geo',
#                   triangulate_faces=False,
#                   solve_duplicated=True,solve_overlap=True, divided_zones=False,break_wall_vertical=True, break_wall_horizontal=True, solve_redundant=True,
#                   attach_shading=False, standardize=True)
model = loadModel(r'test\NBuilding.rdf')
# for spc in model.spaceList:
#     spc.applySettings("climatezone2_GB55015-2021_OFFICE")

saveModel(model,r'test\NBuilding.rdf')
saveModel(model,r'test\NBuilding_out.geo')
saveModel(model,r'test\NBuilding.xml')

# # for spc in model.spaceList:
# #     print(spc.settings)
# from MoosasPy.energy import energyAnalysis
# res = energyAnalysis(model)
# print(res)
# from MoosasPy.energy import roofAnnualGeneration,facadeAnnualGeneration
# res = roofAnnualGeneration(model)
# res2 = facadeAnnualGeneration(model)
# print(res2)
# IO.writeRDF(model,r"test\example0_c.RDF")
# geoFile = r'\\166.111.40.8\protect\moosasTestModelDataset\SRT_DATA\new_geo\cyh_25_01101_01101-01.geo'
# xmlFile = r'\\166.111.40.8\protect\moosasTestModelDataset\SRT_DATA\new_xml\cyh_25_01101_01101-01.xml'
# model = loadModel(xmlFile,geoFile,fileFormat='xml')
# IO.writeIDF(model,'test/test.idf')
