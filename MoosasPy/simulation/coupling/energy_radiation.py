"""Energy workflows that require radiation-domain results."""

from __future__ import annotations

from ..energy.runner import energyAnalysis
from ..radiation import modelRadiation
from ..weather import load_cumulative_sky, load_station_weather


def run_energy_with_radiation(
    model,
    *,
    radiation_mode: int = 1,
    station_id: str = "545110",
    reflection: int = 0,
    **energy_options,
):
    """Calculate radiation, then run energy analysis with those results."""
    if radiation_mode not in (1, 2):
        raise ValueError("radiation_mode must be 1 or 2")
    weather = load_station_weather(station_id)
    cumulative_sky = load_cumulative_sky(station_id)
    modelRadiation(model, cumulative_sky, reflection=reflection)
    return energyAnalysis(
        model,
        weather=weather,
        requireRadiation=radiation_mode,
        **energy_options,
    )
