"""Tests unitaires de l'orchestrateur de publication Export."""

import os
import sys
import tempfile
import unittest

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

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_service import PublicationService


class FakeView(object):
    """Vue Revit minimale utilisée pour la validation."""

    def __init__(self, printable=True):
        self.CanBePrinted = printable


class FakeDocument(object):
    """Document Revit minimal utilisé sans charger Revit."""

    def __init__(self, views=None):
        self.views = views or {}

    def GetElement(self, element_id):
        return self.views.get(element_id)


class FakePdfService(object):
    """Simule le service PDF pour tester l'orchestrateur."""

    def export(self, *args, **kwargs):
        return True


class FakeDwgService(object):
    """Simule le service DWG pour tester l'orchestrateur."""

    def export(self, *args, **kwargs):
        return True


class PublicationServiceTests(unittest.TestCase):

    def setUp(self):
        self.document = FakeDocument({1: FakeView(), 2: FakeView()})
        self.service = PublicationService(self.document)
        self.service.pdf_service = FakePdfService()
        self.service.dwg_service = FakeDwgService()
        self.items = [
            PublicationItem("u2", 2, "SHEET", "A102", "Plan R+1", "DCE"),
            PublicationItem("u1", 1, "SHEET", "A101", "Plan RDC", "DCE"),
        ]

    def test_validation_accepte_un_carnet_exportable(self):
        carnet = PublicationSet("DCE", self.items)

        errors = self.service.validate_publication_set(carnet)

        self.assertEqual([], errors)

    def test_validation_refuse_une_feuille_non_imprimable(self):
        self.document.views[2] = FakeView(False)
        carnet = PublicationSet("DCE", self.items)

        errors = self.service.validate_publication_set(carnet)

        self.assertEqual(1, len(errors))
        self.assertIn("A102", errors[0])

    def test_sort_items_respecte_le_numero_de_feuille(self):
        carnet = PublicationSet("DCE", self.items)

        sorted_items = self.service.sort_items(carnet)

        self.assertEqual(["A101", "A102"],
                         [item.sheet_number for item in sorted_items])

    def test_publish_exécute_pdf_et_dwg(self):
        carnet = PublicationSet("DCE", self.items)
        output = tempfile.mkdtemp()

        result = self.service.publish(
            carnet,
            output,
            export_pdf=True,
            export_dwg=True,
            pdf_combined=True,
            dwg_combined=True
        )

        self.assertTrue(result["success"])
        self.assertEqual(2, len(result["results"]))
        self.assertEqual("combined", result["results"][0]["mode"])
        self.assertEqual("combined", result["results"][1]["mode"])


if __name__ == "__main__":
    unittest.main()
