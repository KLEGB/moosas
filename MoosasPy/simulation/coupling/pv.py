"""Radiation-to-energy workflows for building-integrated photovoltaics."""

from __future__ import annotations

from ...model import MoosasModel
from ...transform.geometry.element import MoosasElement
from ...utils import np
from ..energy.pv import calculate_pv_generation
from ..radiation import faceRadiation, writeRadGeo
from ..weather import CumulativeSky, load_cumulative_sky_matrix


def run_roof_pv(
    model: MoosasModel,
    useful_area_ratio: float = 0.7,
    efficiency: float = 0.17,
    station_id: str = "545110",
    grid_size: float = 1.0,
    grid_offset: float = 0.2,
    reflection: int = 0,
) -> np.ndarray:
    """Calculate hourly PV generation for exterior roof faces."""
    faces = [
        face
        for face in model.getAllFaces(True)["MoosasFace"]
        if face.isOuter and list(model.levelList).index(face.level) != 0
    ]
    return _run_pv(
        model,
        faces,
        useful_area_ratio=useful_area_ratio,
        efficiency=efficiency,
        station_id=station_id,
        grid_size=grid_size,
        grid_offset=grid_offset,
        reflection=reflection,
    )


def run_facade_pv(
    model: MoosasModel,
    useful_area_ratio: float = 0.4,
    efficiency: float = 0.17,
    station_id: str = "545110",
    grid_size: float | None = None,
    grid_offset: float = 0.2,
    reflection: int = 0,
) -> np.ndarray:
    """Calculate hourly PV generation for exterior facade faces."""
    faces = [
        face
        for face in model.getAllFaces(True)["MoosasWall"]
        if face.isOuter and list(model.levelList).index(face.level) != 0
    ]
    return _run_pv(
        model,
        faces,
        useful_area_ratio=useful_area_ratio,
        efficiency=efficiency,
        station_id=station_id,
        grid_size=grid_size,
        grid_offset=grid_offset,
        reflection=reflection,
    )


def calculate_face_incident_energy(
    faces: MoosasElement | list[MoosasElement],
    cumulative_sky_values,
    *,
    grid_size: float | None = None,
    grid_offset: float = 0.2,
    reflection: int = 0,
    geo_path: str,
    radiation_scale: float = CumulativeSky.RADIATION_SCALE,
) -> np.ndarray:
    """Aggregate hourly incident solar energy across a collection of faces."""
    if isinstance(faces, MoosasElement):
        faces = [faces]
    faces = list(faces)
    sky_values = np.asarray(cumulative_sky_values, dtype=float)
    if sky_values.ndim != 2:
        raise ValueError("cumulative_sky_values must be a patch-by-hour matrix")
    if radiation_scale <= 0:
        raise ValueError("radiation_scale must be positive")
    if not faces:
        return np.zeros(sky_values.shape[1])

    generation_series = []
    for face in faces:
        visibility = faceRadiation(
            face,
            grid_size,
            grid_offset,
            None,
            reflection,
            geo_path,
        )
        if len(visibility) != sky_values.shape[0]:
            raise ValueError("sky patch count does not match radiation visibility")
        generation_series.append(
            face.area * np.sum(visibility[:, np.newaxis] * sky_values, axis=0) / radiation_scale
        )
    return np.sum(generation_series, axis=0)


def _run_pv(
    model,
    faces,
    *,
    useful_area_ratio,
    efficiency,
    station_id,
    grid_size,
    grid_offset,
    reflection,
):
    sky_values = load_cumulative_sky_matrix(station_id)
    incident_energy = calculate_face_incident_energy(
        faces,
        sky_values,
        grid_size=grid_size,
        grid_offset=grid_offset,
        reflection=reflection,
        geo_path=writeRadGeo(model),
    )
    return calculate_pv_generation(
        incident_energy,
        useful_area_ratio=useful_area_ratio,
        efficiency=efficiency,
    )
