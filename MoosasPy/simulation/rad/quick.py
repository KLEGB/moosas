"""Fast daylight-factor estimates."""

from ...transformation.geometry.element import MoosasSpace
from ...utils import np


def spaceDaylightFactor_quick(space: MoosasSpace, light_transmittance: float = 0.6) -> float:
    """Estimate a space daylight factor from exterior window area."""
    window_area = np.sum([wall.area * wall.wwr for wall in space.edge.wall if wall.isOuter])
    daylight_factor = 45 * window_area * light_transmittance / space.area / 0.76
    return min(daylight_factor, 100)


# The incomplete grid-based ``spaceDaylightFactor`` implementation was retired
# during the daylight API consolidation. Use radiance.simModel for Radiance-based
# calculations.
