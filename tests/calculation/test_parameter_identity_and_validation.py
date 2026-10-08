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

from common.exceptions import ValidationError
from calculation.parameter_descriptor import RoomParameterDescriptor
from room_parameter_service import RoomParameterService
from room_parameter_validator import RoomParameterValidator


class FakeForgeTypeId(object):
    def __init__(self, type_id):
        self.TypeId = type_id


class FakeDefinition(object):
    def __init__(
        self,
        name,
        data_type_id=None,
        built_in_type_id=None,
        definition_type_id=None,
    ):
        self.Name = name
        self._data_type_id = data_type_id
        self._built_in_type_id = built_in_type_id
        self._definition_type_id = definition_type_id
        self.data_type_calls = 0
        self.parameter_type_calls = 0
        self.definition_type_calls = 0

    def GetDataType(self):
        self.data_type_calls += 1
        return FakeForgeTypeId(self._data_type_id)

    def GetParameterTypeId(self):
        self.parameter_type_calls += 1
        if self._built_in_type_id is None:
            return None
        return FakeForgeTypeId(self._built_in_type_id)

    def GetTypeId(self):
        self.definition_type_calls += 1
        if self._definition_type_id is None:
            return None
        return FakeForgeTypeId(self._definition_type_id)


class FakeParameter(object):
    def __init__(
        self,
        name,
        storage_type,
        value=None,
        read_only=False,
        shared_guid=None,
        data_type_id=None,
        unit_type_id=None,
        built_in_type_id=None,
        definition_type_id=None,
        parameter_id=None,
    ):
        self.Definition = FakeDefinition(
            name,
            data_type_id=data_type_id,
            built_in_type_id=built_in_type_id,
            definition_type_id=definition_type_id,
        )
        self.StorageType = storage_type
        self.value = value
        self.IsReadOnly = read_only
        self.IsShared = shared_guid is not None
        self.GUID = shared_guid
        self._unit_type_id = unit_type_id
        self.unit_type_calls = 0
        if parameter_id is not None:
            self.Id = parameter_id

    def GetUnitTypeId(self):
        self.unit_type_calls += 1
        if self._unit_type_id is None:
            raise RuntimeError("no unit")
        return FakeForgeTypeId(self._unit_type_id)

    def AsString(self):
        return self.value

    def AsInteger(self):
        return self.value

    def AsDouble(self):
        return self.value

    def AsValueString(self):
        return None if self.value is None else str(self.value)


class FakeRoom(object):
    def __init__(self, parameters):
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


