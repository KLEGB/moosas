from types import SimpleNamespace

from MoosasPy.model.io.idf import adapter
from MoosasPy.transform.stages.assembly import identify_basement_spaces


def _space(space_id: str, elevation: float, space_type: str = "room", conditioned: bool = True):
    return SimpleNamespace(
        id=space_id,
        floor=SimpleNamespace(level=elevation, offset=0.0),
        space_type=space_type,
        conditioned=conditioned,
    )


def test_identify_basement_spaces_uses_floor_elevation_and_half_meter_threshold():
    basement = _space("basement", -3.0)
    threshold = _space("threshold", -0.5)
    ground_floor = _space("ground", 0.0)
    model = SimpleNamespace(spaceList=[basement, threshold, ground_floor])

    result = identify_basement_spaces(model)

    assert result is model
    assert basement.space_type == "basement"
    assert threshold.space_type == "room"
    assert ground_floor.space_type == "room"


def test_identify_basement_spaces_preserves_core_conditioning_settings():
    core = _space("core", -3.0, space_type="core", conditioned=False)
    model = SimpleNamespace(spaceList=[core])

    identify_basement_spaces(model)

    assert core.space_type == "basement"
    assert core.conditioned is False


def test_idf_auto_zone_mapping_maps_recognized_space_types(monkeypatch):
    zones = [
        {"Name": "Room Template"},
        {"Name": "Main Attic"},
        {"Name": "Main Basement"},
    ]
    monkeypatch.setattr(adapter, "IDF", lambda _: SimpleNamespace(idfobjects={"ZONE": zones}))
    model = SimpleNamespace(
        spaceList=[
            _space("room", 0.0),
            _space("attic", 3.0, space_type="attic"),
            _space("basement", -3.0, space_type="basement"),
        ]
    )

    mapping = adapter._idf_auto_zone_mapping(model, "template.idf")

    assert mapping == {
        "Room Template": ["room"],
        "Main Attic": ["attic"],
        "Main Basement": ["basement"],
    }
