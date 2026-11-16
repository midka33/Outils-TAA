# -*- coding: utf-8 -*-
"""Contrats automatisables de la recette collaborative Export V1.2.

Ces tests couvrent la partie hors Revit de COLLAB-01 à COLLAB-11. Les points
qui exigent réellement deux processus Revit 2025.4 restent dans la recette
manuelle docs/28_Export_Recette_Collaborative_Revit.md.
"""
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from carnet_repository import CarnetRepository
from local_config_migration import (
    find_local_migration_candidate,
    import_local_configuration,
)
from project_storage_resolver import ProjectStorageResolver
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_settings import PublicationSettings
from shared_json_storage import (
    ConcurrentModificationError,
    SharedJsonStorage,
    StorageCorruptedError,
)


SHARED_ID = r"CENTRAL:\\serveur\projets\a\central.rvt"
LOCAL_ID = "EMBEDDED:local-project"


def storage(root, identity=SHARED_ID):
    target = root / "OutilsTAA"
    return SharedJsonStorage(
        str(target / "export.json"),
        str(target / "export.lock"),
        str(target / "backups"),
        identity,
        lock_timeout_seconds=0.10,
        lock_retry_seconds=0.01,
    )


def repository(root, identity=SHARED_ID):
    backend = storage(root, identity)
    return CarnetRepository(
        storage_path=backend.config_path,
        project_identity=identity,
        shared_storage=backend,
    )


def publication_settings():
    return PublicationSettings(
        pdf_enabled=True,
        pdf_mode="COMBINED",
        pdf_quality=600,
        dwg_enabled=True,
        dwg_setup_name="TAA_DWG",
        dwg_true_color=True,
        dwg_merge_views=True,
        output_directory=r"\\serveur\livrables",
        filename_template="{carnet}",
        dwg_filename_independent=True,
        dwg_filename_template="{numero} {nom}",
        separate_carnet_subfolder=True,
    )


def publication(set_id="plans", folder_id="dce"):
    return PublicationSet(
        "Plans",
        [
            PublicationItem(
                "uid-A101",
                101,
                "SHEET",
                "A101",
                "Plan RDC",
            ),
            PublicationItem(
                "uid-A102",
                102,
                "SHEET",
                "A102",
                "Plan R+1",
            ),
        ],
        set_id=set_id,
        folder_id=folder_id,
        persistent=True,
        publication_settings=publication_settings(),
    )


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_collab01_two_sessions_open_same_tree_and_settings(tmp_path):
    alice = repository(tmp_path / "server")
    alice.list_folders()
    alice.save_folder(
        PublicationFolder(
            "DCE",
            folder_id="dce",
            publication_settings=publication_settings(),
        )
    )
    alice.save(publication())

    # B ouvre après A : il doit charger le même état directement du serveur.
    bob = repository(tmp_path / "server")
    folders = bob.list_folders()
    sets = bob.list_all()

    assert [folder.id for folder in folders] == ["default", "dce"]
    assert [value.id for value in sets] == ["plans"]
    assert sets[0].publication_settings.pdf_mode == "COMBINED"
    assert sets[0].publication_settings.dwg_setup_name == "TAA_DWG"
    assert sets[0].publication_settings.dwg_filename_template == "{numero} {nom}"


def test_collab02_refresh_recovers_folder_and_moved_sheets(tmp_path):
    alice = repository(tmp_path / "server")
    bob = repository(tmp_path / "server")
    alice.list_folders()
    bob.list_folders()

    alice.save_folder(PublicationFolder("DCE", folder_id="dce"))
    alice.save_folder(PublicationFolder("Plans RDC", folder_id="rdc", parent_id="dce"))
    alice.save(publication(folder_id="dce"))

    assert alice.move_sheets_into_folder(
        [("plans", "uid-A101")],
        "rdc",
    )

    assert [folder.id for folder in bob.list_folders()] == ["default"]
    assert bob.has_external_change()

    bob.refresh()
    promoted = next(value for value in bob.list_all() if value.id == "rdc")
    assert [item.unique_id for item in promoted.items] == ["uid-A101"]


def test_collab03_empty_folder_and_subfolder_settings_survive_refresh(tmp_path):
    alice = repository(tmp_path / "server")
    bob = repository(tmp_path / "server")
    alice.list_folders()
    bob.list_folders()

    alice.save_folder(
        PublicationFolder(
            "DCE",
            folder_id="dce",
            publication_settings=PublicationSettings(
                pdf_enabled=True,
                pdf_mode="SEPARATE",
                output_directory=r"\\serveur\sorties",
            ),
        )
    )
    alice.save_folder(
        PublicationFolder(
            "Coupes",
            folder_id="coupes",
            parent_id="dce",
        )
    )

    bob.refresh()
    by_id = dict((folder.id, folder) for folder in bob.list_folders())

    assert "dce" in by_id
    assert "coupes" in by_id
    assert by_id["coupes"].parent_id == "dce"
    assert by_id["dce"].publication_settings.pdf_mode == "SEPARATE"
    assert bob.list_all() == []


