import eppy
from eppy.modeleditor import IDF
import os

_ENERGYPLUS_DIR = r"C:/EnergyPlusV23-1-0"
idd = os.path.join(_ENERGYPLUS_DIR, "Energy+.idd")
IDF.setiddname(idd)
f = IDF(r'\\166.111.40.8\home\2024_MOOSASIDF_BS2025\MO2IDF\1.idf')
