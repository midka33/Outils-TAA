# -*- coding: utf-8 -*-
import json
import os
import sys

import pytest

CURRENT_DIR = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
SERVICES = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Export.panel",
    "services",
)
if SERVICES not in sys.path:
    sys.path.insert(0, SERVICES)

from shared_json_storage import (
    ConcurrentModificationError,
    ProjectIdentityMismatchError,
    SharedJsonStorage,
    StorageCorruptedError,
    StorageLockTimeoutError,
    _PortableExclusiveLock,
)


IDENTITY = r"CENTRAL:\\serveur\projets\a\central.rvt"


def storage(tmp_path, backup_limit=20, timeout=0.10):
    root = tmp_path / "OutilsTAA"
    return SharedJsonStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        IDENTITY,
        lock_timeout_seconds=timeout,
        lock_retry_seconds=0.01,
        backup_limit=backup_limit,
    )


def write_raw(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def base_data(revision=None):
    data = {
        "schema_version": 8,
        "project_identity": IDENTITY,
        "folders": [],
        "sets": [],
    }
    if revision is not None:
        data["storage_revision"] = revision
    return data


def test_legacy_schema8_without_storage_revision_is_revision_zero(tmp_path):
    target = tmp_path / "OutilsTAA" / "export.json"
    write_raw(target, base_data())

    repo = storage(tmp_path)
    data = repo.read()

    assert data["schema_version"] == 8
    assert repo.known_revision == 0


def test_first_shared_write_creates_revision_one_without_backup(tmp_path):
    repo = storage(tmp_path)
    assert repo.read() is None

    payload = repo.write(base_data())

    assert payload["storage_revision"] == 1
    assert payload["last_write_id"]
    assert repo.known_revision == 1

    disk = json.loads(
        (tmp_path / "OutilsTAA" / "export.json").read_text(
            encoding="utf-8"
        )
    )
    assert disk["storage_revision"] == 1
    assert not (tmp_path / "OutilsTAA" / "backups").exists()


def test_two_writers_detect_stale_revision_instead_of_last_writer_wins(tmp_path):
    first = storage(tmp_path)
    second = storage(tmp_path)

    assert first.read() is None
    assert second.read() is None

    first_data = base_data()
    first_data["folders"] = [{"id": "A"}]
    first.write(first_data)

    second_data = base_data()
    second_data["folders"] = [{"id": "B"}]
    with pytest.raises(ConcurrentModificationError):
        second.write(second_data)

    disk = json.loads(
        (tmp_path / "OutilsTAA" / "export.json").read_text(
            encoding="utf-8"
        )
    )
    assert disk["folders"] == [{"id": "A"}]
    assert disk["storage_revision"] == 1


def test_refresh_allows_second_writer_after_conflict(tmp_path):
    first = storage(tmp_path)
    second = storage(tmp_path)
    first.read()
    second.read()

    first.write(base_data())

    second.read()
    next_data = base_data()
    next_data["sets"] = [{"id": "publication-1"}]
    payload = second.write(next_data)

    assert payload["storage_revision"] == 2
    assert payload["sets"] == [{"id": "publication-1"}]


def test_has_external_change_observes_revision_change(tmp_path):
    first = storage(tmp_path)
    second = storage(tmp_path)
    first.read()
    second.read()

    first.write(base_data())

    assert second.has_external_change()
    second.refresh()
    assert not second.has_external_change()


def test_existing_write_creates_backup_of_previous_revision(tmp_path):
    repo = storage(tmp_path)
    repo.read()
    first = base_data()
    first["folders"] = [{"id": "A"}]
    repo.write(first)

    second = base_data()
    second["folders"] = [{"id": "A"}, {"id": "B"}]
    repo.write(second)

    backups = list((tmp_path / "OutilsTAA" / "backups").glob("export_*.json"))
    assert len(backups) == 1
    previous = json.loads(backups[0].read_text(encoding="utf-8"))
    assert previous["storage_revision"] == 1
    assert previous["folders"] == [{"id": "A"}]


def test_backup_rotation_keeps_only_requested_limit(tmp_path):
    repo = storage(tmp_path, backup_limit=3)
    repo.read()

    for index in range(7):
        data = base_data()
        data["sets"] = [{"id": str(index)}]
        repo.write(data)

    backups = list((tmp_path / "OutilsTAA" / "backups").glob("export_*.json"))
    assert len(backups) == 3


def test_corrupted_json_is_reported_and_never_reset_silently(tmp_path):
    target = tmp_path / "OutilsTAA" / "export.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{ invalid json", encoding="utf-8")

    repo = storage(tmp_path)

    with pytest.raises(StorageCorruptedError):
        repo.read()

    assert target.read_text(encoding="utf-8") == "{ invalid json"


