"""
green-building-report: 数据提取脚本 (修复版)
=====================================
用法：python analyze.py <weather_json> <energy_json> <rdf_file> <rdf_helper_py> <output_json>

职责：从三个数据文件中提取所有可用数值，输出一个结构化 JSON 数据包。
修复重点：
1. 确保从 energy_json 的 summary 字段提取年度总能耗、发电量和净能耗。
2. 确保从 area 字段提取建筑面积。
3. 计算单位面积指标 (EUI, 发电强度, 净能耗强度)。
4. 增强对 JSON 结构的鲁棒性。
"""

import json
import re
import sys
from pathlib import Path

# ── 参数解析 ──────────────────────────────────────────────────────────────────
if len(sys.argv) != 6:
    print("用法: python analyze.py <weather_json> <energy_json> <rdf_file> <rdf_helper_py> <output_json>")
    sys.exit(1)

weather_json_path = Path(sys.argv[1])
energy_json_path  = Path(sys.argv[2])
rdf_file_path     = Path(sys.argv[3])
rdf_helper_path   = Path(sys.argv[4])
output_json_path  = Path(sys.argv[5])

result = {}

# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK 1 — 能耗 JSON
# ═══════════════════════════════════════════════════════════════════════════════
try:
    with open(energy_json_path, encoding="utf-8") as f:
        energy_raw = json.load(f)

    # 1. 基础信息提取
    building_area_m2 = energy_raw.get("area", 0)
    summary          = energy_raw.get("summary", {})
    daily_records    = energy_raw.get("daily", [])

    # 2. 年度总量提取 (优先从 summary 提取)
    annual_consumption = summary.get("annualConsumption", 0)
    annual_generation  = summary.get("annualGeneration", 0)
    annual_net         = summary.get("annualNet", 0)

    # 3. 逐日数据处理
    cooling_daily    = [d.get("cooling", 0)          for d in daily_records]
    heating_daily    = [d.get("heating", 0)          for d in daily_records]
    lighting_daily   = [d.get("lighting", 0)         for d in daily_records]
    total_daily      = [d.get("totalConsumption", 0) for d in daily_records]
    generation_daily = [d.get("generation", 0)       for d in daily_records]

    # 如果 summary 为空，则通过逐日数据累加作为兜底
    if annual_consumption == 0: annual_consumption = sum(total_daily)
    if annual_generation == 0:  annual_generation = sum(generation_daily)
    
    annual_cooling  = sum(cooling_daily)
    annual_heating  = sum(heating_daily)
    annual_lighting = sum(lighting_daily)
    
    # 重新计算净能耗 (消耗 - 发电)
    # 注意：JSON 中的 annualNet 可能是 发电 - 消耗，这里统一为 消耗 - 发电
    calculated_net = annual_consumption - annual_generation

    # 4. 单位面积指标计算
    eui_consumption = annual_consumption / building_area_m2 if building_area_m2 else None
    eui_generation  = annual_generation  / building_area_m2 if building_area_m2 else None
    eui_net         = calculated_net     / building_area_m2 if building_area_m2 else None
    
    pv_self_sufficiency_ratio = (
        annual_generation / annual_consumption if annual_consumption else None
    )

    # 5. 季节性分析
    def season_of(day_of_year: int) -> str:
        if day_of_year <= 59 or day_of_year >= 335:  return "winter"
        elif day_of_year <= 151:                      return "spring"
        elif day_of_year <= 243:                      return "summer"
        else:                                         return "autumn"

    season_keys = ["winter", "spring", "summer", "autumn"]
    seasonal_energy: dict = {k: {"consumption": 0.0, "cooling": 0.0,
                                  "heating": 0.0, "generation": 0.0}
                              for k in season_keys}
    for day_record in daily_records:
        season = season_of(day_record.get("dayOfYear", 1))
        seasonal_energy[season]["consumption"] += day_record.get("totalConsumption", 0)
        seasonal_energy[season]["cooling"]     += day_record.get("cooling", 0)
        seasonal_energy[season]["heating"]     += day_record.get("heating", 0)
        seasonal_energy[season]["generation"]  += day_record.get("generation", 0)

    # 6. 逐日峰值
    def day_summary(day_record: dict) -> dict:
        return {
            "date":       day_record.get("date"),
            "day_of_year": day_record.get("dayOfYear"),
            "cooling_kwh":    round(day_record.get("cooling", 0), 2),
            "heating_kwh":    round(day_record.get("heating", 0), 2),
            "generation_kwh": round(day_record.get("generation", 0), 2),
            "total_consumption_kwh": round(day_record.get("totalConsumption", 0), 2),
        }

    peak_cooling_idx    = cooling_daily.index(max(cooling_daily)) if cooling_daily else 0
    peak_heating_idx    = heating_daily.index(max(heating_daily)) if heating_daily else 0
    peak_generation_idx = generation_daily.index(max(generation_daily)) if generation_daily else 0

    result["energy"] = {
        "building_area_m2":          building_area_m2,
        "annual_consumption_kwh":    round(annual_consumption, 2),
        "annual_generation_kwh":     round(annual_generation, 2),
        "annual_net_kwh":            round(calculated_net, 2),
        "annual_cooling_kwh":        round(annual_cooling, 2),
        "annual_heating_kwh":        round(annual_heating, 2),
        "annual_lighting_kwh":       round(annual_lighting, 2),
        
        # 单位面积指标
        "eui_consumption_kwh_per_m2": round(eui_consumption, 2) if eui_consumption is not None else None,
        "eui_generation_kwh_per_m2":  round(eui_generation, 2) if eui_generation is not None else None,
        "eui_net_kwh_per_m2":         round(eui_net, 2) if eui_net is not None else None,
        
        "pv_self_sufficiency_ratio": round(pv_self_sufficiency_ratio, 4) if pv_self_sufficiency_ratio is not None else None,
        "days_with_cooling":         sum(1 for v in cooling_daily if v > 0.1),
        "days_with_heating":         sum(1 for v in heating_daily if v > 0.1),
        "days_with_lighting":        sum(1 for v in lighting_daily if v > 0.1),
        "seasonal_breakdown":        {k: {kk: round(vv, 2) for kk, vv in v.items()}
                                      for k, v in seasonal_energy.items()},
        "peak_cooling_day":          day_summary(daily_records[peak_cooling_idx]) if daily_records else None,
        "peak_heating_day":          day_summary(daily_records[peak_heating_idx]) if daily_records else None,
        "peak_generation_day":       day_summary(daily_records[peak_generation_idx]) if daily_records else None,
        "data_source":               str(energy_json_path.name),
        "parse_error":               None,
    }
