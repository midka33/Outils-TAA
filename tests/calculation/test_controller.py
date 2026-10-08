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
from calculation_controller import CalculationController


def descriptor(name, storage_type, writable=True):
    return RoomParameterDescriptor(
        name=name,
        identity_kind=RoomParameterDescriptor.KIND_NAME,
        identity_value=name,
        storage_type=storage_type,
        writable=writable,
    )


class FakeCollector(object):
    def __init__(self):
        self.rooms = [object(), object()]

    def collect_all_rooms(self):
        return list(self.rooms)


class FakeParameterService(object):
    def __init__(self):
        self.scan_calls = 0

    def get_parameter_descriptors(
        self,
        rooms,
        numeric_only=False,
        writable_only=False,
    ):
        self.scan_calls += 1
        values = [
            descriptor("Zone", "String"),
            descriptor("Surface", "Double"),
            descriptor("Nombre", "Integer"),
            descriptor("Lien", "ElementId"),
            descriptor("Bloqué", "Double", writable=False),
        ]
        if numeric_only:
            values = [
                item
                for item in values
                if item.storage_type in ("Double", "Integer")
            ]
        if writable_only:
            values = [item for item in values if item.writable]
        return values


class FakeValidator(object):
    SUPPORTED_TARGET_TYPES = ("Double", "Integer", "String")


class FakeUnitService(object):
    def get_unit_options(self, descriptor):
        return ["AUTO", descriptor.name if descriptor else "NONE"]


class FakeWorkflow(object):
    def prepare(self, request, progress=None):
        return ("prepared", request)

    def execute(self, prepared, progress=None):
        return ("executed", prepared)


class FakeSettings(object):
    def load(self):
        return {"x": 1}

    def save_request(self, request):
        return {"saved": request}

    def match_descriptor(self, saved, available):
        return available[0] if available else None


class CalculationControllerTests(unittest.TestCase):

    def setUp(self):
        self.parameter_service = FakeParameterService()
        self.controller = CalculationController(
            collector_service=FakeCollector(),
            parameter_service=self.parameter_service,
            parameter_validator=FakeValidator(),
            unit_service=FakeUnitService(),
            workflow=FakeWorkflow(),
            settings_service=FakeSettings(),
        )

    def test_context_exposes_all_numeric_and_supported_writable_targets(self):
        context = self.controller.load_context()

        self.assertEqual(2, context.rooms_count)
        self.assertEqual(
            ["Zone", "Surface", "Nombre", "Lien", "Bloqué"],
            [item.name for item in context.all_parameters],
        )
        self.assertEqual(
            ["Surface", "Nombre", "Bloqué"],
            [item.name for item in context.numeric_parameters],
        )
        self.assertEqual(
            ["Zone", "Surface", "Nombre"],
            [item.name for item in context.target_parameters],
        )
        self.assertEqual(
            1,
            self.parameter_service.scan_calls,
            "L'ouverture ne doit scanner les paramètres qu'une seule fois.",
        )

    def test_create_request_preserves_optional_filter_and_unit(self):
        group = descriptor("Zone", "String")
        source = descriptor("Surface", "Double")
        target = descriptor("Total", "Double")
        filter_parameter = descriptor("Phase", "String")

        request = self.controller.create_request(
            group,
            source,
            target,
            filter_parameter=filter_parameter,
            filter_value="DCE",
            output_unit_type_id="unit:square-meters",
        )

        self.assertIs(group, request.group_parameter)
        self.assertIs(source, request.source_parameter)
        self.assertIs(target, request.target_parameter)
        self.assertIs(filter_parameter, request.filter_parameter)
        self.assertEqual("DCE", request.filter_value)
        self.assertEqual("unit:square-meters", request.output_unit_type_id)

    def test_controller_delegates_prepare_execute_settings_and_units(self):
        source = descriptor("Surface", "Double")
        request = self.controller.create_request(
            descriptor("Zone", "String"),
            source,
            descriptor("Total", "Double"),
        )

        prepared = self.controller.prepare(request)
        executed = self.controller.execute(prepared)

        self.assertEqual("prepared", prepared[0])
        self.assertEqual("executed", executed[0])
        self.assertEqual(["AUTO", "Surface"], self.controller.unit_options(source))
        self.assertEqual({"x": 1}, self.controller.load_settings())
        self.assertEqual({"saved": request}, self.controller.save_settings(request))


if __name__ == "__main__":
    unittest.main()
