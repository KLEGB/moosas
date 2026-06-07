#!/usr/bin/env python3
"""Package-native IFC bridge for Moosas models.

This module converts between ``MoosasModel`` and IFC4 for use by the shared
``saveModel`` / ``loadModel`` interface.  The project now routes IFC through an
intermediate RDF step when entering or leaving the public I/O boundary, while
still embedding a Moosas snapshot in the IFC file to preserve the original
project data.

The helpers here remain the IFC-specific implementation layer; they are not the
public dispatch point and should be called through :mod:`MoosasPy.IO.transIO`
when possible.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import uuid
from pathlib import Path
from typing import Any, Optional

import xml.etree.ElementTree as ET

try:
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.guid
except Exception:  # pragma: no cover - import guard for environments without IFC deps
    ifcopenshell = None

from ..utils.tools import path

PSET_SNAPSHOT = "Pset_MoosasModel_Snapshot"
PSET_IFC = "Pset_MoosasIFC"


def require_ifc() -> None:
    if ifcopenshell is None:
        raise ImportError(
            "ifcopenshell is required for IFC import/export. "
            "Install it in the Moosas environment and retry."
        )


def local_name(value: Any) -> str:
    text = str(value)
    if "#" in text:
        return text.rsplit("#", 1)[1]
    return text.rstrip("/").rsplit("/", 1)[-1]


def stable_guid(seed: str) -> str:
    require_ifc()
    return ifcopenshell.guid.compress(uuid.uuid5(uuid.NAMESPACE_URL, seed).hex)


def chunk_text(text: str, size: int = 24000) -> list[str]:
    if not text:
        return [""]
    return [text[i : i + size] for i in range(0, len(text), size)]


def join_chunks(data: dict[str, Any], prefix: str) -> str:
    count_key = f"{prefix}_ChunkCount"
    try:
        count = int(data.get(count_key) or 0)
    except Exception:
        count = 0
    if count <= 0:
        return ""
    return "".join(str(data.get(f"{prefix}_{i:04d}") or "") for i in range(count))


def add_pset(model, product: Any, properties: dict[str, Any], name: str = PSET_IFC) -> None:
    require_ifc()
    clean: dict[str, Any] = {}
    for key, value in properties.items():
        if value is None:
            continue
        if isinstance(value, (list, tuple, set, dict)):
            value = json.dumps(value, ensure_ascii=False)
        elif not isinstance(value, (str, int, float, bool)):
            value = str(value)
        if isinstance(value, str) and len(value) > 32000:
            value = value[:32000]
        clean[str(key)[:250]] = value
    if not clean:
        return
    pset = ifcopenshell.api.run("pset.add_pset", model, product=product, name=name)
    ifcopenshell.api.run("pset.edit_pset", model, pset=pset, properties=clean)


def setup_ifc_model(project_name: str = "Moosas IFC Project") -> tuple[Any, Any, Any]:
    require_ifc()
    model = ifcopenshell.file(schema="IFC4")
    project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject", name=project_name)
    length_unit = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="LENGTHUNIT")
    area_unit = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="AREAUNIT")
    volume_unit = ifcopenshell.api.run("unit.add_si_unit", model, unit_type="VOLUMEUNIT")
    ifcopenshell.api.run("unit.assign_unit", model, units=[length_unit, area_unit, volume_unit])
    context_3d = ifcopenshell.api.run("context.add_context", model, context_type="Model")
    body_context = ifcopenshell.api.run(
        "context.add_context",
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context_3d,
    )
    return model, project, body_context


def _snapshot_model(model) -> dict[str, Any]:
    root = model.buildXml(writeGeometry=True)
    xml_text = ET.tostring(root, encoding="unicode")

    geo_path = Path(path.tempDir) / f"ifc_snapshot_{uuid.uuid4().hex}.geo"
    try:
        from ._geo import writeGeo

        geo_text = writeGeo(str(geo_path), model)
    finally:
        if geo_path.exists():
            geo_path.unlink(missing_ok=True)

    schedule_text = json.dumps(getattr(model, "schedule", {}) or {}, ensure_ascii=False)
    weather_station = ""
    weather = getattr(model, "weather", None)
    if weather is not None:
        location = getattr(weather, "location", None)
        weather_station = str(getattr(location, "stationId", "") or getattr(weather, "stationId", "") or "")

    return {
        "version": "moosas-ifc-v1",
        "xml": xml_text,
        "geo": geo_text,
        "schedule": schedule_text,
        "weather_station": weather_station,
    }


def _write_snapshot_pset(model, project, snapshot: dict[str, Any]) -> None:
    payload = {}
    for prefix in ("XML", "GEO", "SCHEDULE"):
        chunks = chunk_text(snapshot.get(prefix.lower(), "") or "")
        payload[f"{prefix}_ChunkCount"] = len(chunks)
        for i, chunk in enumerate(chunks):
            payload[f"{prefix}_{i:04d}"] = chunk
    payload["SnapshotVersion"] = snapshot.get("version", "moosas-ifc-v1")
    payload["WeatherStationId"] = snapshot.get("weather_station", "")
    add_pset(model, project, payload, name=PSET_SNAPSHOT)


def _read_snapshot_pset(project) -> dict[str, str]:
    require_ifc()
    try:
        import ifcopenshell.util.element

        data = ifcopenshell.util.element.get_psets(project) or {}
    except Exception:
        data = {}
    snapshot = data.get(PSET_SNAPSHOT, {}) if isinstance(data, dict) else {}
    if not snapshot:
        return {}
    return {
        "xml": join_chunks(snapshot, "XML"),
        "geo": join_chunks(snapshot, "GEO"),
        "schedule": join_chunks(snapshot, "SCHEDULE"),
        "weather_station": str(snapshot.get("WeatherStationId") or ""),
    }


def _element_ifc_class(element: Any) -> tuple[str, Optional[str]]:
    cls_name = element.__class__.__name__.lower()
    if "glazing" in cls_name or "skylight" in cls_name:
        return "IfcWindow", None
    if "wall" in cls_name:
        return "IfcWall", None
    if "face" in cls_name:
        return "IfcSlab", "FLOOR"
    return "IfcBuildingElementProxy", None


def _safe_face_wkt(geom: Any) -> str:
    try:
        from shapely import wkt as shapely_wkt

        return shapely_wkt.dumps(geom, rounding_precision=6, trim=True)
    except Exception:
        return ""


def _maybe_json_load(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        loaded = json.loads(value)
        return loaded
    except Exception:
        return default if default is not None else value


def _maybe_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except Exception:
        return None


def _get_psets(product: Any) -> dict[str, Any]:
    require_ifc()
    try:
        import ifcopenshell.util.element

        return ifcopenshell.util.element.get_psets(product) or {}
    except Exception:
        return {}


def _get_pset(product: Any, name: str = PSET_IFC) -> dict[str, Any]:
    data = _get_psets(product)
    pset = data.get(name, {})
    return pset if isinstance(pset, dict) else {}


def writeIfc(model, ifc_path: str | Path, project_name: str = "Moosas IFC Project") -> dict[str, Any]:
    require_ifc()
    model_file, project, _body_context = setup_ifc_model(project_name)
    from ..utils.tools import mixItemListToList
    from shapely import force_3d

    site = ifcopenshell.api.run("root.create_entity", model_file, ifc_class="IfcSite", name=project_name)
    site.GlobalId = stable_guid(f"{project_name}:site")
    ifcopenshell.api.run("aggregate.assign_object", model_file, products=[site], relating_object=project)

    building = ifcopenshell.api.run("root.create_entity", model_file, ifc_class="IfcBuilding", name=project_name)
    building.GlobalId = stable_guid(f"{project_name}:building")
    ifcopenshell.api.run("aggregate.assign_object", model_file, products=[building], relating_object=site)

    levels = [float(v) for v in getattr(model, "levelList", []) or [0.0]]
    if not levels:
        levels = [0.0]
    storeys: dict[float, Any] = {}
    for level in levels:
        storey = ifcopenshell.api.run("root.create_entity", model_file, ifc_class="IfcBuildingStorey", name=f"Level_{level:g}")
        storey.GlobalId = stable_guid(f"{project_name}:storey:{level:g}")
        storey.Elevation = float(level)
        ifcopenshell.api.run("aggregate.assign_object", model_file, products=[storey], relating_object=building)
        storeys[round(float(level), 6)] = storey

    default_storey = storeys[round(levels[0], 6)]

    spaces = []
    for space in getattr(model, "spaceList", []) or []:
        space_level = float(getattr(getattr(space, "floor", None), "level", 0.0) or 0.0)
        storey = storeys.get(round(space_level, 6), default_storey)
        is_void = False
        try:
            is_void = bool(space.is_void())
        except Exception:
            is_void = False
        if is_void:
            ent = ifcopenshell.api.run(
                "root.create_entity",
                model_file,
                ifc_class="IfcBuildingElementProxy",
                name=str(space.id),
            )
        else:
            ent = ifcopenshell.api.run("root.create_entity", model_file, ifc_class="IfcSpace", name=str(space.id))
        try:
            ent.GlobalId = stable_guid(f"space:void:{space.id}") if is_void else stable_guid(f"space:{space.id}")
        except Exception:
            ent.GlobalId = stable_guid(f"space:{space.id}")
        try:
            if is_void:
                ifcopenshell.api.run("spatial.assign_container", model_file, products=[ent], relating_structure=storey)
            else:
                ifcopenshell.api.run("aggregate.assign_object", model_file, products=[ent], relating_object=storey)
        except Exception:
            ifcopenshell.api.run("aggregate.assign_object", model_file, products=[ent], relating_object=storey)
        floor_uids = [f.Uid for f in getattr(getattr(space, "floor", None), "face", [])] if getattr(space, "floor", None) else []
        ceiling_uids = [f.Uid for f in getattr(getattr(space, "ceiling", None), "face", [])] if getattr(space, "ceiling", None) else []
        wall_uids = [w.Uid for w in getattr(getattr(space, "edge", None), "wall", [])] if getattr(space, "edge", None) else []
        void_ids = [v.id for v in getattr(space, "void", [])] if getattr(space, "void", None) is not None else []
        add_pset(
            model_file,
            ent,
            {
                "MoosasType": "MoosasVoidSpace" if is_void else "MoosasSpace",
                "SpaceId": space.id,
                "SpaceSettings": json.dumps(space.settings, ensure_ascii=False),
                "SpaceLevel": space_level,
                "FloorUids": json.dumps(floor_uids, ensure_ascii=False),
                "CeilingUids": json.dumps(ceiling_uids, ensure_ascii=False),
                "WallUids": json.dumps(wall_uids, ensure_ascii=False),
                "InternalMassUids": json.dumps([w.Uid for w in getattr(space, "internalMass", [])], ensure_ascii=False),
                "VoidSpaceIds": json.dumps(void_ids, ensure_ascii=False),
            },
        )
        spaces.append(ent)

    elements = []
    all_elements = list(getattr(model, "getAllFaces", lambda dumpUseless=False: [])(False))
    for element in all_elements:
        if element is None:
            continue
        level = float(getattr(element, "level", 0.0) or 0.0)
        storey = storeys.get(round(level, 6), default_storey)
        ifc_class, predefined = _element_ifc_class(element)
        try:
            ent = ifcopenshell.api.run(
                "root.create_entity",
                model_file,
                ifc_class=ifc_class,
                predefined_type=predefined,
                name=str(getattr(element, "Uid", "")) or str(getattr(element, "id", "")),
            )
        except Exception:
            ent = ifcopenshell.api.run("root.create_entity", model_file, ifc_class="IfcBuildingElementProxy", name=str(getattr(element, "Uid", "")) or str(getattr(element, "id", "")))
        ent.GlobalId = stable_guid(f"element:{getattr(element, 'Uid', getattr(element, 'id', ''))}")
        ifcopenshell.api.run("spatial.assign_container", model_file, products=[ent], relating_structure=storey)
        geom = getattr(element, "mergedFace", None)
        if geom is None:
            geom = getattr(element, "face", None)
        if geom is not None:
            add_pset(
                model_file,
                ent,
                {
                    "MoosasType": element.__class__.__name__,
                    "IfcClass": ifc_class,
                    "Uid": getattr(element, "Uid", ""),
                    "FaceId": " ".join(mixItemListToList(getattr(element, "faceId", ""))),
                    "Level": level,
                    "Offset": getattr(element, "offset", None),
                    "U_Value": getattr(element, "U_Value", None),
                    "SHGC": getattr(element, "SHGC", None),
                    "Category": getattr(element, "category", None),
                    "Spaces": mixItemListToList(getattr(element, "space", [])),
                    "WKT": _safe_face_wkt(geom),
                    "ParentFaceUid": getattr(getattr(element, "parentFace", None), "Uid", ""),
                },
            )
        elements.append(ent)

    if getattr(model, "weather", None) is not None:
        add_pset(
            model_file,
            project,
            {
                "WeatherStationId": str(getattr(getattr(model.weather, "location", None), "stationId", "") or ""),
            },
            name=PSET_IFC,
        )

    ifc_path = Path(ifc_path)
    ifc_path.parent.mkdir(parents=True, exist_ok=True)
    model_file.write(str(ifc_path))
    return {
        "ifc_path": str(ifc_path),
        "storeys": len(storeys),
        "spaces": len(spaces),
        "elements": len(elements),
        "snapshot": True,
    }


def loadIfc(ifc_path: str | Path) -> Any:
    require_ifc()
    from ..models import MoosasModel
    from ..geometry.element import (
        MoosasFace,
        MoosasWall,
        MoosasGlazing,
        MoosasSkylight,
        MoosasFloor,
        MoosasEdge,
        MoosasSpace,
    )
    from shapely import wkt as shapely_wkt
    from shapely import force_3d, Geometry

    ifc = ifcopenshell.open(str(ifc_path))
    model = MoosasModel()
    model.geometryList = []
    model.geoId = []
    model.faceList = []
    model.wallList = []
    model.glazingList = []
    model.skylightList = []
    model.spaceList = []
    model.voidList = []
    model.levelList = []

    product_psets: dict[int, dict[str, Any]] = {}
    for product in ifc.by_type("IfcProduct"):
        pset = _get_pset(product, PSET_IFC)
        if pset:
            product_psets[product.id()] = pset

    # storeys first, so levels are available to element constructors
    storey_entities = [s for s in ifc.by_type("IfcBuildingStorey")]
    storeys = []
    for storey in storey_entities:
        elev = float(getattr(storey, "Elevation", 0.0) or 0.0)
        storeys.append(elev)
    if storeys:
        model.levelList = sorted(list({round(float(v), 6) for v in storeys}))

    element_by_uid: dict[str, Any] = {}
    element_psets: dict[str, dict[str, Any]] = {}

    def _new_geometry_from_wkt(wkt_text: str, cat: int = 0) -> str:
        geom = shapely_wkt.loads(wkt_text)
        if getattr(geom, "has_z", False) is False:
            geom = force_3d(geom, z=0.0)
        return model.includeGeo(geom, cat=cat)

    # Build all geometry-backed elements first.
    for product in ifc.by_type("IfcProduct"):
        pset = product_psets.get(product.id())
        if not pset:
            continue
        moosas_type = str(pset.get("MoosasType") or "").strip()
        if moosas_type in {"MoosasSpace", "Space"}:
            continue
        wkt_text = str(pset.get("WKT") or "").strip()
        if not wkt_text:
            continue
        uid = str(pset.get("Uid") or getattr(product, "GlobalId", "") or "")
        level = float(pset.get("Level") or getattr(product, "Elevation", 0.0) or 0.0)
        offset = float(pset.get("Offset") or 0.0)
        cat = int(float(pset.get("Category") or 0))
        geo_id = _new_geometry_from_wkt(wkt_text, cat=cat)
        if moosas_type == "MoosasFace":
            obj = MoosasFace(model, geo_id, level=level, offset=offset, uid=uid)
            u_value = _maybe_float(pset.get("U_Value"))
            if u_value is not None:
                obj.U_Value = u_value
            model.faceList.append(obj)
        elif moosas_type == "MoosasWall":
            obj = MoosasWall(model, geo_id, level=level, offset=offset, uid=uid)
            u_value = _maybe_float(pset.get("U_Value"))
            if u_value is not None:
                obj.U_Value = u_value
            model.wallList.append(obj)
        elif moosas_type == "MoosasGlazing":
            obj = MoosasGlazing(model, geo_id, level=level, offset=offset, uid=uid)
            u_value = _maybe_float(pset.get("U_Value"))
            if u_value is not None:
                obj.U_Value = u_value
            obj.SHGC = _maybe_float(pset.get("SHGC"))
            model.glazingList.append(obj)
        elif moosas_type == "MoosasSkylight":
            obj = MoosasSkylight(model, geo_id, level=level, offset=offset, uid=uid)
            u_value = _maybe_float(pset.get("U_Value"))
            if u_value is not None:
                obj.U_Value = u_value
            obj.SHGC = _maybe_float(pset.get("SHGC"))
            model.skylightList.append(obj)
        else:
            obj = MoosasFace(model, geo_id, level=level, offset=offset, uid=uid)
            u_value = _maybe_float(pset.get("U_Value"))
            if u_value is not None:
                obj.U_Value = u_value
            model.faceList.append(obj)
        element_by_uid[uid] = obj
        element_psets[uid] = pset

    # Restore glazing host links.
    for uid, obj in element_by_uid.items():
        pset = element_psets.get(uid, {})
        parent_uid = str(pset.get("ParentFaceUid") or "").strip()
        if parent_uid and hasattr(obj, "parentFace"):
            parent = element_by_uid.get(parent_uid)
            if parent is not None:
                obj.parentFace = parent
                try:
                    parent.add_glazing(obj)
                except Exception:
                    pass

    # Build spaces from the stored topology lists. The void space fallback is
    # exported as an IfcBuildingElementProxy to avoid IFC writers dropping the
    # void-only record, so we collect both native IfcSpace entities and that
    # explicit proxy form here.
    space_entities = [p for p in ifc.by_type("IfcSpace")]
    for product in ifc.by_type("IfcProduct"):
        pset = product_psets.get(product.id())
        if not pset:
            continue
        if str(pset.get("MoosasType") or "").strip() == "MoosasVoidSpace":
            space_entities.append(product)
    space_by_id: dict[str, MoosasSpace] = {}
    void_relations: list[tuple[str, list[str]]] = []
    for space_ent in space_entities:
        pset = _get_pset(space_ent, PSET_IFC)
        if not pset:
            continue
        space_id = str(pset.get("SpaceId") or space_ent.Name or getattr(space_ent, "GlobalId", ""))
        floor_ids = [str(v) for v in (_maybe_json_load(pset.get("FloorUids"), []) or [])]
        ceiling_ids = [str(v) for v in (_maybe_json_load(pset.get("CeilingUids"), []) or [])]
        wall_ids = [str(v) for v in (_maybe_json_load(pset.get("WallUids"), []) or [])]
        internal_mass_ids = [str(v) for v in (_maybe_json_load(pset.get("InternalMassUids"), []) or [])]
        void_ids = [str(v) for v in (_maybe_json_load(pset.get("VoidSpaceIds"), []) or [])]
        settings = _maybe_json_load(pset.get("SpaceSettings"), {})
        floor = MoosasFloor([element_by_uid[v] for v in floor_ids if v in element_by_uid]) if floor_ids else None
        ceiling = MoosasFloor([element_by_uid[v] for v in ceiling_ids if v in element_by_uid]) if ceiling_ids else None
        walls = [element_by_uid[v] for v in wall_ids if v in element_by_uid]
        if not walls:
            continue
        edge = MoosasEdge(walls)
        space = MoosasSpace(floor, edge, ceiling)
        if isinstance(settings, dict):
            space.settings.update(settings)
        space.settings["zone_name"] = space_id
        try:
            space._MoosasSpace__id = space_id
        except Exception:
            pass
        for internal_uid in internal_mass_ids:
            if internal_uid in element_by_uid:
                try:
                    space.addInternalMass(element_by_uid[internal_uid])
                except Exception:
                    pass
        # Keep IFC-loaded spaces in the main space list to match the RDF/XML
        # import convention used elsewhere in the project. Void semantics are
        # preserved on the space object itself and via parent.add_void().
        model.spaceList.append(space)
        space_by_id[space_id] = space
        if void_ids:
            void_relations.append((space_id, void_ids))

    for parent_id, void_ids in void_relations:
        parent = space_by_id.get(parent_id)
        if parent is None:
            continue
        for void_id in void_ids:
            void = space_by_id.get(void_id)
            if void is not None and void not in parent.void:
                try:
                    parent.add_void(void)
                except Exception:
                    pass

    # Restore schedule and weather if present in IFC project pset.
    projects = ifc.by_type("IfcProject")
    if projects:
        project_pset = _get_pset(projects[0], PSET_IFC)
        weather_station = str(project_pset.get("WeatherStationId") or "").strip()
        if weather_station:
            try:
                model.loadWeatherData(weather_station)
            except Exception:
                pass

    return model


def rdf_to_ifc(rdf_path: str | Path, ifc_path: str | Path, rdf_format: str = "turtle", project_name: str = "RDF-IFC Project") -> dict[str, Any]:
    from ._rdf import loadRDF

    model = loadRDF(str(rdf_path), fileFormat=rdf_format)
    return writeIfc(model, ifc_path, project_name=project_name)


def ifc_to_rdf(ifc_path: str | Path, rdf_path: str | Path, rdf_format: str = "turtle") -> dict[str, Any]:
    from ._rdf import writeRDF

    model = loadIfc(ifc_path)
    writeRDF(model, str(rdf_path), fileFormat=rdf_format, dumpUseless=True)
    return {
        "rdf_path": str(rdf_path),
        "source_restored": True,
    }


def inspect_ifc(ifc_path: str | Path) -> dict[str, Any]:
    require_ifc()
    model = ifcopenshell.open(str(ifc_path))
    counts = {name: len(model.by_type(name)) for name in [
        "IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcSpace",
        "IfcWall", "IfcWindow", "IfcDoor", "IfcSlab", "IfcCovering", "IfcRoof", "IfcBuildingElementProxy",
        "IfcProductDefinitionShape", "IfcPropertySet",
    ]}
    counts["schema"] = model.schema
    counts["total_entities"] = len(list(model))
    return counts


def roundtrip(rdf_input: str | Path, ifc_output: str | Path, rdf_output: str | Path, rdf_format: str = "turtle") -> dict[str, Any]:
    rdf_to_ifc_result = rdf_to_ifc(rdf_input, ifc_output, rdf_format=rdf_format)
    ifc_stats = inspect_ifc(ifc_output)
    ifc_to_rdf_result = ifc_to_rdf(ifc_output, rdf_output, rdf_format=rdf_format)
    return {"rdf_to_ifc": rdf_to_ifc_result, "ifc_stats": ifc_stats, "ifc_to_rdf": ifc_to_rdf_result}


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Moosas IFC bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("rdf2ifc", help="Convert RDF to IFC4 using the Moosas model bridge")
    p1.add_argument("rdf_input")
    p1.add_argument("ifc_output")
    p1.add_argument("--format", default="turtle", help="rdflib input format, default: turtle")
    p1.add_argument("--project-name", default="RDF-IFC Project")

    p2 = sub.add_parser("ifc2rdf", help="Convert IFC4 to RDF using the Moosas model bridge")
    p2.add_argument("ifc_input")
    p2.add_argument("rdf_output")
    p2.add_argument("--format", default="turtle", help="rdflib output format, default: turtle")

    p3 = sub.add_parser("inspect", help="Inspect IFC entity counts")
    p3.add_argument("ifc_input")

    p4 = sub.add_parser("roundtrip", help="Run RDF -> IFC -> RDF")
    p4.add_argument("rdf_input")
    p4.add_argument("ifc_output")
    p4.add_argument("rdf_output")
    p4.add_argument("--format", default="turtle")

    args = parser.parse_args(argv)
    if args.command == "rdf2ifc":
        result = rdf_to_ifc(args.rdf_input, args.ifc_output, rdf_format=args.format, project_name=args.project_name)
    elif args.command == "ifc2rdf":
        result = ifc_to_rdf(args.ifc_input, args.rdf_output, rdf_format=args.format)
    elif args.command == "inspect":
        result = inspect_ifc(args.ifc_input)
    elif args.command == "roundtrip":
        result = roundtrip(args.rdf_input, args.ifc_output, args.rdf_output, rdf_format=args.format)
    else:
        raise AssertionError(args.command)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
