# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SERVICE_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Calculs.panel",
    "services",
)
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from room_collector_service import RoomCollectorService
from room_parameter_service import RoomParameterService


class FakeCollector(object):
    def __init__(self, document):
        self.document = document
        self.category = None
        self.non_types_only = False

    def OfCategory(self, category):
        self.category = category
        return self

    def WhereElementIsNotElementType(self):
        self.non_types_only = True
        return self

    def ToElements(self):
        return list(self.document.rooms)


class FakeDocument(object):
    def __init__(self, rooms):
        self.rooms = rooms
        self.ActiveView = object()


class FakeDefinition(object):
    def __init__(self, name):
        self.Name = name


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeParameter(object):
    def __init__(self, name, storage_type, value, read_only=False):
        self.Definition = FakeDefinition(name)
        self.StorageType = storage_type
        self.value = value
        self.IsReadOnly = read_only

    def AsString(self):
        return self.value

    def AsInteger(self):
        return self.value

    def AsDouble(self):
        return self.value

    def AsElementId(self):
        return FakeElementId(self.value)

    def AsValueString(self):
        return None if self.value is None else str(self.value)


class FakeRoom(object):
    def __init__(self, parameters, area=1.0):
        self.Parameters = parameters
        self.Area = area

    def LookupParameter(self, name):
        for parameter in self.Parameters:
            if parameter.Definition.Name == name:
                return parameter
        return None


class RoomCollectorServiceTests(unittest.TestCase):

    def test_collects_all_project_rooms_without_view_or_area_filter(self):
        placed = FakeRoom([], area=25.0)
        zero_area = FakeRoom([], area=0.0)
        document = FakeDocument([placed, zero_area])

        service = RoomCollectorService(
            document,
            collector_factory=FakeCollector,
            room_category="OST_Rooms",
        )

        result = service.collect_all_rooms()

        self.assertEqual([placed, zero_area], result)


class RoomParameterServiceTests(unittest.TestCase):

    def setUp(self):
        self.service = RoomParameterService()

    def test_parameter_names_are_unique_sorted_and_can_be_numeric_only(self):
        rooms = [
            FakeRoom([
                FakeParameter("Zone", "String", "A"),
                FakeParameter("Surface utile", "Double", 20.0),
            ]),
            FakeRoom([
                FakeParameter("zone", "String", "B"),
                FakeParameter("Nombre", "Integer", 2),
            ]),
        ]

        self.assertEqual(
            ["Nombre", "Surface utile", "Zone"],
            self.service.get_parameter_names(rooms),
        )
        self.assertEqual(
            ["Nombre", "Surface utile"],
            self.service.get_parameter_names(rooms, numeric_only=True),
        )

    def test_reads_supported_storage_types(self):
        room = FakeRoom([
            FakeParameter("Texte", "String", "ABC"),
            FakeParameter("Entier", "Integer", 3),
            FakeParameter("Double", "Double", 12.5),
            FakeParameter("Id", "ElementId", 42),
        ])

        self.assertEqual("ABC", self.service.read_value(room, "Texte"))
        self.assertEqual(3, self.service.read_value(room, "Entier"))
        self.assertEqual(12.5, self.service.read_value(room, "Double"))
        self.assertEqual(42, self.service.read_value(room, "Id"))
        self.assertIsNone(self.service.read_value(room, "Absent"))

    def test_writable_state_is_explicit(self):
        writable = FakeParameter("A", "Double", 1.0, read_only=False)
        read_only = FakeParameter("B", "Double", 1.0, read_only=True)

        self.assertTrue(self.service.is_writable(writable))
        self.assertFalse(self.service.is_writable(read_only))
        self.assertFalse(self.service.is_writable(None))


if __name__ == "__main__":
    unittest.main()
