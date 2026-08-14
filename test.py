import shapely, os
import numpy as np
import sys, re, time
from datetime import datetime
from MoosasPy import transform,saveModel,loadModel,includeEpw

file = r'temp\in.idf'
for geoFile in os.listdir(r'test'):
    if geoFile.endswith('.geo'):
        print(geoFile)
        geoFile = os.path.join(r'test',geoFile)
        model = transform(geoFile,attach_shading=True)
        saveModel(model,r'temp\out.idf',idfTemplate = file)
        # model = loadModel(file,'idf',xmlPath=r'temp\in.xml',geoPath=r'temp\in.geo')
