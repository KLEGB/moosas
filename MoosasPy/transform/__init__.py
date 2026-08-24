"""Model transformation public API and staged refactoring boundary."""

__all__ = [
    "complete_topology",
    "load_model",
    "model_from_file",
    "save_model",
    "structured",
    "transform",
]


def __getattr__(name):
    if name in {"complete_topology", "load_model", "structured", "transform"}:
        from . import pipeline

        return getattr(pipeline, name)
    if name in {"model_from_file", "save_model"}:
        from . import io

        return getattr(io, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")