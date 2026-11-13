# -*- coding: utf-8 -*-
"""Selection de longueurs de secours pour pieces biaises groupees.

Test geometrique pur, sans API Revit.
Commande :
python -m unittest discover -s tests -p test_annotations_group_length_axes.py
"""
import math
import os
import sys
import unittest


LIB = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "OutilsTAA.extension", "lib",
)
if LIB not in sys.path:
    sys.path.insert(0, LIB)

from annotations.group_length_axes import select_group_length_fallbacks


def wall(length, degrees):
    angle = math.radians(degrees)
    return (0.0, 0.0,
            float(length) * math.cos(angle),
            float(length) * math.sin(angle))


class GroupFallbackAxesTests(unittest.TestCase):

    def test_trapezoid_chooses_length_and_width_not_two_long_walls(self):
        # Reproduction analogue au plan Niveau 1 :
        # deux grands murs quasi paralleles et une paroi oblique.
        segments = [wall(657, 0), wall(646, 18), wall(324, 75)]
        result = select_group_length_fallbacks(
            segments, [0, 1, 2], min_axis_angle_degrees=30)
        self.assertEqual(set(result), {0, 2})

    def test_bottom_room_does_not_duplicate_longitudinal_axis(self):
        segments = [wall(723, -10), wall(659, 0), wall(194, 70)]
        result = select_group_length_fallbacks(
            segments, [0, 1, 2], min_axis_angle_degrees=30)
        self.assertEqual(set(result), {0, 2})

    def test_all_parallel_returns_one_only(self):
        segments = [wall(750, 0), wall(650, 3), wall(550, 8)]
        self.assertEqual(select_group_length_fallbacks(
            segments, [0, 1, 2]), [0])

    def test_existing_face_to_face_axis_excludes_parallel_wall(self):
        segments = [wall(500, 0), wall(400, 80)]
        result = select_group_length_fallbacks(
            segments, [0, 1],
            existing_dimension_lines=[wall(250, 0)],
            max_results=2)
        self.assertEqual(result, [1])

    def test_only_native_eligible_indices_can_be_returned(self):
        segments = [wall(1000, 0), wall(500, 70), wall(350, -60)]
        result = select_group_length_fallbacks(
            segments, [1, 2], min_axis_angle_degrees=30)
        self.assertEqual(set(result), {1, 2})

    def test_no_valid_second_orientation_cannot_fake_two_dimensions(self):
        segments = [wall(250, 0), wall(200, 6)]
        self.assertEqual(select_group_length_fallbacks(
            segments, [0, 1], min_axis_angle_degrees=30), [0])

    def test_zero_length_or_no_references_rejected(self):
        segments = [(0, 0, 0, 0), wall(100, 90)]
        self.assertEqual(select_group_length_fallbacks(
            segments, [0, 1]), [1])
        self.assertEqual(select_group_length_fallbacks(
            segments, []), [])


if __name__ == "__main__":
    unittest.main()
