# -*- coding: utf-8 -*-
"""Regressions hors Revit du mode cotation beta dans un groupe de modele.

Execution : python -m unittest discover -s tests -p test_annotations_group_dimensions_beta.py
Ne constitue pas une validation de l'API Revit ou des references natives.
"""
import ast
import os
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERV = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab",
                    "Annotations.panel", "services", "annotations_service.py")
LAUNCH = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab",
                      "Annotations.panel", "services", "launcher.py")


def read(path):
    with open(path, encoding="utf-8") as stream:
        return stream.read()


def method_source_ast(name):
    tree = ast.parse(read(SERV), filename=SERV)
    matches = [node for node in ast.walk(tree)
               if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise AssertionError("Methode {} introuvable/ambigue".format(name))
    return matches[0]


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeReference(object):
    def __init__(self, element_id):
        self.ElementId = element_id


class FakeDimension(object):
    def __init__(self, dimension_id, reference_ids):
        self.Id = FakeElementId(dimension_id)
        self.References = (None if reference_ids is None else [
            FakeReference(FakeElementId(item)) for item in reference_ids
        ])


class FakeDoc(object):
    def __init__(self):
        self.deleted = []

    def Delete(self, element_id):
        self.deleted.append(element_id.Value)


class FakeTransaction(object):
    def __init__(self, document, label):
        self.document = document

    def Start(self):
        pass

    def Commit(self):
        pass

    def RollBack(self):
        pass


class FakeService(object):
    def __init__(self, dimensions):
        self.doc = FakeDoc()
        self.dimensions = dimensions

    def _elements(self, view, kind):
        if kind != "dims":
            raise AssertionError("Type inattendu")
        return self.dimensions


def load_cleanup_method():
    method = method_source_ast("_cleanup_unused_group_proxies")
    namespace = {
        "DB": types.SimpleNamespace(Transaction=FakeTransaction),
        "id_value": lambda item: item.Value,
    }
    tree = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
    exec(compile(tree, SERV, "exec"), namespace)
    return namespace[method.name]


class GroupDimensionsBetaTests(unittest.TestCase):
    def test_python_syntax_of_modified_modules(self):
        ast.parse(read(SERV), filename=SERV)
        ast.parse(read(LAUNCH), filename=LAUNCH)

    def test_one_group_is_explicit_and_safe(self):
        launcher = read(LAUNCH)
        service = read(SERV)
        self.assertIn('("group", "Un groupe de modele', launcher)
        self.assertIn('diagnostic_group_uid=diagnostic_group_uid', launcher)
        self.assertIn('group_mode = kind == "dims" and diagnostic_group_uid is not None',
                      service)
        self.assertIn('str(group.UniqueId) == str(diagnostic_group_uid)', service)
        self.assertIn('if not candidates or len(candidates) > 12:', service)
        self.assertIn('if len(views) != 1:', service)
        self.assertIn('if any(room.GroupId != DB.ElementId.InvalidElementId',
                      service)

    def test_attached_members_and_per_room_cache_protected(self):
        service = read(SERV)
        self.assertIn('_group_length_fallback_state[key] =', service)
        self.assertIn('state = getattr(self, "_group_length_fallback_state"', service)
        self.assertIn('list(annotation_ids) + list(proxy_ids)', service)
        self.assertIn('group.GetMemberIds()) != original_members', service)
        self.assertIn('id_value(item.AttachedParentId) == parent_group_id',
                      service)
        self.assertIn('tx.RollBack()', service)

    def test_unused_group_proxies_are_deleted(self):
        method = load_cleanup_method()
        service = FakeService([FakeDimension(300, [12, 700])])
        keep = method(service, object(), [FakeElementId(11), FakeElementId(12)],
                      {300})
        self.assertEqual([item.Value for item in keep], [12])
        self.assertEqual(service.doc.deleted, [11])

    def test_missing_dimension_rejects_group_proxies(self):
        method = load_cleanup_method()
        service = FakeService([])
        with self.assertRaises(RuntimeError):
            method(service, object(), [FakeElementId(11)], set())
        self.assertEqual(service.doc.deleted, [])

    def test_unreadable_references_fail_closed(self):
        method = load_cleanup_method()
        service = FakeService([FakeDimension(300, None)])
        with self.assertRaises(RuntimeError):
            method(service, object(), [FakeElementId(11)], {300})
        self.assertEqual(service.doc.deleted, [])

    def test_no_proxies_are_noop(self):
        self.assertEqual(load_cleanup_method()(FakeService([]), object(), [], set()), [])


if __name__ == "__main__":
    unittest.main()
