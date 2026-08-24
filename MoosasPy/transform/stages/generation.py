"""Space-boundary generation stage for the transformation pipeline."""
from __future__ import annotations

from collections.abc import Callable

from ...models import MoosasModel


def generate_space_boundaries(
    model: MoosasModel,
    generation_method: Callable[[MoosasModel], MoosasModel],
) -> MoosasModel:
    """Populate a cleansed model's boundary list using the selected generator."""
    return generation_method(model)