def test_collab04_dwg_naming_and_combined_pdf_are_shared(tmp_path):
    alice = repository(tmp_path / "server")
    alice.list_folders()
    alice.save_folder(PublicationFolder("DCE", folder_id="dce"))
    alice.save(publication())

    bob = repository(tmp_path / "server")
    value = bob.list_all()[0]
    settings = value.publication_settings

    assert settings.pdf_mode == "COMBINED"
    assert settings.dwg_enabled is True
    assert settings.dwg_filename_independent is True
    assert settings.dwg_filename_template == "{numero} {nom}"
    assert settings.dwg_merge_views is True


def test_collab05_stale_writer_is_blocked_then_can_refresh(tmp_path):
    alice = repository(tmp_path / "server")
    bob = repository(tmp_path / "server")
    alice.list_folders()
    bob.list_folders()

    alice.save_folder(PublicationFolder("DCE", folder_id="dce"))

    with pytest.raises(ConcurrentModificationError):
        bob.save_folder(PublicationFolder("PRO", folder_id="pro"))

    bob.refresh()
    bob.save_folder(PublicationFolder("PRO", folder_id="pro"))

    alice.refresh()
    assert [folder.id for folder in alice.list_folders()] == [
        "default",
        "dce",
        "pro",
    ]


def test_collab06_corruption_never_resets_server_silently(tmp_path):
    backend = storage(tmp_path / "server")
    target = Path(backend.config_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{ broken json", encoding="utf-8")

    with pytest.raises(StorageCorruptedError):
        backend.read()

    assert target.read_text(encoding="utf-8") == "{ broken json"


def test_collab07_local_import_preserves_source_and_does_not_merge(tmp_path):
    local_path = tmp_path / "local" / "project.json"
    local_data = {
        "schema_version": 8,
        "project_identity": LOCAL_ID,
        "folders": [
            {
                "id": "default",
                "name": "Général",
                "parent_id": None,
                "persistent": True,
            },
            {
                "id": "dce",
                "name": "DCE",
                "parent_id": None,
                "persistent": True,
            },
        ],
        "sets": [],
    }
    write_json(local_path, local_data)
    before = local_path.read_text(encoding="utf-8")

    candidate = find_local_migration_candidate(
        [(str(local_path), LOCAL_ID)],
        SHARED_ID,
    )
    backend = storage(tmp_path / "server")
    backend.probe_access()
    import_local_configuration(candidate, backend)

    assert local_path.read_text(encoding="utf-8") == before
    shared = backend.read()
    assert shared["project_identity"] == SHARED_ID
    assert [folder["id"] for folder in shared["folders"]] == ["default", "dce"]


def test_collab08_different_centrals_never_share_configuration(tmp_path):
    id_a = r"CENTRAL:\\serveur\projets\a\central.rvt"
    id_b = r"CENTRAL:\\serveur\projets\b\central.rvt"
    repo_a = repository(tmp_path / "project-a", id_a)
    repo_b = repository(tmp_path / "project-b", id_b)

    repo_a.list_folders()
    repo_b.list_folders()
    repo_a.save_folder(PublicationFolder("DCE A", folder_id="a"))
    repo_b.save_folder(PublicationFolder("DCE B", folder_id="b"))

    assert [folder.id for folder in repo_a.list_folders()] == ["default", "a"]
    assert [folder.id for folder in repo_b.list_folders()] == ["default", "b"]


class FakeWorksharedDocument(object):
    IsWorkshared = True

    def __init__(self, central, local_path):
        self._central = central
        self.PathName = local_path

    def GetWorksharingCentralModelPath(self):
        return self._central


def test_collab09_two_local_copies_resolve_same_central_storage():
    central = r"\\serveur\projets\a\central.rvt"
    resolver = ProjectStorageResolver(model_path_converter=lambda value: value)

    alice = resolver.resolve(
        FakeWorksharedDocument(
            central,
            r"C:\Users\Alice\central_Alice.rvt",
        ),
        r"C:\local\alice.json",
    )
    bob = resolver.resolve(
        FakeWorksharedDocument(
            central,
            r"D:\RevitLocal\central_Bob.rvt",
        ),
        r"C:\local\bob.json",
    )

    assert alice.shared_config_path == bob.shared_config_path
    assert alice.project_identity == bob.project_identity


def test_collab10_repository_roundtrip_keeps_existing_export_contract(tmp_path):
    repo = repository(tmp_path / "server")
    repo.list_folders()
    repo.save_folder(PublicationFolder("DCE", folder_id="dce"))
    repo.save(publication())

    reopened = repository(tmp_path / "server")
    item = reopened.list_all()[0]
    settings = item.publication_settings

    assert [sheet.unique_id for sheet in item.items] == [
        "uid-A101",
        "uid-A102",
    ]
    assert settings.pdf_mode == "COMBINED"
    assert settings.pdf_enabled is True
    assert settings.dwg_enabled is True
    assert settings.dwg_setup_name == "TAA_DWG"
    assert settings.dwg_filename_template == "{numero} {nom}"


def test_collab11_collaborative_code_requires_no_admin_elevation():
    files = [
        PANEL / "services" / "project_storage_resolver.py",
        PANEL / "services" / "shared_json_storage.py",
        PANEL / "services" / "export_storage_bootstrap.py",
        PANEL / "services" / "local_config_migration.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    forbidden = (
        "runas",
        "shellexecute",
        "requireadministrator",
        "isuseranadmin",
        "programfiles",
        "hkey_local_machine",
    )
    for token in forbidden:
        assert token not in text
