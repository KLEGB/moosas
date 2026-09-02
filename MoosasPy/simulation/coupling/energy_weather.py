"""Weather-to-energy workflow."""

from __future__ import annotations

from ..energy.runner import energyAnalysis
from ..weather import WeatherData


def run_energy_with_weather(model, *, weather: WeatherData, **energy_options):
    """Run energy analysis with an already prepared weather object."""
    return energyAnalysis(model, weather=weather, **energy_options)
