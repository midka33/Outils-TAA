# -*- coding: utf-8 -*-
"""Tests hors Revit du suivi des publications Export."""

import os
import sys
import tempfile
import unittest

SERVICE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel", "services"
))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from publication_history_service import PublicationHistoryService


class FakeItem(object):
    def __init__(self, unique_id, number="A101", name="RDC"):
        self.unique_id = unique_id
        self.sheet_id = 1
        self.sheet_number = number
        self.sheet_name = name


class FakeSet(object):
    def __init__(self, set_id, items):
        self.id = set_id
        self.name = "DCE"
        self.items = items


class PublicationHistoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "history.json")
        self.service = PublicationHistoryService(self.path)
        self.a = FakeItem("sheet-a")
        self.b = FakeItem("sheet-b", "A102", "R+1")
        self.publication_set = FakeSet("set-1", [self.a, self.b])

    def test_first_publication_marks_items_new(self):
        states = {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        }
        classified = self.service.classify_items(self.publication_set, states)
        self.assertEqual([self.a, self.b], classified["NEW"])
        self.assertEqual([], classified["MODIFIED"])
        self.assertEqual([], classified["UNCHANGED"])

    def test_version_guid_change_marks_only_changed_item(self):
        self.service.record_publication(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        })
        classified = self.service.classify_items(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v3"},
        })
        self.assertEqual([self.b], classified["MODIFIED"])
        self.assertEqual([self.a], classified["UNCHANGED"])

    def test_unknown_version_is_conservatively_republished(self):
        self.service.record_publication(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        })
        selected, classified = self.service.candidates(self.publication_set, {
            "sheet-a": {"version_guid": None},
            "sheet-b": {"version_guid": "v2"},
        }, modified_only=True)
        self.assertEqual([self.a], selected)
        self.assertEqual([self.a], classified["UNKNOWN"])

    def test_disabled_modified_only_keeps_all_items(self):
        self.service.record_publication(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        })
        selected, _ = self.service.candidates(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        }, modified_only=False)
        self.assertEqual([self.a, self.b], selected)

    def test_history_survives_new_service_instance(self):
        self.service.record_publication(self.publication_set, {
            "sheet-a": {"version_guid": "v1"},
            "sheet-b": {"version_guid": "v2"},
        }, output_paths=["D:/exports/DCE.pdf"])
        reloaded = PublicationHistoryService(self.path)
        history = reloaded.get_set_history("set-1")
        self.assertEqual("DCE", history["set_name"])
        self.assertEqual("v1", history["items"]["sheet-a"]["version_guid"])
        self.assertEqual(["D:/exports/DCE.pdf"], history["output_paths"])


if __name__ == "__main__":
    unittest.main()
