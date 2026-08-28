"""Weather-to-energy workflow."""

from __future__ import annotations

from ..energy.runner import energyAnalysis
from ..weather import load_station_weather


def run_energy_with_weather(model, *, station_id: str = "545110", **energy_options):
    """Load weather onto a model, then run energy analysis."""
    if model.weather is None:
        model.weather = load_station_weather(station_id)
    return energyAnalysis(model, **energy_options)
