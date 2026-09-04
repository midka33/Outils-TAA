"""Tests unitaires du service de prévisualisation Export."""

import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_DIR = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel")
MODEL_DIR = os.path.join(EXPORT_DIR, "models")
SERVICE_DIR = os.path.join(EXPORT_DIR, "services")
for path in (MODEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_preview_service import PublicationPreviewService


class FakeId(object):
    def __init__(self, value):
        self.IntegerValue = value


class FakeView(object):
    def __init__(self, printable=True):
        self.CanBePrinted = printable


class FakeDocument(object):
    def __init__(self):
        self.views = {1: FakeView(), 2: FakeView()}

    def GetElement(self, element_id):
        value = element_id.IntegerValue if hasattr(element_id, "IntegerValue") else element_id
        return self.views.get(value)


class FakePublicationService(object):
    def __init__(self):
        self.document = FakeDocument()

    def sort_items(self, publication_set):
        return sorted(publication_set.items, key=lambda item: item.sheet_number)

    def _resolve_current_sheet_id(self, item):
        return FakeId(item.sheet_id)


class FakeFilenameService(object):
    def filename(self, template, publication_set, item=None, folder_name=None, extension=".pdf"):
        if item is None:
            return publication_set.name + extension, []
        return item.sheet_number + extension, []


class Settings(object):
    pdf_enabled = True
    pdf_mode = "SEPARATE"
    dwg_enabled = False
    dwg_mode = "SEPARATE"
    filename_template = "{numero}"
    output_directory = None


class PublicationPreviewServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = PublicationPreviewService(FakePublicationService(), FakeFilenameService())
        self.carnet = PublicationSet("DCE", [
            PublicationItem("u2", 2, "SHEET", "A102", "Plan R+1"),
            PublicationItem("u1", 1, "SHEET", "A101", "Plan RDC"),
        ])

    def test_preview_ne_lance_pas_d_export_et_liste_les_fichiers(self):
        settings = Settings()
        settings.output_directory = tempfile.mkdtemp()

        preview = self.service.build(self.carnet, settings)

        self.assertEqual(2, len(preview["rows"]))
        self.assertEqual("A101.pdf", preview["rows"][0].Filename)
        self.assertEqual("A102.pdf", preview["rows"][1].Filename)
        self.assertEqual([], preview["errors"])

    def test_preview_signale_une_feuille_non_imprimable(self):
        self.service.publication_service.document.views[2] = FakeView(False)
        settings = Settings()
        settings.output_directory = tempfile.mkdtemp()

        preview = self.service.build(self.carnet, settings)

        self.assertEqual(1, len(preview["rows"]))
        self.assertTrue(any("A102" in error for error in preview["errors"]))

    def test_preview_signale_un_fichier_deja_present(self):
        settings = Settings()
        settings.output_directory = tempfile.mkdtemp()
        with open(os.path.join(settings.output_directory, "A101.pdf"), "w") as stream:
            stream.write("existing")

        preview = self.service.build(self.carnet, settings)

        self.assertTrue(any("existe déjà" in warning for warning in preview["warnings"]))

    def test_preview_signale_destination_manquante(self):
        settings = Settings()
        settings.output_directory = None

        preview = self.service.build(self.carnet, settings)

        self.assertTrue(any("destination" in error for error in preview["errors"]))


if __name__ == "__main__":
    unittest.main()
