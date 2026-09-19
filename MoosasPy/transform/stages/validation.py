"""Read-only validation for completed Moosas models."""
from __future__ import annotations

from ...model import MoosasModel


def validate_model(model: MoosasModel) -> MoosasModel:
    """Raise ValueError when stable domain-model invariants are violated."""
    space_ids = [str(space.id) for space in model.spaceList]
    issues = []
    if len(space_ids) != len(set(space_ids)):
        issues.append("space IDs must be unique")

    known_ids = set(space_ids)
    residual_walls = set(model.wall_remain)
    for wall in model.wallList:
        if not wall.is_air_boundary or wall in residual_walls:
            continue
        adjacent_ids = {str(space_id) for space_id in wall.space}
        # An AirWall can be an internal virtual boundary, an exterior/open
        # boundary attached to one space, or an unassigned open boundary.
        # Requiring exactly two spaces rejects valid transparent exterior
        # faces imported from SketchUp.
        if not adjacent_ids.issubset(known_ids):
            issues.append(
                f"air boundary {wall.Uid!r} references an unknown model space"
            )
    for space in model.spaceList:
        if space.area <= 0:
            issues.append(f"space {space.id!r} must have positive area")
        for neighbor_id in space.neighbor:
            if str(neighbor_id) == str(space.id):
                issues.append(f"space {space.id!r} cannot neighbor itself")
            elif str(neighbor_id) not in known_ids:
                issues.append(f"space {space.id!r} references unknown neighbor {neighbor_id!r}")
    if issues:
        raise ValueError("Invalid MoosasModel: " + "; ".join(issues))
    return model
