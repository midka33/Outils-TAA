"""Tests unitaires de la découverte des paramètres Export."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXPORT_DIR = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel")
SERVICE_DIR = os.path.join(EXPORT_DIR, "services")
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from parameter_service import ParameterService


class FakeDefinition(object):
    def __init__(self, name):
        self.Name = name


class FakeParameter(object):
    def __init__(self, name):
        self.Definition = FakeDefinition(name)


class FakeSheet(object):
    def __init__(self, parameters):
        self.Parameters = parameters


class FakeParameterUtils(object):
    def __init__(self, values):
        self.values = values

    def get_parameter_value(self, sheet, parameter_name, default=None):
        return self.values.get((id(sheet), parameter_name), default)


class ParameterServiceTests(unittest.TestCase):
    def test_get_sheet_parameter_names_is_unique_and_sorted(self):
        sheets = [
            FakeSheet([FakeParameter("Sous-titre"), FakeParameter("Phase")]),
            FakeSheet([FakeParameter("phase"), FakeParameter("Nom de feuille")])
        ]

        service = ParameterService(FakeParameterUtils({}))
        names = service.get_sheet_parameter_names(sheets)

        self.assertEqual(["Nom de feuille", "Phase", "Sous-titre"], names)

    def test_get_parameter_summary_counts_values(self):
        sheet_a = FakeSheet([])
        sheet_b = FakeSheet([])
        sheet_c = FakeSheet([])
        values = {
            (id(sheet_a), "Sous-titre"): "DCE",
            (id(sheet_b), "Sous-titre"): "DCE",
            (id(sheet_c), "Sous-titre"): "PC",
        }

        service = ParameterService(FakeParameterUtils(values))
        summary = service.get_parameter_summary(
            [sheet_a, sheet_b, sheet_c],
            "Sous-titre"
        )

        self.assertEqual(
            [{"value": "DCE", "count": 2}, {"value": "PC", "count": 1}],
            summary
        )


if __name__ == "__main__":
    unittest.main()
