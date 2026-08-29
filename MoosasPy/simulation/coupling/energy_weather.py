"""Weather-to-energy workflow."""

from __future__ import annotations

from ..energy.runner import energyAnalysis
from ..weather import load_station_weather


def run_energy_with_weather(model, *, station_id: str = "545110", **energy_options):
    """Load weather, then pass it explicitly to energy analysis."""
    weather = load_station_weather(station_id)
    return energyAnalysis(model, weather=weather, **energy_options)
