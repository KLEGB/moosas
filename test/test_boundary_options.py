from __future__ import annotations

import pytest

from MoosasPy.models import MoosasModel
from MoosasPy.transform import TransformOptions
from MoosasPy.transform.stages.boundary import prepare_boundary_geometry
from MoosasPy.transform.geometry.element import MoosasGeometry
from MoosasPy.utils import np


def _three_story_box() -> MoosasModel:
    model = MoosasModel()
    faces = []
    for index, z_value in enumerate((0.0, 3.0, 6.0, 9.0)):
        faces.append(
            MoosasGeometry(
                np.array([
                    [0.0, 0.0, z_value],
                    [10.0, 0.0, z_value],
                    [10.0, 8.0, z_value],
                    [0.0, 8.0, z_value],
                ]),
                f'level_{index}',
                np.array([0.0, 0.0, 1.0]),
            )
        )
    walls = (
        ([[0, 0, 0], [0, 0, 9], [10, 0, 9], [10, 0, 0]], [0, -1, 0]),
        ([[10, 0, 0], [10, 0, 9], [10, 8, 9], [10, 8, 0]], [1, 0, 0]),
        ([[10, 8, 0], [10, 8, 9], [0, 8, 9], [0, 8, 0]], [0, 1, 0]),
        ([[0, 8, 0], [0, 8, 9], [0, 0, 9], [0, 0, 0]], [-1, 0, 0]),
    )
    for index, (face, normal) in enumerate(walls):
        faces.append(MoosasGeometry(np.asarray(face), f'wall_{index}', np.asarray(normal)))
    model.geometryList = faces
    model.geoId = [geometry.faceId for geometry in faces]
    model.newIndex = len(faces)
    return model


def test_boundary_options_default_to_disabled():
    options = TransformOptions()
    assert options.simplify_boundary is False
    assert options.insert_core is False


def test_disabled_boundary_operations_preserve_geometry_objects():
    model = _three_story_box()
    original_geometry = model.geometryList

    result = prepare_boundary_geometry(
        model,
        simplify_boundary=False,
        insert_core=False,
    )

    assert result is model
    assert result.geometryList is original_geometry


@pytest.mark.parametrize('insert_core, expected_faces', ((False, 18), (True, 30)))
def test_simplify_boundary_builds_one_obb_per_story(insert_core, expected_faces):
    model = prepare_boundary_geometry(
        _three_story_box(),
        simplify_boundary=True,
        insert_core=insert_core,
    )

    assert len(model.geometryList) == expected_faces
    assert {
        geometry.faceId.split('_')[0]
        for geometry in model.geometryList
        if geometry.faceId.startswith('layer')
    } == {'layer1', 'layer2', 'layer3'}
    assert sum(geometry.faceId.startswith('core_wall_') for geometry in model.geometryList) == (
        12 if insert_core else 0
    )


def test_insert_core_operates_on_unsimplified_boundary():
    model = prepare_boundary_geometry(
        _three_story_box(),
        simplify_boundary=False,
        insert_core=True,
    )

    assert len(model.geometryList) == 20
    assert sum(geometry.faceId.startswith('core_wall_') for geometry in model.geometryList) == 12


def test_simplify_boundary_rejects_single_level_geometry():
    model = _three_story_box()
    model.geometryList = model.geometryList[:1]

    with pytest.raises(ValueError, match='at least two horizontal levels'):
        prepare_boundary_geometry(
            model,
            simplify_boundary=True,
            insert_core=False,
        )
