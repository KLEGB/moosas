"""Weather-to-radiation workflows for direct sunlight analysis."""

from __future__ import annotations

from ..radiation import positionSunHour
from ..weather.directsky import MoosasDirectSky


def run_position_sun_hours(position_rays, location, **radiation_options):
    """Build a direct-sun sky from a location and run sunlight analysis."""
    sky = MoosasDirectSky(location.latitude, location.longitude)
    return positionSunHour(position_rays, sky=sky, **radiation_options)
