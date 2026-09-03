"""Tests unitaires de résolution des carnets persistants."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_DIR = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel")
MODEL_DIR = os.path.join(EXPORT_DIR, "models")
SERVICE_DIR = os.path.join(EXPORT_DIR, "services")
for path in (MODEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from carnet_service import CarnetService
from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource


class FakeId(object):
    def __init__(self, value):
        self.IntegerValue = value


class FakeSheet(object):
    def __init__(self, unique_id, sheet_id, number, name):
        self.UniqueId = unique_id
        self.Id = FakeId(sheet_id)
        self.SheetNumber = number
        self.Name = name


class FakeExportService(object):
    def get_publication_items(self, parameter_name=None, parameter_value=None):
        return []

    def get_sheets(self):
        return []


class CarnetResolutionTests(unittest.TestCase):
    def test_resolve_by_unique_id_and_report_missing(self):
        carnet = PublicationSet(
            "DCE",
            [
                PublicationItem("u1", 99, "SHEET", "OLD", "Ancien nom", "DCE"),
                PublicationItem("u_missing", 98, "SHEET", "A999", "Supprimée", "DCE"),
            ],
            PublicationSource(PublicationSource.MANUAL),
            set_id="carnet-1",
            persistent=True
        )
        sheets = [FakeSheet("u1", 12, "A101", "Plan RDC")]

        service = CarnetService(FakeExportService())
        resolution = service.resolve_persistent_carnet(carnet, sheets)

        self.assertEqual(1, resolution.resolved_count)
        self.assertEqual(1, resolution.missing_count)
        self.assertFalse(resolution.is_complete)
        self.assertEqual("A101", resolution.items[0].sheet_number)
        self.assertEqual("u_missing", resolution.missing_items[0].unique_id)


if __name__ == "__main__":
    unittest.main()
