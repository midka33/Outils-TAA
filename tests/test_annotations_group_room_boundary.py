# -*- coding: utf-8 -*-
"""Regression : la cote de groupe ne doit JAMAIS mesurer deux pieces.

Pure Python 3, sans Revit :
python -m unittest discover -s tests -p test_annotations_group_room_boundary.py
"""
import ast
import math
import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "OutilsTAA.extension", "lib")
SOURCE = os.path.join(
    ROOT, "OutilsTAA.extension", "OutilsTAA.tab",
    "Annotations.panel", "services", "annotations_service.py")
if LIB not in sys.path:
    sys.path.insert(0, LIB)

from annotations.group_length_axes import (
    room_boundary_end_markers, local_boundary_value_matches)


class MarkerGeometryTests(unittest.TestCase):
    def test_boundary_segment_not_full_wall(self):
        # Un meme mur physique mesure 7.20 m, mais borde deux pieces.
        # La limite de la premiere piece est limitee a 4.30 m.
        room_segment = (0.0, 0.0, 4.30, 0.0)
        first, second, expected = room_boundary_end_markers(
            room_segment, 0.0025)
        self.assertAlmostEqual(expected, 4.30)
        self.assertAlmostEqual((first[0] + first[2]) / 2., 0.)
        self.assertAlmostEqual((second[0] + second[2]) / 2., 4.30)
        self.assertTrue(local_boundary_value_matches(4.30, expected, 0.005))
        self.assertFalse(local_boundary_value_matches(7.20, expected, 0.005))

    def test_slanted_room_markers_perpendicular_to_boundary(self):
        first, second, expected = room_boundary_end_markers(
            (1.0, 2.0, 4.0, 6.0), 0.005)
        self.assertAlmostEqual(expected, 5.)
        for marker in (first, second):
            vx = marker[2] - marker[0]
            vy = marker[3] - marker[1]
            self.assertAlmostEqual(vx * 3. + vy * 4., 0., places=9)

    def test_zero_length_rejected(self):
        with self.assertRaises(ValueError):
            room_boundary_end_markers((1., 2., 1., 2.), 0.0025)

    def test_invalid_value_and_tolerance(self):
        self.assertFalse(local_boundary_value_matches(None, 4.3, .005))
        self.assertFalse(local_boundary_value_matches(float("nan"), 4.3, .005))
        self.assertFalse(local_boundary_value_matches(4.31, 4.3, .005))
        self.assertTrue(local_boundary_value_matches(4.303, 4.3, .005))


class FakeElementId(object):
    def __init__(self, number):
        self.Value = number


class FakeReference(object):
    def __init__(self, number):
        self.ElementId = FakeElementId(number)


class FakeRoom(object):
    def __init__(self, inside=True):
        self.inside = inside

    def IsPointInRoom(self, point):
        return self.inside


class FakeDimension(object):
    def __init__(self, value, references):
        self.Id = FakeElementId(300)
        self.Value = value
        self.References = [FakeReference(x) for x in references]
        self.Origin = types.SimpleNamespace(X=2., Y=2.)


class FakeService(object):
    def __init__(self, value, inside=True):
        self.room = FakeRoom(inside)
        self.dim = FakeDimension(value, (100, 101))
        self.dims = types.SimpleNamespace(
            _group_local_expected={
                frozenset((100, 101)): (4.30, self.room, "12")},
            _guardrail_warnings=[],
            _probe_z=lambda room: 1.0)

    def _elements(self, view, kind):
        return [self.dim]


def load_production_verifier():
    with open(SOURCE, encoding="utf-8") as f:
        content = f.read()
    tree = ast.parse(content, filename=SOURCE)
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef)
               and node.name == "_verify_group_local_dimensions"]
    if len(matches) != 1:
        raise AssertionError("Methode de verification introuvable")
    fake_db = types.SimpleNamespace(
        UnitTypeId=types.SimpleNamespace(Millimeters="mm"),
        UnitUtils=types.SimpleNamespace(
            ConvertToInternalUnits=lambda x, unit: x / 304.8),
        XYZ=lambda x, y, z: (x, y, z))
    script = ast.fix_missing_locations(ast.Module(
        body=[matches[0]], type_ignores=[]))
    namespace = {
        "DB": fake_db,
        "id_value": lambda x: x.Value,
    }
    # Le module de production est structure pour importer son controle pur.
    # Le runtime doit disposer de la bibliotheque annotations.
    exec(compile(script, SOURCE, "exec"), namespace)
    return namespace["_verify_group_local_dimensions"]


class ProductionValidationTests(unittest.TestCase):
    def test_local_value_accepted(self):
        s = FakeService(4.30)
        load_production_verifier()(s, object(), {300})
        self.assertIn("COTE LOCALE VERIFIEE", s.dims._guardrail_warnings[0])

    def test_full_wall_crossing_two_rooms_is_rejected(self):
        s = FakeService(7.20)
        with self.assertRaises(RuntimeError):
            load_production_verifier()(s, object(), {300})

    def test_dimension_origin_in_other_room_is_rejected(self):
        s = FakeService(4.30, inside=False)
        with self.assertRaises(RuntimeError):
            load_production_verifier()(s, object(), {300})

    def test_group_logic_never_uses_original_wall_endpoint_references(self):
        with open(SOURCE, encoding="utf-8") as f:
            code = f.read()
        self.assertIn("for c in candidates:\n                    c.length_references = None", code)
        self.assertIn("c.length_references = tuple(references)", code)
        self.assertIn("self._verify_group_local_dimensions(view, new_ids)", code)
        self.assertIn("scope.RollBack()", code)


if __name__ == "__main__":
    unittest.main()
