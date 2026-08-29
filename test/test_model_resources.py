import unittest

from MoosasPy.model_resources import configure_model_resources
from MoosasPy.models import MoosasModel


class ModelResourceBoundaryTests(unittest.TestCase):
    def test_model_initialization_does_not_load_external_resources(self):
        model = MoosasModel()

        self.assertEqual(model.buildingTemplate, {})
        self.assertEqual(model.schedule, {})
        self.assertFalse(hasattr(model, "weather"))
        self.assertFalse(hasattr(model, "cumSky"))
        self.assertFalse(hasattr(model, "idfZoneTemplate"))
        self.assertFalse(hasattr(model, "loadSchedule"))
        self.assertFalse(hasattr(model, "loadWeatherData"))

    def test_resource_service_configures_a_domain_model(self):
        model = configure_model_resources(MoosasModel())

        self.assertTrue(model.buildingTemplate)
        self.assertTrue(model.schedule)
        self.assertTrue(model.scheduleByType)


if __name__ == "__main__":
    unittest.main()
