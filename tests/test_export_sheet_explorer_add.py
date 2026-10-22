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
    with pytest.raises(ValueError):
        repo.add_sheets_to_folder([_item("a", "A101")], "missing")
    with pytest.raises(ValueError):
        repo.add_sheets_to_folder([_item("a", "A101")], "default")
    assert any(f.id == "plans" for f in repo.list_folders())


def test_reopen_keeps_added_sheets_and_folder_children(tmp_path):
    repo = _repo(tmp_path)
    repo.save_folder(PublicationFolder("Sous dossier", folder_id="child", parent_id="plans"))
    repo.add_sheets_to_folder([_item("a", "A101")], "plans")
    reopened = CarnetRepository(repo.storage_path)
    assert [i.unique_id for i in next(s for s in reopened.list_all() if s.id == "plans").items] == ["a"]
    assert next(f for f in reopened.list_folders() if f.id == "child").parent_id == "plans"
