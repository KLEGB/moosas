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
    for wall in model.wallList:
        if not wall.is_air_boundary:
            continue
        adjacent_ids = {str(space_id) for space_id in wall.space}
        if len(adjacent_ids) != 2 or not adjacent_ids.issubset(known_ids):
            issues.append(
                f"air boundary {wall.Uid!r} must connect exactly two model spaces"
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
