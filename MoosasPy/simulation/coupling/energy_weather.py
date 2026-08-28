"""Weather-to-energy workflow."""

from __future__ import annotations

from ...model_resources import load_weather
from ..energy.runner import energyAnalysis


def run_energy_with_weather(model, *, station_id: str = "545110", **energy_options):
    """Load weather onto a model, then run energy analysis."""
    if model.weather is None:
        load_weather(model, station_id)
    return energyAnalysis(model, **energy_options)
