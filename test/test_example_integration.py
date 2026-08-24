from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import math
import unittest

from MoosasPy.model_resources import configure_model_resources, load_weather
from MoosasPy.simulation.energy.runner import EnergyRunner
from MoosasPy.transform import TransformOptions, structured, transform
from MoosasPy.transform.pipeline import _load_geometry_source
from MoosasPy.transform.stages.classification import classify_model
from MoosasPy.transform.stages.cleansing import cleanse_model
from MoosasPy.transform.stages.generation import generate_space_boundaries
from MoosasPy.transform.io._json import build_geojson
from MoosasPy.transform.io._xml import build_xml
from MoosasPy.transform.stages.glazing import attach_glazing_to_faces
from MoosasPy.transform.stages.splitting import split_wall_intersections
from MoosasPy.transform.stages.validation import validate_model
from MoosasPy.transform.geometry.spaceGen import CCRSpaceGeneration
from MoosasPy.utils import np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GEOMETRY_FIXTURE = PROJECT_ROOT / "test" / "caseFile" / "test8_topology.geo"
ENERGY_ENGINE = PROJECT_ROOT / "MoosasPy" / "libs" / "energy" / "MoosasEnergy.exe"
BEIJING_WEATHER = PROJECT_ROOT / "MoosasPy" / "db" / "weather" / "545110.csv"


class ExampleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.model = transform(
            str(GEOMETRY_FIXTURE),
            input_type="geo",
            stdout=StringIO(),
        )

    def test_geometry_fixture_transforms_to_expected_topology(self):
        self.assertGreaterEqual(len(self.model.geometryList), 450)
        self.assertEqual(len(self.model.spaceList), 70)
        self.assertEqual(len(self.model.voidList), 0)
        self.assertEqual(len(self.model.wallList), 249)
        self.assertEqual(len(self.model.faceList), 153)
        self.assertEqual(len(self.model.glazingList), 91)
        self.assertEqual(len(self.model.skylightList), 0)
        self.assertEqual(
            tuple(self.model.levelList),
            (0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0),
        )
        self.assertTrue(all(space.area > 0 for space in self.model.spaceList))
        self.assertAlmostEqual(sum(space.area for space in self.model.spaceList), 28199.6484, places=4)

        neighbor_pairs = {
            tuple(sorted((str(space.id), str(neighbor_id))))
            for space in self.model.spaceList
            for neighbor_id in space.neighbor
            if str(neighbor_id) != str(space.id)
        }
        self.assertEqual(len(neighbor_pairs), 122)
        self.assertTrue(all(space.neighbor for space in self.model.spaceList))

    def test_classification_stage_builds_elements_before_topology(self):
        model = _load_geometry_source(str(GEOMETRY_FIXTURE), "geo")
        classified_model = classify_model(model)

        self.assertIs(classified_model, model)
        self.assertEqual(len(model.faceList), 144)
        self.assertEqual(len(model.wallList), 193)
        self.assertEqual(len(model.glazingList), 91)
        self.assertEqual(len(model.skylightList), 0)
        self.assertEqual(tuple(model.levelList), (0.0, 4.5, 9.0, 13.5, 18.0, 22.5, 27.0, 31.5, 36.0, 40.5, 45.0))

    def test_file_and_model_entries_share_transform_options(self):
        options = TransformOptions()
        model = configure_model_resources(_load_geometry_source(str(GEOMETRY_FIXTURE), "geo"))
        with redirect_stdout(StringIO()):
            model = structured(model, options=options)

        self.assertEqual(len(model.spaceList), len(self.model.spaceList))
        self.assertEqual(len(model.wallList), len(self.model.wallList))
        self.assertAlmostEqual(
            sum(space.area for space in model.spaceList),
            sum(space.area for space in self.model.spaceList),
            places=4,
        )

    def test_generation_stage_builds_boundaries_before_assembly(self):
        model = _load_geometry_source(str(GEOMETRY_FIXTURE), "geo")
        with redirect_stdout(StringIO()):
            model = classify_model(model)
            model.faceList = np.array(model.faceList)
            model.wallList = np.array(model.wallList)
            model.glazingList = np.array(model.glazingList)
            model, _ = cleanse_model(
                model,
                solve_duplicated=True,
                solve_redundant=True,
                solve_overlap=True,
                match_glazing=attach_glazing_to_faces,
            )
            model = split_wall_intersections(model, enabled=True)
            model = generate_space_boundaries(model, CCRSpaceGeneration)

        self.assertEqual(len(model.boundaryList), 82)
        self.assertEqual(len(model.edgeList), 0)
        self.assertEqual(len(model.spaceList), 0)

    def test_validation_rejects_an_unknown_neighbor(self):
        self.model.spaceList[0].neighbor["missing-space"] = []

        with self.assertRaisesRegex(ValueError, "unknown neighbor"):
            validate_model(self.model)

    def test_xml_serialization_is_owned_by_the_io_boundary(self):
        root = build_xml(self.model)

        self.assertFalse(hasattr(self.model, "buildXml"))
        self.assertEqual(root.tag, "model")
        self.assertEqual(len(root.findall("space")), len(self.model.spaceList))
        self.assertEqual(root.findtext("level"), " ".join(str(level) for level in self.model.levelList))

    def test_geojson_serialization_is_owned_by_the_io_boundary(self):
        geojson = build_geojson(self.model)
        first_geometry_id = geojson["features"][0]["properties"]["id"]

        self.assertFalse(hasattr(self.model, "buildGeojson"))
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 443)
        self.assertEqual(len(build_geojson(self.model, [first_geometry_id])["features"]), 1)

    @unittest.skipUnless(
        ENERGY_ENGINE.is_file() and BEIJING_WEATHER.is_file(),
        "requires the bundled MoosasEnergy engine and Beijing 545110 weather data",
    )
    def test_energy_engine_returns_real_results_for_geometry_fixture(self):
        load_weather(self.model, "545110")

        with TemporaryDirectory() as work_dir:
            result = EnergyRunner(
                model=self.model,
                work_dir=work_dir,
                timeout_seconds=60,
            ).run()

        self.assertEqual(result.commands[0].returncode, 0)
        self.assertEqual(len(result.data["spaces"]), 70)
        self.assertEqual(len(result.data["months"]), 12)

        total = result.data["total"]
        component_total = 0.0
        for key in ("cooling", "heating", "lighting"):
            value = float(total[key])
            self.assertTrue(math.isfinite(value))
            self.assertGreaterEqual(value, 0.0)
            component_total += value
        self.assertGreater(component_total, 0.0)
        self.assertAlmostEqual(float(total["cooling"]), 3.54, places=2)
        self.assertAlmostEqual(float(total["heating"]), 11.59, places=2)
        self.assertAlmostEqual(float(total["lighting"]), 2.63, places=2)
        self.assertAlmostEqual(float(total["total"]), 17.76, places=2)
        self.assertAlmostEqual(float(total["total"]), component_total, places=6)


if __name__ == "__main__":
    unittest.main()