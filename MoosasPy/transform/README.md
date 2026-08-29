# Transformation Boundary

`MoosasPy.transform` accepts GEO, OBJ, and STL geometry sources and produces a
structured `MoosasModel`. It does not load or save semantic model formats.

| Module | Responsibility |
| --- | --- |
| `pipeline.py` | Geometry source to complete `MoosasModel` pipeline |
| `importers/` | GEO, OBJ, and STL source readers |
| `stages/` | Classification, cleanup, generation, assembly, and topology |
| `geometry/` | Geometry types and transformation algorithms |
| `alignment/` | RDF/IDF graph linking and multi-file alignment |

Model formats are owned by `MoosasPy.model.io` and exposed only through
`MoosasModel.load()` and `model.save()`.

Dependency rules:

1. Geometry files enter through `transform()` only.
2. Transform stages return a complete `MoosasModel`.
3. Geometry algorithms do not import model I/O or simulation.
4. Simulation consumes `MoosasModel` and does not invoke transform.
