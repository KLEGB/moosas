from .analysis import getEnergyInput, ThermalSettings, energyAnalysis
from ..geometry.geos import Vector, Ray
from ..models import MoosasModel, MoosasCumSky
from ..weather.dest import MoosasWeather
from ..weather.cumsky import MoosasCumSky
from ..rad import modelRadiation, writeRadGeo, rayTest
from ..utils import np, path, os
from ..utils.date import DateTime
from numpy.linalg import LinAlgError
from ..vent.afn import AfnNetwork, buildPrj, buildZoneInfoFile, AfnPath, AfnZone
from ..vent.iteration import (
    iterateFile,
    contam_iteration,
    sensible_heat_iteration,
    write_contam,
    readPathResult,
    ZoneResult,
)
from ..vent import iteration as vent_iteration
import networkx as nx
from copy import deepcopy


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
    __slots__ = [
        'model', 'zones', 'paths', 'networkDict', 'skySeries', 'pathRadIntensity', 'runtime',
        'schedulePath', '_sch_daily_map', '_sch_weekly_map', 'weather'
    ]
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
    LPG_OUTSIDE_NODE = "OUTSIDE"
    LPG_ZONE_FIELDS = ("zone_wallU", "zone_winU", "zone_win_SHGC")
    LPG_PATH_FIELDS = ("pathHeight", "pathWidth", "pressure")

    def __init__(self, model: MoosasModel, stationid='545110',
                 schedulePath=os.path.join(path.dataBaseDir, 'office.sch')):
        print("-----------------------\nPrepareing network...\n-----------------------")
        import time
        t0 = time.time()
        self.model = model
        self.schedulePath = schedulePath
        self._sch_daily_map = {}
        self._sch_weekly_map = {}
        self._parse_schedule_file()
        self.weather = MoosasWeather(stationid)
        self.model.loadCumSky(stationid)
        modelRadiation(self.model, reflection=0)
        network = AfnNetwork(self.model)
        self.zones = network.zones
        self.paths = network.paths
        self.networkDict = self.buildNetwork(network)
        self._normalize_operable_once(value=0.5)
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

    def _normalize_operable_once(self, value=0.5):
        if not isinstance(self.networkDict, dict):
            return
        for p in self.networkDict.get("paths", {}).values():
            p["operable"] = value

    def _parse_schedule_file(self):
        self._sch_daily_map = {}
        self._sch_weekly_map = {}
        if self.schedulePath is None:
            return
        schedule_path = os.path.abspath(self.schedulePath)
        if not os.path.isfile(schedule_path):
            raise FileNotFoundError(f"Schedule file not found: {schedule_path}")
        with open(schedule_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                text = line.strip()
                if (not text) or text.startswith("!"):
                    continue
                parts = [p.strip() for p in text.split(",")]
                if len(parts) < 3:
                    continue
                name = parts[0]
                mode = parts[1].lower()
                if mode == "daily":
                    if len(parts) < 26:
                        raise ValueError(f"Invalid daily schedule row '{name}', expected 24 hourly values.")
                    try:
                        self._sch_daily_map[name] = [float(v) for v in parts[2:26]]
                    except Exception as e:
                        raise ValueError(f"Invalid numeric value in daily schedule '{name}': {e}")
                elif mode == "weekly":
                    if len(parts) < 9:
                        raise ValueError(f"Invalid weekly schedule row '{name}', expected 7 day references.")
                    self._sch_weekly_map[name] = parts[2:9]

    def _value_from_schedule(self, schedule_name, hoy):
        if schedule_name in self._sch_weekly_map:
            week_refs = self._sch_weekly_map[schedule_name]
            dt = DateTime.from_hoy(float(hoy))
            daily_name = week_refs[dt.weekday()]
            if daily_name not in self._sch_daily_map:
                raise ValueError(
                    f"Weekly schedule '{schedule_name}' references missing daily schedule '{daily_name}'."
                )
            return self._sch_daily_map[daily_name][dt.hour]
        if schedule_name in self._sch_daily_map:
            dt = DateTime.from_hoy(float(hoy))
            return self._sch_daily_map[schedule_name][dt.hour]
        raise KeyError(schedule_name)

    def _resolve_gain_value(self, raw_value, hoy, field_name, zone_name):
        if raw_value is None:
            return 0.0
        if isinstance(raw_value, str) and raw_value.strip().lower() in ("", "none", "null", "nan"):
            return 0.0
        try:
            return float(raw_value)
        except Exception:
            pass
        if self.schedulePath is None:
            raise ValueError(
                f"Zone '{zone_name}' field '{field_name}' uses schedule name '{raw_value}' "
                f"but schedulePath is None."
            )
        try:
            # Heatload is treated as instantaneous power (W), so schedule-driven
            # internal gains are aligned to a fixed baseline hour instead of
            # accumulating/changing with hoy.
            return float(self._value_from_schedule(str(raw_value), 0))
        except KeyError:
            raise ValueError(
                f"Schedule '{raw_value}' for zone '{zone_name}' field '{field_name}' not found in "
                f"'{os.path.abspath(self.schedulePath)}'."
            )

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
            zone_ppsm = self._resolve_gain_value(zValue.get('zone_ppsm'), hoy, 'zone_ppsm', zUserName)
            zone_equipment = self._resolve_gain_value(zValue.get('zone_equipment'), hoy, 'zone_equipment', zUserName)
            zone_lighting = self._resolve_gain_value(zValue.get('zone_lighting'), hoy, 'zone_lighting', zUserName)
            zone_popheat = _safe_float(zValue.get('zone_popheat'))
            heat = zone_ppsm * zone_popheat * zone_area
            heat += zone_equipment * zone_area
            heat += zone_lighting * zone_area
            self.networkDict['zones'][zUserName]['heatLoad'] = heat
            idx = self.networkDict['zones'][zUserName]['prjIndex']
            prjDict[idx] = zUserName
            prjDict[str(idx)] = zUserName

        for ps in self.networkDict['paths'].values():
            # Keep AFN heatload power baseline fixed at the initial hour.
            pid = ps["userName"]
            if pid not in self.pathRadIntensity:
                self.pathRadIntensity[pid] = [0.0] * 8760
            radHeat = self.pathRadIntensity[pid][hoy] * float(ps['pathHeight']) * float(ps['pathWidth'])
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
        energyDict = getEnergyInput(self.model, requireRadiation=True, schedulePath=self.schedulePath)
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

    def networkDict_to_lpg(self, energyDict: dict = None):
        """
        Convert network dictionary to a zone-node/path-edge LPG.

        Returns
        -------
        nx.MultiDiGraph
            Zone nodes with selected zone attributes and directed path edges.
        """
        if energyDict is not None:
            self.networkDict = energyDict
        energyDict = self.networkDict

        graph = nx.MultiDiGraph()
        graph.add_node(self.LPG_OUTSIDE_NODE)

        zones = energyDict.get("zones", {})
        paths = energyDict.get("paths", {})

        prj_to_node = {}
        for zone_key, zone in zones.items():
            node_id = zone.get("userName", zone_key)
            prj_idx = str(zone.get("prjIndex"))
            prj_to_node[prj_idx] = node_id
            graph.add_node(
                node_id,
                zone_wallU=zone.get("zone_wallU"),
                zone_winU=zone.get("zone_winU"),
                zone_win_SHGC=zone.get("zone_win_SHGC"),
            )

        for path_key, path_value in paths.items():
            from_zone = str(path_value.get("fromZone"))
            to_zone = str(path_value.get("toZone"))
            if from_zone == "-1":
                u = self.LPG_OUTSIDE_NODE
            else:
                if from_zone not in prj_to_node:
                    raise ValueError(
                        f"Path '{path_key}' has fromZone='{from_zone}' but no matching zone.prjIndex."
                    )
                u = prj_to_node[from_zone]
            if to_zone == "-1":
                v = self.LPG_OUTSIDE_NODE
            else:
                if to_zone not in prj_to_node:
                    raise ValueError(
                        f"Path '{path_key}' has toZone='{to_zone}' but no matching zone.prjIndex."
                    )
                v = prj_to_node[to_zone]
            edge_key = path_value.get("userName", path_key)
            graph.add_edge(
                u,
                v,
                key=edge_key,
                pathHeight=path_value.get("pathHeight"),
                pathWidth=path_value.get("pathWidth"),
                pressure=path_value.get("pressure"),
            )
        return graph

    def lpg_to_networkDict(self, graph: nx.MultiDiGraph, base_networkDict: dict = None):
        """
        Apply edited LPG attributes back into network dictionary.

        Only whitelisted fields are written back.
        """
        if not isinstance(graph, nx.MultiDiGraph):
            raise TypeError("graph must be an instance of nx.MultiDiGraph.")

        if base_networkDict is None:
            base_networkDict = self.networkDict
        networkDict = deepcopy(base_networkDict)

        zones = networkDict.get("zones", {})
        paths = networkDict.get("paths", {})

        zone_node_to_key = {}
        for zone_key, zone_value in zones.items():
            node_id = zone_value.get("userName", zone_key)
            zone_node_to_key[node_id] = zone_key

        path_id_to_key = {}
        for path_key, path_value in paths.items():
            path_id_to_key[path_key] = path_key
            user_name = path_value.get("userName")
            if user_name is not None:
                path_id_to_key[user_name] = path_key

        for node_id, node_attrs in graph.nodes(data=True):
            if node_id == self.LPG_OUTSIDE_NODE:
                continue
            zone_key = zone_node_to_key.get(node_id)
            if zone_key is None:
                continue
            for field in self.LPG_ZONE_FIELDS:
                if field in node_attrs:
                    zones[zone_key][field] = node_attrs[field]

        for _, _, edge_key, edge_attrs in graph.edges(keys=True, data=True):
            path_key = path_id_to_key.get(edge_key)
            if path_key is None:
                continue
            for field in self.LPG_PATH_FIELDS:
                if field in edge_attrs:
                    paths[path_key][field] = edge_attrs[field]

        # Recompute zone.window_area from original outside-linked paths only.
        # Rule requested:
        # - sum area for paths linked with '-1'
        # - exclude newly added toZone='-1' paths
        zone_by_prj = {}
        for zone_key, zone_value in zones.items():
            zone_by_prj[str(zone_value.get("prjIndex"))] = zone_key
            zones[zone_key]["window_area"] = 0.0

        def _is_newly_added_outside_path(path_obj: dict) -> bool:
            user_name = str(path_obj.get("userName", ""))
            path_id = str(path_obj.get("prjIndex", ""))
            # New optimization paths follow cem_* naming in BiCEM pipeline.
            return (
                user_name.startswith("cem_")
                or path_id.startswith("cem_")
            )

        for path_value in paths.values():
            from_zone = str(path_value.get("fromZone", ""))
            to_zone = str(path_value.get("toZone", ""))
            is_outside_link = (from_zone == "-1" and to_zone != "-1") or (to_zone == "-1" and from_zone != "-1")
            if not is_outside_link:
                continue
            if to_zone == "-1" and _is_newly_added_outside_path(path_value):
                continue
            zone_prj = to_zone if from_zone == "-1" else from_zone
            zone_key = zone_by_prj.get(zone_prj)
            if zone_key is None:
                continue
            try:
                area = float(path_value.get("pathHeight", 0.0)) * float(path_value.get("pathWidth", 0.0))
            except Exception:
                area = 0.0
            zones[zone_key]["window_area"] = float(zones[zone_key].get("window_area", 0.0)) + area

        self.networkDict = networkDict
        return networkDict

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
            {
              "zone_name": {
                "zone_area": ...,
                "heating": [...], "cooling": [...], "Lighting": [...],              # daily (365)
                "heating_hourly": [...], "cooling_hourly": [...], "Lighting_hourly": [...]  # hourly (8760)
              }
            }
        """
        if energyDict:
            self.networkDict = energyDict

        zoneIndexDict = {}
        for z in self.networkDict['zones'].keys():
            self.networkDict['zones'][z]['zone_summerrad'] = 0
            self.networkDict['zones'][z]['zone_winterrad'] = 0
            zoneIndexDict[self.networkDict['zones'][z]['prjIndex']] = z

        for ps in self.networkDict['paths'].values():
            pid = ps["userName"]
            if pid not in self.pathRadIntensity:
                self.pathRadIntensity[pid] = [0.0] * 8760
            summer_intensity = np.sum(self.pathRadIntensity[pid][MoosasCumSky.SUMMER_START_HOY:MoosasCumSky.SUMMER_END_HOY])
            winter_intensity = np.sum(self.pathRadIntensity[pid][MoosasCumSky.WINTER_START_HOY:]) + \
                               np.sum(self.pathRadIntensity[pid][:MoosasCumSky.WINTER_END_HOY])
            summerradHeat = summer_intensity * float(ps['pathHeight']) * float(ps['pathWidth'])
            winterradHeat = winter_intensity * float(ps['pathHeight']) * float(ps['pathWidth'])
            if ps["fromZone"] != "-1":
                zUserName = zoneIndexDict.get(ps["fromZone"])
                if zUserName is not None:
                    self.networkDict['zones'][zUserName]['zone_summerrad'] += summerradHeat
                    self.networkDict['zones'][zUserName]['zone_winterrad'] += winterradHeat
            if ps["toZone"] != "-1":
                zUserName = zoneIndexDict.get(ps["toZone"])
                if zUserName is not None:
                    self.networkDict['zones'][zUserName]['zone_summerrad'] += summerradHeat
                    self.networkDict['zones'][zUserName]['zone_winterrad'] += winterradHeat
        
        energyDict = self.networkDict
        energyInput = self.reconstructEnergyInputs(energyDict)
        energyInput['args'] = list(energyInput.get('args', []))
        if '-d' not in energyInput['args']:
            energyInput['args'] += ['-d', '1']
        if '-z' not in energyInput['args']:
            energyInput['args'] += ['-z', '1']
        e_data = energyAnalysis(
            energyInput=energyInput,
            exportDaily=True,
            exportHourly=True,
            exportByZone=True,
            schedulePath=self.schedulePath
        )
        return self._format_energy_result(energyInput, e_data)

    @staticmethod
    def _fit_series(values, size):
        vals = list(values)[:size]
        if len(vals) < size:
            vals += [np.nan] * (size - len(vals))
        return vals

    def _format_energy_result(self, energyInput, e_data):
        zone_days = e_data.get("zone_days", [])
        zone_hours = e_data.get("zone_hours", [])
        result = {}
        for i, z in enumerate(energyInput["zones"]):
            zone_name = z.params.get("zone_name", f"zone_{i}")
            zone_area = float(z.params.get("zone_area", 0.0))
            days = zone_days[i] if i < len(zone_days) else []
            hours = zone_hours[i] if i < len(zone_hours) else []
            heating = self._fit_series([float(d["heating"]) for d in days], 365)
            cooling = self._fit_series([float(d["cooling"]) for d in days], 365)
            lighting = self._fit_series([float(d["lighting"]) for d in days], 365)
            heating_hourly = self._fit_series([float(h["heating"]) for h in hours], 8760)
            cooling_hourly = self._fit_series([float(h["cooling"]) for h in hours], 8760)
            lighting_hourly = self._fit_series([float(h["lighting"]) for h in hours], 8760)
            result[zone_name] = {
                "zone_area": zone_area,
                "heating": heating,
                "cooling": cooling,
                "Lighting": lighting,
                "heating_hourly": heating_hourly,
                "cooling_hourly": cooling_hourly,
                "Lighting_hourly": lighting_hourly
            }
        return result

    @staticmethod
    def _window_mean(arr, st, ed):
        if st >= ed:
            return 0.0
        vals = np.array(arr[st:ed], dtype=float)
        if vals.size == 0:
            return 0.0
        return float(np.mean(vals))

    @staticmethod
    def _to_float(value, default=0.0):
        if value is None:
            return float(default)
        if isinstance(value, str) and value.strip().lower() in ("", "none", "null", "nan"):
            return float(default)
        try:
            return float(value)
        except Exception:
            return float(default)

    def _mechanical_candidate_paths(self):
        candidates = []
        for path_key, p in self.networkDict.get("paths", {}).items():
            from_zone = str(p.get("fromZone", ""))
            to_zone = str(p.get("toZone", ""))
            is_outside_edge = (from_zone == "-1" and to_zone != "-1") or (to_zone == "-1" and from_zone != "-1")
            if not is_outside_edge:
                continue
            # Mechanical path identification should be strict.
            # Do not treat all outside-linked pressure paths as mechanical,
            # otherwise natural ventilation openings are over-counted as fan power.
            user_name = str(p.get("userName", path_key)).lower()
            path_type = str(p.get("pathType", "")).lower()
            is_mechanical = (
                bool(p.get("is_mechanical", False))
                or user_name.startswith("cem_mech_")
                or ("mech" in user_name)
                or ("fan" in user_name)
                or (path_type == "mechanical")
            )
            if not is_mechanical:
                continue
            indoor_prj = to_zone if from_zone == "-1" else from_zone
            candidates.append((str(p.get("userName", path_key)), str(indoor_prj)))
        return candidates

    def _zone_occupancy_switch(self, hoy):
        occ = {}
        for zone_key, z in self.networkDict.get("zones", {}).items():
            zone_user = str(z.get("userName", zone_key))
            ppsm = self._resolve_gain_value(z.get("zone_ppsm"), hoy, "zone_ppsm", zone_user)
            occ[zone_user] = bool(float(ppsm) > 0.0)
        return occ

    def _mechanical_energy_kwh_m2_by_zone(self, prj_file, hoy, specific_power=0.27):
        mech_energy = {}
        if (not prj_file) or (not os.path.exists(prj_file)):
            return mech_energy

        mech_paths = self._mechanical_candidate_paths()
        if len(mech_paths) == 0:
            return mech_energy

        flow_by_path = {}
        try:
            flow_result = readPathResult(prj_file)
            path_list = list(self.networkDict.get("paths", {}).values())
            for i, p in enumerate(path_list):
                if i not in flow_result:
                    continue
                pid = str(p.get("userName", f"path_{i}"))
                flow_by_path[pid] = self._to_float(flow_result[i].get("flow"), 0.0)
        except Exception:
            return mech_energy

        zones = self.networkDict.get("zones", {})
        prj_to_zone_user = {
            str(z.get("prjIndex")): str(z.get("userName", zone_key))
            for zone_key, z in zones.items()
        }
        zone_user_to_info = {
            str(z.get("userName", zone_key)): z
            for zone_key, z in zones.items()
        }
        occ = self._zone_occupancy_switch(hoy)

        for path_id, indoor_prj in mech_paths:
            zone_user = prj_to_zone_user.get(str(indoor_prj))
            if zone_user is None:
                continue
            if not occ.get(zone_user, False):
                continue
            zone_area = self._to_float(zone_user_to_info.get(zone_user, {}).get("zone_area"), 0.0)
            if zone_area <= 0:
                continue
            flow_m3h = abs(self._to_float(flow_by_path.get(path_id), 0.0))
            energy_wh = float(specific_power) * flow_m3h
            mech_energy[zone_user] = mech_energy.get(zone_user, 0.0) + (energy_wh / 1000.0 / zone_area)
        return mech_energy

    def coupledTask(self, energyDict: dict = None, timestep=1, iteration=1, mode="sequence",
                    preheat=10, k=0.0, w=1, start_hoy=0, end_hoy=8759):
        """
        Coupled simulation between energy and comfort results.

        Parameters
        ----------
        start_hoy : int, default 0
            Inclusive start hour-of-year for coupling simulation.
        end_hoy : int, default 8759
            Inclusive end hour-of-year for coupling simulation.

        Returns
        -------
        dict
            {
              "zone_name": {
                "hoy": [...],
                "zone_area": ...,
                "heating": [...],
                "cooling": [...],
                "lighting": [...],
                "total_energy": [...],
                "total_energy_vent": [...],
                "Temperature": [...],
                "ACH": [...],
                "Comfort": [...],
                "delta_t": [...]
              }
            }
        """
        e_res = self.energyTask(energyDict=energyDict)
        c_res = self.annualComfort(
            energyDict=energyDict,
            timestep=timestep,
            iteration=iteration,
            mode=mode,
            preheat=preheat,
            k=k,
            w=w,
            start_hoy=start_hoy,
            end_hoy=end_hoy
        )

        step = int(timestep)
        if step <= 0:
            raise ValueError("timestep must be a positive integer.")
        st_hoy = int(start_hoy)
        ed_hoy = int(end_hoy)
        if st_hoy < 0 or st_hoy > 8759:
            raise ValueError("start_hoy must be in [0, 8759].")
        if ed_hoy < 0 or ed_hoy > 8759:
            raise ValueError("end_hoy must be in [0, 8759].")
        if st_hoy > ed_hoy:
            raise ValueError("start_hoy must be <= end_hoy.")
        hoys = list(range(st_hoy, ed_hoy + 1, step))
        period_end_exclusive = ed_hoy + 1
        n = len(hoys)
        zone_names = [zn for zn in c_res.keys() if zn in e_res]
        result = {}
        for zn in zone_names:
            ez = e_res[zn]
            cz = c_res[zn]
            heating_s, cooling_s, lighting_s = [], [], []
            total_energy_s, total_energy_vent_s = [], []
            comfort_s = list(cz.get("Comfort", []))[:n]
            ach_s = list(cz.get("ACH", []))[:n]
            temp_s = list(cz.get("Temperature", []))[:n]
            delta_s = list(cz.get("delta_t", []))[:n]
            mech_s = list(cz.get("MechanicalVent", []))[:n]
            if len(comfort_s) < n:
                comfort_s += [0] * (n - len(comfort_s))
            if len(ach_s) < n:
                ach_s += [np.nan] * (n - len(ach_s))
            if len(temp_s) < n:
                temp_s += [np.nan] * (n - len(temp_s))
            if len(delta_s) < n:
                delta_s += [np.nan] * (n - len(delta_s))
            if len(mech_s) < n:
                mech_s += [0.0] * (n - len(mech_s))
            for i, hoy in enumerate(hoys):
                st = int(hoy)
                ed = min(8760, period_end_exclusive, st + step)
                h = self._window_mean(ez.get("heating_hourly", []), st, ed)
                c = self._window_mean(ez.get("cooling_hourly", []), st, ed)
                l = self._window_mean(ez.get("Lighting_hourly", []), st, ed)
                comfort = float(comfort_s[i])
                total_energy = h + c + l
                total_energy_vent = (h + c) * (1.0 - comfort) + l + float(mech_s[i])
                heating_s.append(h)
                cooling_s.append(c)
                lighting_s.append(l)
                total_energy_s.append(total_energy)
                total_energy_vent_s.append(total_energy_vent)
            result[zn] = {
                "hoy": list(hoys),
                "zone_area": float(cz.get("zone_area", ez.get("zone_area", 0.0))),
                "heating": heating_s,
                "cooling": cooling_s,
                "lighting": lighting_s,
                "total_energy": total_energy_s,
                "total_energy_vent": total_energy_vent_s,
                "mechanical_vent_energy": mech_s,
                "Temperature": temp_s,
                "ACH": ach_s,
                "Comfort": comfort_s,
                "delta_t": delta_s
            }
        return result

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

    @staticmethod
    def _moving_average(values, w):
        vals = np.array(values, dtype=float)
        n = len(vals)
        out = []
        for i in range(n):
            st = max(0, i - w)
            ed = min(n, i + w + 1)
            out.append(float(np.mean(vals[st:ed])))
        return out

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
            self.runtime['last_prj_file'] = prjFile
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
            self.runtime['last_prj_file'] = self.runtime.get('AFN_ref_prj')
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
            self.runtime['last_prj_file'] = current_prj
            achIteration = [max(x, y) for x, y in zip(last_AFN[-1], last_AFN[:, -1])]
            tC = (np.array(last_t) - 273.15).flatten().tolist()
            for i in range(len(zones)):
                zones[i].temperature.append(tC[i])
                zones[i].ACH.append(achIteration[i])
            return zones

        raise ValueError("mode must be one of ['onions', 'sequence', 'ping-pong'].")

    def annualComfort(self, energyDict: dict = None, iteration=1, mode="sequence", timestep=1,
                      preheat=10, k=0.0, w=1, start_hoy=0, end_hoy=8759):
        """
        Run annual ventilation comfort simulation with selectable coupling strategy.

        Parameters
        ----------
        energyDict : dict, optional
            Network dictionary override.
        iteration : int, default 1
            Per-hour coupling iterations (ignored in `sequence` mode).
        mode : {"onions", "sequence", "ping-pong"}, default "sequence"
            Annual coupling strategy.
        timestep : int, default 1
            Hour step size. Number of hoy samples is
            `len(range(start_hoy, end_hoy + 1, timestep))`.
        preheat : int, default 10
            Bootstrap ping-pong rounds at peak-load hour to generate initial project state.
        k : float, default 0.0
            Thermal inertia strength. Recommended range [0, 1].
        w : int, default 1
            Half-window size for moving-average outdoor temperature on sampled sequence.

        Returns
        -------
        dict
            {"zone_name": {"zone_area": ..., "ACH": [...], "Temperature": [...]} }
        """
        self._ensure_runtime_workspace(reset=True)
        if energyDict:
            self.networkDict = energyDict
        if int(timestep) <= 0:
            raise ValueError("timestep must be a positive integer.")
        if int(w) < 0:
            raise ValueError("w must be a non-negative integer.")
        st_hoy = int(start_hoy)
        ed_hoy = int(end_hoy)
        if st_hoy < 0 or st_hoy > 8759:
            raise ValueError("start_hoy must be in [0, 8759].")
        if ed_hoy < 0 or ed_hoy > 8759:
            raise ValueError("end_hoy must be in [0, 8759].")
        if st_hoy > ed_hoy:
            raise ValueError("start_hoy must be <= end_hoy.")
        hoys = list(range(st_hoy, ed_hoy + 1, int(timestep)))
        outdoor_series = [25.0] * len(hoys)

        preheated_prj = self._preheat(hoys=hoys, outdoor_series=outdoor_series, preheat=preheat, energyDict=energyDict)

        if mode == "sequence":
            AFN_ref = contam_iteration(preheated_prj)
            self.runtime['AFN_ref'] = AFN_ref
            self.runtime['AFN_ref_prj'] = preheated_prj
        elif mode == "ping-pong":
            self.runtime['current_prj'] = preheated_prj
        elif mode == "onions":
            self.runtime['onions_prj'] = preheated_prj
        else:
            raise ValueError("mode must be one of ['onions', 'sequence', 'ping-pong'].")

        zResult = None
        zone_users = [str(z.get("userName", k)) for k, z in self.networkDict.get("zones", {}).items()]
        mech_hourly_by_user = {zu: [] for zu in zone_users}
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
                for zu in zone_users:
                    mech_hourly_by_user[zu].append(0.0)
                print(f"Warning: Singular matrix at hoy={hoy}, filled NaN for this timestep.")
                continue
            except Exception as e:
                if zResult is None:
                    self.updateHeatLoad(hoy, energyDict=energyDict)
                    zResult = self._zone_result_template()
                for i in range(len(zResult)):
                    zResult[i].temperature += [np.nan]
                    zResult[i].ACH += [np.nan]
                for zu in zone_users:
                    mech_hourly_by_user[zu].append(0.0)
                print(f"Warning: Exception at hoy={hoy} ({type(e).__name__}: {e}), filled NaN for this timestep.")
                continue
            if (not zResultHoy) or len(zResultHoy[0].temperature) == 0 or len(zResultHoy[0].ACH) == 0:
                if zResult is None:
                    self.updateHeatLoad(hoy, energyDict=energyDict)
                    zResult = self._zone_result_template()
                for i in range(len(zResult)):
                    zResult[i].temperature += [np.nan]
                    zResult[i].ACH += [np.nan]
                for zu in zone_users:
                    mech_hourly_by_user[zu].append(0.0)
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
            mech_this_h = self._mechanical_energy_kwh_m2_by_zone(
                prj_file=self.runtime.get('last_prj_file'),
                hoy=hoy,
                specific_power=0.27
            )
            for zu in zone_users:
                mech_hourly_by_user[zu].append(float(mech_this_h.get(zu, 0.0)))
        zResult = postprocess_zone_results_linear(zResult)
        result = self._format_comfort_result(zResult, hoys=hoys, k=float(k), w=int(w))
        for zone_key, z in self.networkDict.get("zones", {}).items():
            zone_user = str(z.get("userName", zone_key))
            zone_name = str(z.get("zone_name", zone_user))
            if zone_name in result:
                result[zone_name]["MechanicalVent"] = mech_hourly_by_user.get(zone_user, [0.0] * len(hoys))
        return result

    def _format_comfort_result(self, zResult, hoys, k, w):
        weather_t = [float(self.weather.weatherData['temperature'][h]) for h in hoys]
        avg_t = self._moving_average(weather_t, w=w)
        indoor_ref_t = [(1.0 - k) * t + k * a for t, a in zip(weather_t, avg_t)]
        result = {}
        for z in zResult:
            z_meta = self.networkDict['zones'].get(z.userName, {})
            zone_name = z_meta.get("zone_name", z.userName)
            zone_area = float(z_meta.get("zone_area", 0.0))
            raw_temp = [float(v) for v in z.temperature]
            delta_zt = [t - 25.0 for t in raw_temp]
            z_t = [dz + ref_t for dz, ref_t in zip(delta_zt, indoor_ref_t)]
            comfort = [
                1 if (0.31 * out_t <= t_val < 0.31 * out_t + 20.3) else 0
                for out_t, t_val in zip(weather_t, z_t)
            ]
            result[zone_name] = {
                "zone_area": zone_area,
                "hoys": int(8760.0/len(z.temperature)),
                "ACH": [float(v) for v in z.ACH],
                "delta_t": delta_zt,
                "Temperature": z_t,
                "Comfort": comfort
            }
        return result
