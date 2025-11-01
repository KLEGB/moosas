import traceback
try:
    from MoosasPy import loadModel,vent
    from MoosasPy.geometry import Vector
    import json
    netWork,prjFile,zoneFile,netFile = [],[],[],[]
    model = loadModel('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/geometry/selection0.owl')
    net = vent.afn.AfnNetwork(model)
    net.applyWindPressure(windVector=Vector(0.7071067811865476,0.7071067811865476,0),speed=3.0,alpha=0.22)
    # net.applyZoneHeat('C:/Users/Lenovo/AppData/Roaming/SketchUp/SketchUp 2022/SketchUp/Plugins/pkpm-moosas/data/vent/zInfo.heat')
    for zone in net.zones:
         zone.temperature = 20.0
    netWork.append(net)
    for net in netWork:
         prjFile.append(net.toPrj())
         zoneFile.append(net.toZoneFile())
         netFile.append(net.toFile())
    vent.runFile(prjFile)
    pathResult = {}
    for prj,nFile in zip(prjFile,netFile):
        prjJson = vent.readPathResult(prj,nFile)
        for key,value in prjJson.items():
            pathResult[key] = value

    with open('status.log','w+') as f:
        f.write('1')
except Exception as e:
    print(traceback.format_exc())
    with open('error.log','w+') as f:
        f.write(traceback.format_exc())
    with open('status.log','w+') as f:
        f.write('0')
