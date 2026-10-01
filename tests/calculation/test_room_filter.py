# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CALCULATION_DIR = os.path.join(ROOT, "OutilsTAA.extension", "lib", "calculation")
if CALCULATION_DIR not in sys.path:
    sys.path.insert(0, CALCULATION_DIR)

from room_filter import RoomFilter


class RoomFilterTests(unittest.TestCase):

    def setUp(self):
        self.filter = RoomFilter()
        self.rooms = [object(), object(), object()]

    def test_no_filter_returns_all_rooms(self):
        result = self.filter.apply(self.rooms)
        self.assertEqual(self.rooms, result)

    def test_blank_filter_value_does_not_filter(self):
        result = self.filter.apply(
            self.rooms,
            parameter_name="Zone",
            expected_value="  ",
            value_reader=lambda room, name: "A",
        )
        self.assertEqual(self.rooms, result)

    def test_filter_matches_exact_normalized_value(self):
        values = {
            id(self.rooms[0]): "A",
            id(self.rooms[1]): " B ",
            id(self.rooms[2]): "B",
        }

        result = self.filter.apply(
            self.rooms,
            parameter_name="Zone",
            expected_value="B",
            value_reader=lambda room, name: values[id(room)],
        )

        self.assertEqual([self.rooms[1], self.rooms[2]], result)

    def test_filter_requires_reader(self):
        with self.assertRaises(ValueError):
            self.filter.apply(self.rooms, "Zone", "A")


if __name__ == "__main__":
    unittest.main()
