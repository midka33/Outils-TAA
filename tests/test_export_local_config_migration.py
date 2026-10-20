# -*- coding: utf-8 -*-
"""Migration locale explicite vers le stockage collaboratif Export."""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from local_config_migration import (
    LocalConfigurationIdentityMismatchError,
    find_local_migration_candidate,
    has_meaningful_project_data,
    import_local_configuration,
    mark_declined,
)
from shared_json_storage import ConcurrentModificationError, SharedJsonStorage


LOCAL_ID = "EMBEDDED:local-project"
SHARED_ID = r"CENTRAL:\\serveur\projets\a\central.rvt"


def local_data(extra_folder=True):
    folders = [{
        "id": "default",
        "name": "Général",
        "parent_id": None,
        "persistent": True,
        "sort_order": 0,
        "tree_order": 0,
    }]
    if extra_folder:
        folders.append({
            "id": "dce",
            "name": "DCE",
            "parent_id": None,
            "persistent": True,
            "sort_order": 1,
            "tree_order": 1,
            "publication_settings": {
                "pdf_enabled": True,
                "dwg_enabled": True,
                "filename_template": "{numero} {nom}",
            },
        })
    return {
        "schema_version": 8,
        "project_identity": LOCAL_ID,
        "folders": folders,
        "sets": [{
            "id": "plans",
            "name": "Plans",
            "folder_id": "dce",
            "persistent": True,
            "sort_order": 0,
            "tree_order": 0,
            "source": {
                "mode": "MANUAL",
                "parameter_name": None,
                "parameter_value": None,
            },
            "items": [{
                "unique_id": "uid-1",
                "sheet_id": 1,
                "item_type": "SHEET",
                "sheet_number": "A101",
                "sheet_name": "Plan RDC",
                "parameter_value": None,
            }],
        }],
    }


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def shared_storage(tmp_path):
    root = tmp_path / "server" / "OutilsTAA"
    return SharedJsonStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        SHARED_ID,
        lock_timeout_seconds=0.10,
        lock_retry_seconds=0.01,
    )


def test_empty_default_local_configuration_is_not_offered(tmp_path):
    path = tmp_path / "local.json"
    write_json(path, {
        "schema_version": 8,
        "project_identity": LOCAL_ID,
        "folders": [{
            "id": "default",
            "name": "Général",
            "parent_id": None,
            "persistent": True,
        }],
        "sets": [],
    })

    candidate = find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID,
    )

    assert candidate is None


def test_default_folder_settings_are_meaningful_even_without_sets():
    assert has_meaningful_project_data({
        "folders": [{
            "id": "default",
            "name": "Général",
            "publication_settings": {
                "pdf_quality": 600,
            },
        }],
        "sets": [],
    })


def test_local_configuration_is_detected_and_summarized(tmp_path):
    path = tmp_path / "local.json"
    write_json(path, local_data())

    candidate = find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID,
    )

    assert candidate is not None
    assert candidate.path == str(path)
    assert candidate.folder_count == 1
    assert candidate.publication_count == 1
    assert candidate.sheet_count == 1
    assert "1 dossier(s)" in candidate.summary()


def test_wrong_local_project_identity_is_never_offered(tmp_path):
    path = tmp_path / "local.json"
    data = local_data()
    data["project_identity"] = "EMBEDDED:another-project"
    write_json(path, data)

    with pytest.raises(LocalConfigurationIdentityMismatchError):
        find_local_migration_candidate(
            [(str(path), LOCAL_ID)],
            SHARED_ID,
        )


def test_legacy_unscoped_local_json_can_be_imported_from_scoped_filename(tmp_path):
    path = tmp_path / "local.json"
    data = local_data()
    data.pop("project_identity")
    write_json(path, data)

    candidate = find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID,
    )

    assert candidate is not None
    assert candidate.publication_count == 1