class ParameterIdentityTests(unittest.TestCase):

    def setUp(self):
        self.service = RoomParameterService()

    def test_shared_guid_has_priority_identity(self):
        parameter = FakeParameter(
            "Surface TAA",
            "Double",
            shared_guid="11111111-1111-1111-1111-111111111111",
            data_type_id="autodesk.spec.aec:area-2.0.0",
            definition_type_id="custom:surface",
        )

        descriptor = self.service.create_descriptor(parameter)

        self.assertEqual(RoomParameterDescriptor.KIND_SHARED_GUID, descriptor.identity_kind)
        self.assertEqual(
            "11111111-1111-1111-1111-111111111111",
            descriptor.identity_value,
        )
        self.assertEqual("autodesk.spec.aec:area-2.0.0", descriptor.data_type_id)

    def test_built_in_parameter_uses_forge_type_identity(self):
        parameter = FakeParameter(
            "Surface",
            "Double",
            built_in_type_id="autodesk.parameter:roomArea-1.0.0",
            data_type_id="autodesk.spec.aec:area-2.0.0",
        )

        descriptor = self.service.create_descriptor(parameter)

        self.assertEqual(RoomParameterDescriptor.KIND_BUILT_IN, descriptor.identity_kind)
        self.assertEqual(
            "autodesk.parameter:roomArea-1.0.0",
            descriptor.identity_value,
        )

    def test_project_definition_uses_definition_identity(self):
        parameter = FakeParameter(
            "Zone",
            "String",
            definition_type_id="project:zone-123",
        )

        descriptor = self.service.create_descriptor(parameter)

        self.assertEqual(RoomParameterDescriptor.KIND_DEFINITION, descriptor.identity_kind)
        self.assertEqual("project:zone-123", descriptor.identity_value)

    def test_same_display_name_with_different_identities_is_not_deduplicated(self):
        rooms = [
            FakeRoom([
                FakeParameter(
                    "Surface",
                    "Double",
                    shared_guid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                ),
                FakeParameter(
                    "Surface",
                    "Double",
                    shared_guid="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                ),
            ])
        ]

        descriptors = self.service.get_parameter_descriptors(rooms)

        self.assertEqual(2, len(descriptors))
        self.assertNotEqual(descriptors[0].identity_key, descriptors[1].identity_key)

    def test_parameter_metadata_is_cached_per_parameter_id_during_scan(self):
        first = FakeParameter(
            "Surface TAA",
            "Double",
            parameter_id=7001,
            data_type_id="autodesk.spec.aec:area-2.0.0",
            unit_type_id="autodesk.unit.unit:squareMeters-1.0.1",
            definition_type_id="project:surface-taa",
        )
        second = FakeParameter(
            "Surface TAA",
            "Double",
            parameter_id=7001,
            data_type_id="autodesk.spec.aec:area-2.0.0",
            unit_type_id="autodesk.unit.unit:squareMeters-1.0.1",
            definition_type_id="project:surface-taa",
        )

        descriptors = self.service.get_parameter_descriptors([
            FakeRoom([first]),
            FakeRoom([second]),
        ])

        self.assertEqual(1, len(descriptors))
        self.assertEqual(1, first.Definition.data_type_calls)
        self.assertEqual(1, first.Definition.parameter_type_calls)
        self.assertEqual(1, first.Definition.definition_type_calls)
        self.assertEqual(1, first.unit_type_calls)

        self.assertEqual(0, second.Definition.data_type_calls)
        self.assertEqual(0, second.Definition.parameter_type_calls)
        self.assertEqual(0, second.Definition.definition_type_calls)
        self.assertEqual(0, second.unit_type_calls)

    def test_writable_only_rejects_identity_read_only_on_any_room(self):
        shared_guid = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        rooms = [
            FakeRoom([
                FakeParameter(
                    "Surface calculée",
                    "Double",
                    read_only=False,
                    shared_guid=shared_guid,
                ),
            ]),
            FakeRoom([
                FakeParameter(
                    "Surface calculée",
                    "Double",
                    read_only=True,
                    shared_guid=shared_guid,
                ),
            ]),
        ]

        descriptors = self.service.get_parameter_descriptors(
            rooms,
            writable_only=True,
        )

        self.assertEqual([], descriptors)

    def test_definition_descriptor_resolves_exact_parameter_among_homonyms(self):
        first = FakeParameter(
            "Zone",
            "String",
            value="A",
            definition_type_id="project:zone-a",
        )
        second = FakeParameter(
            "Zone",
            "String",
            value="B",
            definition_type_id="project:zone-b",
        )
        room = FakeRoom([first, second])
        descriptor = self.service.create_descriptor(second)

        resolved = self.service.get_parameter(room, descriptor)

        self.assertIs(second, resolved)

    def test_name_fallback_rejects_ambiguous_parameter(self):
        first = FakeParameter("Zone", "String", value="A")
        second = FakeParameter("Zone", "String", value="B")
        room = FakeRoom([first, second])
        descriptor = RoomParameterDescriptor(
            name="Zone",
            identity_kind=RoomParameterDescriptor.KIND_NAME,
            identity_value="Zone",
            storage_type="String",
        )

        with self.assertRaises(ValidationError):
            self.service.get_parameter(room, descriptor)

    def test_descriptor_round_trip_is_serializable(self):
        descriptor = RoomParameterDescriptor(
            name="Surface TAA",
            identity_kind=RoomParameterDescriptor.KIND_SHARED_GUID,
            identity_value="11111111-1111-1111-1111-111111111111",
            storage_type="Double",
            data_type_id="area",
            unit_type_id="square_meters",
            writable=False,
        )

        restored = RoomParameterDescriptor.from_dict(descriptor.to_dict())

        self.assertEqual(descriptor.identity_key, restored.identity_key)
        self.assertEqual("Double", restored.storage_type)
        self.assertEqual("area", restored.data_type_id)
        self.assertEqual("square_meters", restored.unit_type_id)
        self.assertFalse(restored.writable)


class ParameterValidationTests(unittest.TestCase):

    def setUp(self):
        self.validator = RoomParameterValidator()

    @staticmethod
    def descriptor(name, storage, data_type=None, writable=True):
        return RoomParameterDescriptor(
            name=name,
            identity_kind=RoomParameterDescriptor.KIND_NAME,
            identity_value=name,
            storage_type=storage,
            data_type_id=data_type,
            writable=writable,
        )

    def test_double_parameters_with_same_data_type_are_compatible(self):
        source = self.descriptor("Source", "Double", "area")
        target = self.descriptor("Destination", "Double", "area")

        result = self.validator.validate_pair(source, target)

        self.assertTrue(result.is_valid)
        self.assertEqual([], result.errors)

    def test_double_parameters_with_different_data_types_are_rejected(self):
        source = self.descriptor("Surface", "Double", "area")
        target = self.descriptor("Volume", "Double", "volume")

        result = self.validator.validate_pair(source, target)

        self.assertFalse(result.is_valid)
        self.assertTrue(result.errors)

    def test_read_only_target_is_rejected(self):
        source = self.descriptor("Source", "Integer")
        target = self.descriptor("Cible", "Integer", writable=False)

        result = self.validator.validate_pair(source, target)

        self.assertFalse(result.is_valid)
        self.assertIn("lecture seule", result.errors[0])

    def test_double_to_integer_is_allowed_with_warning(self):
        source = self.descriptor("Source", "Double", "number")
        target = self.descriptor("Cible", "Integer")

        result = self.validator.validate_pair(source, target)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.warnings)

    def test_integer_to_double_is_allowed_with_warning(self):
        source = self.descriptor("Source", "Integer")
        target = self.descriptor("Cible", "Double", "number")

        result = self.validator.validate_pair(source, target)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.warnings)

    def test_string_target_is_allowed_with_warning(self):
        source = self.descriptor("Source", "Integer")
        target = self.descriptor("Cible", "String")

        result = self.validator.validate_pair(source, target)

        self.assertTrue(result.is_valid)
        self.assertTrue(result.warnings)

    def test_element_id_target_is_rejected(self):
        source = self.descriptor("Source", "Integer")
        target = self.descriptor("Cible", "ElementId")

        result = self.validator.validate_pair(source, target)

        self.assertFalse(result.is_valid)


if __name__ == "__main__":
    unittest.main()
