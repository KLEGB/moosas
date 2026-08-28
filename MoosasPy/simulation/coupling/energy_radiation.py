"""Energy workflows that require radiation-domain results."""

from __future__ import annotations

from ...model_resources import load_cumulative_sky, load_weather
from ..energy.runner import energyAnalysis
from ..radiation import modelRadiation


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
    if model.weather is None:
        load_weather(model, station_id)
    if model.cumSky is None:
        load_cumulative_sky(model, station_id)
    modelRadiation(model, reflection=reflection)
    return energyAnalysis(
        model,
        requireRadiation=radiation_mode,
        **energy_options,
    )
