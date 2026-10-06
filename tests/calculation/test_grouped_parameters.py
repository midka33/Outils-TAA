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

from calculation.parameter_descriptor import RoomParameterDescriptor
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
    def __init__(
        self,
        name,
        varies_across_groups=True,
        built_in_parameter=-1,
        changed_on_restore=None,
    ):
        self.Name = name
        self.VariesAcrossGroups = bool(varies_across_groups)
        self.BuiltInParameter = built_in_parameter
        self.changed_on_restore = list(changed_on_restore or [])
        self.calls = []

    def SetAllowVaryBetweenGroups(self, document, allow):
        self.calls.append(bool(allow))
        self.VariesAcrossGroups = bool(allow)
        if allow:
            return []
        return list(self.changed_on_restore)


class FakeParameter(object):
    def __init__(
        self,
        name,
        storage_type,
        value=None,
        definition=None,
        read_only=False,
        locked_by_group=False,
    ):
        self.Definition = definition or FakeDefinition(name)
        self.StorageType = storage_type
        self.value = value
        self._read_only = bool(read_only)
        self.locked_by_group = bool(locked_by_group)
        self.IsShared = False
        self.set_values = []

    @property
    def IsReadOnly(self):
        if self._read_only:
            return True
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
    def __init__(self, unique_id, parameters, group_id=10):
        self.UniqueId = unique_id
        self.Id = FakeElementId(unique_id)
        self.GroupId = FakeElementId(group_id)
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


def descriptor(name, storage_type, writable=True, group_unlockable=False):
    return RoomParameterDescriptor(
        name=name,
        identity_kind=RoomParameterDescriptor.KIND_NAME,
        identity_value=name,
        storage_type=storage_type,
        writable=writable,
        group_unlockable=group_unlockable,
    )


class GroupedParameterServiceTests(unittest.TestCase):

    def setUp(self):
        self.document = object()
        self.service = GroupedParameterService(self.document)

    def test_group_aligned_non_builtin_parameter_can_be_unlocked(self):
        definition = FakeDefinition("Total", varies_across_groups=False)
        parameter = FakeParameter(
            "Total",
            "Double",
            definition=definition,
            locked_by_group=True,
        )
        room = FakeRoom("r1", [parameter])

        self.assertTrue(self.service.is_grouped(room))
        self.assertTrue(
            self.service.can_temporarily_unlock(room, parameter)
        )

    def test_builtin_parameter_is_never_exposed_as_unlockable(self):
        definition = FakeDefinition(
            "BuiltIn",
            varies_across_groups=False,
            built_in_parameter=42,
        )
        parameter = FakeParameter(
            "BuiltIn",
            "Double",
            definition=definition,
            locked_by_group=True,
        )
        room = FakeRoom("r1", [parameter])

        self.assertFalse(
            self.service.can_temporarily_unlock(room, parameter)
        )

    def test_parameter_discovery_keeps_group_locked_target(self):
        definition = FakeDefinition("Total", varies_across_groups=False)
        target = FakeParameter(
            "Total",
            "Double",
            definition=definition,
            locked_by_group=True,
        )
        room = FakeRoom("r1", [target])
        parameter_service = RoomParameterService(self.service)

        values = parameter_service.get_parameter_descriptors(
            [room],
            writable_only=True,
        )

        self.assertEqual(1, len(values))
        self.assertFalse(values[0].writable)
        self.assertTrue(values[0].group_unlockable)
        self.assertTrue(values[0].write_supported)

    def test_validator_accepts_group_unlockable_target(self):
        validator = RoomParameterValidator()
        source = descriptor("Surface", "Double")
        target = descriptor(
            "Total",
            "Double",
            writable=False,
            group_unlockable=True,
        )

        result = validator.validate_pair(source, target)

        self.assertTrue(result.is_valid)


class GroupedWorkflowTests(unittest.TestCase):

    def _build(self, rooms):
        document = object()
        grouped_service = GroupedParameterService(document)
        parameter_service = RoomParameterService(grouped_service)
        unit_service = RoomUnitService()
        writer = RoomWriter(parameter_service, unit_service)
        transactions = []

        def factory(doc, name):
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
            transaction_factory=factory,
        )
        return workflow, parameter_service, transactions

    def _rooms(self, changed_on_restore=None):
        target_definition = FakeDefinition(
            "Total",
            varies_across_groups=False,
            changed_on_restore=changed_on_restore,
        )
        target1 = FakeParameter(
            "Total",
            "Double",
            0.0,
            definition=target_definition,
            locked_by_group=True,
        )
        target2 = FakeParameter(
            "Total",
            "Double",
            0.0,
            definition=target_definition,
            locked_by_group=True,
        )
        room1 = FakeRoom(
            "r1",
            [
                FakeParameter("Appartement", "String", "A"),
                FakeParameter("Surface", "Double", 10.0),
                target1,
            ],
        )
        room2 = FakeRoom(
            "r2",
            [
                FakeParameter("Appartement", "String", "A"),
                FakeParameter("Surface", "Double", 5.0),
                target2,
            ],
        )
        return [room1, room2], target_definition, target1, target2

    def _request(self, parameter_service, rooms):
        descriptors = parameter_service.get_parameter_descriptors(rooms)
        by_name = dict((item.name, item) for item in descriptors)
        target_values = parameter_service.get_parameter_descriptors(
            rooms,
            writable_only=True,
        )
        target_by_name = dict((item.name, item) for item in target_values)

        return CalculationRequest(
            by_name["Appartement"],
            by_name["Surface"],
            target_by_name["Total"],
        )

    def test_group_locked_target_is_temporarily_unlocked_then_restored(self):
        rooms, definition, target1, target2 = self._rooms()
        workflow, parameter_service, transactions = self._build(rooms)
        request = self._request(parameter_service, rooms)

        prepared = workflow.prepare(request)
        report = workflow.execute(prepared)

        self.assertTrue(report.is_success)
        self.assertEqual(2, report.success_count)
        self.assertEqual(15.0, target1.value)
        self.assertEqual(15.0, target2.value)
        self.assertEqual([True, False], definition.calls)
        self.assertFalse(definition.VariesAcrossGroups)
        self.assertTrue(transactions[0].committed)
        self.assertTrue(
            any("temporairement" in warning for warning in prepared.warnings)
        )

    def test_realignment_on_restore_rolls_back_transaction(self):
        rooms, definition, target1, target2 = self._rooms(
            changed_on_restore=[FakeElementId(99)]
        )
        workflow, parameter_service, transactions = self._build(rooms)
        request = self._request(parameter_service, rooms)

        prepared = workflow.prepare(request)
        report = workflow.execute(prepared)

        self.assertFalse(report.is_success)
        self.assertIsNotNone(report.transaction_error)
        self.assertIn("réalign", report.transaction_error.lower())
        self.assertTrue(transactions[0].rolled_back)
        self.assertFalse(transactions[0].committed)
        self.assertEqual([True, False], definition.calls)


if __name__ == "__main__":
    unittest.main()
