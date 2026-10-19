"""Reference-aware cleanup of exported construction and material definitions."""

from collections import defaultdict

from eppy.modeleditor import IDF


def prune_unused_constructions_and_materials(idf: IDF):
    """Keep definitions reachable from consumers through IDD object-list fields."""
    candidates = {
        id(obj): obj for key, objects in idf.idfobjects.items()
        if key in {"CONSTRUCTION", "MATERIAL"} or key.startswith((
            "CONSTRUCTION:", "MATERIAL:", "WINDOWMATERIAL:",
        ))
        for obj in objects
    }
    definitions = defaultdict(set)
    for object_id, obj in candidates.items():
        for value, metadata in zip(obj.obj, obj.objidd):
            if isinstance(value, str) and value:
                for reference in metadata.get("reference", ()):
                    definitions[(reference.casefold(), value.casefold())].add(object_id)

    pending = [obj for objects in idf.idfobjects.values() for obj in objects if id(obj) not in candidates]
    retained = set()
    while pending:
        obj = pending.pop()
        for value, metadata in zip(obj.obj, obj.objidd):
            if not isinstance(value, str) or not value:
                continue
            for reference in metadata.get("object-list", ()):
                for object_id in definitions.get((reference.casefold(), value.casefold()), ()):
                    if object_id not in retained:
                        retained.add(object_id)
                        pending.append(candidates[object_id])
    for object_id, obj in candidates.items():
        if object_id not in retained:
            idf.removeidfobject(obj)
