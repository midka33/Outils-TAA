# -*- coding: utf-8 -*-
"""Regression: dropping sheet(s) on a freshly created empty folder."""
import json
import sys
from pathlib import Path

PANEL = Path(__file__).resolve().parents[1] / "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from carnet_repository import CarnetRepository
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from publication_set import PublicationSet


def _fixture(tmp_path):
    repo = CarnetRepository(str(tmp_path / "publisher.json"))
    repo.save_folder(PublicationFolder("DCE", folder_id="dce", parent_id=None))
    repo.save_folder(PublicationFolder("PDF", folder_id="pdf", parent_id="dce"))
    repo.save_folder(PublicationFolder("Sous-dossier", folder_id="nested", parent_id="pdf"))
    source = PublicationSet(
        "A1100", [
            PublicationItem("uid-rdc", 1, "SHEET", "A1100", "RDC"),
            PublicationItem("uid-r1", 2, "SHEET", "A1101", "R+1"),
        ],
        set_id="a1100", folder_id="dce", persistent=True,
    )
    repo.save(source)
    return repo


def test_sheet_drop_into_empty_folder_preserves_subfolders(tmp_path):
    repo = _fixture(tmp_path)
    assert repo.move_sheets_into_folder([("a1100", "uid-rdc")], "pdf")
    assert all(f.id != "pdf" for f in repo.list_folders())
    destination = next(s for s in repo.list_all() if s.id == "pdf")
    assert destination.name == "PDF"
    assert destination.folder_id == "dce"
    assert [i.unique_id for i in destination.items] == ["uid-rdc"]
    assert next(f for f in repo.list_folders() if f.id == "nested").parent_id == "pdf"
    assert [i.unique_id for i in next(s for s in repo.list_all() if s.id == "a1100").items] == ["uid-r1"]
    # Reload from disk; migration must remain stable.
    reopened = CarnetRepository(repo.storage_path)
    assert [i.unique_id for i in next(s for s in reopened.list_all() if s.id == "pdf").items] == ["uid-rdc"]
    assert json.loads(Path(repo.storage_path).read_text(encoding="utf-8"))["schema_version"] == 8


def test_multiple_sheet_drop_preserves_order(tmp_path):
    repo = _fixture(tmp_path)
    assert repo.move_sheets_into_folder(
        [("a1100", "uid-r1"), ("a1100", "uid-rdc")], "pdf"
    )
    destination = next(s for s in repo.list_all() if s.id == "pdf")
    assert [i.unique_id for i in destination.items] == ["uid-r1", "uid-rdc"]


def test_invalid_sheet_drop_does_not_promote_folder(tmp_path):
    repo = _fixture(tmp_path)
    assert not repo.move_sheets_into_folder([("a1100", "missing")], "pdf")
    assert any(f.id == "pdf" for f in repo.list_folders())
    assert not any(s.id == "pdf" for s in repo.list_all())
