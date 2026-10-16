"""The public room inspection contract used by OpenFOAM clients."""

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

from MoosasPy.model.io import foam
from MoosasPy.transform import transform


def _surface(uid, points, glazing=()):
    return SimpleNamespace(
        Uid=uid,
        face=np.array([shapely.Polygon(points)], dtype=object),
        glazingElement=list(glazing),
        area=1.0,
    )


def _room(opening_y=0.0, missing_wall=False):
    opening = _surface("gls_window", [(1, opening_y, 1), (2, opening_y, 1),
                                      (2, opening_y, 2), (1, opening_y, 2)])
    walls = [
        _surface("wall_front", [(0, 0, 0), (4, 0, 0), (4, 0, 3), (0, 0, 3)], [opening]),
        _surface("wall_back", [(0, 4, 0), (4, 4, 0), (4, 4, 3), (0, 4, 3)]),
        _surface("wall_left", [(0, 0, 0), (0, 4, 0), (0, 4, 3), (0, 0, 3)]),
    ]
    if not missing_wall:
        walls.append(_surface("wall_right", [(4, 0, 0), (4, 4, 0), (4, 4, 3), (4, 0, 3)]))
    faces = {
        "MoosasFloor": [_surface("floor", [(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)])],
        "MoosasCeiling": [_surface("ceiling", [(0, 0, 3), (4, 0, 3), (4, 4, 3), (0, 4, 3)])],
        "MoosasWall": walls,
        "MoosasGlazing": [opening],
        "MoosasSkylight": [],
    }
    space = SimpleNamespace(id="room_0", getAllFaces=lambda to_dict: faces)
    return SimpleNamespace(spaceList=[space]), faces


def test_inspection_reports_ready_opening_and_closed_room():
    model, _ = _room()
    result = foam.inspectFoamSpace(model, 0)
    assert result["spaces"] == [{"index": 0, "id": "room_0"}]
    assert result["room_closed"] is True
    assert result["openings"][0]["parent_uids"] == ["wall_front"]
    assert result["openings"][0]["patch_valid"] is True


def test_inspection_keeps_offset_opening_and_missing_wall_separate():
    offset, _ = _room(opening_y=0.3)
    result = foam.inspectFoamSpace(offset, 0)
    assert result["room_closed"] is True
    assert result["openings"][0]["patch_valid"] is False
    assert "gls_window" in result["openings"][0]["status"]

    incomplete, _ = _room(missing_wall=True)
    result = foam.inspectFoamSpace(incomplete, 0)
    assert result["room_closed"] is False
    assert result["openings"][0]["patch_valid"] is True
    assert any("wall" in item and "not closed" in item for item in result["diagnostics"])


def test_inspection_reports_overlapping_opening_selections():
    model, faces = _room()
    original = faces["MoosasGlazing"][0]
    second = SimpleNamespace(Uid="gls_overlap", face=original.face, area=1.0)
    faces["MoosasGlazing"].append(second)
    faces["MoosasWall"][0].glazingElement.append(second)
    result = foam.inspectFoamSpace(model, 0)
    assert all(opening["patch_valid"] for opening in result["openings"])
    assert any("overlap" in item and "wall_front" in item for item in result["diagnostics"])


def test_real_boundary_openings_are_inspected_by_exporter_geometry():
    model = transform(str(Path(__file__).parent / "caseFile/room_boundary_openings.geo"), input_type="geo")
    result = foam.inspectFoamSpace(model, 0)
    assert result["room_closed"] is True
    by_uid = {opening["uid"]: opening for opening in result["openings"]}
    assert by_uid["gls_glazing_0"]["patch_valid"] is True
    assert by_uid["gls_glazing_2"]["patch_valid"] is True


@pytest.mark.parametrize("index", [-1, 1, "0", True])
def test_inspection_rejects_invalid_space_index(index):
    model, _ = _room()
    with pytest.raises(ValueError, match="zero-based integer"):
        foam.inspectFoamSpace(model, index)
