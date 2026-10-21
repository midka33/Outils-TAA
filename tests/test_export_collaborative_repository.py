# -*- coding: utf-8 -*-
"""Repository Export raccordé au stockage collaboratif révisionné."""
import ast
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from carnet_repository import CarnetRepository
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from publication_set import PublicationSet
from shared_json_storage import (
    ConcurrentModificationError,
    SharedJsonStorage,
)


IDENTITY = r"CENTRAL:\\serveur\projets\a\central.rvt"


def shared_repository(tmp_path):
    root = tmp_path / "OutilsTAA"
    storage = SharedJsonStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        IDENTITY,
        lock_timeout_seconds=0.10,
        lock_retry_seconds=0.01,
    )
    return CarnetRepository(
        storage_path=storage.config_path,
        project_identity=IDENTITY,
        shared_storage=storage,
    )


def publication(set_id="plans", folder_id="default"):
    return PublicationSet(
        "Plans",
        [
            PublicationItem(
                "uid-1",
                1,
                "SHEET",
                "A101",
                "Plan niveau 1",
            ),
        ],
        set_id=set_id,
        folder_id=folder_id,
        persistent=True,
    )


def test_shared_repository_initial_read_establishes_revision_zero(tmp_path):
    repo = shared_repository(tmp_path)

    folders = repo.list_folders()

    assert [folder.id for folder in folders] == ["default"]
    assert repo.uses_shared_storage
    assert repo.storage_revision == 0
    assert not (tmp_path / "OutilsTAA" / "export.json").exists()


def test_first_repository_mutation_creates_shared_schema8(tmp_path):
    repo = shared_repository(tmp_path)
    repo.list_folders()

    repo.save_folder(
        PublicationFolder(
            "DCE",
            folder_id="dce",
            parent_id=None,
        )
    )

    assert repo.storage_revision == 1
    assert [folder.id for folder in repo.list_folders()] == [
        "default",
        "dce",
    ]

    data = repo.shared_storage.read()
    assert data["schema_version"] == 8
    assert data["storage_revision"] == 1
    assert data["project_identity"] == IDENTITY


def test_two_open_repositories_refuse_silent_overwrite(tmp_path):
    alice = shared_repository(tmp_path)
    bob = shared_repository(tmp_path)

    alice.list_folders()
    bob.list_folders()

    alice.save_folder(
        PublicationFolder("DCE", folder_id="dce", parent_id=None)
    )

    with pytest.raises(ConcurrentModificationError):
        bob.save_folder(
            PublicationFolder("PRO", folder_id="pro", parent_id=None)
        )

    alice.refresh()
    assert [folder.id for folder in alice.list_folders()] == [
        "default",
        "dce",
    ]


def test_refresh_then_retry_preserves_both_users_changes(tmp_path):
    alice = shared_repository(tmp_path)
    bob = shared_repository(tmp_path)

    alice.list_folders()
    bob.list_folders()

    alice.save_folder(
        PublicationFolder("DCE", folder_id="dce", parent_id=None)
    )

    with pytest.raises(ConcurrentModificationError):
        bob.save_folder(
            PublicationFolder("PRO", folder_id="pro", parent_id=None)
        )

    bob.refresh()
    bob.save_folder(
        PublicationFolder("PRO", folder_id="pro", parent_id=None)
    )

    alice.refresh()
    assert [folder.id for folder in alice.list_folders()] == [
        "default",
        "dce",
        "pro",
    ]
    assert alice.storage_revision == 2


def test_external_change_is_visible_without_implicit_refresh(tmp_path):
    alice = shared_repository(tmp_path)
    bob = shared_repository(tmp_path)

    alice.list_folders()
    bob.list_folders()

    alice.save_folder(
        PublicationFolder("DCE", folder_id="dce", parent_id=None)
    )

    # La vue de Bob reste volontairement sur la révision qu'il a chargée :
    # le conflit doit être explicite et non masqué par une lecture automatique.
    assert [folder.id for folder in bob.list_folders()] == ["default"]
    assert bob.has_external_change()

    bob.refresh()
    assert [folder.id for folder in bob.list_folders()] == [
        "default",
        "dce",
    ]
    assert not bob.has_external_change()


def test_save_delete_move_and_sheet_promotion_use_shared_mutations(tmp_path):
    repo = shared_repository(tmp_path)
    repo.list_folders()

    repo.save_folder(
        PublicationFolder("DCE", folder_id="dce", parent_id=None)
    )
    repo.save_folder(
        PublicationFolder("PDF", folder_id="pdf", parent_id="dce")
    )
    repo.save(publication(folder_id="dce"))

    assert repo.move_sheets_into_folder(
        [("plans", "uid-1")],
        "pdf",
    )
    promoted = next(
        value for value in repo.list_all()
        if value.id == "pdf"
    )
    assert [item.unique_id for item in promoted.items] == ["uid-1"]

    assert repo.move_set("pdf", "dce")
    assert repo.delete("plans")
    assert repo.delete("pdf")
    assert repo.delete_folder("dce")
    assert repo.storage_revision == 8


def test_invalid_mutation_does_not_increment_shared_revision(tmp_path):
    repo = shared_repository(tmp_path)
    repo.list_folders()
    repo.save_folder(
        PublicationFolder("DCE", folder_id="dce", parent_id=None)
    )
    revision = repo.storage_revision

    assert not repo.delete_folder("missing")
    assert repo.storage_revision == revision


def test_repository_source_routes_direct_mutators_through_mutate():
    path = PANEL / "services" / "carnet_repository.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "CarnetRepository"
    )

    expected = {
        "save",
        "save_folder",
        "move_tree_nodes",
        "move_sheets_into_folder",
        "delete",
        "delete_folder",
    }

    for node in cls.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name not in expected:
            continue
        calls = [
            child
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
        ]
        assert any(
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "_mutate"
            for call in calls
        ), node.name
