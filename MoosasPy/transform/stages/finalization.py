"""Topology and optional finalization stage for transformations."""
from __future__ import annotations

from ...models import MoosasModel
from ...utils import np, shapely
from ...utils.tools import searchBy
from .standardization import standardize_model
from .topology import build_face_topology, build_space_topology
from .validation import validate_model


def finalize_model(
    model: MoosasModel,
    *,
    break_wall_vertical: bool,
    attach_shading: bool,
    standardize: bool,
) -> MoosasModel:
    """Build topology, then apply optional content attachment and standardization."""
    model = build_space_topology(model, break_wall_vertical)
    model = build_face_topology(model)
    if attach_shading:
        model = attach_shading_content(model)
    if standardize:
        model = standardize_model(model)
    return validate_model(model)


def attach_shading_content(model: MoosasModel) -> MoosasModel:
    """Attach leftover geometry as internal mass or nearby glazing shading."""
    shading = np.array(model.wall_remain + model.face_remain)
    keep_mask = [True] * len(shading)
    for index, element in enumerate(shading):
        print(f"\rCONTENT: attach internal thermal mass:{index}/{len(shading)}", end="")
        space_indices = searchBy("level", element.level, model.spaceList)
        for space_index in space_indices:
            if shapely.contains(model.spaceList[space_index].force_2d(), element.force_2d()):
                model.spaceList[space_index].addInternalMass(element)
                keep_mask[space_index] = False
                break

    shading = shading[keep_mask]
    print()
    for index, face in enumerate(shading):
        print(f"\rCONTENT: attach shading element:{index}/{len(shading)}", end="")
        centroid = face.getWeightCenter()
        levels = [level for level in model.levelList if level < centroid[2]]
        if not levels:
            continue
        glazing = list(np.array(model.glazingList)[searchBy("level", levels[-1], model.glazingList)])
        glazing += list(np.array(model.skylightList)[searchBy("level", levels[-1], model.skylightList)])
        if not glazing:
            continue
        target_glazing = min(glazing, key=lambda item: shapely.distance(face.force_2d(), item.force_2d()))
        if shapely.distance(face.force_2d(), target_glazing.force_2d()) < 1.5:
            target_glazing.shading.append(face)
    print()
    return model
