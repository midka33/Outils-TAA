# -*- coding: utf-8 -*-

import os
import tempfile
import unittest

from models.dynamic_publication_set import DynamicPublicationSet
from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition
from services.dynamic_publication_set_store import DynamicPublicationSetStore
from services.dynamic_publication_set_lifecycle import DynamicPublicationSetLifecycle


class DynamicPublicationSetStoreTests(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "dynamic_sets.json")
        self.store = DynamicPublicationSetStore(self.path)
        self.lifecycle = DynamicPublicationSetLifecycle(self.store)

    def _make_set(self, set_id="dyn-01", name="Carnet Architecture"):
        definition = DynamicRuleDefinition(
            root=DynamicRuleGroup("all", [
                DynamicRule("discipline", "equals", "Architecture")
            ]),
            exclusions=["sheet-excluded"],
            name="Architecture",
        )
        return DynamicPublicationSet(
            name=name,
            set_id=set_id,
            folder_id="folder-01",
            output_directory="C:/Exports",
            filename_template_id="template-01",
            publication_settings={"pdf": True, "dwg": True},
            rule_definition=definition,
            exclusions=["sheet-excluded"],
            snapshot_key="project-01:carnet-01",
        )

    def tearDown(self):
        try:
            os.remove(self.path)
        except OSError:
            pass
        try:
            os.rmdir(self.directory)
        except OSError:
            pass

    def test_save_and_load_survive_new_store_instance(self):
        self.lifecycle.create("project-01", self._make_set())
        restored = DynamicPublicationSetStore(self.path).get("project-01", "dyn-01")
        self.assertEqual(restored.name, "Carnet Architecture")
        self.assertEqual(restored.rule_definition.name, "Architecture")
        self.assertEqual(restored.exclusions, ["sheet-excluded"])

    def test_project_isolation(self):
        self.lifecycle.create("project-01", self._make_set())
        self.assertIsNone(self.store.get("project-02", "dyn-01"))
        self.assertEqual(len(self.store.list("project-02")), 0)
        self.assertEqual(len(self.store.list("project-01")), 1)

    def test_update_requires_existing_set(self):
        with self.assertRaises(ValueError):
            self.lifecycle.update("project-01", self._make_set())
        self.lifecycle.create("project-01", self._make_set())
        updated = self._make_set(name="Carnet modifié")
        self.lifecycle.update("project-01", updated)
        self.assertEqual(self.store.get("project-01", "dyn-01").name, "Carnet modifié")

    def test_duplicate_is_independent(self):
        self.lifecycle.create("project-01", self._make_set())
        copy = self.lifecycle.duplicate("project-01", "dyn-01", "dyn-02", "Copie")
        copy.rule_definition.name = "Règle copie"
        source = self.store.get("project-01", "dyn-01")
        self.assertEqual(source.rule_definition.name, "Architecture")
        self.assertEqual(self.store.get("project-01", "dyn-02").name, "Copie")

    def test_delete_removes_only_selected_set(self):
        self.lifecycle.create("project-01", self._make_set("dyn-01"))
        self.lifecycle.create("project-01", self._make_set("dyn-02", "Deux"))
        self.assertTrue(self.lifecycle.delete("project-01", "dyn-01"))
        self.assertIsNone(self.store.get("project-01", "dyn-01"))
        self.assertIsNotNone(self.store.get("project-01", "dyn-02"))

    def test_corrupt_file_is_recovered_as_empty_store(self):
        with open(self.path, "w") as handle:
            handle.write("not-json")
        self.assertEqual(self.store.list("project-01"), [])

    def test_future_schema_is_rejected(self):
        with open(self.path, "w") as handle:
            handle.write('{"schema_version": 999, "projects": {}}')
        with self.assertRaises(ValueError):
            self.store.list("project-01")

    def test_replace_project_isolated_and_replaces_atomically(self):
        self.lifecycle.create("project-01", self._make_set("dyn-old"))
        self.store.replace_project("project-01", [self._make_set("dyn-new")])
        self.assertIsNone(self.store.get("project-01", "dyn-old"))
        self.assertIsNotNone(self.store.get("project-01", "dyn-new"))


if __name__ == "__main__":
    unittest.main()