def test_wrong_project_identity_is_blocked(tmp_path):
    target = tmp_path / "OutilsTAA" / "export.json"
    data = base_data(revision=4)
    data["project_identity"] = r"CENTRAL:\\serveur\autre\central.rvt"
    write_raw(target, data)

    repo = storage(tmp_path)

    with pytest.raises(ProjectIdentityMismatchError):
        repo.read()


def test_payload_for_another_project_is_rejected_before_replacement(tmp_path):
    repo = storage(tmp_path)
    repo.read()
    repo.write(base_data())

    wrong = base_data()
    wrong["project_identity"] = r"CENTRAL:\\serveur\autre\central.rvt"

    with pytest.raises(ProjectIdentityMismatchError):
        repo.write(wrong)

    disk = json.loads(
        (tmp_path / "OutilsTAA" / "export.json").read_text(
            encoding="utf-8"
        )
    )
    assert disk["storage_revision"] == 1


def test_portable_lock_times_out_while_another_writer_holds_it(tmp_path):
    lock_path = str(tmp_path / "export.lock")
    first = _PortableExclusiveLock(
        lock_path,
        timeout_seconds=0.2,
        retry_seconds=0.01,
    )

    with first:
        second = _PortableExclusiveLock(
            lock_path,
            timeout_seconds=0.03,
            retry_seconds=0.01,
        )
        with pytest.raises(StorageLockTimeoutError):
            with second:
                pass


def test_invalid_temporary_file_does_not_replace_existing_json(tmp_path):
    class CorruptingStorage(SharedJsonStorage):
        def _write_temporary(self, payload):
            path = SharedJsonStorage._write_temporary(self, payload)
            with open(path, "w") as handle:
                handle.write("{ broken")
            return path

    normal = storage(tmp_path)
    normal.read()
    normal.write(base_data())

    root = tmp_path / "OutilsTAA"
    broken = CorruptingStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        IDENTITY,
    )
    broken.read()

    with pytest.raises(StorageCorruptedError):
        broken.write(base_data())

    disk = json.loads((root / "export.json").read_text(encoding="utf-8"))
    assert disk["storage_revision"] == 1


def test_replace_failure_leaves_existing_json_untouched(tmp_path):
    class BrokenReplaceStorage(SharedJsonStorage):
        def _replace_existing(self, temp_path, backup_path):
            raise RuntimeError("replace refused")

    normal = storage(tmp_path)
    normal.read()
    first = base_data()
    first["folders"] = [{"id": "original"}]
    normal.write(first)

    root = tmp_path / "OutilsTAA"
    broken = BrokenReplaceStorage(
        str(root / "export.json"),
        str(root / "export.lock"),
        str(root / "backups"),
        IDENTITY,
    )
    broken.read()

    changed = base_data()
    changed["folders"] = [{"id": "changed"}]

    with pytest.raises(RuntimeError):
        broken.write(changed)

    disk = json.loads((root / "export.json").read_text(encoding="utf-8"))
    assert disk["folders"] == [{"id": "original"}]
    assert disk["storage_revision"] == 1


def test_write_requires_prior_read_to_establish_revision_contract(tmp_path):
    repo = storage(tmp_path)

    with pytest.raises(RuntimeError):
        repo.write(base_data())
