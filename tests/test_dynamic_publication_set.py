# -*- coding: utf-8 -*-

import unittest

from models.dynamic_publication_set import DynamicPublicationSet, DynamicPublicationSetSerializer
from services.dynamic_publication_set_manager import DynamicPublicationSetManager
from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition


class DynamicPublicationSetTests(unittest.TestCase):

    def _make_set(self, set_id="dyn-01"):
        rule = DynamicRule("discipline", "equals", "Architecture")
        definition = DynamicRuleDefinition(
            root=DynamicRuleGroup("all", [rule]),
            exclusions=["sheet-excluded"],
            name="Architecture",
        )
        return DynamicPublicationSet(
            name="Carnet Architecture",
            set_id=set_id,
            folder_id="folder-01",
            output_directory="C:/Exports",
            filename_template_id="template-01",
            publication_settings={"pdf": True, "dwg": True},
            rule_definition=definition,
            exclusions=["sheet-excluded"],
            snapshot_key="project-01:carnet-01",
        )

    def test_roundtrip(self):
        source = self._make_set()
        data = DynamicPublicationSetSerializer.serialize(source)
        restored = DynamicPublicationSetSerializer.deserialize(data)
        self.assertEqual(restored.name, source.name)
        self.assertEqual(restored.id, source.id)
        self.assertTrue(restored.is_dynamic)
        self.assertEqual(restored.rule_definition.name, "Architecture")
        self.assertEqual(restored.rule_definition.root.children[0].field, "discipline")
        self.assertEqual(restored.exclusions, ["sheet-excluded"])

    def test_manual_set_has_no_dynamic_definition(self):
        item = DynamicPublicationSet("Manuel", set_id="manual-01", set_type="manual")
        self.assertTrue(item.is_manual)
        self.assertFalse(item.is_dynamic)
        self.assertIsNone(item.rule_definition)
        self.assertEqual(item.validate(), [])

    def test_invalid_dynamic_set_is_rejected(self):
        item = DynamicPublicationSet("Invalide", set_id="dyn-01")
        with self.assertRaises(ValueError):
            DynamicPublicationSetSerializer.serialize(item)

    def test_unknown_future_schema_is_rejected(self):
        data = self._make_set().to_dict()
        data["schema_version"] = 999
        with self.assertRaises(ValueError):
            DynamicPublicationSetSerializer.deserialize(data)

    def test_legacy_schema_is_migrated(self):
        data = self._make_set().to_dict()
        data.pop("schema_version")
        restored = DynamicPublicationSetSerializer.deserialize(data)
        self.assertEqual(restored.SCHEMA_VERSION, 1)
        self.assertTrue(restored.is_dynamic)

    def test_duplicate_creates_independent_configuration(self):
        manager = DynamicPublicationSetManager([self._make_set()])
        copy = manager.duplicate("dyn-01", "dyn-02")
        copy.name = "Copie modifiée"
        copy.rule_definition.name = "Nouvelle règle"
        source = manager.get("dyn-01")
        self.assertEqual(source.name, "Carnet Architecture")
        self.assertEqual(source.rule_definition.name, "Architecture")

    def test_manager_crud_and_duplicate_id(self):
        manager = DynamicPublicationSetManager()
        manager.add(self._make_set())
        self.assertIsNotNone(manager.get("dyn-01"))
        with self.assertRaises(ValueError):
            manager.add(self._make_set())
        updated = self._make_set()
        updated.name = "Carnet modifié"
        manager.update(updated)
        self.assertEqual(manager.get("dyn-01").name, "Carnet modifié")
        self.assertTrue(manager.delete("dyn-01"))
        self.assertFalse(manager.delete("dyn-01"))

    def test_manager_load_and_serialize_all(self):
        manager = DynamicPublicationSetManager([self._make_set()])
        data = manager.serialize_all()
        restored_manager = DynamicPublicationSetManager()
        restored_manager.load_all(data)
        self.assertEqual(len(restored_manager.list()), 1)
        self.assertEqual(restored_manager.get("dyn-01").name, "Carnet Architecture")


if __name__ == "__main__":
    unittest.main()
