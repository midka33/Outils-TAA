# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PANEL = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Calculs.panel")
for folder in (os.path.join(PANEL, "services"),
               os.path.join(ROOT, "OutilsTAA.extension", "lib"),
               os.path.dirname(__file__)):
    if folder not in sys.path:
        sys.path.insert(0, folder)

from test_grouped_parameters import (
    FakeDefinition, FakeParameter, FakeRoom, FakeElementId,
    GroupedWorkflowTests,
)
from calculation_diagnostics import empty_result_explanation
from calculation.room_calculator import RoomCalculator
from calculation.models import RoomCalculationItem


class Type(object):
    def __init__(self):
        self.Id = FakeElementId(42)
        self.Name = "APPARTEMENT-TYPE"


class Group(object):
    def __init__(self, gid, group_type, member):
        self.Id = FakeElementId(gid)
        self.GroupType = group_type
        self.Name = "G{}".format(gid)
        self.members = [FakeElementId(member)]

    def GetMemberIds(self):
        return list(self.members)


class Document(object):
    def __init__(self, rooms):
        group_type = Type()
        self.groups = {10: Group(10, group_type, "r1"),
                       20: Group(20, group_type, "r2")}
        self.items = dict(self.groups)
        for room in rooms:
            self.items[room.UniqueId] = room

    def GetElement(self, element_id):
        return self.items.get(element_id.Value)


