"""Energy workflows that require radiation-domain results."""

from __future__ import annotations

from ..energy.runner import EnergyRunner
from ..radiation import modelRadiation
from ..weather import CumulativeSky, WeatherData


def run_energy_with_radiation(
    model,
    *,
    weather: WeatherData,
    cumulative_skies: dict[str, CumulativeSky],
    radiation_mode: int = 1,
    reflection: int = 0,
    **energy_options,
):
    """Calculate radiation, then run energy analysis with those results."""
    if radiation_mode not in (1, 2):
        raise ValueError("radiation_mode must be 1 or 2")
    modelRadiation(model, cumulative_skies, reflection=reflection)
    return EnergyRunner(
        model=model,
        weather=weather,
        require_radiation=radiation_mode,
        **energy_options,
    ).run()
