# -*- coding: utf-8 -*-
"""Sélection du stockage Export au lancement du module.

Ce service ne modifie jamais le document Revit. Il choisit le stockage partagé
lorsqu'un central Windows exploitable est disponible, sinon conserve le dépôt
local fourni par l'appelant.
"""

from carnet_repository import CarnetRepository
from project_storage_resolver import ProjectStorageResolver, StoragePaths
from shared_json_storage import (
    SharedJsonStorage,
    StorageAccessDeniedError,
    StorageUnavailableError,
)


class ExportStorageContext(object):
    MODE_SHARED = StoragePaths.MODE_SHARED
    MODE_LOCAL = StoragePaths.MODE_LOCAL

    def __init__(
            self,
            repository,
            mode,
            local_config_path,
            project_identity,
            central_path=None,
            shared_config_path=None,
            warning=None,
            fallback_from_shared=False):
        self.repository = repository
        self.mode = mode
        self.local_config_path = local_config_path
        self.project_identity = project_identity
        self.central_path = central_path
        self.shared_config_path = shared_config_path
        self.warning = warning
        self.fallback_from_shared = bool(fallback_from_shared)

    @property
    def is_shared(self):
        return self.mode == self.MODE_SHARED

    @property
    def revision(self):
        return getattr(self.repository, "storage_revision", None)


def _shared_warning(exc):
    return (
        "Configuration locale de secours : le stockage partagé Export "
        "est indisponible ({0})."
    ).format(exc)


def build_export_storage(
        document,
        local_config_path,
        local_project_identity,
        resolver=None,
        shared_storage_factory=None,
        repository_factory=None):
    """Construit le repository à utiliser pendant la session Export.

    Seules les indisponibilités réseau / droits du partage provoquent un
    fallback local. Une corruption JSON ou une identité projet incohérente est
    volontairement propagée : elle ne doit jamais être masquée par un mode local.
    """
    if not local_config_path:
        raise ValueError("Le chemin local de secours est obligatoire.")
    if not local_project_identity:
        raise ValueError("L'identité locale du projet est obligatoire.")

    resolver = resolver or ProjectStorageResolver()
    shared_storage_factory = shared_storage_factory or SharedJsonStorage
    repository_factory = repository_factory or CarnetRepository

    resolved = resolver.resolve(document, local_config_path)

    if resolved.uses_shared_storage:
        storage = shared_storage_factory(
            resolved.shared_config_path,
            resolved.shared_lock_path,
            resolved.shared_backups_path,
            resolved.project_identity,
        )
        try:
            storage.probe_access()
        except (StorageUnavailableError, StorageAccessDeniedError) as exc:
            repository = repository_factory(
                local_config_path,
                project_identity=local_project_identity,
            )
            return ExportStorageContext(
                repository,
                ExportStorageContext.MODE_LOCAL,
                local_config_path,
                local_project_identity,
                central_path=resolved.central_path,
                shared_config_path=resolved.shared_config_path,
                warning=_shared_warning(exc),
                fallback_from_shared=True,
            )

        repository = repository_factory(
            resolved.shared_config_path,
            project_identity=resolved.project_identity,
            shared_storage=storage,
        )
        return ExportStorageContext(
            repository,
            ExportStorageContext.MODE_SHARED,
            local_config_path,
            resolved.project_identity,
            central_path=resolved.central_path,
            shared_config_path=resolved.shared_config_path,
        )

    repository = repository_factory(
        local_config_path,
        project_identity=local_project_identity,
    )
    return ExportStorageContext(
        repository,
        ExportStorageContext.MODE_LOCAL,
        local_config_path,
        local_project_identity,
        warning=resolved.warning,
    )
