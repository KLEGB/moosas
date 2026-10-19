"""Match exported ground floors to the template's heat-transfer method."""

from collections import defaultdict
from hashlib import sha256
from math import isclose, isfinite
import warnings

import shapely
from eppy.modeleditor import IDF

from ....utils.constant import geom


def capture_ground_templates(idf: IDF, zone_map):
    """Capture source-zone ground policies before replacing template geometry."""
    constructions = {
        obj.Name.casefold(): obj
        for key, objects in idf.idfobjects.items()
        if key == "CONSTRUCTION" or key.startswith("CONSTRUCTION:")
        for obj in objects
    }
    by_zone = defaultdict(dict)
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        boundary = surface.Outside_Boundary_Condition
        if surface.Surface_Type.casefold() != "floor" or not (
            boundary.casefold().startswith("ground")
            or boundary.casefold() in {"foundation", "othersidecoefficients", "othersideconditionsmodel"}
        ):
            continue
        construction = constructions.get(surface.Construction_Name.casefold())
        kind = construction.key.upper() if construction is not None else ""
        thermal = (float(construction.FFactor) if kind == "CONSTRUCTION:FFACTORGROUNDFLOOR"
                   else surface.Construction_Name.casefold())
        by_zone[surface.Zone_Name.casefold()][boundary.casefold(), kind, thermal] = (
            boundary, construction,
        )

    all_policies = {key: value for policies in by_zone.values() for key, value in policies.items()}
    return {
        str(space_id): by_zone.get(zone.casefold(), all_policies)
        for zone, space_ids in zone_map.items()
        for space_id in space_ids
    }


def _select_policy(policies, zone):
    if len(policies) > 1:
        raise ValueError(
            f"Ambiguous template ground floors for zone '{zone}'; select a template zone "
            "with one ground method and construction."
        )
    if not policies:
        return "Ground", None
    (boundary, kind, _), (boundary_name, construction) = next(iter(policies.items()))
    if boundary not in {"ground", "groundfcfactormethod"}:
        raise ValueError(
            f"Unsupported template ground method '{boundary_name}' for zone "
            f"'{zone}'; only Ground and GroundFCfactorMethod are supported."
        )
    expected_type = "CONSTRUCTION:FFACTORGROUNDFLOOR" if boundary == "groundfcfactormethod" else "CONSTRUCTION"
    if kind != expected_type:
        raise ValueError(
            f"Template ground construction for zone '{zone}' "
            f"must be {expected_type} when using {boundary_name}."
        )
    if boundary == "groundfcfactormethod":
        factor = float(construction.FFactor)
        if not isfinite(factor) or factor <= 0:
            raise ValueError(f"Template ground construction '{construction.Name}' has an invalid F-factor.")
    return boundary_name, construction


