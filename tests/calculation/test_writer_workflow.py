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

from calculation.models import RoomCalculationItem
from calculation.parameter_descriptor import RoomParameterDescriptor
from calculation.room_calculator import RoomCalculator
from calculation.room_filter import RoomFilter
from calculation.workflow_models import CalculationRequest
from room_calculation_workflow import RoomCalculationWorkflow
from room_parameter_service import RoomParameterService
from room_parameter_validator import RoomParameterValidator
from room_unit_service import RoomUnitService
from room_writer import RoomWriter


class FakeForgeTypeId(object):
    def __init__(self, value):
        self.TypeId = value
        self.factor = 10.0


class FakeUnitUtils(object):
    @staticmethod
    def ConvertFromInternalUnits(value, unit_type_id):
        return value * unit_type_id.factor

    @staticmethod
    def ConvertToInternalUnits(value, unit_type_id):
        return value / unit_type_id.factor


class FakeDefinition(object):
    def __init__(self, name):
        self.Name = name


class FakeParameter(object):
    def __init__(self, name, storage_type, value=None, read_only=False):
        self.Definition = FakeDefinition(name)
        self.StorageType = storage_type
        self.value = value
        self.IsReadOnly = read_only
        self.IsShared = False
        self.set_values = []

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


class FakeElementId(object):
    def __init__(self, value):
        self.Value = value


class FakeRoom(object):
    def __init__(self, unique_id, parameters):
        self.UniqueId = unique_id
        self.Id = FakeElementId(unique_id)
        self.Parameters = list(parameters)

    def LookupParameter(self, name):
        matches = self.GetParameters(name)
        return matches[0] if matches else None

    def GetParameters(self, name):
        return [
            parameter
            for parameter in self.Parameters
            if parameter.Definition.Name == name
        ]


class FakeCollectorService(object):
    def __init__(self, rooms):
        self.rooms = list(rooms)

    def collect_all_rooms(self):
        return list(self.rooms)


class FakeTransaction(object):
    def __init__(self, document, name, fail_commit=False):
        self.document = document
        self.name = name
        self.fail_commit = fail_commit
        self.started = False
        self.committed = False
        self.rolled_back = False

    def Start(self):
        self.started = True

    def Commit(self):
        if self.fail_commit:
            raise RuntimeError("commit failed")
        self.committed = True

    def RollBack(self):
        self.rolled_back = True


def descriptor(name, storage_type, data_type_id=None, unit_type_id=None):
    return RoomParameterDescriptor(
        name=name,
        identity_kind=RoomParameterDescriptor.KIND_NAME,
        identity_value=name,
        storage_type=storage_type,
        data_type_id=data_type_id,
        unit_type_id=unit_type_id,
        writable=True,
    )


class RoomWriterTests(unittest.TestCase):

    def setUp(self):
        self.parameter_service = RoomParameterService()
        self.unit_service = RoomUnitService(
            unit_utils=FakeUnitUtils,
            forge_type_factory=FakeForgeTypeId,
        )
        self.writer = RoomWriter(self.parameter_service, self.unit_service)

    def test_double_target_keeps_internal_value(self):
        source = descriptor("Source", "Double", data_type_id="area")
        target = descriptor("Target", "Double", data_type_id="area")

        value = self.writer.prepare_value(source, target, 12.5)

        self.assertEqual(12.5, value)

    def test_string_target_converts_double_to_selected_unit(self):
        source = descriptor(
            "Source",
            "Double",
            data_type_id="area",
            unit_type_id="unit:area",
        )
        target = descriptor("Target", "String")

        value = self.writer.prepare_value(source, target, 2.5)

        self.assertEqual("25", value)

    def test_integer_target_rounds_converted_double(self):
        source = descriptor(
            "Source",
            "Double",
            data_type_id="area",
            unit_type_id="unit:area",
        )
        target = descriptor("Target", "Integer")

        value = self.writer.prepare_value(source, target, 2.56)

        self.assertEqual(26, value)

    def test_write_rejects_missing_target(self):
        room = FakeRoom("r1", [])
        target = descriptor("Target", "Double")

        with self.assertRaises(Exception):
            self.writer.write_value(room, target, 10.0)


