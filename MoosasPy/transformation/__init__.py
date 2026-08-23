"""Model transformation public API and staged refactoring boundary."""

__all__ = [
    "load_model",
    "loadModel",
    "model_from_file",
    "modelFromFile",
    "save_model",
    "saveModel",
    "structured",
    "transform",
]


def __getattr__(name):
    if name in {"structured", "transform"}:
        from . import pipeline

        return getattr(pipeline, name)
    if name in {"load_model", "model_from_file", "save_model"}:
        from . import io

        return getattr(io, name)
    legacy_names = {
        "loadModel": "load_model",
        "modelFromFile": "model_from_file",
        "saveModel": "save_model",
    }
    if name in legacy_names:
        return getattr(__import__(__name__, fromlist=[legacy_names[name]]), legacy_names[name])
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")