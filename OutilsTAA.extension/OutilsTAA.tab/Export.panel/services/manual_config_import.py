# -*- coding: utf-8 -*-
"""Import volontaire d'un JSON Export comme base d'un nouveau projet central.

La source n'est jamais modifiée. Une identité source différente est autorisée
uniquement par ce parcours explicite ; le stockage cible garde tous les contrôles
de verrouillage SMB, de révision et d'identité du projet courant.
"""

import copy
import os

from carnet_repository import CarnetRepository
from local_config_migration import (
    LocalConfigurationCorruptedError,
    _load_json,
    _counts,
    _STORAGE_METADATA,
)
from shared_json_storage import ConcurrentModificationError


class ManualImportError(Exception):
    pass


def prepare_manual_import(source_path, target_identity, current_sheet_ids):
    """Prépare un aperçu non destructif pour l'UI, sans écrire sur disque."""
    if not source_path or not os.path.isfile(source_path):
        raise ManualImportError("Sélectionnez un fichier JSON Export existant.")
    if not target_identity:
        raise ManualImportError("Le modèle central cible est introuvable.")

    try:
        data = _load_json(source_path)
    except LocalConfigurationCorruptedError as exc:
        raise ManualImportError(str(exc))

    version = data.get("schema_version")
    try:
        version_number = int(version) if version is not None else 0
    except (TypeError, ValueError):
        raise ManualImportError("Schéma du fichier source invalide.")
    if version_number > CarnetRepository.SCHEMA_VERSION or version_number < 0:
        raise ManualImportError(
            "Version JSON non prise en charge : {0}.".format(version)
        )
    if not isinstance(data.get("sets", []), list) or not isinstance(
            data.get("folders", []), list):
        raise ManualImportError("Arborescence de la configuration source invalide.")

    # Ignore the old identity while normalizing: this operation is explicitly
    # an import from another model, never a silent adoption of that model.
    normalized = CarnetRepository(source_path)._ensure_structure(
        copy.deepcopy(data)
    )
    ids = set(str(value) for value in (current_sheet_ids or []))
    folders, publications, before = _counts(normalized)
    kept = 0
    for publication in normalized.get("sets", []):
        items = publication.get("items") or []
        if not isinstance(items, list):
            raise ManualImportError("Liste de feuilles invalide dans la source.")
        filtered = [
            item for item in items
            if isinstance(item, dict)
            and str(item.get("unique_id") or "") in ids
        ]
        publication["items"] = filtered
        kept += len(filtered)

    payload = normalized
    payload["project_identity"] = target_identity
    payload["schema_version"] = CarnetRepository.SCHEMA_VERSION
    for field in _STORAGE_METADATA:
        payload.pop(field, None)

    return {
        "source_path": source_path,
        "source_identity": str(data.get("project_identity") or "Non renseignée"),
        "folder_count": folders,
        "publication_count": publications,
        "source_sheet_count": before,
        "matching_sheet_count": kept,
        "payload": payload,
    }


def create_shared_from_manual_import(preview, shared_storage):
    """Crée seulement une cible absente, sous verrou et contrôle de révision."""
    if not preview or shared_storage is None:
        raise ManualImportError("Import ou stockage cible non défini.")
    if os.path.normcase(os.path.abspath(preview["source_path"])) == os.path.normcase(
            os.path.abspath(shared_storage.config_path)):
        raise ManualImportError(
            "Le fichier source ne peut pas être la configuration cible."
        )

    # Recheck after user confirmation, because another user may create the JSON.
    if shared_storage.read() is not None:
        raise ConcurrentModificationError(
            "La configuration partagée a déjà été créée par un autre utilisateur."
        )
    # SharedJsonStorage.write() compares the revision again under its SMB lock.
    return shared_storage.write(copy.deepcopy(preview["payload"]))
