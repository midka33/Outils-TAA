# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Tests unitaires du moteur métier Calculs des pièces."""

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "lib",
)

if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)

from calculation.models import RoomCalculationItem
from calculation.room_calculator import RoomCalculator


class RoomCalculatorTests(unittest.TestCase):

    def setUp(self):
        self.calculator = RoomCalculator()

    def test_sums_values_by_group(self):
        items = [
            RoomCalculationItem("r1", "A", 20.0),
            RoomCalculationItem("r2", "A", 15.0),
            RoomCalculationItem("r3", "B", 10.0),
        ]

        result = self.calculator.calculate(items)

        self.assertEqual(35.0, result.get_total("A"))
        self.assertEqual(10.0, result.get_total("B"))
        self.assertEqual(3, result.calculated_items)
        self.assertEqual(0, result.skipped_items)
        self.assertEqual(2, result.group_count)

    def test_empty_input_returns_empty_result(self):
        result = self.calculator.calculate([])

        self.assertEqual({}, result.totals)
        self.assertEqual(0, result.total_items)
        self.assertEqual(0, result.calculated_items)
        self.assertEqual(0, result.skipped_items)

    def test_skips_empty_group_and_non_numeric_source(self):
        items = [
            RoomCalculationItem("r1", "", 10.0),
            RoomCalculationItem("r2", None, 5.0),
            RoomCalculationItem("r3", "A", None),
            RoomCalculationItem("r4", "A", "12.0"),
        ]

        result = self.calculator.calculate(items)

        self.assertEqual({}, result.totals)
        self.assertEqual(0, result.calculated_items)
        self.assertEqual(4, result.skipped_items)
        self.assertEqual(
            [
                RoomCalculator.REASON_EMPTY_GROUP,
                RoomCalculator.REASON_EMPTY_GROUP,
                RoomCalculator.REASON_NON_NUMERIC_SOURCE,
                RoomCalculator.REASON_NON_NUMERIC_SOURCE,
            ],
            [item.reason for item in result.skipped],
        )

    def test_room_with_invalid_source_still_belongs_to_valid_group(self):
        items = [
            RoomCalculationItem("r1", "A", 10.0),
            RoomCalculationItem("r2", "A", None),
        ]

        result = self.calculator.calculate(items)

        self.assertEqual(10.0, result.get_total("A"))
        self.assertEqual(["r1", "r2"], result.get_members("A"))
        self.assertEqual(1, result.skipped_items)

    def test_zero_group_and_zero_value_are_valid(self):
        items = [
            RoomCalculationItem("r1", 0, 0),
            RoomCalculationItem("r2", 0, 5),
        ]

        result = self.calculator.calculate(items)

        self.assertEqual(5, result.get_total(0))
        self.assertEqual(2, result.calculated_items)

    def test_progress_is_reported_for_every_input_item(self):
        calls = []
        items = [
            RoomCalculationItem("r1", "A", 1),
            RoomCalculationItem("r2", "A", 2),
        ]

        self.calculator.calculate(
            items,
            progress=lambda current, total: calls.append((current, total)),
        )

        self.assertEqual([(1, 2), (2, 2)], calls)

    def test_totals_property_returns_a_copy(self):
        result = self.calculator.calculate([
            RoomCalculationItem("r1", "A", 3),
        ])

        exposed = result.totals
        exposed["A"] = 999

        self.assertEqual(3, result.get_total("A"))


if __name__ == "__main__":
    unittest.main()