def test_decline_marker_suppresses_future_offer_for_same_shared_project(tmp_path):
    path = tmp_path / "local.json"
    write_json(path, local_data())

    candidate = find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID,
    )
    mark_declined(candidate)

    assert find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID,
    ) is None

    # Une autre cible partagée n'hérite pas du refus.
    assert find_local_migration_candidate(
        [(str(path), LOCAL_ID)],
        SHARED_ID + "-other",
    ) is not None


def test_import_preserves_local_and_creates_shared_revision_one(tmp_path):
    local_path = tmp_path / "local.json"
    original = local_data()
    write_json(local_path, original)
    original_text = local_path.read_text(encoding="utf-8")

    candidate = find_local_migration_candidate(
        [(str(local_path), LOCAL_ID)],
        SHARED_ID,
    )
    storage = shared_storage(tmp_path)
    storage.probe_access()

    payload = import_local_configuration(candidate, storage)

    assert payload["storage_revision"] == 1
    assert payload["project_identity"] == SHARED_ID
    assert payload["sets"][0]["items"][0]["unique_id"] == "uid-1"
    assert local_path.read_text(encoding="utf-8") == original_text

    disk = json.loads(
        Path(storage.config_path).read_text(encoding="utf-8")
    )
    assert disk["project_identity"] == SHARED_ID
    assert disk["storage_revision"] == 1


def test_existing_shared_configuration_always_wins_over_local(tmp_path):
    local_path = tmp_path / "local.json"
    write_json(local_path, local_data())
    candidate = find_local_migration_candidate(
        [(str(local_path), LOCAL_ID)],
        SHARED_ID,
    )

    storage = shared_storage(tmp_path)
    storage.read()
    storage.write({
        "schema_version": 8,
        "project_identity": SHARED_ID,
        "folders": [],
        "sets": [{
            "id": "server",
            "name": "Serveur",
            "items": [],
        }],
    })

    with pytest.raises(ConcurrentModificationError):
        import_local_configuration(candidate, storage)

    disk = json.loads(
        Path(storage.config_path).read_text(encoding="utf-8")
    )
    assert [item["id"] for item in disk["sets"]] == ["server"]


def test_shared_file_appearing_during_import_causes_conflict_not_merge(tmp_path):
    local_path = tmp_path / "local.json"
    write_json(local_path, local_data())
    candidate = find_local_migration_candidate(
        [(str(local_path), LOCAL_ID)],
        SHARED_ID,
    )

    root = tmp_path / "server" / "OutilsTAA"
    competitor = SharedJsonStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        SHARED_ID,
        lock_timeout_seconds=0.10,
        lock_retry_seconds=0.01,
    )

    class RacingStorage(SharedJsonStorage):
        def __init__(self, *args, **kwargs):
            SharedJsonStorage.__init__(self, *args, **kwargs)
            self._raced = False

        def read(self):
            result = SharedJsonStorage.read(self)
            if result is None and not self._raced:
                self._raced = True
                competitor.read()
                competitor.write({
                    "schema_version": 8,
                    "project_identity": SHARED_ID,
                    "folders": [],
                    "sets": [{
                        "id": "other-user",
                        "name": "Autre utilisateur",
                        "items": [],
                    }],
                })
            return result

    racing = RacingStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        SHARED_ID,
        lock_timeout_seconds=0.10,
        lock_retry_seconds=0.01,
    )
    racing.probe_access()

    with pytest.raises(ConcurrentModificationError):
        import_local_configuration(candidate, racing)

    disk = json.loads(
        Path(racing.config_path).read_text(encoding="utf-8")
    )
    assert [item["id"] for item in disk["sets"]] == ["other-user"]


def test_smartbutton_requires_explicit_confirmation_and_keeps_local_file():
    source = (
        PANEL / "Export.smartbutton" / "script.py"
    ).read_text(encoding="utf-8")

    assert "find_local_migration_candidate(" in source
    assert "Importer cette organisation" in source
    assert "yes=True" in source
    assert "no=True" in source
    assert "Le fichier local sera conservé." in source
    assert "mark_declined(candidate)" in source
    assert "import_local_configuration(candidate, shared_storage)" in source
    assert "aucun mélange automatique" in source.lower()
