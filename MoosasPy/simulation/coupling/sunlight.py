"""Weather-to-radiation workflows for direct sunlight analysis."""

from __future__ import annotations

from ..radiation import positionSunHour
from ..weather import DirectSky


def run_position_sun_hours(position_rays, location, **radiation_options):
    """Build a direct-sun sky from a location and run sunlight analysis."""
    sky = DirectSky(location.latitude, location.longitude)
    return positionSunHour(position_rays, sky=sky, **radiation_options)
