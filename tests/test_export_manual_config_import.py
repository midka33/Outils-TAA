# -*- coding: utf-8 -*-
"""Import volontaire d'une configuration tierce à la création d'un central."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from manual_config_import import (
    ManualImportError,
    prepare_manual_import,
    create_shared_from_manual_import,
)
from shared_json_storage import ConcurrentModificationError, SharedJsonStorage

TARGET_ID = r"CENTRAL:\\server\project\new.rvt"
SOURCE_ID = r"CENTRAL:\\server\old\former.rvt"


def source(tmp_path, encoding="utf-8"):
    path = tmp_path / "former" / "export.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 8,
        "project_identity": SOURCE_ID,
        "storage_revision": 27,
        "last_write_id": "old-write",
        "folders": [
            {"id": "default", "name": "Général", "parent_id": None},
            {"id": "dce", "name": "DCE — Façades", "parent_id": None,
             "publication_settings": {"pdf_enabled": True}},
        ],
        "sets": [{
            "id": "plans", "name": "Plans", "folder_id": "dce",
            "items": [
                {"unique_id": "sheet-1", "sheet_name": "Plan RDC"},
                {"unique_id": "obsolete", "sheet_name": "Ancien plan"},
            ],
        }],
    }
    path.write_bytes(json.dumps(data, ensure_ascii=False).encode(encoding))
    return path


def storage(tmp_path):
    root = tmp_path / "new" / "OutilsTAA" / "new_hash"
    backend = SharedJsonStorage(
        str(root / "export.json"), str(root / "export.lock"),
        str(root / "backups"), TARGET_ID,
        lock_timeout_seconds=0.1, lock_retry_seconds=0.01,
    )
    backend.probe_access()
    return backend


@pytest.mark.parametrize("encoding", ["cp1252", "utf-8", "utf-8-sig"])
def test_import_foreign_central_keeps_settings_only_matching_sheets(tmp_path, encoding):
    path = source(tmp_path, encoding)
    original = path.read_bytes()
    preview = prepare_manual_import(str(path), TARGET_ID, ["sheet-1"])

    assert preview["folder_count"] == 1
    assert preview["publication_count"] == 1
    assert preview["source_sheet_count"] == 2
    assert preview["matching_sheet_count"] == 1
    assert preview["payload"]["project_identity"] == TARGET_ID
    assert "storage_revision" not in preview["payload"]
    assert preview["payload"]["folders"][1]["name"] == "DCE — Façades"
    assert preview["payload"]["sets"][0]["items"] == [
        {"unique_id": "sheet-1", "sheet_name": "Plan RDC"}
    ]

    backend = storage(tmp_path)
    result = create_shared_from_manual_import(preview, backend)
    assert result["storage_revision"] == 1
    assert result["folders"][1]["publication_settings"]["pdf_enabled"]
    assert result["sets"][0]["items"][0]["unique_id"] == "sheet-1"
    assert path.read_bytes() == original


def test_import_from_completely_other_project_keeps_folders_but_no_sheets(tmp_path):
    preview = prepare_manual_import(
        str(source(tmp_path)), TARGET_ID, ["not-in-source"],
    )
    assert preview["matching_sheet_count"] == 0
    assert preview["payload"]["sets"][0]["items"] == []


def test_refuse_older_import_after_another_user_created_shared_json(tmp_path):
    preview = prepare_manual_import(
        str(source(tmp_path)), TARGET_ID, ["sheet-1"],
    )
    backend = storage(tmp_path)
    backend.write({
        "schema_version": 8, "project_identity": TARGET_ID,
        "folders": [{"id": "other-user", "name": "Protected"}],
        "sets": [],
    })
    with pytest.raises(ConcurrentModificationError):
        create_shared_from_manual_import(preview, backend)
    assert backend.read()["folders"][0]["id"] == "other-user"


def test_invalid_json_and_future_schema_are_refused(tmp_path):
    path = source(tmp_path)
    path.write_text("{ invalid json", encoding="utf-8")
    with pytest.raises(ManualImportError):
        prepare_manual_import(str(path), TARGET_ID, [])
    path.write_text(
        json.dumps({"schema_version": 99, "folders": [], "sets": []}),
        encoding="utf-8",
    )
    with pytest.raises(ManualImportError):
        prepare_manual_import(str(path), TARGET_ID, [])


def test_xaml_button_and_window_handler_exist():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")
    window = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert 'x:Name="StorageImportButton"' in xaml
    assert 'Click="StorageImport_Click"' in xaml
    assert "def StorageImport_Click(" in window
    assert "not os.path.exists(target)" in window
    assert "create_shared_from_manual_import(preview, storage)" in window