class UniformMemberTests(unittest.TestCase):
    def fixture(self, changed=None):
        definition = FakeDefinition(
            "Total", varies_across_groups=False,
            changed_on_restore=changed,
        )
        rooms = []
        targets = []
        for key, group_id, apartment in [
            ("r1", 10, "B200"), ("r2", 20, "B200")
        ]:
            target = FakeParameter(
                "Total", "Double", 0.0, definition=definition,
                locked_by_group=True,
            )
            room = FakeRoom(key, [
                FakeParameter("Appartement", "String", apartment),
                FakeParameter("Surface", "Double", 12.0),
                target,
            ], group_id=group_id)
            rooms.append(room)
            targets.append(target)

        # Seule r1 est dans le périmètre des sommes; r2 reste un membre
        # homologue du type de groupe à remettre en cohérence.
        fixture = GroupedWorkflowTests()
        workflow, service, transactions = fixture._build([rooms[0]])
        document = Document(rooms)
        workflow.document = document
        workflow.grouped_parameter_service.document = document
        request = fixture._request(service, [rooms[0]])
        request.group_mode = "uniform"
        return workflow, request, rooms, targets, definition, transactions

    def test_uniform_writes_corresponding_rooms_in_other_group_instances(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        prepared = workflow.prepare(request)
        self.assertEqual(1, len(prepared.uniform_extra_members))
        report = workflow.execute(prepared)
        self.assertTrue(report.is_success)
        self.assertEqual(2, report.success_count)
        self.assertEqual(12.0, targets[0].value)
        self.assertEqual(12.0, targets[1].value)
        self.assertFalse(definition.VariesAcrossGroups)
        self.assertEqual([True, False], definition.calls)
        self.assertTrue(transactions[0].committed)

    def test_auto_mode_can_be_switched_to_uniform_in_single_review(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        request.group_mode = "auto"
        prepared = workflow.prepare(request)
        self.assertEqual(1, len(prepared.uniform_extra_members))
        prepared.group_mode = "uniform"
        report = workflow.execute(prepared)
        self.assertTrue(report.is_success)
        self.assertEqual(12.0, targets[1].value)

    def test_explicit_uniform_changes_previously_varying_parameter_to_aligned(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        definition.VariesAcrossGroups = True
        report = workflow.execute(workflow.prepare(request))
        self.assertTrue(report.is_success)
        self.assertFalse(definition.VariesAcrossGroups)
        self.assertEqual([False], definition.calls)

    def test_explicit_vary_preserves_different_values_setting(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        request.group_mode = "vary"
        report = workflow.execute(workflow.prepare(request))
        self.assertTrue(report.is_success)
        self.assertTrue(definition.VariesAcrossGroups)
        self.assertEqual([True], definition.calls)

    def test_expected_revit_realignment_is_allowed_only_if_values_match(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture(
            changed=[FakeElementId("r2")]
        )
        prepared = workflow.prepare(request)
        report = workflow.execute(prepared)
        self.assertTrue(report.is_success)
        self.assertTrue(transactions[0].committed)

    def test_unplanned_revit_realignment_rolls_back(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture(
            changed=[FakeElementId("outside")]
        )
        report = workflow.execute(workflow.prepare(request))
        self.assertFalse(report.is_success)
        self.assertEqual(0, report.success_count)
        self.assertIn("hors du perimetre", report.transaction_error)
        self.assertTrue(transactions[0].rolled_back)

    def test_revit_overwriting_expected_member_rolls_back(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        original = definition.SetAllowVaryBetweenGroups

        def destructive(document, allow):
            result = original(document, allow)
            if not allow:
                targets[1].value = 77.0
                return [FakeElementId("r2")]
            return result

        definition.SetAllowVaryBetweenGroups = destructive
        report = workflow.execute(workflow.prepare(request))
        self.assertFalse(report.is_success)
        self.assertIn("Valeur commune non conservee", report.transaction_error)
        self.assertIn("type de groupe", report.transaction_error)
        self.assertIn("l'editeur de groupes Revit", report.transaction_error)
        self.assertTrue(transactions[0].rolled_back)

    def test_preflight_rejects_two_values_for_same_member_position(self):
        from group_member_alignment import validate_uniform_targets_by_member
        from calculation.workflow_models import WriteOperation
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        operations = [
            WriteOperation("r1", "B200", 380.286410009),
            WriteOperation("r2", "B200", 324.979623715),
        ]
        document = workflow.document
        with self.assertRaises(Exception) as caught:
            validate_uniform_targets_by_member(
                document, {"r1": rooms[0], "r2": rooms[1]}, operations,
            )
        self.assertIn("le même membre", str(caught.exception))
        self.assertIn("380.286410009", str(caught.exception))
        self.assertIn("324.979623715", str(caught.exception))
        self.assertEqual([], transactions)

    def test_preflight_accepts_matching_values_for_same_position(self):
        from group_member_alignment import validate_uniform_targets_by_member
        from calculation.workflow_models import WriteOperation
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        operations = [
            WriteOperation("r1", "B200", 380.286410009),
            WriteOperation("r2", "B200", 380.286410009),
        ]
        validate_uniform_targets_by_member(
            workflow.document,
            {"r1": rooms[0], "r2": rooms[1]},
            operations,
        )
        self.assertEqual([], transactions)

    def test_uniform_regenerates_before_realigning_the_definition(self):
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        document = workflow.document
        calls = []
        document.Regenerate = lambda: calls.append("regenerate")
        original = definition.SetAllowVaryBetweenGroups

        def track_alignment(doc, enabled):
            calls.append("vary" if enabled else "restore")
            return original(doc, enabled)

        definition.SetAllowVaryBetweenGroups = track_alignment
        report = workflow.execute(workflow.prepare(request))
        self.assertTrue(report.is_success)
        self.assertEqual(["vary", "regenerate", "restore"], calls)

    def test_regeneration_can_publish_all_writes_before_revit_realignment(self):
        # Double modelisant le cache des groupes Revit. Ce scenario est
        # une hypothese d'integration, pas une preuve du comportement Revit.
        workflow, request, rooms, targets, definition, transactions = self.fixture()
        document = workflow.document
        document.regenerated = False
        document.Regenerate = lambda: setattr(document, "regenerated", True)
        original = definition.SetAllowVaryBetweenGroups

        def cached_group_alignment(doc, enabled):
            changed = original(doc, enabled)
            if not enabled and not doc.regenerated:
                targets[1].value = 324.979623715
                return [FakeElementId("r2")]
            return changed

        definition.SetAllowVaryBetweenGroups = cached_group_alignment
        report = workflow.execute(workflow.prepare(request))
        self.assertTrue(report.is_success)
        self.assertTrue(document.regenerated)
        self.assertEqual(12.0, targets[1].value)

    def test_rollback_report_does_not_repeat_one_error_per_room(self):
        report_path = os.path.join(
            PANEL, "ui", "calculation_report_window.py"
        )
        with open(report_path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("if report.transaction_error:", source)
        self.assertIn("une seule transaction", source)

    def test_no_totals_is_not_confused_with_group_parameter_write_lock(self):
        class Descriptor(object):
            def __init__(self, name):
                self.name = name
        class Request(object):
            group_parameter = Descriptor("N° Appartement")
            source_parameter = Descriptor("Surface")
        class Prepared(object):
            request = Request()
            filtered_rooms = 2
            result = RoomCalculator().calculate([
                RoomCalculationItem("r1", "", 12.0),
                RoomCalculationItem("r2", "B200", None),
            ])
        message = empty_result_explanation(Prepared())
        self.assertIn("sans valeur", message)
        self.assertIn("valeur non numérique", message)
        self.assertIn("aucun paramètre n'a été modifié", message)


if __name__ == "__main__":
    unittest.main()
