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

from common.unit_utils import (
    convert_from_internal_units,
    convert_to_internal_units,
    data_type_ids_are_compatible,
)
from room_unit_service import RoomUnitService


class FakeUnitUtils(object):

    @staticmethod
    def ConvertFromInternalUnits(value, unit_type_id):
        return value * unit_type_id.factor

    @staticmethod
    def ConvertToInternalUnits(value, unit_type_id):
        return value / unit_type_id.factor


class FakeUnitTypeId(object):
    def __init__(self, factor):
        self.factor = factor


class FakeParameter(object):
    def __init__(self, unit_type_id=None):
        self._unit_type_id = unit_type_id

    def GetUnitTypeId(self):
        if self._unit_type_id is None:
            raise RuntimeError("not measurable")
        return self._unit_type_id


class UnitUtilsTests(unittest.TestCase):

    def test_convert_from_internal_uses_explicit_unit_api(self):
        unit_id = FakeUnitTypeId(2.0)

        value = convert_from_internal_units(
            3.0,
            unit_id,
            unit_utils=FakeUnitUtils,
        )

        self.assertEqual(6.0, value)

    def test_convert_to_internal_uses_explicit_unit_api(self):
        unit_id = FakeUnitTypeId(2.0)

        value = convert_to_internal_units(
            6.0,
            unit_id,
            unit_utils=FakeUnitUtils,
        )

        self.assertEqual(3.0, value)

    def test_missing_unit_id_is_rejected(self):
        with self.assertRaises(ValueError):
            convert_to_internal_units(1.0, None, unit_utils=FakeUnitUtils)

    def test_data_type_compatibility(self):
        self.assertTrue(data_type_ids_are_compatible("area", "area"))
        self.assertFalse(data_type_ids_are_compatible("area", "volume"))
        self.assertTrue(data_type_ids_are_compatible(None, "area"))


class RoomUnitServiceTests(unittest.TestCase):

    def setUp(self):
        self.service = RoomUnitService(unit_utils=FakeUnitUtils)

    def test_uses_parameter_unit_when_no_unit_is_explicit(self):
        parameter = FakeParameter(FakeUnitTypeId(10.0))

        self.assertEqual(20.0, self.service.from_internal(2.0, parameter=parameter))
        self.assertEqual(2.0, self.service.to_internal(20.0, parameter=parameter))

    def test_non_measurable_parameter_is_rejected(self):
        parameter = FakeParameter(None)

        with self.assertRaises(ValueError):
            self.service.from_internal(2.0, parameter=parameter)


if __name__ == "__main__":
    unittest.main()
