# -*- coding: utf-8 -*-
"""Non-regression du passage des ElementId Revit dans _attach.

Ce test ne charge pas Revit. Il execute les seules affectations du code
de production liees aux identifiants, avec une API factice stricte.
"""
import ast
import os
import unittest


MODULE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "OutilsTAA.extension", "OutilsTAA.tab", "Annotations.panel",
    "services", "annotations_service.py",
)


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeGroup(object):
    def __init__(self, type_ids):
        self._type_ids = type_ids

    def GetAvailableAttachedDetailGroupTypeIds(self):
        return self._type_ids


class FakeDocument(object):
    def GetElement(self, element_id):
        if not isinstance(element_id, FakeElementId):
            raise TypeError("expected ElementId, got int")
        return element_id


def _production_id_assignments():
    with open(MODULE_PATH, "r", encoding="utf-8") as stream:
        tree = ast.parse(stream.read(), filename=MODULE_PATH)
    method = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "_attach":
            method = node
            break
    if method is None:
        raise AssertionError("_attach introuvable")
    names = ("available_type_ids", "available", "new_ids", "group_type_id")
    assignments = {}
    for node in ast.walk(method):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in names:
                    assignments[target.id] = node
    if set(assignments) != set(names):
        raise AssertionError("Affectations d'ElementId de _attach incompletes")
    return ast.Module(
        body=[assignments[name] for name in names],
        type_ignores=[],
    )


class AttachedGroupElementIdTests(unittest.TestCase):
    def test_native_elementid_is_preserved(self):
        old = FakeElementId(100)
        new = FakeElementId(200)
        variables = {
            "group": FakeGroup([old, new]),
            "previous": {100},
            "id_value": lambda item: int(item.Value),
        }
        program = ast.fix_missing_locations(_production_id_assignments())
        exec(compile(program, MODULE_PATH, "exec"), variables)
        self.assertEqual(variables["new_ids"], {200})
        selected = variables["group_type_id"]
        self.assertIs(selected, new)
        self.assertIs(FakeDocument().GetElement(selected), new)

    def test_no_bare_int_passed_to_getelement(self):
        with open(MODULE_PATH, "r", encoding="utf-8") as stream:
            code = stream.read()
        self.assertNotIn("GetElement(next(iter(new_ids)))", code)
        self.assertIn("available_type_ids[next(iter(new_ids))]", code)


if __name__ == "__main__":
    unittest.main()
