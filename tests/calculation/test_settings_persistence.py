# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import shutil
import sys
import tempfile
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

from common.settings import JsonSettingsStore
from calculation.parameter_descriptor import RoomParameterDescriptor
from calculation.workflow_models import CalculationRequest
from calculation_settings_service import CalculationSettingsService


def descriptor(name, kind="NAME", value=None, storage="String"):
    return RoomParameterDescriptor(
        name=name,
        identity_kind=kind,
        identity_value=value or name,
        storage_type=storage,
    )


class JsonSettingsStoreTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="outilstaa_calc_")
        self.path = os.path.join(self.folder, "settings.json")

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_set_get_update_and_replace(self):
        store = JsonSettingsStore(self.path)
        store.set("a", 1)
        store.update({"b": 2})

        self.assertEqual(1, store.get("a"))
        self.assertEqual(2, store.get("b"))

        store.replace({"c": 3})
        self.assertIsNone(store.get("a"))
        self.assertEqual(3, store.get("c"))


class CalculationSettingsServiceTests(unittest.TestCase):

    def setUp(self):
        self.folder = tempfile.mkdtemp(prefix="outilstaa_calc_")
        self.path = os.path.join(self.folder, "settings.json")
        self.legacy = os.path.join(self.folder, "legacy.json")
        self.service = CalculationSettingsService(
            storage_path=self.path,
            legacy_path=self.legacy,
        )

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_save_request_serializes_only_stable_data(self):
        request = CalculationRequest(
            group_parameter=descriptor("Groupe"),
            source_parameter=descriptor(
                "Surface",
                kind=RoomParameterDescriptor.KIND_SHARED_GUID,
                value="guid-surface",
                storage="Double",
            ),
            target_parameter=descriptor("Total", storage="Double"),
            filter_parameter=descriptor("Zone"),
            filter_value="A",
            output_unit_type_id="unit:square-meters",
        )

        saved = self.service.save_request(request)
        loaded = self.service.load()

        self.assertEqual(saved, loaded)
        self.assertEqual("guid-surface", loaded["source_parameter"]["identity_value"])
        self.assertEqual("A", loaded["filter_value"])
        self.assertEqual("unit:square-meters", loaded["output_unit_type_id"])

    def test_match_descriptor_prefers_exact_identity(self):
        available = [
            descriptor(
                "Surface",
                kind=RoomParameterDescriptor.KIND_SHARED_GUID,
                value="guid-a",
                storage="Double",
            ),
            descriptor(
                "Surface",
                kind=RoomParameterDescriptor.KIND_SHARED_GUID,
                value="guid-b",
                storage="Double",
            ),
        ]
        saved = available[1].to_dict()

        restored = self.service.match_descriptor(saved, available)

        self.assertIs(available[1], restored)

    def test_name_fallback_requires_unique_match(self):
        saved = descriptor("Zone").to_dict()
        one = [descriptor("Zone", kind="DEFINITION", value="id-a")]

        self.assertIs(one[0], self.service.match_descriptor(saved, one))

        ambiguous = [
            descriptor("Zone", kind="DEFINITION", value="id-a"),
            descriptor("Zone", kind="DEFINITION", value="id-b"),
        ]
        self.assertIsNone(self.service.match_descriptor(saved, ambiguous))

    def test_legacy_settings_migrate_parameter_names_but_not_manual_unit_tag(self):
        legacy = {
            "group": "Appartement",
            "sum": "Surface",
            "target": "Surface totale",
            "filter_param": "Phase",
            "filter_value": "DCE",
            "unit": "square_meter",
        }
        with open(self.legacy, "w") as handle:
            json.dump(legacy, handle)

        loaded = self.service.load()

        self.assertEqual("Appartement", loaded["group_parameter"]["name"])
        self.assertEqual("Surface", loaded["source_parameter"]["name"])
        self.assertEqual("Surface totale", loaded["target_parameter"]["name"])
        self.assertEqual("Phase", loaded["filter_parameter"]["name"])
        self.assertEqual("DCE", loaded["filter_value"])
        self.assertIsNone(loaded["output_unit_type_id"])
        self.assertEqual("square_meter", loaded["legacy_unit_tag"])


if __name__ == "__main__":
    unittest.main()
