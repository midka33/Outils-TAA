# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB_DIR = os.path.join(ROOT, "OutilsTAA.extension", "lib")
PANEL_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Calculs.panel",
)
SERVICE_DIR = os.path.join(PANEL_DIR, "services")

for path in (LIB_DIR, PANEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from calculation.parameter_descriptor import RoomParameterDescriptor
from room_unit_service import RoomUnitService


class FakeForgeTypeId(object):
    def __init__(self, type_id):
        self.TypeId = type_id


class FakeUnitUtils(object):
    @staticmethod
    def IsMeasurableSpec(spec_id):
        return spec_id.TypeId == "spec:area"

    @staticmethod
    def GetValidUnits(spec_id):
        return [
            FakeForgeTypeId("unit:square-feet"),
            FakeForgeTypeId("unit:square-meters"),
        ]


class FakeLabelUtils(object):
    LABELS = {
        "unit:square-feet": "Pieds carrés",
        "unit:square-meters": "Mètres carrés",
    }

    @staticmethod
    def GetLabelForUnit(unit_id):
        return FakeLabelUtils.LABELS[unit_id.TypeId]


class UnitOptionsTests(unittest.TestCase):

    def setUp(self):
        self.service = RoomUnitService(
            unit_utils=FakeUnitUtils,
            forge_type_factory=FakeForgeTypeId,
            label_utils=FakeLabelUtils,
        )

    def test_numeric_non_double_only_has_automatic(self):
        source = RoomParameterDescriptor(
            "Nombre", "NAME", "Nombre", "Integer", data_type_id=None
        )

        options = self.service.get_unit_options(source)

        self.assertEqual(1, len(options))
        self.assertTrue(options[0].is_automatic)

    def test_measurable_double_lists_valid_units_after_automatic(self):
        source = RoomParameterDescriptor(
            "Surface", "NAME", "Surface", "Double", data_type_id="spec:area"
        )

        options = self.service.get_unit_options(source)

        self.assertEqual("Automatique", options[0].label)
        self.assertEqual(
            ["Mètres carrés", "Pieds carrés"],
            [option.label for option in options[1:]],
        )
        self.assertEqual(
            ["unit:square-meters", "unit:square-feet"],
            [option.type_id for option in options[1:]],
        )

    def test_non_measurable_double_only_has_automatic(self):
        source = RoomParameterDescriptor(
            "Ratio", "NAME", "Ratio", "Double", data_type_id="spec:not-measurable"
        )

        options = self.service.get_unit_options(source)

        self.assertEqual(1, len(options))


if __name__ == "__main__":
    unittest.main()
