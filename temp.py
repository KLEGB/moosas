import eppy
from eppy.modeleditor import IDF
import os

IDF.setiddname(r'MoosasPy/db/Energy+.idd')
idf = IDF(r'MoosasPy/db/in.idf')
inft = idf.idfobjects['ZoneInfiltration:DesignFlowRate'][0]
