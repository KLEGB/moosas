from MoosasPy import energy,loadModel

model = loadModel(r'.\test\test_v2.rdf')
heatModel = energy.heatLoadModel(model)

import json
with open(r'.\test\heatModel.json','w') as f:
    json.dump(heatModel.networkDict,f,indent=4)
