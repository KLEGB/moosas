"""Geometry representation standardization stage."""
from __future__ import annotations

from ...models import MoosasModel
from ...utils import mixItemListToList, np
from ..geometry.element import MoosasFace, MoosasGlazing, MoosasSkylight
from ..geometry.geos import GeometryError


def standardize_model(model: MoosasModel) -> MoosasModel:
    """Replace active element geometry with simplified representations."""
    elements = model.getAllFaces()
    for index, element in enumerate(elements):
        try:
            if isinstance(element, MoosasFace) and abs(np.asarray(element.normal, dtype=float)[2]) < 0.99:
                continue
            category = (
                mixItemListToList(element.category)[0]
                if isinstance(element, (MoosasSkylight, MoosasGlazing))
                else 0
            )
            geometry_id = model.includeGeo(element.representation(), element.normal, cat=category)
            element.replaceGeo(geometry_id)
            print(f"\rIO: standardizing faces {index}/{len(elements)}", end="")
        except GeometryError:
            print("******Warning: GeometryError, this face would not be standardized")
    print()
    return model
