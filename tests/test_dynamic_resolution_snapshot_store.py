# -*- coding: utf-8 -*-
import json
import os
import sys
import tempfile
import unittest

EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel"))
if EXPORT_DIR not in sys.path:
    sys.path.insert(0, EXPORT_DIR)

from services.dynamic_resolution_snapshot_store import DynamicResolutionSnapshot, DynamicResolutionSnapshotStore


class DynamicResolutionSnapshotStoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "snapshots.json")
        self.store = DynamicResolutionSnapshotStore(self.path)

    def test_save_load_roundtrip(self):
        snapshot = DynamicResolutionSnapshot("project-a", "carnet-1", "Logements", ["b", "a"], ["x"])
        self.store.save(snapshot)
        loaded = self.store.load("project-a", "carnet-1")
        self.assertEqual(["a", "b"], loaded.included_keys)
        self.assertEqual(["x"], loaded.excluded_keys)
        self.assertEqual("project-a", loaded.project_key)

    def test_projects_and_carnets_are_isolated(self):
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-1", "A", ["a"], []))
        self.store.save(DynamicResolutionSnapshot("project-b", "carnet-1", "B", ["b"], []))
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-2", "C", ["c"], []))
        self.assertEqual(["a"], self.store.load("project-a", "carnet-1").included_keys)
        self.assertEqual(["b"], self.store.load("project-b", "carnet-1").included_keys)
        self.assertEqual(["c"], self.store.load("project-a", "carnet-2").included_keys)

    def test_missing_snapshot_returns_none(self):
        self.assertIsNone(self.store.load("project-a", "missing"))

    def test_schema_version_is_persisted(self):
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-1", "A", ["a"], []))
        with open(self.path, "r") as handle:
            data = json.load(handle)
        entry = data["snapshots"]["project-a::carnet-1"]
        self.assertEqual(1, entry["schema_version"])

    def test_corrupt_file_is_treated_as_empty_store(self):
        with open(self.path, "w") as handle:
            handle.write("not json")
        self.assertIsNone(self.store.load("project-a", "carnet-1"))

    def test_overwrite_only_replaces_same_identity(self):
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-1", "A", ["a"], []))
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-2", "B", ["b"], []))
        self.store.save(DynamicResolutionSnapshot("project-a", "carnet-1", "A", ["new"], []))
        self.assertEqual(["new"], self.store.load("project-a", "carnet-1").included_keys)
        self.assertEqual(["b"], self.store.load("project-a", "carnet-2").included_keys)


if __name__ == "__main__":
    unittest.main()
