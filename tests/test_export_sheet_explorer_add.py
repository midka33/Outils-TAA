# -*- coding: utf-8 -*-
"""Ajout depuis l'explorateur Revit : copier, ne jamais déplacer."""
import sys
from pathlib import Path

PANEL = Path(__file__).resolve().parents[1] / "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

import pytest
from carnet_repository import CarnetRepository
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from publication_set import PublicationSet


def _repo(tmp_path):
    repo = CarnetRepository(str(tmp_path / "export.json"))
    repo.save_folder(PublicationFolder("DCE", folder_id="dce", parent_id=None))
    repo.save_folder(PublicationFolder("Plans", folder_id="plans", parent_id="dce"))
    repo.save_folder(PublicationFolder("PRO", folder_id="pro", parent_id="dce"))
    source = PublicationSet("Source", [PublicationItem("a", 1, "SHEET", "A101", "RDC")],
                            set_id="source", folder_id="dce", persistent=True)
    repo.save(source)
    return repo


def _item(uid, number):
    return PublicationItem(uid, 1, "SHEET", number, number)


def test_add_preserves_source_and_promotes_folder(tmp_path):
    repo = _repo(tmp_path)
    assert repo.add_sheets_to_folder([_item("a", "A101"), _item("b", "A102")], "plans") == (2, 0)
    assert [i.unique_id for i in next(s for s in repo.list_all() if s.id == "source").items] == ["a"]
    target = next(s for s in repo.list_all() if s.id == "plans")
    assert [i.unique_id for i in target.items] == ["a", "b"]
    assert target.folder_id == "dce"
    assert not any(f.id == "plans" for f in repo.list_folders())


def test_duplicate_in_same_folder_ignored_other_folder_allowed(tmp_path):
    repo = _repo(tmp_path)
    assert repo.add_sheets_to_folder([_item("a", "A101")], "plans") == (1, 0)
    assert repo.add_sheets_to_folder([_item("a", "A101"), _item("b", "A102")], "plans") == (1, 1)
    assert repo.add_sheets_to_folder([_item("a", "A101")], "pro") == (1, 0)
    assert [i.unique_id for i in next(s for s in repo.list_all() if s.id == "plans").items] == ["a", "b"]


def test_invalid_destination_does_not_write(tmp_path):
    repo = _repo(tmp_path)
    with pytest.raises(ValueError, match="valide"):
        repo.add_sheets_to_folder([_item("a", "A101")], "missing")
    with pytest.raises(ValueError, match="racine"):
        repo.add_sheets_to_folder([_item("a", "A101")], "default")
    assert any(f.id == "plans" for f in repo.list_folders())


def test_root_folder_message_names_the_real_cause(tmp_path):
    # Le dossier racine est un identifiant connu : l'erreur doit nommer la
    # règle métier, pas laisser croire à une cible inconnue.
    repo = _repo(tmp_path)
    with pytest.raises(ValueError) as excinfo:
        repo.add_sheets_to_folder([_item("a", "A101")], "default")
    assert "Général" in str(excinfo.value)


def test_reopen_keeps_added_sheets_and_folder_children(tmp_path):
    repo = _repo(tmp_path)
    repo.save_folder(PublicationFolder("Sous dossier", folder_id="child", parent_id="plans"))
    repo.add_sheets_to_folder([_item("a", "A101")], "plans")
    reopened = CarnetRepository(repo.storage_path)
    assert [i.unique_id for i in next(s for s in reopened.list_all() if s.id == "plans").items] == ["a"]
    assert next(f for f in reopened.list_folders() if f.id == "child").parent_id == "plans"



def test_root_level_folder_remains_root_after_first_sheet(tmp_path):
    """Un dossier placé hors Général doit rester à la racine après ajout."""
    repo = _repo(tmp_path)
    repo.save_folder(PublicationFolder(
        "Dossier indépendant", folder_id="independent", parent_id=None))
    assert repo.add_sheets_to_folder(
        [_item("root-a", "A301")], "independent") == (1, 0)
    promoted = next(value for value in repo.list_all()
                    if value.id == "independent")
    assert promoted.folder_id is None
    assert [item.unique_id for item in promoted.items] == ["root-a"]
    assert not any(value.id == "independent" for value in repo.list_folders())

    reopened = CarnetRepository(repo.storage_path)
    persisted = next(value for value in reopened.list_all()
                     if value.id == "independent")
    assert persisted.folder_id is None
    assert len(persisted.items) == 1


def test_root_level_published_folder_is_rendered():
    """Contrat structurel : l'arbre affiche les dossiers publiables racine."""
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert "roots = container_children(None)" in source
    assert 'populate(kind, value, node, set())' in source
