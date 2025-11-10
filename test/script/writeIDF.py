import traceback

from MoosasPy import loadModel,IO
model = loadModel('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/moosas/data/geometry/selection0.owl')
IO.writeIDF('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/moosas/data/energy/selection0.idf',model,r'G:\Ph.D\2024_MOOSASIDF_BS2025\idfTestingSet\ORIIDF\1028_17_46_89_255_ORI.idf')
with open('status.log','w+') as f:
	f.write('1')
