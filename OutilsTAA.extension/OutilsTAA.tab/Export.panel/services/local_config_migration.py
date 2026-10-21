# -*- coding: utf-8 -*-
"""Migration explicite d'une configuration Export locale vers le partage.

La migration ne supprime ni ne modifie le JSON local. Elle n'est proposée que
si aucun export.json partagé n'existe encore et si la configuration locale
contient réellement des données utilisateur.
"""

import io
import json
import os
from datetime import datetime

from carnet_repository import CarnetRepository
from shared_json_storage import ConcurrentModificationError


_STORAGE_METADATA = (
    "storage_revision",
    "last_write_id",
    "last_write_utc",
    "last_write_user",
    "last_write_machine",
)


class LocalMigrationError(Exception):
    pass


class LocalConfigurationCorruptedError(LocalMigrationError):
    pass


class LocalConfigurationIdentityMismatchError(LocalMigrationError):
    pass


class LocalMigrationCandidate(object):
    def __init__(
            self,
            path,
            local_project_identity,
            shared_project_identity,
            data,
            folder_count,
            publication_count,
            sheet_count):
        self.path = path
        self.local_project_identity = local_project_identity
        self.shared_project_identity = shared_project_identity
        self.data = data
        self.folder_count = int(folder_count)
        self.publication_count = int(publication_count)
        self.sheet_count = int(sheet_count)

    @property
    def decision_path(self):
        return self.path + ".collaborative-migration.json"

    def summary(self):
        return (
            "{0} dossier(s), {1} dossier(s) de publication, "
            "{2} mise(s) en page"
        ).format(
            self.folder_count,
            self.publication_count,
            self.sheet_count,
        )


def _load_json(path):
    try:
        with io.open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except ValueError as exc:
        raise LocalConfigurationCorruptedError(
            "Le JSON local est invalide : {0}".format(exc)
        )
    except Exception as exc:
        raise LocalConfigurationCorruptedError(
            "Impossible de lire la configuration locale : {0}".format(exc)
        )

    if not isinstance(data, dict):
        raise LocalConfigurationCorruptedError(
            "La configuration locale doit contenir un objet JSON."
        )
    return data


def _identity_matches(actual, expected):
    if not actual:
        return True
    if not expected:
        return False
    return str(actual).lower() == str(expected).lower()


def _meaningful_settings(value):
    settings = value.get("publication_settings")
    if not isinstance(settings, dict):
        return False
    return any(item is not None for item in settings.values())


def has_meaningful_project_data(data):
    """Ignore une arborescence neuve contenant seulement Général vide."""
    if not isinstance(data, dict):
        return False

    sets = list(data.get("sets") or [])
    if sets:
        return True

    folders = list(data.get("folders") or [])
    for folder in folders:
        folder_id = str(folder.get("id") or "")
        if folder_id != CarnetRepository.DEFAULT_FOLDER_ID:
            return True
        if (folder.get("name") or CarnetRepository.DEFAULT_FOLDER_NAME) != (
                CarnetRepository.DEFAULT_FOLDER_NAME):
            return True
        if _meaningful_settings(folder):
            return True

    return False


def _normalised_local_data(path, local_project_identity):
    raw = _load_json(path)

    schema = raw.get("schema_version")
    if schema is not None:
        try:
            if int(schema) > CarnetRepository.SCHEMA_VERSION:
                raise LocalConfigurationCorruptedError(
                    "Le schéma local {0} est plus récent que le schéma "
                    "pris en charge ({1}).".format(
                        schema,
                        CarnetRepository.SCHEMA_VERSION,
                    )
                )
        except (TypeError, ValueError):
            raise LocalConfigurationCorruptedError(
                "La version de schéma du JSON local est invalide."
            )

    if not _identity_matches(
            raw.get("project_identity"),
            local_project_identity):
        raise LocalConfigurationIdentityMismatchError(
            "La configuration locale appartient à un autre projet."
        )

    repository = CarnetRepository(
        path,
        project_identity=(
            local_project_identity
            if raw.get("project_identity")
            else None
        ),
    )
    return repository._read()


def _counts(data):
    folders = list(data.get("folders") or [])
    sets = list(data.get("sets") or [])
    visible_folders = [
        value for value in folders
        if str(value.get("id")) != CarnetRepository.DEFAULT_FOLDER_ID
    ]
    sheet_count = sum(
        len(value.get("items") or [])
        for value in sets
    )
    return len(visible_folders), len(sets), sheet_count


def _decision_matches(path, shared_project_identity):
    if not os.path.exists(path):
        return False
    try:
        data = _load_json(path)
    except LocalMigrationError:
        return False

    return (
        data.get("decision") == "declined"
        and str(data.get("shared_project_identity") or "").lower()
        == str(shared_project_identity or "").lower()
    )


def was_declined(candidate):
    return _decision_matches(
        candidate.decision_path,
        candidate.shared_project_identity,
    )


def mark_declined(candidate):
    directory = os.path.dirname(candidate.decision_path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)

    payload = {
        "decision": "declined",
        "shared_project_identity": candidate.shared_project_identity,
        "local_config_path": candidate.path,
        "recorded_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with io.open(candidate.decision_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def find_local_migration_candidate(
        candidates,
        shared_project_identity,
        skip_declined=True):
    """Retourne la première configuration locale sûre et non vide."""
    seen = set()
    for path, local_identity in candidates or []:
        if not path:
            continue

        key = os.path.normcase(os.path.abspath(path))
        if key in seen:
            continue
        seen.add(key)

        if not os.path.exists(path):
            continue

        data = _normalised_local_data(path, local_identity)
        if not has_meaningful_project_data(data):
            continue

        folder_count, publication_count, sheet_count = _counts(data)
        candidate = LocalMigrationCandidate(
            path,
            local_identity,
            shared_project_identity,
            data,
            folder_count,
            publication_count,
            sheet_count,
        )
        if skip_declined and was_declined(candidate):
            continue
        return candidate

    return None


def _payload_for_shared(candidate):
    payload = dict(candidate.data)
    payload["schema_version"] = CarnetRepository.SCHEMA_VERSION
    payload["project_identity"] = candidate.shared_project_identity

    for field in _STORAGE_METADATA:
        payload.pop(field, None)

    return payload


def import_local_configuration(candidate, shared_storage):
    """Importe sous contrôle de révision, sans fusion ni suppression locale."""
    if candidate is None:
        raise ValueError("La configuration locale à importer est obligatoire.")
    if shared_storage is None:
        raise ValueError("Le stockage partagé est obligatoire.")

    existing = shared_storage.read()
    if existing is not None:
        raise ConcurrentModificationError(
            "Une configuration partagée existe déjà. "
            "L'import local a été annulé."
        )

    payload = _payload_for_shared(candidate)
    return shared_storage.write(payload)
