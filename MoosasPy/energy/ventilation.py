from .analysis import getEnergyInput, ThermalSettings, energyAnalysis
from ..geometry.geos import Vector, Ray
from ..models import MoosasModel, MoosasCumSky
from ..rad import modelRadiation, writeRadGeo, rayTest
from ..utils import np, path, os
from ..vent.afn import AfnNetwork, buildPrj, buildZoneInfoFile, AfnPath, AfnZone
from ..vent.iteration import iterateFile


class heatLoadModel(object):
    __slots__ = ['model', 'zones', 'paths', 'networkDict', 'skySeries', 'pathRadIntensity']
    ENERGY_INDEX = ["space_height", "zone_area", "outside_area", "facade_area", "window_area", "roof_area",
                    "skylight_area", "floor_area",
                    "summer_solar", "winter_solar", "zone_wallU", "zone_winU", "zone_win_SHGC", "zone_c_temp",
                    "zone_c_hum", "zone_h_temp",
                    "zone_collingEER", "zone_HeatingEER", "zone_work_start", "zone_work_end", "zone_ppsm", "zone_pfav",
                    "zone_popheat",
                    "zone_equipment", "zone_lighting", "zone_infiltration", "zone_nightACH", "zone_name",
                    "zone_summerrad", "zone_winterrad", "zone_template"
                    ]
    AFN_INDEX = ['userName', 'temperature', 'prjIndex', 'heatLoad', 'volume', 'position_x', 'position_y', 'position_z',
                 'boundary']

    def __init__(self, model: MoosasModel, stationid='545110'):
        print("-----------------------\nPrepareing network...\n-----------------------")
        import time
        t0 = time.time()
        self.model = model
        self.model.loadCumSky(stationid)
        modelRadiation(self.model, reflection=0)
        network = AfnNetwork(self.model)
        self.zones = network.zones
        self.paths = network.paths
        self.networkDict = self.buildNetwork(network)
        self.pathRadIntensity = {ps.userName: [] for ps in self.paths}
        print("-----------------------\nPrepareing cumSky series...\n-----------------------")
        print(time.time() - t0)
        t0 = time.time()
        self.skySeries = []
        with open(os.path.join(path.dataBaseDir, 'cum_sky', f'cumsky_{stationid}.csv')) as f:
            cumValue = np.array([line.split(',') for line in f.read().split('\n') if len(line) > 1]).astype(float)
            for i in range(8760):
                self.skySeries.append(MoosasCumSky(cumValue[:, i] / MoosasCumSky.FIX_RADIATION))

        print("-----------------------\nCalculating path radiation intensity...\n-----------------------")
        print(time.time() - t0)
        t0 = time.time()
        rays = []
        fixMatrix = []
        for ps in self.paths:
            origin = Vector(ps.position_x, ps.position_y, ps.position_z)
            thisRays = [Ray(origin, pos) for pos in self.skySeries[0].position]
            rays += thisRays
            fixMatrix.append(np.array([abs(Vector.dot(ps.element.normal, r.direction)) for r in thisRays]))
        rays = np.array(rays)
        geo_path = writeRadGeo(model)
        resRay = rayTest(rays, geo_path=geo_path)
        resRay = np.array([1.0 if r is not None else 0 for r in resRay])
        resRay = resRay.reshape(len(self.paths), int(len(resRay) / len(self.paths)))

        for i, ps in enumerate(self.paths):
            for sky in self.skySeries:
                self.pathRadIntensity[ps.userName].append(np.sum(resRay[i] * sky.value * fixMatrix[i]) * 1000)
        print("-----------------------\nNetwork Ready...\n-----------------------")
        print(time.time() - t0)
        t0 = time.time()

    def updateHeatLoad(self, hoy, energyDict: dict = None):

        if energyDict:
            self.networkDict = energyDict
        prjDict = {}
        for zUserName, zValue in self.networkDict['zones'].items():
            heat = float(zValue['zone_ppsm']) * float(zValue['zone_popheat']) * float(zValue["zone_area"])
            heat += float(zValue['zone_equipment']) * float(zValue["zone_area"])
            heat += float(zValue['zone_lighting']) * float(zValue["zone_area"])
            self.networkDict['zones'][zUserName]['heatLoad'] = heat
            prjDict[self.networkDict['zones'][zUserName]['prjIndex']] = zUserName
        for ps in self.networkDict['paths'].values():
            radHeat = self.pathRadIntensity[ps["userName"]][hoy] * float(ps['pathHeight']) * float(ps['pathWidth'])
            if ps["fromZone"] != "-1":
                zUserName = prjDict[ps["fromZone"]]
                self.networkDict['zones'][zUserName]['heatLoad'] += radHeat
            elif ps["toZone"] != "-1":
                zUserName = prjDict[ps["toZone"]]
                self.networkDict['zones'][zUserName]['heatLoad'] += radHeat
        return self.networkDict

    def buildNetwork(self, network):

        # network.checkTopology()
        # raise Exception
        # for z in network.zones:
        #     print(z.printHeatLoad())
        zoneDict = {z.userName: z.toDict() for z in network.zones}
        pathDict = {p.userName: p.toDict() for p in network.paths}
        energyDict = getEnergyInput(self.model, require_radiation=True)
        for z in energyDict['zones']:
            for key in z.params.keys():
                zName = z.params['zone_name']
                if zName in zoneDict:
                    zoneDict[zName][key] = z.params[key]
        energyDict['paths'] = pathDict
        energyDict['zones'] = zoneDict
        return energyDict

    def reconstructEnergyInputs(self, energyDict: dict = None):
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        energyInput = {"zones": [], "args": energyDict['args']}
        for z in energyDict['zones'].values():
            theZone = {key: z[key] for key in self.ENERGY_INDEX}
            energyInput["zones"].append(ThermalSettings(**(theZone)))
        return energyInput

    def reconstructVentilationInputs(self, energyDict: dict = None):
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        paths = [AfnPath(**pathDict) for pathDict in energyDict['paths'].values()]
        zones = [{key: zoneDict[key] for key in self.AFN_INDEX} for zoneDict in energyDict['zones'].values()]
        zones = [AfnZone(**zoneDict) for zoneDict in zones]
        return {"paths": paths, "zones": zones}

    def energyTask(self, energyDict: dict = None):
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        energyInput = self.reconstructEnergyInputs(energyDict)
        return energyAnalysis(energyInput=energyInput)

    def ventilationTask(self, hoy, energyDict: dict = None, iteration=1):
        if energyDict:
            self.networkDict = energyDict
        self.updateHeatLoad(hoy)
        energyDict = self.networkDict
        venNetwork = self.reconstructVentilationInputs(energyDict)
        zFile = buildZoneInfoFile(zoneList=venNetwork['zones'], pathList=venNetwork['paths'])
        prjFile = buildPrj(zoneList=venNetwork['zones'], pathList=venNetwork['paths'])
        zones = iterateFile(prjFile, zFile, maxIteration=iteration)
        return zones

    def annualComfort(self, energyDict: dict = None, iteration=1):
        zResult = self.ventilationTask(hoy=0, energyDict=energyDict, iteration=iteration)
        for i, zR in enumerate(zResult):
            zResult[i].temperature = [zResult[i].temperature[-1]]
            zResult[i].ACH = [zResult[i].ACH[-1]]
        for hoy in range(1, 8760):
            print("--------------------Hoy:", hoy)
            zResultHoy = self.ventilationTask(hoy=hoy, energyDict=energyDict, iteration=iteration)
            for i, zR in enumerate(zResultHoy):
                zResult[i].temperature += [zResultHoy[i].temperature[-1]]
                zResult[i].ACH += [zResultHoy[i].ACH[-1]]
        return zResult
