# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PANEL = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Calculs.panel")
SERVICES = os.path.join(PANEL, "services")
LIB = os.path.join(ROOT, "OutilsTAA.extension", "lib")
for folder in (SERVICES, LIB, os.path.dirname(__file__)):
    if folder not in sys.path:
        sys.path.insert(0, folder)

from calculation_diagnostics import group_conflicts, design_option_summary
from test_grouped_parameters import (
    GroupedWorkflowTests, FakeElementId
)
from common.exceptions import ValidationError


class FakeGroupType(object):
    def __init__(self, type_id):
        self.Id = FakeElementId(type_id)
        self.Name = "TYPE-LOGEMENT"


class FakeGroup(object):
    def __init__(self, instance_id, group_type):
        self.Id = FakeElementId(instance_id)
        self.Name = "A{}".format(instance_id)
        self.GroupType = group_type


class FakeDocument(object):
    def __init__(self):
        group_type = FakeGroupType(42)
        self.groups = {
            10: FakeGroup(10, group_type),
            20: FakeGroup(20, group_type),
        }

    def GetElement(self, element_id):
        return self.groups.get(element_id.Value)


class GroupConflictDecisionTests(unittest.TestCase):
    def setUp(self):
        fixture = GroupedWorkflowTests()
        rooms, self.definition, self.target1, self.target2 = fixture._rooms()
        rooms[1].GroupId = FakeElementId(20)
        rooms[1].LookupParameter("Appartement").value = "B"
        self.workflow, self.parameter_service, self.transactions = fixture._build(rooms)
        self.document = FakeDocument()
        self.workflow.document = self.document
        self.workflow.grouped_parameter_service.document = self.document
        self.request = fixture._request(self.parameter_service, rooms)
        self.prepared = self.workflow.prepare(self.request)

    def test_conflict_identified_by_group_type_not_group_instance(self):
        self.assertEqual(1, len(self.prepared.group_conflicts))
        item = self.prepared.group_conflicts[0]
        self.assertEqual(42, item["type_key"])
        self.assertEqual({10.0, 5.0},
                         set(candidate["value"] for candidate in item["candidates"]))

    def test_no_implicit_writing_when_conflict_awaits_user(self):
        with self.assertRaises(ValidationError):
            self.workflow.execute(self.prepared)
        self.assertFalse(self.transactions)

    def test_user_can_keep_distinct_values_and_parameter_setting(self):
        self.prepared.group_mode = "vary"
        report = self.workflow.execute(self.prepared)
        self.assertTrue(report.is_success)
        self.assertEqual(10.0, self.target1.value)
        self.assertEqual(5.0, self.target2.value)
        self.assertTrue(self.definition.VariesAcrossGroups)
        self.assertEqual([True], self.definition.calls)

    def test_user_can_keep_alignment_using_selected_reference_value(self):
        item = self.prepared.group_conflicts[0]
        self.prepared.group_mode = "uniform"
        self.prepared.uniform_values = {42: 10.0}
        report = self.workflow.execute(self.prepared)
        self.assertTrue(report.is_success)
        self.assertEqual(10.0, self.target1.value)
        self.assertEqual(10.0, self.target2.value)
        self.assertFalse(self.definition.VariesAcrossGroups)
        self.assertEqual([True, False], self.definition.calls)

    def test_uniform_forbidden_if_one_instance_contains_distinct_apartments(self):
        self.prepared.room_by_key["r2"].GroupId = FakeElementId(10)
        self.prepared.group_conflicts = group_conflicts(
            self.document, self.prepared.room_by_key, self.prepared.operations
        )
        self.assertFalse(self.prepared.group_conflicts[0]["uniform_safe"])
        self.prepared.group_mode = "uniform"
        self.prepared.uniform_values = {42: 10.0}
        with self.assertRaises(ValidationError):
            self.workflow.execute(self.prepared)

    def test_same_apartment_number_is_independent_in_two_design_options(self):
        from calculation_diagnostics import variant_group_key
        class Option(object):
            def __init__(self, oid, primary):
                self.Id = FakeElementId(oid)
                self.IsPrimary = primary

        class Room(object):
            def __init__(self, option):
                self.DesignOption = option

        primary = Room(Option(101, True))
        secondary_a = Room(Option(102, False))
        secondary_b = Room(Option(103, False))
        main_model = Room(None)

        self.assertEqual("B200", variant_group_key(primary, "B200"))
        self.assertEqual("B200", variant_group_key(main_model, "B200"))
        a_key = variant_group_key(secondary_a, "B200")
        b_key = variant_group_key(secondary_b, "B200")
        self.assertNotEqual("B200", a_key)
        self.assertNotEqual("B200", b_key)
        self.assertNotEqual(a_key, b_key)

        from calculation.room_calculator import RoomCalculator
        from calculation.models import RoomCalculationItem
        result = RoomCalculator().calculate([
            RoomCalculationItem("r0", variant_group_key(primary, "B200"), 20.0),
            RoomCalculationItem("r1", variant_group_key(secondary_a, "B200"), 30.0),
            RoomCalculationItem("r2", variant_group_key(secondary_b, "B200"), 40.0),
            RoomCalculationItem("r3", variant_group_key(main_model, "B200"), 5.0),
        ])
        self.assertEqual(3, result.group_count)
        self.assertEqual(25.0, result.get_total("B200"))
        self.assertEqual(30.0, result.get_total(a_key))
        self.assertEqual(40.0, result.get_total(b_key))

    def test_empty_group_still_skipped_in_secondary_option(self):
        from calculation_diagnostics import variant_group_key
        class Option(object):
            Id = FakeElementId(102)
            IsPrimary = False
        class Room(object):
            DesignOption = Option()
        self.assertEqual("", variant_group_key(Room(), ""))
        self.assertIsNone(variant_group_key(Room(), None))

    def test_variant_summary_counts_main_primary_and_secondary_rooms(self):
        import types
        class FakeOption(object):
            def __init__(self, oid, name, primary):
                self.Id = FakeElementId(oid)
                self.Name = name
                self.IsPrimary = primary

        class FakeOptionsCollector(object):
            def __init__(self, document):
                self.document = document

            def OfClass(self, _klass):
                return self

            def ToElements(self):
                return self.document.options

        option_a = FakeOption(1, "Variante A", True)
        option_b = FakeOption(2, "Variante B", False)
        self.document.options = [option_a, option_b]
        rooms = [types.SimpleNamespace(DesignOption=None),
                 types.SimpleNamespace(DesignOption=option_a),
                 types.SimpleNamespace(DesignOption=option_b)]
        original = {}
        names = ("Autodesk", "Autodesk.Revit", "Autodesk.Revit.DB")
        for name in names:
            original[name] = sys.modules.get(name)
            sys.modules[name] = types.ModuleType(name)
        module = sys.modules["Autodesk.Revit.DB"]
        module.FilteredElementCollector = FakeOptionsCollector
        module.DesignOption = FakeOption
        try:
            report = design_option_summary(self.document, rooms)
        finally:
            for name in names:
                if original[name] is None:
                    del sys.modules[name]
                else:
                    sys.modules[name] = original[name]
        self.assertTrue(any("Variante A (principale) : 1" in line for line in report))
        self.assertTrue(any("Variante B (secondaire) : 1" in line for line in report))
        self.assertTrue(any("Modele principal : 1" in line for line in report))

    def test_uniform_mode_rejects_unapproved_value(self):
        self.prepared.group_mode = "uniform"
        self.prepared.uniform_values = {42: 999.0}
        with self.assertRaises(ValidationError):
            self.workflow.execute(self.prepared)
        self.assertFalse(self.transactions)


if __name__ == "__main__":
    unittest.main()
