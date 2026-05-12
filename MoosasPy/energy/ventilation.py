from .analysis import getEnergyInput, ThermalSettings, energyAnalysis
from ..geometry.geos import Vector, Ray
from ..models import MoosasModel, MoosasCumSky
from ..rad import modelRadiation, writeRadGeo, rayTest
from ..utils import np, path, os
from numpy.linalg import LinAlgError
from ..vent.afn import AfnNetwork, buildPrj, buildZoneInfoFile, AfnPath, AfnZone
from ..vent.iteration import (
    iterateFile,
    contam_iteration,
    sensible_heat_iteration,
    write_contam,
    ZoneResult,
)
from ..vent import iteration as vent_iteration


def _linear_interpolate_nan_series(values):
    arr = np.array(values, dtype=float)
    if arr.size == 0:
        return []
    x = np.arange(arr.size)
    mask = np.isfinite(arr)
    if not mask.any() or mask.all():
        return arr.tolist()
    return np.interp(x, x[mask], arr[mask]).tolist()


def postprocess_zone_results_linear(zones: list[ZoneResult]) -> list[ZoneResult]:
    """
    Linearly interpolate NaN values for each zone time series.

    Parameters
    ----------
    zones : list[ZoneResult]
        Zone results containing `temperature` and `ACH` histories.

    Returns
    -------
    list[ZoneResult]
        Same objects with NaN values interpolated in-place.
    """
    for z in zones:
        z.temperature = _linear_interpolate_nan_series(z.temperature)
        z.ACH = _linear_interpolate_nan_series(z.ACH)
    return zones