class RoomCalculationWorkflowTests(unittest.TestCase):

    def _build(self, rooms, transaction_holder, fail_commit=False):
        parameter_service = RoomParameterService()
        unit_service = RoomUnitService(
            unit_utils=FakeUnitUtils,
            forge_type_factory=FakeForgeTypeId,
        )
        writer = RoomWriter(parameter_service, unit_service)

        def factory(document, name):
            transaction = FakeTransaction(
                document,
                name,
                fail_commit=fail_commit,
            )
            transaction_holder.append(transaction)
            return transaction

        return RoomCalculationWorkflow(
            document=object(),
            collector_service=FakeCollectorService(rooms),
            parameter_service=parameter_service,
            parameter_validator=RoomParameterValidator(),
            room_filter=RoomFilter(),
            calculator=RoomCalculator(),
            writer=writer,
            transaction_factory=factory,
        )

    def test_prepare_writes_total_to_all_rooms_of_group_even_invalid_source(self):
        group = descriptor("Group", "String")
        source = descriptor("Source", "Double", data_type_id="area")
        target = descriptor("Target", "Double", data_type_id="area")

        room1 = FakeRoom("r1", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Double", 10.0),
            FakeParameter("Target", "Double", 0.0),
        ])
        room2 = FakeRoom("r2", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Double", None),
            FakeParameter("Target", "Double", 0.0),
        ])

        workflow = self._build([room1, room2], [])
        request = CalculationRequest(group, source, target)

        prepared = workflow.prepare(request)

        self.assertEqual(2, len(prepared.operations))
        self.assertEqual(
            ["r1", "r2"],
            sorted(operation.room_key for operation in prepared.operations),
        )
        self.assertEqual(10.0, prepared.result.get_total("A"))

    def test_execute_commits_valid_writes(self):
        group = descriptor("Group", "String")
        source = descriptor("Source", "Double", data_type_id="area")
        target = descriptor("Target", "Double", data_type_id="area")

        target1 = FakeParameter("Target", "Double", 0.0)
        target2 = FakeParameter("Target", "Double", 0.0)
        room1 = FakeRoom("r1", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Double", 10.0),
            target1,
        ])
        room2 = FakeRoom("r2", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Double", 5.0),
            target2,
        ])

        transactions = []
        workflow = self._build([room1, room2], transactions)
        prepared = workflow.prepare(CalculationRequest(group, source, target))
        report = workflow.execute(prepared)

        self.assertTrue(report.is_success)
        self.assertEqual(2, report.success_count)
        self.assertEqual(15.0, target1.value)
        self.assertEqual(15.0, target2.value)
        self.assertTrue(transactions[0].committed)

    def test_execute_keeps_valid_room_when_other_target_is_missing(self):
        group = descriptor("Group", "String")
        source = descriptor("Source", "Integer")
        target = descriptor("Target", "Integer")

        target1 = FakeParameter("Target", "Integer", 0)
        room1 = FakeRoom("r1", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Integer", 2),
            target1,
        ])
        room2 = FakeRoom("r2", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Integer", 3),
        ])

        transactions = []
        workflow = self._build([room1, room2], transactions)
        prepared = workflow.prepare(CalculationRequest(group, source, target))
        report = workflow.execute(prepared)

        self.assertEqual(1, report.success_count)
        self.assertEqual(1, report.failed_count)
        self.assertEqual(5, target1.value)
        self.assertTrue(transactions[0].committed)

    def test_commit_failure_reports_rollback_and_no_success(self):
        group = descriptor("Group", "String")
        source = descriptor("Source", "Integer")
        target = descriptor("Target", "Integer")
        target1 = FakeParameter("Target", "Integer", 0)
        room = FakeRoom("r1", [
            FakeParameter("Group", "String", "A"),
            FakeParameter("Source", "Integer", 2),
            target1,
        ])

        transactions = []
        workflow = self._build([room], transactions, fail_commit=True)
        prepared = workflow.prepare(CalculationRequest(group, source, target))
        report = workflow.execute(prepared)

        self.assertFalse(report.is_success)
        self.assertEqual(0, report.success_count)
        self.assertEqual(1, report.failed_count)
        self.assertEqual("commit failed", report.transaction_error)
        self.assertTrue(transactions[0].rolled_back)


if __name__ == "__main__":
    unittest.main()
