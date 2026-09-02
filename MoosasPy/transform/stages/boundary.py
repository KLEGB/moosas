"""Boundary preparation stage for draft geometry models."""
from __future__ import annotations

from ...model import MoosasModel
from ..geometry.boundary import geometry_arrays, simplify_to_layered_obb
from ..geometry.core import inject_minimal_core
from ..geometry.element import MoosasGeometry
from ..geometry.geos import Vector


def _replace_geometry(model, categories, face_ids, normals, faces, holes):
    geometry_list = []
    for category, face_id, normal, face, face_holes in zip(
        categories, face_ids, normals, faces, holes
    ):
        if isinstance(face_holes, dict):
            face_holes = [face_holes[index] for index in sorted(face_holes)]
        geometry_list.append(
            MoosasGeometry(
                face,
                str(face_id),
                Vector(normal),
                int(category),
                face_holes or [],
                errors="raise",
            )
        )
    model.geometryList = geometry_list
    model.geoId = [geometry.faceId for geometry in geometry_list]
    model.newIndex = len(geometry_list)
    return model


def prepare_boundary_geometry(
    model: MoosasModel,
    *,
    simplify_boundary: bool,
    insert_core: bool,
) -> MoosasModel:
    """Apply requested boundary operations to a draft geometry model."""
    if not simplify_boundary and not insert_core:
        return model

    categories, face_ids, normals, faces, holes = geometry_arrays(model.geometryList)
    if simplify_boundary:
        categories, face_ids, normals, faces, holes = simplify_to_layered_obb(
            categories, normals, faces
        )

    if insert_core:
        original_face_count = len(faces)
        categories, face_ids, normals, faces, holes = inject_minimal_core(
            categories, face_ids, normals, faces, holes
        )
        if len(faces) == original_face_count:
            raise ValueError("Core insertion could not find a valid multi-level footprint.")

    return _replace_geometry(model, categories, face_ids, normals, faces, holes)
