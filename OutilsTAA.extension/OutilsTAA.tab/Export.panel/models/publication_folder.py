# -*- coding: utf-8 -*-
"""Modèle métier d'un dossier de publication Export."""


class PublicationFolder(object):
    """Dossier persistant contenant des carnets de publication."""

    def __init__(self, name, folder_id=None, parent_id=None, persistent=True,
                 publication_settings=None):
        self.id = folder_id
        self.name = name
        self.parent_id = parent_id
        self.persistent = persistent
        self.publication_settings = publication_settings


def _folder_targets(window, folder):
    """Retourne les carnets rattachés au dossier et à ses sous-dossiers."""
    if folder is None:
        return []

    folder_ids = set([str(folder.id)])
    changed = True
    while changed:
        changed = False
        for candidate in getattr(window, "_folders", []) or []:
            parent_id = getattr(candidate, "parent_id", None)
            if parent_id is None:
                continue
            if str(parent_id) in folder_ids and str(candidate.id) not in folder_ids:
                folder_ids.add(str(candidate.id))
                changed = True

    result = []
    seen = set()
    for carnet in getattr(window, "_carnets", []) or []:
        carnet_id = getattr(carnet, "id", None)
        if carnet_id is None or str(carnet_id) in seen:
            continue
        if str(getattr(carnet, "folder_id", "default")) in folder_ids:
            result.append(carnet)
            seen.add(str(carnet_id))
    return result
