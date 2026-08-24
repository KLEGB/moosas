# Transformation Boundary

`MoosasPy.transform` owns all geometry, model conversion, encoding, and
multi-file alignment workflows.

| Target module | Current source | Responsibility |
| --- | --- | --- |
| `pipeline.py` | former `transformation.py` | draft geometry to structured model pipeline |
| `geometry/` | former `MoosasPy.geometry`, convexification helpers | geometry types, cleanup, topology, and space generation |
| `io/` | former `MoosasPy.IO` and graph encoders | model loading, saving, format adapters, graph encoding, and dispatch |
| `alignment/` | former `MoosasPy.IO.alignment` | RDF/IDF graph linking and multi-file alignment |

Migration rules:

1. New code imports from `MoosasPy.transform` or one of its subpackages.
2. File adapters return a model representation only; topology completion and
   cleanup remain explicit pipeline steps.
3. Geometry algorithms must not import the encoding or IO layers.
4. Add a focused regression test before changing a format adapter or pipeline
   stage.