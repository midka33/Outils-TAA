# -*- coding: utf-8 -*-
"""Régressions JSON et conversion dynamique -> manuel, hors Revit."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for path in (PANEL / "models", PANEL / "services"):
    sys.path.insert(0, str(path))

from carnet_repository import CarnetRepository
from publication_set import PublicationSet
from publication_source import PublicationSource
from publication_item import PublicationItem


def test_rule_roundtrips_with_legacy_schema(tmp_path):
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    dynamic = PublicationSet(
        "DEP", items=[], source=PublicationSource(
            PublicationSource.DYNAMIC, "Carnet", "A5000", "Sous-carnet"),
        set_id="dyn-parent", persistent=True, folder_id="default")
    repo.save(dynamic)
    loaded = repo.get("dyn-parent")
    assert loaded.source.mode == PublicationSource.DYNAMIC
    assert loaded.source.parameter_name == "Carnet"
    assert loaded.source.parameter_value == "A5000"
    assert loaded.source.group_parameter == "Sous-carnet"
    import json
    data = json.loads((tmp_path / "publication.json").read_text())
    assert data["schema_version"] == 8


def test_freeze_preserves_identifiers_and_creates_fixed_children(tmp_path):
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    root = PublicationSet(
        "DEP", source=PublicationSource(
            PublicationSource.DYNAMIC, "Carnet", "DEP", "Zone"),
        set_id="root", persistent=True, folder_id="default")
    repo.save(root)
    manual = PublicationSet("Manuel", items=[], source=PublicationSource(
        PublicationSource.MANUAL), set_id="manual", persistent=True)
    repo.save(manual)
    items = [PublicationItem("uid-A", 12, "SHEET", "A101", "Plan A")]
    group = PublicationSet("Zone A", items=items,
                           source=PublicationSource(PublicationSource.MANUAL),
                           set_id="dyn-root-zone", persistent=False,
                           folder_id="root")
    assert repo.freeze_dynamic(root, [], [group]) is True
    loaded = repo.get("root")
    assert loaded.source.mode == PublicationSource.MANUAL
    assert loaded.id == "root"
    child = repo.get("dyn-root-zone")
    assert child.folder_id == "root"
    assert [x.unique_id for x in child.items] == ["uid-A"]
    assert repo.get("manual") is not None


def test_freeze_cannot_repeat_or_misidentify(tmp_path):
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    source = PublicationSet("Auto", source=PublicationSource(
        PublicationSource.DYNAMIC, "P", "V"), set_id="p",
        persistent=True)
    repo.save(source)
    repo.freeze_dynamic(source, [], [])
    try:
        repo.freeze_dynamic(source, [], [])
    except ValueError as exc:
        assert "plus automatique" in str(exc)
    else:
        raise AssertionError("La conversion ne doit pas être répétée")


def test_legacy_source_without_group_loads(tmp_path):
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    obj = PublicationSet("Ancien", source=PublicationSource(
        PublicationSource.MANUAL), set_id="legacy", persistent=True)
    repo.save(obj)
    import json
    path = tmp_path / "publication.json"
    data = json.loads(path.read_text())
    for entry in data["sets"]:
        entry["source"].pop("group_parameter", None)
    path.write_text(json.dumps(data))
    loaded = repo.get("legacy")
    assert loaded.source.group_parameter is None
