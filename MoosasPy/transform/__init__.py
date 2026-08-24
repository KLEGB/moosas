"""Model transformation public API and staged refactoring boundary."""

__all__ = [
    "complete_topology",
    "load",
    "save",
    "TransformOptions",
    "structured",
    "transform",
]


def __getattr__(name):
    if name == "TransformOptions":
        from .stages.options import TransformOptions

        return TransformOptions
    if name in {"complete_topology", "structured", "transform"}:
        from . import pipeline

        return getattr(pipeline, name)
    if name in {"load", "save"}:
        from . import io

        return getattr(io, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")