def _equivalent_ground_geometry(by_zone, selected):
    footprints = {}
    levels = defaultdict(list)
    groups = defaultdict(list)
    for zone, surfaces in by_zone.items():
        boundary, construction = selected[zone]
        for surface in surfaces:
            coordinates = surface.coords
            z = [point[2] for point in coordinates]
            if max(z) - min(z) > geom.POINT_PRECISION:
                raise ValueError(f"F-factor ground export requires horizontal floors: '{surface.Name}'.")
            polygon = shapely.set_precision(
                shapely.Polygon([(x, y) for x, y, _ in coordinates]), geom.POINT_PRECISION,
            )
            if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
                raise ValueError(f"Invalid ground floor footprint for surface '{surface.Name}'.")
            footprints[surface.Name] = polygon
            level = round(z[0] / geom.POINT_PRECISION)
            levels[level].append(polygon)
            if boundary.casefold() == "groundfcfactormethod":
                groups[level, float(construction.FFactor)].append(surface.Name)
    exterior_by_level = {
        level: shapely.union_all(polygons, grid_size=geom.POINT_PRECISION).boundary
        for level, polygons in levels.items()
    }
    geometry = {}
    for (level, source_factor), names in groups.items():
        slabs = shapely.union_all([footprints[name] for name in names], grid_size=geom.POINT_PRECISION)
        components = slabs.geoms if slabs.geom_type == "MultiPolygon" else (slabs,)
        for slab in components:
            members = [name for name in names if slab.covers(footprints[name].representative_point())]
            if not isclose(sum(footprints[name].area for name in members), slab.area,
                           rel_tol=1e-9, abs_tol=geom.POINT_PRECISION ** 2):
                raise ValueError("Overlapping ground floors cannot be assigned an equivalent slab F-factor.")
            perimeter = shapely.intersection(
                slab.boundary, exterior_by_level[level], grid_size=geom.POINT_PRECISION,
            ).length
            for name in members:
                area = footprints[name].area
                allocated_perimeter = perimeter * area / slab.area
                effective_perimeter = min(allocated_perimeter, footprints[name].length)
                # EnergyPlus disallows exposed perimeter beyond the face boundary.
                # Rescale F with it, preserving both F*P and equivalent resistance.
                factor = (
                    source_factor * allocated_perimeter / effective_perimeter
                    if effective_perimeter < allocated_perimeter else source_factor
                )
                geometry[name] = area, effective_perimeter, factor
    return geometry


def apply_ground_templates(idf: IDF, policies_by_zone):
    """Apply whole-slab equivalent ground physics without changing model topology."""
    by_zone = defaultdict(list)
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if (surface.Surface_Type.casefold() == "floor"
                and surface.Outside_Boundary_Condition.casefold() == "ground"):
            by_zone[surface.Zone_Name].append(surface)
    selected = {
        zone:         _select_policy(policies_by_zone.get(zone, {}), zone)
        for zone in by_zone
    }
    geometry = (
        _equivalent_ground_geometry(by_zone, selected)
        if any(boundary.casefold() == "groundfcfactormethod" for boundary, _ in selected.values())
        else {}
    )
    constructions = {
        obj.Name.casefold(): obj
        for key, objects in idf.idfobjects.items()
        if key == "CONSTRUCTION" or key.startswith("CONSTRUCTION:")
        for obj in objects
    }
    for zone, surfaces in by_zone.items():
        boundary, construction = selected[zone]
        temperature_type = (
            "SITE:GROUNDTEMPERATURE:FCFACTORMETHOD"
            if boundary.casefold() == "groundfcfactormethod"
            else "SITE:GROUNDTEMPERATURE:BUILDINGSURFACE"
        )
        if not idf.idfobjects[temperature_type]:
            warnings.warn(
                f"Template has no {temperature_type}; exported ground floors use "
                "EnergyPlus fallback temperatures; Moosas does not infer ground temperatures.",
                UserWarning, stacklevel=2,
            )
        if construction is None:
            continue
        for surface in surfaces:
            construction_name = construction.Name
            if boundary.casefold() == "groundfcfactormethod":
                area, perimeter, factor = geometry[surface.Name]
                digest = sha256(
                    f"{zone}|{factor!r}|{area!r}|{perimeter!r}".encode("utf-8")
                ).hexdigest()[:16]
                construction_name = f"MoosasGround_{digest}"
                existing = constructions.get(construction_name.casefold())
                if existing is None:
                    existing = idf.newidfobject(
                        "Construction:FfactorGroundFloor", Name=construction_name,
                        FFactor=factor, Area=area, PerimeterExposed=perimeter,
                    )
                    constructions[construction_name.casefold()] = existing
                elif existing.key.upper() != "CONSTRUCTION:FFACTORGROUNDFLOOR" or not all(
                    isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-9)
                    for actual, expected in zip(
                        (existing.FFactor, existing.Area, existing.PerimeterExposed), (factor, area, perimeter),
                    )
                ):
                    raise ValueError(f"Ground construction name conflict: '{construction_name}'.")
            surface.Outside_Boundary_Condition = boundary
            surface.Construction_Name = construction_name
