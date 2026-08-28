"""Photovoltaic energy conversion without radiation-domain dependencies."""

from __future__ import annotations

from ...utils import np


def calculate_pv_generation(
    incident_energy,
    *,
    useful_area_ratio: float,
    efficiency: float,
) -> np.ndarray:
    """Convert area-integrated incident solar energy into PV generation.

    ``incident_energy`` may be a scalar or an array. Its unit is preserved;
    for example, hourly kWh input produces hourly kWh output.
    """
    useful_area_ratio = float(useful_area_ratio)
    efficiency = float(efficiency)
    if not 0.0 <= useful_area_ratio <= 1.0:
        raise ValueError("useful_area_ratio must be between 0 and 1")
    if not 0.0 <= efficiency <= 1.0:
        raise ValueError("efficiency must be between 0 and 1")
    return np.asarray(incident_energy, dtype=float) * useful_area_ratio * efficiency