class heatLoadModel(object):
    __slots__ = ['model', 'zones', 'paths', 'networkDict', 'skySeries', 'pathRadIntensity', 'runtime']
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
        self.runtime = {}
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
        """
        Update per-zone sensible heat load for a given hour of year.

        Parameters
        ----------
        hoy : int
            Hour-of-year index.
        energyDict : dict, optional
            Network dictionary override.

        Returns
        -------
        dict
            Updated `networkDict`.
        """

        if energyDict:
            self.networkDict = energyDict
        def _safe_float(value, default=0.0):
            if value is None:
                return default
            if isinstance(value, str) and value.strip().lower() in ("", "none", "null", "nan"):
                return default
            try:
                return float(value)
            except Exception:
                return default

        prjDict = {}
        for zUserName, zValue in self.networkDict['zones'].items():
            zone_area = _safe_float(zValue.get("zone_area"))
            heat = _safe_float(zValue.get('zone_ppsm')) * _safe_float(zValue.get('zone_popheat')) * zone_area
            heat += _safe_float(zValue.get('zone_equipment')) * zone_area
            heat += _safe_float(zValue.get('zone_lighting')) * zone_area
            self.networkDict['zones'][zUserName]['heatLoad'] = heat
            idx = self.networkDict['zones'][zUserName]['prjIndex']
            prjDict[idx] = zUserName
            prjDict[str(idx)] = zUserName
        for ps in self.networkDict['paths'].values():
            radHeat = self.pathRadIntensity[ps["userName"]][hoy] * float(ps['pathHeight']) * float(ps['pathWidth'])
            if ps["fromZone"] != "-1":
                zUserName = prjDict.get(ps["fromZone"])
                if zUserName is not None:
                    self.networkDict['zones'][zUserName]['heatLoad'] += radHeat
            elif ps["toZone"] != "-1":
                zUserName = prjDict.get(ps["toZone"])
                if zUserName is not None:
                    self.networkDict['zones'][zUserName]['heatLoad'] += radHeat
        return self.networkDict

    def buildNetwork(self, network):
        """
        Build merged ventilation-energy network dictionary.

        Parameters
        ----------
        network : AfnNetwork
            Airflow network object.

        Returns
        -------
        dict
            Combined network dictionary.
        """

        # network.checkTopology()
        # raise Exception
        # for z in network.zones:
        #     print(z.printHeatLoad())
        zoneDict = {z.userName: z.toDict() for z in network.zones}
        pathDict = {p.userName: p.toDict() for p in network.paths}
        energyDict = getEnergyInput(self.model, requireRadiation=True)
        for z in energyDict['zones']:
            for key in z.params.keys():
                zName = z.params['zone_name']
                if zName in zoneDict:
                    zoneDict[zName][key] = z.params[key]
        energyDict['paths'] = pathDict
        energyDict['zones'] = zoneDict
        return energyDict

    def reconstructEnergyInputs(self, energyDict: dict = None):
        """
        Reconstruct thermal energy-analysis inputs from network dictionary.

        Parameters
        ----------
        energyDict : dict, optional
            Network dictionary override.

        Returns
        -------
        dict
            Energy input structure for `energyAnalysis`.
        """
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        energyInput = {"zones": [], "args": energyDict['args']}
        for z in energyDict['zones'].values():
            theZone = {key: z[key] for key in self.ENERGY_INDEX}
            energyInput["zones"].append(ThermalSettings(**(theZone)))
        return energyInput

    def reconstructVentilationInputs(self, energyDict: dict = None):
        """
        Reconstruct AFN zones and paths objects from network dictionary.

        Parameters
        ----------
        energyDict : dict, optional
            Network dictionary override.

        Returns
        -------
        dict
            `{\"paths\": list[AfnPath], \"zones\": list[AfnZone]}`.
        """
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        paths = [AfnPath(**pathDict) for pathDict in energyDict['paths'].values()]
        zones = [{key: zoneDict[key] for key in self.AFN_INDEX} for zoneDict in energyDict['zones'].values()]
        zones = [AfnZone(**zoneDict) for zoneDict in zones]
        return {"paths": paths, "zones": zones}

    def energyTask(self, energyDict: dict = None):
        """
        Run one thermal-energy analysis task.

        Parameters
        ----------
        energyDict : dict, optional
            Network dictionary override.

        Returns
        -------
        dict
            Energy analysis result.
        """
        if energyDict:
            self.networkDict = energyDict
        energyDict = self.networkDict
        energyInput = self.reconstructEnergyInputs(energyDict)
        return energyAnalysis(energyInput=energyInput)

    def _sorted_zone_values(self):
        return sorted(self.networkDict['zones'].values(), key=lambda z: int(z['prjIndex']))

    def _zone_heat_array(self):
        return np.array([float(z['heatLoad']) for z in self._sorted_zone_values()])

    def _zone_result_template(self):
        zones = []
        for z in self._sorted_zone_values():
            zones.append(ZoneResult(
                name=f"z{int(z['prjIndex']):03d}",
                heat=float(z['heatLoad']),
                volume=float(z['volume']),
                userName=z['userName']
            ))
        return zones

    def _normalize_outdoor_temperature(self, outdoorTemperature, hoys):
        if isinstance(outdoorTemperature, (int, float)):
            return [float(outdoorTemperature)] * len(hoys)
        arr = np.array(outdoorTemperature).flatten().tolist()
        if len(arr) != len(hoys):
            raise ValueError("outdoorTemperature array length must equal number of hoys.")
        return [float(x) for x in arr]

    def _ensure_runtime_workspace(self, reset=False):
        """
        Prepare isolated per-task workspace under ``__temp__`` and remap vent FilePath.

        Parameters
        ----------
        reset : bool, default False
            Whether to always create a new random workspace.
        """
        if (not reset) and self.runtime.get('workspace'):
            ws = self.runtime['workspace']
            if os.path.exists(ws.get('root', '')):
                return ws

        token = f"{int(os.times().elapsed * 1000)}_{os.getpid()}_{np.random.randint(1000, 9999)}"
        root = os.path.join(path.tempDir, f"vent_task_{token}")
        project_dir = os.path.join(root, "project")
        result_dir = os.path.join(root, "result")
        room_info_file = os.path.join(root, "roomInfo.txt")
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(result_dir, exist_ok=True)

        if 'filepath_backup' not in self.runtime:
            self.runtime['filepath_backup'] = {
                'project_dir': vent_iteration.FilePath.get('project_dir'),
                'result_dir': vent_iteration.FilePath.get('result_dir'),
                'roomInfo': vent_iteration.FilePath.get('roomInfo'),
            }

        vent_iteration.FilePath['project_dir'] = project_dir
        vent_iteration.FilePath['result_dir'] = result_dir
        vent_iteration.FilePath['roomInfo'] = room_info_file

        ws = {
            'root': root,
            'project_dir': project_dir,
            'result_dir': result_dir,
            'room_info_file': room_info_file,
        }
        self.runtime['workspace'] = ws
        self.runtime['prj_counter'] = 0
        return ws

    def _preheat(self, hoys, outdoor_series, preheat, energyDict=None):
        peak_hoy = hoys[0]
        peak_sum = -float("inf")
        for hoy in hoys:
            self.updateHeatLoad(hoy, energyDict=energyDict)
            this_sum = sum(float(z['heatLoad']) for z in self.networkDict['zones'].values())
            if this_sum > peak_sum:
                peak_sum = this_sum
                peak_hoy = hoy

        self.updateHeatLoad(peak_hoy, energyDict=energyDict)
        venNetwork = self.reconstructVentilationInputs()
        zone_info = buildZoneInfoFile(zoneList=venNetwork['zones'], pathList=venNetwork['paths'])
        prj_file = buildPrj(
            zoneList=venNetwork['zones'],
            pathList=venNetwork['paths'],
            prjFilePath=self._next_workspace_prj_path("preheat")
        )
        peak_t = outdoor_series[hoys.index(peak_hoy)]
        for _ in range(max(int(preheat), 0)):
            AFN = contam_iteration(prj_file)
            temperature = sensible_heat_iteration(AFN=AFN, zoneInfo=zone_info, outdoorTemperature=peak_t)
            prj_file = write_contam(temperature=temperature, prjFile=prj_file)
        return prj_file

    def _next_workspace_prj_path(self, prefix="afn"):
        ws = self._ensure_runtime_workspace(reset=False)
        idx = int(self.runtime.get('prj_counter', 0)) + 1
        self.runtime['prj_counter'] = idx
        return os.path.join(ws['project_dir'], f"{prefix}_{idx:06d}.prj")

    def ventilationTask(self, hoy, energyDict: dict = None, iteration=1, mode="onions"):
        """
        Run one-hour ventilation coupling task in selected mode.

        Parameters
        ----------
        hoy : int
            Hour-of-year index.
        energyDict : dict, optional
            Network dictionary override.
        iteration : int, default 1
            Coupling iterations per hour (ignored in `sequence`).
        mode : {"onions", "sequence", "ping-pong"}, default "onions"
            Coupling strategy.

        Returns
        -------
        list[ZoneResult]
            One-hour result snapshot.
        """
        self._ensure_runtime_workspace(reset=False)
        if energyDict:
            self.networkDict = energyDict
        self.updateHeatLoad(hoy, energyDict=energyDict)
        venNetwork = self.reconstructVentilationInputs(self.networkDict)
        zText = buildZoneInfoFile(zoneList=venNetwork['zones'], pathList=venNetwork['paths'])

        if mode == "onions":
            zoneInfoFilePath = os.path.join(path.tempDir, f"zoneinfo_{hoy}.info")
            zFile = buildZoneInfoFile(
                zoneList=venNetwork['zones'],
                pathList=venNetwork['paths'],
                zoneInfoFilePath=zoneInfoFilePath
            )
            prjFile = self.runtime.pop('onions_prj', None)
            if prjFile is None:
                prjFile = buildPrj(
                    zoneList=venNetwork['zones'],
                    pathList=venNetwork['paths'],
                    prjFilePath=self._next_workspace_prj_path("onions")
                )
            return iterateFile(
                prjFile,
                zFile,
                maxIteration=iteration,
                outdoorTemperature=self.runtime.get('outdoor_temperature', 25)
            )

        zones = self._zone_result_template()
        if mode == "sequence":
            AFN = self.runtime.get('AFN_ref')
            if AFN is None:
                raise ValueError("AFN_ref is not prepared for sequence mode.")
            temperature = sensible_heat_iteration(
                AFN=AFN, zoneInfo=zText, outdoorTemperature=self.runtime.get('outdoor_temperature', 25)
            )
            achIteration = [max(x, y) for x, y in zip(AFN[-1], AFN[:, -1])]
            tC = (np.array(temperature) - 273.15).flatten().tolist()
            for i in range(len(zones)):
                zones[i].temperature.append(tC[i])
                zones[i].ACH.append(achIteration[i])
            return zones

        if mode == "ping-pong":
            current_prj = self.runtime.get('current_prj')
            if current_prj is None:
                current_prj = buildPrj(
                    zoneList=venNetwork['zones'],
                    pathList=venNetwork['paths'],
                    prjFilePath=self._next_workspace_prj_path("pingpong")
                )
            last_AFN = None
            last_t = None
            for _ in range(max(int(iteration), 1)):
                last_AFN = contam_iteration(current_prj)
                last_t = sensible_heat_iteration(
                    AFN=last_AFN, zoneInfo=zText, outdoorTemperature=self.runtime.get('outdoor_temperature', 25)
                )
                current_prj = write_contam(temperature=last_t, prjFile=current_prj)
            self.runtime['current_prj'] = current_prj
            achIteration = [max(x, y) for x, y in zip(last_AFN[-1], last_AFN[:, -1])]
            tC = (np.array(last_t) - 273.15).flatten().tolist()
            for i in range(len(zones)):
                zones[i].temperature.append(tC[i])
                zones[i].ACH.append(achIteration[i])
            return zones

        raise ValueError("mode must be one of ['onions', 'sequence', 'ping-pong'].")

    def annualComfort(self, energyDict: dict = None, iteration=1, mode="onions", timestep=1,
                      outdoorTemperature=25, preheat=10):
        """
        Run annual ventilation comfort simulation with selectable coupling strategy.

        Parameters
        ----------
        energyDict : dict, optional
            Network dictionary override.
        iteration : int, default 1
            Per-hour coupling iterations (ignored in `sequence` mode).
        mode : {"onions", "sequence", "ping-pong"}, default "onions"
            Annual coupling strategy.
        timestep : int, default 1
            Hour step size. Number of hoy samples is `len(range(0, 8760, timestep))`.
        outdoorTemperature : float or array-like, default 25
            Scalar outdoor temperature or a per-hoy array aligned with sampled hoys.
        preheat : int, default 10
            Bootstrap ping-pong rounds at peak-load hour to generate initial project state.

        Returns
        -------
        list[ZoneResult]
            Annual zone results with sampled hourly `temperature` and `ACH` histories.
        """
        self._ensure_runtime_workspace(reset=True)
        if energyDict:
            self.networkDict = energyDict
        if int(timestep) <= 0:
            raise ValueError("timestep must be a positive integer.")
        hoys = list(range(0, 8760, int(timestep)))
        outdoor_series = self._normalize_outdoor_temperature(outdoorTemperature, hoys)

        preheated_prj = self._preheat(hoys=hoys, outdoor_series=outdoor_series, preheat=preheat, energyDict=energyDict)

        if mode == "sequence":
            AFN_ref = contam_iteration(preheated_prj)
            self.runtime['AFN_ref'] = AFN_ref
        elif mode == "ping-pong":
            self.runtime['current_prj'] = preheated_prj
        elif mode == "onions":
            self.runtime['onions_prj'] = preheated_prj
        else:
            raise ValueError("mode must be one of ['onions', 'sequence', 'ping-pong'].")

        zResult = None
        for hi, hoy in enumerate(hoys):
            print("--------------------Hoy:", hoy)
            self.runtime['outdoor_temperature'] = outdoor_series[hi]
            try:
                zResultHoy = self.ventilationTask(
                    hoy=hoy,
                    energyDict=energyDict,
                    iteration=iteration if mode != "sequence" else 1,
                    mode=mode
                )
            except LinAlgError as e:
                if "Singular matrix" not in str(e):
                    raise
                if zResult is None:
                    self.updateHeatLoad(hoy, energyDict=energyDict)
                    zResult = self._zone_result_template()
                for i in range(len(zResult)):
                    zResult[i].temperature += [np.nan]
                    zResult[i].ACH += [np.nan]
                print(f"Warning: Singular matrix at hoy={hoy}, filled NaN for this timestep.")
                continue
            except Exception as e:
                if zResult is None:
                    self.updateHeatLoad(hoy, energyDict=energyDict)
                    zResult = self._zone_result_template()
                for i in range(len(zResult)):
                    zResult[i].temperature += [np.nan]
                    zResult[i].ACH += [np.nan]
                print(f"Warning: Exception at hoy={hoy} ({type(e).__name__}: {e}), filled NaN for this timestep.")
                continue
            if (not zResultHoy) or len(zResultHoy[0].temperature) == 0 or len(zResultHoy[0].ACH) == 0:
                if zResult is None:
                    self.updateHeatLoad(hoy, energyDict=energyDict)
                    zResult = self._zone_result_template()
                for i in range(len(zResult)):
                    zResult[i].temperature += [np.nan]
                    zResult[i].ACH += [np.nan]
                print(f"Warning: Empty result at hoy={hoy}, filled NaN for this timestep.")
                continue
            if zResult is None:
                zResult = zResultHoy
                for i in range(len(zResult)):
                    zResult[i].temperature = [zResult[i].temperature[-1]]
                    zResult[i].ACH = [zResult[i].ACH[-1]]
            else:
                for i in range(len(zResultHoy)):
                    zResult[i].temperature += [zResultHoy[i].temperature[-1]]
                    zResult[i].ACH += [zResultHoy[i].ACH[-1]]
        return postprocess_zone_results_linear(zResult)
