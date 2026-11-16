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

from calculation_diagnostics import group_conflicts
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

    def test_uniform_mode_rejects_unapproved_value(self):
        self.prepared.group_mode = "uniform"
        self.prepared.uniform_values = {42: 999.0}
        with self.assertRaises(ValidationError):
            self.workflow.execute(self.prepared)
        self.assertFalse(self.transactions)


if __name__ == "__main__":
    unittest.main()
