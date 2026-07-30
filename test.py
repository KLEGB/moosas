import shapely, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,saveModel,loadModel,includeEpw

file = r'temp\in.idf'
geoFile = r'test\test.geo'

model = transform(geoFile)
saveModel(model,r'temp\out.idf',idfTemplate = file)
# model = loadModel(file,'idf',xmlPath=r'temp\in.xml',geoPath=r'temp\in.geo')