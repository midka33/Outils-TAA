# -*- coding: utf-8 -*-
"""Sélection du stockage Export au lancement du module."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from export_storage_bootstrap import build_export_storage
from project_storage_resolver import StoragePaths
from shared_json_storage import (
    StorageCorruptedError,
    StorageUnavailableError,
)


LOCAL_ID = "EMBEDDED:local-project"
SHARED_ID = r"CENTRAL:\\serveur\projets\a\central.rvt"


class FakeResolver(object):
    def __init__(self, result):
        self.result = result
        self.calls = []

    def resolve(self, document, local_path):
        self.calls.append((document, local_path))
        return self.result


class FakeRepository(object):
    def __init__(
            self,
            storage_path,
            project_identity=None,
            shared_storage=None):
        self.storage_path = storage_path
        self.project_identity = project_identity
        self.shared_storage = shared_storage
        self.storage_revision = (
            getattr(shared_storage, "known_revision", None)
            if shared_storage is not None
            else None
        )


class GoodSharedStorage(object):
    def __init__(
            self,
            config_path,
            lock_path,
            backups_path,
            project_identity):
        self.config_path = config_path
        self.lock_path = lock_path
        self.backups_path = backups_path
        self.project_identity = project_identity
        self.known_revision = None
        self.probed = False

    def probe_access(self):
        self.probed = True
        self.known_revision = 4
        return {"storage_revision": 4}


class UnavailableSharedStorage(GoodSharedStorage):
    def probe_access(self):
        raise StorageUnavailableError("serveur hors ligne")


class CorruptedSharedStorage(GoodSharedStorage):
    def probe_access(self):
        raise StorageCorruptedError("json cassé")


def shared_paths():
    return StoragePaths(
        StoragePaths.MODE_SHARED,
        local_config_path=r"C:\local\fallback.json",
        central_path=r"\\serveur\projets\a\central.rvt",
        project_identity=SHARED_ID,
        shared_config_path=r"\\serveur\projets\a\OutilsTAA\export.json",
        shared_lock_path=r"\\serveur\projets\a\OutilsTAA\export.lock",
        shared_backups_path=r"\\serveur\projets\a\OutilsTAA\backups",
    )


def local_paths():
    return StoragePaths(
        StoragePaths.MODE_LOCAL,
        local_config_path=r"C:\local\candidate.json",
        warning="aucun central",
    )


def test_shared_central_uses_shared_repository_without_local_prepare():
    prepared = []

    context = build_export_storage(
        object(),
        r"C:\local\candidate.json",
        LOCAL_ID,
        resolver=FakeResolver(shared_paths()),
        shared_storage_factory=GoodSharedStorage,
        repository_factory=FakeRepository,
        prepare_local_callback=lambda: prepared.append(True),
    )

    assert context.is_shared
    assert context.project_identity == SHARED_ID
    assert context.repository.shared_storage.probed
    assert context.repository.shared_storage.known_revision == 4
    assert context.repository.storage_path.endswith("export.json")
    assert prepared == []


def test_unavailable_shared_storage_falls_back_locally_without_model_prepare():
    prepared = []

    context = build_export_storage(
        object(),
        r"C:\local\candidate.json",
        LOCAL_ID,
        resolver=FakeResolver(shared_paths()),
        shared_storage_factory=UnavailableSharedStorage,
        repository_factory=FakeRepository,
        prepare_local_callback=lambda: prepared.append(True),
    )

    assert not context.is_shared
    assert context.fallback_from_shared
    assert context.repository.storage_path == r"C:\local\candidate.json"
    assert context.project_identity == LOCAL_ID
    assert "secours" in context.warning
    # Central connu mais serveur indisponible : aucune préparation locale
    # historique susceptible d'écrire dans le document Revit.
    assert prepared == []


def test_nonshared_project_keeps_historical_local_prepare_callback():
    prepared = []

    def prepare():
        prepared.append(True)
        return r"C:\local\prepared.json", "EMBEDDED:prepared"

    context = build_export_storage(
        object(),
        r"C:\local\candidate.json",
        LOCAL_ID,
        resolver=FakeResolver(local_paths()),
        shared_storage_factory=GoodSharedStorage,
        repository_factory=FakeRepository,
        prepare_local_callback=prepare,
    )

    assert not context.is_shared
    assert not context.fallback_from_shared
    assert prepared == [True]
    assert context.repository.storage_path == r"C:\local\prepared.json"
    assert context.project_identity == "EMBEDDED:prepared"


def test_corrupted_shared_json_is_never_hidden_by_local_fallback():
    with pytest.raises(StorageCorruptedError):
        build_export_storage(
            object(),
            r"C:\local\candidate.json",
            LOCAL_ID,
            resolver=FakeResolver(shared_paths()),
            shared_storage_factory=CorruptedSharedStorage,
            repository_factory=FakeRepository,
        )


def test_smartbutton_wires_bootstrap_before_export_window():
    source = (
        PANEL / "Export.smartbutton" / "script.py"
    ).read_text(encoding="utf-8")

    assert "build_export_storage(" in source
    assert "storage_context.repository" in source
    assert "storage_context=storage_context" in source
    assert "prepare_local_callback=prepare_historical_local_storage" in source
    assert "Aucun basculement local automatique" in source


def test_fallback_context_can_retry_and_return_to_shared_mode():
    state = {"available": False}

    class RecoveringStorage(GoodSharedStorage):
        def probe_access(self):
            if not state["available"]:
                raise StorageUnavailableError("serveur hors ligne")
            self.known_revision = 7
            return {"storage_revision": 7}

    resolver = FakeResolver(shared_paths())
    context = build_export_storage(
        object(),
        r"C:\local\candidate.json",
        LOCAL_ID,
        resolver=resolver,
        shared_storage_factory=RecoveringStorage,
        repository_factory=FakeRepository,
    )

    assert context.fallback_from_shared
    assert not context.is_shared

    state["available"] = True
    recovered = context.retry()

    assert recovered.is_shared
    assert not recovered.fallback_from_shared
    assert recovered.repository.shared_storage.known_revision == 7
    assert recovered.shared_config_path.endswith("export.json")


def test_existing_legacy_configuration_belongs_only_to_its_original_central(tmp_path):
    import json
    from project_storage_resolver import ProjectStorageResolver
    from shared_json_storage import SharedJsonStorage

    class FakeDocument(object):
        IsWorkshared = True

        def __init__(self, central):
            self.central = central

        def GetWorksharingCentralModelPath(self):
            return self.central

    parent = tmp_path / "centrals"
    parent.mkdir()
    central_a = str(parent / "architecture.rvt")
    central_b = str(parent / "structure.rvt")
    # Resolving on Linux uses ntpath, so use real filesystem paths solely
    # for storage, while the FakeResolver supplies canonical identities.
    legacy = parent / "OutilsTAA" / "export.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({
        "schema_version": 8,
        "project_identity": "CENTRAL:architecture",
        "storage_revision": 7,
        "folders": [{"id": "a", "name": "ARCHI"}],
        "sets": [],
    }), encoding="utf-8")

    def paths(identity, stem):
        root = parent / "OutilsTAA" / stem
        return StoragePaths(
            StoragePaths.MODE_SHARED,
            local_config_path=str(tmp_path / "local.json"),
            central_path=identity,
            project_identity=identity,
            shared_config_path=str(root / "export.json"),
            shared_lock_path=str(root / "export.lock"),
            shared_backups_path=str(root / "backups"),
            legacy_config_path=str(legacy),
            legacy_lock_path=str(legacy.parent / "export.lock"),
            legacy_backups_path=str(legacy.parent / "backups"),
        )

    a = build_export_storage(
        object(), str(tmp_path / "local.json"), LOCAL_ID,
        resolver=FakeResolver(paths("CENTRAL:architecture", "architecture_hash")),
    )
    assert a.is_shared
    assert a.shared_config_path == str(legacy)
    assert a.revision == 7

    b = build_export_storage(
        object(), str(tmp_path / "local.json"), LOCAL_ID,
        resolver=FakeResolver(paths("CENTRAL:structure", "structure_hash")),
    )
    assert b.is_shared
    assert b.shared_config_path != str(legacy)
    assert b.revision == 0
    assert legacy.exists()
    assert json.loads(legacy.read_text(encoding="utf-8"))["storage_revision"] == 7


def test_model_specific_json_precedes_legacy_config_even_if_legacy_matches(tmp_path):
    import json

    parent = tmp_path / "centrals" / "OutilsTAA"
    scoped = parent / "architecture_hash"
    scoped.mkdir(parents=True)
    legacy = parent / "export.json"
    legacy.write_text(json.dumps({
        "schema_version": 8,
        "project_identity": SHARED_ID,
        "storage_revision": 3,
        "folders": [], "sets": [],
    }), encoding="utf-8")
    scoped_json = scoped / "export.json"
    scoped_json.write_text(json.dumps({
        "schema_version": 8,
        "project_identity": SHARED_ID,
        "storage_revision": 8,
        "folders": [], "sets": [],
    }), encoding="utf-8")

    paths = StoragePaths(
        StoragePaths.MODE_SHARED,
        local_config_path=str(tmp_path / "local.json"),
        central_path=SHARED_ID,
        project_identity=SHARED_ID,
        shared_config_path=str(scoped_json),
        shared_lock_path=str(scoped / "export.lock"),
        shared_backups_path=str(scoped / "backups"),
        legacy_config_path=str(legacy),
        legacy_lock_path=str(parent / "export.lock"),
        legacy_backups_path=str(parent / "backups"),
    )
    context = build_export_storage(
        object(), str(tmp_path / "local.json"), LOCAL_ID,
        resolver=FakeResolver(paths),
    )
    assert context.is_shared
    assert context.revision == 8
    assert context.shared_config_path == str(scoped_json)
