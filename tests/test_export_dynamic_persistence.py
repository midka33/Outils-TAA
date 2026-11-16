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


class _FakeParameter(object):
    def __init__(self, value):
        self.value = value

    def AsString(self):
        return self.value

    def AsValueString(self):
        return self.value


class _FakeSheet(object):
    def __init__(self, uid, group):
        self.UniqueId = uid
        self.SheetNumber = uid
        self.Name = "Plan " + uid
        self.Id = type("Id", (), {"IntegerValue": len(uid)})()
        self.params = {"Phase": "PRO", "Groupe": group}

    def LookupParameter(self, name):
        value = self.params.get(name)
        return _FakeParameter(value) if value is not None else None


def _create_parent(repo):
    obj = PublicationSet(
        "PRO", items=[], source=PublicationSource(
            PublicationSource.DYNAMIC, "Phase", "PRO", "Groupe"),
        set_id="auto-pro", persistent=True, folder_id="default")
    repo.save(obj)
    return obj


def test_one_group_freezes_and_others_remain_dynamic(tmp_path):
    from dynamic_sheet_groups import resolve_dynamic
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    parent = _create_parent(repo)
    a = _FakeSheet("A101", "A")
    b = _FakeSheet("B101", "B")
    direct, groups = resolve_dynamic(parent, [a, b])
    assert not direct and len(groups) == 2
    frozen = next(group for group in groups if group.name == "A")
    assert repo.freeze_dynamic_group(parent.id, frozen) is True

    reloaded = CarnetRepository(str(tmp_path / "publication.json"))
    root = reloaded.get(parent.id)
    assert root.source.mode == PublicationSource.DYNAMIC
    assert root.source.frozen_group_ids == [frozen.id]
    saved = reloaded.get(frozen.id)
    assert saved.folder_id == parent.id
    assert saved.source.mode == PublicationSource.MANUAL
    assert [item.unique_id for item in saved.items] == ["A101"]

    # La feuille existante A change de groupe et une nouvelle feuille A
    # apparaît : le dossier figé reste intact, B continue à se mettre à jour.
    a.params["Groupe"] = "C"
    new_b = _FakeSheet("B102", "B")
    new_a = _FakeSheet("A102", "A")
    _, remaining = resolve_dynamic(root, [a, b, new_b, new_a])
    assert [group.name for group in remaining] == ["B", "C"]
    assert [item.unique_id for item in remaining[0].items] == ["B101", "B102"]
    assert [item.unique_id for item in reloaded.get(frozen.id).items] == ["A101"]

    # Une conversion ultérieure de l'ensemble ne doit pas recréer A en double.
    assert reloaded.freeze_dynamic(root, [], remaining) is True
    assert reloaded.get(parent.id).source.mode == PublicationSource.MANUAL
    assert reloaded.get(frozen.id) is not None
    all_children = [item for item in reloaded.list_all()
                    if item.folder_id == parent.id]
    assert len(all_children) == 3
    assert len({item.id for item in all_children}) == 3


def test_freeze_same_group_twice_does_not_write_duplicates(tmp_path):
    from dynamic_sheet_groups import resolve_dynamic
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    parent = _create_parent(repo)
    selected = resolve_dynamic(parent, [_FakeSheet("A101", "A")])[1][0]
    assert repo.freeze_dynamic_group(parent.id, selected) is True
    try:
        repo.freeze_dynamic_group(parent.id, selected)
    except ValueError as exc:
        assert "déjà figé" in str(exc)
    else:
        raise AssertionError("Un groupe figé ne peut pas être enregistré deux fois.")
    assert sum(str(item.id) == str(selected.id)
               for item in repo.list_all()) == 1


def test_empty_group_identifier_is_not_literal_sans_valeur(tmp_path):
    from dynamic_sheet_groups import group_identifier, resolve_dynamic
    assert group_identifier("root", None) != group_identifier("root", "Sans valeur")
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    parent = _create_parent(repo)
    # Le groupe vide est volontairement représenté par None.
    empty = _FakeSheet("A000", "")
    literal = _FakeSheet("A001", "Sans valeur")
    direct, groups = resolve_dynamic(parent, [empty, literal])
    assert len(groups) == 2
    assert len(set(item.id for item in groups)) == 2
    frozen_empty = next(g for g in groups
                        if g.dynamic_group_key is None)
    repo.freeze_dynamic_group(parent.id, frozen_empty)
    _, remaining = resolve_dynamic(repo.get(parent.id), [empty, literal])
    assert len(remaining) == 1
    assert remaining[0].dynamic_group_key == "Sans valeur"


def test_frozen_exclusion_survives_regular_parent_save(tmp_path):
    from dynamic_sheet_groups import resolve_dynamic
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    parent = _create_parent(repo)
    sheets = [_FakeSheet("A101", "A"), _FakeSheet("B101", "B")]
    frozen = resolve_dynamic(parent, sheets)[1][0]
    assert repo.freeze_dynamic_group(parent.id, frozen)
    reloaded_parent = repo.get(parent.id)
    reloaded_parent.name = "PRO actualisé"
    repo.save(reloaded_parent)

    second_session = CarnetRepository(str(tmp_path / "publication.json"))
    new_parent = second_session.get(parent.id)
    assert new_parent.name == "PRO actualisé"
    assert new_parent.source.frozen_group_ids == [frozen.id]
    _, automatic_children = resolve_dynamic(new_parent, sheets)
    assert [item.name for item in automatic_children] == ["B"]
    assert second_session.get(frozen.id) is not None
