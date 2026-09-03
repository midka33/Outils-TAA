"""Tests unitaires du moteur de création des carnets Export."""

import os
import tempfile
import unittest

import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Export.panel"
)
MODEL_DIR = os.path.join(EXPORT_DIR, "models")
SERVICE_DIR = os.path.join(EXPORT_DIR, "services")

for path in (MODEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from carnet_service import CarnetService
from carnet_repository import CarnetRepository
from publication_item import PublicationItem


class FakeExportService(object):
    """Fournit des éléments de test sans charger l'API Revit."""

    def __init__(self, items):
        self.items = items

    def get_publication_items(self, parameter_name=None, parameter_value=None):
        return self.items


class CarnetServiceTests(unittest.TestCase):

    def setUp(self):
        self.items = [
            PublicationItem("u3", 3, "SHEET", "A103", "Plan R+2", "DCE"),
            PublicationItem("u1", 1, "SHEET", "A101", "Plan RDC", "DCE"),
            PublicationItem("u2", 2, "SHEET", "A201", "Coupe", "PC"),
            PublicationItem("u4", 4, "SHEET", "A104", "Sans carnet", ""),
        ]
        self.service = CarnetService(FakeExportService(self.items))

    def test_create_from_parameter_groups_and_sorts(self):
        carnets = self.service.create_from_parameter("Sous-titre")

        self.assertEqual(2, len(carnets))
        self.assertEqual("DCE", carnets[0].name)
        self.assertEqual(["A101", "A103"], [i.sheet_number for i in carnets[0].items])
        self.assertEqual("PARAMETER", carnets[0].source.mode)
        self.assertEqual("Sous-titre", carnets[0].source.parameter_name)

    def test_create_manual_persistent(self):
        carnet = self.service.create_manual_persistent("DCE", self.items[:2])

        self.assertTrue(carnet.persistent)
        self.assertEqual("MANUAL", carnet.source.mode)
        self.assertTrue(carnet.id)
        self.assertEqual(2, len(carnet.items))

    def test_create_manual_temporary(self):
        carnet = self.service.create_manual_temporary("Sélection", self.items[:2])

        self.assertFalse(carnet.persistent)
        self.assertEqual("TEMPORARY", carnet.source.mode)

    def test_repository_round_trip(self):
        carnet = self.service.create_manual_persistent("DCE", self.items[:2])
        storage = os.path.join(tempfile.gettempdir(), "outils_taa_test_carnets.json")

        try:
            repository = CarnetRepository(storage)
            repository.save(carnet)
            loaded = repository.get(carnet.id)

            self.assertIsNotNone(loaded)
            self.assertEqual(carnet.name, loaded.name)
            self.assertEqual(2, len(loaded.items))
            self.assertEqual("u1", loaded.items[0].unique_id)
        finally:
            if os.path.exists(storage):
                os.remove(storage)


if __name__ == "__main__":
    unittest.main()
