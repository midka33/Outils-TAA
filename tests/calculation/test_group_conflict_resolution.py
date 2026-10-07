# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB_DIR = os.path.join(ROOT, "OutilsTAA.extension", "lib")
PANEL_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Calculs.panel",
)
SERVICE_DIR = os.path.join(PANEL_DIR, "services")

for path in (LIB_DIR, PANEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from calculation.group_alignment import GroupAlignmentResolution
from calculation.room_calculator import RoomCalculator
from calculation.room_filter import RoomFilter
from calculation.workflow_models import CalculationRequest
from grouped_parameter_service import GroupedParameterService
from room_calculation_workflow import RoomCalculationWorkflow
from room_parameter_service import RoomParameterService
from room_parameter_validator import RoomParameterValidator
from room_unit_service import RoomUnitService
from room_writer import RoomWriter


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeDefinition(object):
    def __init__(self, name):
        self.Name = name
        self.VariesAcrossGroups = False
        self.BuiltInParameter = -1
        self.calls = []

    def SetAllowVaryBetweenGroups(self, document, allow):
        self.calls.append(bool(allow))
        self.VariesAcrossGroups = bool(allow)
        return []


class FakeParameter(object):
    def __init__(
        self,
        name,
        storage_type,
        value=None,
        definition=None,
        locked_by_group=False,
    ):
        self.Definition = definition or FakeDefinition(name)
        self.StorageType = storage_type
        self.value = value
        self.locked_by_group = bool(locked_by_group)
        self.IsShared = False
        self.set_values = []

    @property
    def IsReadOnly(self):
        if self.locked_by_group:
            return not bool(self.Definition.VariesAcrossGroups)
        return False

    def AsString(self):
        return self.value

    def AsInteger(self):
        return self.value

    def AsDouble(self):
        return self.value

    def AsValueString(self):
        return None if self.value is None else str(self.value)

    def Set(self, value):
        if self.IsReadOnly:
            raise RuntimeError("readonly")
        self.value = value
        self.set_values.append(value)
        return True


class FakeRoom(object):
    def __init__(
        self,
        element_id,
        group_id,
        number,
        name,
        parameters,
    ):
        self.Id = FakeElementId(element_id)
        self.UniqueId = "room-{}".format(element_id)
        self.GroupId = FakeElementId(group_id)
        self.Number = number
        self.Name = name
        self.Parameters = list(parameters)

    def LookupParameter(self, name):
        values = self.GetParameters(name)
        return values[0] if values else None

    def GetParameters(self, name):
        return [
            parameter
            for parameter in self.Parameters
            if parameter.Definition.Name == name
        ]


class FakeGroupType(object):
    def __init__(self, element_id, name):
        self.Id = FakeElementId(element_id)
        self.Name = name
        self.Groups = []


class FakeGroup(object):
    def __init__(self, element_id, group_type, member_ids):
        self.Id = FakeElementId(element_id)
        self.GroupType = group_type
        self._member_ids = [
            FakeElementId(value)
            for value in member_ids
        ]

    def GetMemberIds(self):
        return list(self._member_ids)


class FakeDocument(object):
    def __init__(self):
        self._elements = {}

    def add(self, element):
        element_id = getattr(getattr(element, "Id", None), "Value", None)
        self._elements[element_id] = element

    def GetElement(self, element_id):
        value = getattr(element_id, "Value", element_id)
        return self._elements.get(value)


class FakeCollectorService(object):
    def __init__(self, rooms):
        self.rooms = list(rooms)

    def collect_all_rooms(self):
        return list(self.rooms)


class FakeTransaction(object):
    def __init__(self, document, name):
        self.document = document
        self.name = name
        self.started = False
        self.committed = False
        self.rolled_back = False

    def Start(self):
        self.started = True

    def Commit(self):
        self.committed = True

    def RollBack(self):
        self.rolled_back = True


class GroupConflictResolutionTests(unittest.TestCase):

    def _build_fixture(self):
        document = FakeDocument()
        group_type = FakeGroupType(900, "LOGEMENT T2-A")
        target_definition = FakeDefinition("Surface totale logement")

        values = [
            ("A1", 10.0),
            ("A2", 12.0),
            ("A3", 10.0),
        ]

        rooms = []
        targets = []
        groups = []

        for index, item in enumerate(values):
            apartment, source_value = item
            room_id = 100 + index
            group_id = 200 + index

            target = FakeParameter(
                "Surface totale logement",
                "Double",
                0.0,
                definition=target_definition,
                locked_by_group=True,
            )
            room = FakeRoom(
                room_id,
                group_id,
                apartment,
                "Séjour",
                [
                    FakeParameter("Appartement", "String", apartment),
                    FakeParameter("Surface", "Double", source_value),
                    target,
                ],
            )
            group = FakeGroup(
                group_id,
                group_type,
                [room_id],
            )

            rooms.append(room)
            targets.append(target)
            groups.append(group)
            document.add(room)
            document.add(group)

        group_type.Groups = list(groups)
        document.add(group_type)

        grouped_service = GroupedParameterService(document)
        parameter_service = RoomParameterService(grouped_service)
        writer = RoomWriter(parameter_service, RoomUnitService())
        transactions = []

        def transaction_factory(doc, name):
            transaction = FakeTransaction(doc, name)
            transactions.append(transaction)
            return transaction

        workflow = RoomCalculationWorkflow(
            document=document,
            collector_service=FakeCollectorService(rooms),
            parameter_service=parameter_service,
            parameter_validator=RoomParameterValidator(),
            room_filter=RoomFilter(),
            calculator=RoomCalculator(),
            writer=writer,
            grouped_parameter_service=grouped_service,
            transaction_factory=transaction_factory,
        )

        descriptors = parameter_service.get_parameter_descriptors(rooms)
        by_name = dict((item.name, item) for item in descriptors)
        target_descriptors = parameter_service.get_parameter_descriptors(
            rooms,
            writable_only=True,
        )
        targets_by_name = dict(
            (item.name, item)
            for item in target_descriptors
        )
        request = CalculationRequest(
            by_name["Appartement"],
            by_name["Surface"],
            targets_by_name["Surface totale logement"],
        )

        return {
            "workflow": workflow,
            "request": request,
            "targets": targets,
            "definition": target_definition,
            "transactions": transactions,
        }

    def test_analysis_detects_majority_without_imposing_it(self):
        fixture = self._build_fixture()
        prepared = fixture["workflow"].prepare(fixture["request"])

        analysis = fixture["workflow"].analyze_group_alignment(prepared)

        self.assertTrue(analysis.has_conflicts)
        self.assertEqual(1, analysis.conflict_count)

        conflict = analysis.conflicts[0]
        self.assertEqual("LOGEMENT T2-A", conflict.group_type_name)
        self.assertEqual(2, len(conflict.candidates))

        recommended = conflict.candidates[conflict.recommended_index]
        self.assertEqual(10.0, recommended.value)
        self.assertEqual(2, recommended.count)

    def test_exact_values_can_be_kept_and_parameter_stays_variable(self):
        fixture = self._build_fixture()
        workflow = fixture["workflow"]
        prepared = workflow.prepare(fixture["request"])
        analysis = workflow.analyze_group_alignment(prepared)

        report = workflow.execute(
            prepared,
            group_resolution=GroupAlignmentResolution.keep_variable(),
        )

        self.assertTrue(report.is_success)
        self.assertEqual(
            [10.0, 12.0, 10.0],
            [target.value for target in fixture["targets"]],
        )
        self.assertTrue(fixture["definition"].VariesAcrossGroups)
        self.assertEqual([True], fixture["definition"].calls)
        self.assertTrue(fixture["transactions"][0].committed)

    def test_user_can_choose_non_majority_value_and_keep_alignment(self):
        fixture = self._build_fixture()
        workflow = fixture["workflow"]
        prepared = workflow.prepare(fixture["request"])
        analysis = workflow.analyze_group_alignment(prepared)
        conflict = analysis.conflicts[0]

        resolution = GroupAlignmentResolution.align_selected(
            {conflict.key: 12.0}
        )
        report = workflow.execute(
            prepared,
            group_resolution=resolution,
        )

        self.assertTrue(report.is_success)
        self.assertEqual(
            [12.0, 12.0, 12.0],
            [target.value for target in fixture["targets"]],
        )
        self.assertFalse(fixture["definition"].VariesAcrossGroups)
        self.assertEqual([True, False], fixture["definition"].calls)
        self.assertTrue(fixture["transactions"][0].committed)

    def test_conflict_without_user_choice_does_not_open_transaction(self):
        fixture = self._build_fixture()
        workflow = fixture["workflow"]
        prepared = workflow.prepare(fixture["request"])
        workflow.analyze_group_alignment(prepared)

        report = workflow.execute(prepared)

        self.assertIsNotNone(report.transaction_error)
        self.assertIn("choix utilisateur", report.transaction_error)
        self.assertEqual([], fixture["transactions"])
        self.assertEqual(
            [0.0, 0.0, 0.0],
            [target.value for target in fixture["targets"]],
        )


if __name__ == "__main__":
    unittest.main()