except Exception as exc:
    result["energy"] = {"parse_error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK 2 — 气象 JSON
# ═══════════════════════════════════════════════════════════════════════════════
try:
    with open(weather_json_path, encoding="utf-8") as f:
        weather_raw = json.load(f)

    temp_list  = [float(v) for v in weather_raw.get("temperature", [])]
    rad_list   = [float(v) for v in weather_raw.get("globalRad", [])]
    wind_list  = [float(v) for v in weather_raw.get("windVel", [])]
    hum_list   = [float(v) for v in weather_raw.get("humidityRatio", [])]
    press_list = [float(v) for v in weather_raw.get("Pressure", [])]

    n_hours = len(temp_list)

    def hourly_to_daily_max(hourly: list[float]) -> list[float]:
        return [max(hourly[d*24: d*24+24]) for d in range(min(365, len(hourly)//24))]

    def hourly_to_daily_mean(hourly: list[float]) -> list[float]:
        chunk = 24
        return [sum(hourly[d*chunk: d*chunk+chunk]) / chunk
                for d in range(min(365, len(hourly)//chunk))]

    daily_max_temp  = hourly_to_daily_max(temp_list)
    hot_days  = sum(1 for t in daily_max_temp if t > 35)
    cold_days = sum(1 for t in daily_max_temp if t < 0)

    def season_hour_indices(season_name: str) -> list[int]:
        indices = []
        for day_idx in range(min(365, n_hours // 24)):
            if season_of(day_idx + 1) == season_name:
                for h in range(24):
                    i = day_idx * 24 + h
                    if i < n_hours:
                        indices.append(i)
        return indices

    season_avg_temp = {}
    season_avg_rad  = {}
    for sk in season_keys:
        idxs = season_hour_indices(sk)
        season_avg_temp[sk] = (
            round(sum(temp_list[i] for i in idxs) / len(idxs), 2) if idxs else None
        )
        season_avg_rad[sk] = (
            round(sum(rad_list[i] for i in idxs) / len(idxs), 2) if idxs and rad_list else None
        )

    annual_ghi_kwh_m2 = round(sum(rad_list) / 1000, 1) if rad_list else None

    result["weather"] = {
        "n_hourly_records":          n_hours,
        "annual_avg_temp_c":         round(sum(temp_list) / n_hours, 2) if n_hours else None,
        "annual_max_temp_c":         round(max(temp_list), 1) if temp_list else None,
        "annual_min_temp_c":         round(min(temp_list), 1) if temp_list else None,
        "hot_days_above_35c":        hot_days,
        "cold_days_max_below_0c":    cold_days,
        "seasonal_avg_temp_c":       season_avg_temp,
        "seasonal_avg_rad_w_m2":     season_avg_rad,
        "annual_ghi_kwh_m2":         annual_ghi_kwh_m2,
        "annual_avg_wind_speed_m_s": round(sum(wind_list) / len(wind_list), 2) if wind_list else None,
        "data_source":               str(weather_json_path.name),
        "parse_error":               None,
    }
except Exception as exc:
    result["weather"] = {"parse_error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK 3 — RDF 几何与热工参数
# ═══════════════════════════════════════════════════════════════════════════════
try:
    with open(rdf_file_path, encoding="utf-8", errors="ignore") as f:
        rdf_lines = [line.strip() for line in f.readlines()]

    floor_areas: list[float] = []
    volumes: list[float]     = []
    for line in rdf_lines:
        m = re.search(r'hasFloorArea_m2\s+([\d.e+\-]+)', line)
        if m:
            try: floor_areas.append(float(m.group(1)))
            except ValueError: pass
        m = re.search(r'hasVolume_m3\s+([\d.e+\-]+)', line)
        if m:
            try: volumes.append(float(m.group(1)))
            except ValueError: pass

    total_floor_area_m2 = round(sum(floor_areas), 2) if floor_areas else None
    total_volume_m3     = round(sum(volumes), 2)      if volumes     else None

    area_records: list[tuple[int, float]] = []
    for i, line in enumerate(rdf_lines):
        m = re.search(r'hasArea_m2\s+([\d.e+\-]+)', line)
        if m:
            try: area_records.append((i, float(m.group(1))))
            except ValueError: pass

    def nearby_property(lines: list[str], center_idx: int, prop_name: str, search_range: int = 15) -> str | None:
        for j in range(max(0, center_idx - search_range), min(len(lines), center_idx + search_range)):
            if prop_name in lines[j]:
                m = re.search(rf'{re.escape(prop_name)}\s+(?:moosas:|bes:|")?([^";,\s]+)', lines[j])
                if m: return m.group(1).strip('"')
        return None

    surfaces: list[dict] = []
    for idx, area_val in area_records:
        surfaces.append({
            "area_m2":          area_val,
            "surface_type":     nearby_property(rdf_lines, idx, "hasSurfaceType"),
            "boundary_condition": nearby_property(rdf_lines, idx, "hasOutsideBoundaryCondition"),
        })

    outdoor_surfaces    = [s for s in surfaces if "outdoors" in (s["boundary_condition"] or "").lower()]
    total_outdoor_area  = round(sum(s["area_m2"] for s in outdoor_surfaces), 2)

    glazing_area   = round(sum(s["area_m2"] for s in outdoor_surfaces if "glazing" in (s["surface_type"] or "").lower()), 2)
    wall_area      = round(sum(s["area_m2"] for s in outdoor_surfaces if "wall" in (s["surface_type"] or "").lower() and "glazing" not in (s["surface_type"] or "").lower()), 2)

    wall_u_values: list[float] = []
    win_u_values:  list[float] = []
    for line in rdf_lines:
        m = re.search(r'zone_wallU\s+"?([\d.]+)"?', line)
        if m:
            try: wall_u_values.append(float(m.group(1)))
            except ValueError: pass
        m = re.search(r'zone_winU\s+"?([\d.]+)"?', line)
        if m:
            try: win_u_values.append(float(m.group(1)))
            except ValueError: pass

    shape_factor = round(total_outdoor_area / total_volume_m3, 4) if total_outdoor_area and total_volume_m3 else None
    window_to_wall_ratio = round(glazing_area / (glazing_area + wall_area), 4) if (glazing_area + wall_area) > 0 else None

    result["geometry"] = {
        "total_floor_area_m2":       total_floor_area_m2,
        "total_volume_m3":           total_volume_m3,
        "total_outdoor_surface_area_m2": total_outdoor_area,
        "shape_factor_m_inv":        shape_factor,
        "window_to_wall_ratio":      window_to_wall_ratio,
        "wall_u_avg_w_m2k":          round(sum(wall_u_values) / len(wall_u_values), 4) if wall_u_values else None,
        "window_u_avg_w_m2k":        round(sum(win_u_values) / len(win_u_values), 4) if win_u_values else None,
        "parse_error":               None,
    }
except Exception as exc:
    result["geometry"] = {"parse_error": str(exc)}

# ═══════════════════════════════════════════════════════════════════════════════
# 写出 JSON
# ═══════════════════════════════════════════════════════════════════════════════
output_json_path.parent.mkdir(parents=True, exist_ok=True)
output_json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[OK] 数据包已生成：{output_json_path}")
