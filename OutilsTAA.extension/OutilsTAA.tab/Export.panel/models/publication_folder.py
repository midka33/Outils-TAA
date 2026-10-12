# -*- coding: utf-8 -*-
"""Modèle métier d'un dossier de publication Export."""

from copy import copy


class PublicationFolder(object):
    """Dossier persistant pouvant contenir des sous-dossiers."""

    def __init__(self, name, folder_id=None, parent_id=None, persistent=True,
                 publication_settings=None, sort_order=0, tree_order=None):
        self.id = folder_id
        self.name = name
        self.parent_id = parent_id
        self.persistent = persistent
        self.publication_settings = publication_settings
        self.sort_order = sort_order
        self.tree_order = tree_order


def _parent_id(value):
    if value is None:
        return None
    if hasattr(value, "parent_id"):
        return getattr(value, "parent_id", None)
    return getattr(value, "folder_id", None)


def _containers(window):
    result = []
    for value in getattr(window, "_folders", []) or []:
        result.append(("FOLDER", value))
    for value in getattr(window, "_carnets", []) or []:
        result.append(("CARNET", value))
    return result


def _descendant_ids(window, root_id):
    """Tous les conteneurs sous root_id, quel que soit leur type interne."""
    ids = set([str(root_id)])
    changed = True
    while changed:
        changed = False
        for kind, candidate in _containers(window):
            parent = _parent_id(candidate)
            candidate_id = getattr(candidate, "id", None)
            if parent is None or candidate_id is None:
                continue
            if (
                str(parent) in ids
                and str(candidate_id) not in ids
            ):
                ids.add(str(candidate_id))
                changed = True
    return ids


def _path_parts(window, target, root_id):
    """Chemin relatif des parents visuels entre root et target."""
    by_id = {}
    for kind, value in _containers(window):
        value_id = getattr(value, "id", None)
        if value_id is not None:
            by_id[str(value_id)] = value

    parts = []
    current_id = _parent_id(target)
    visited = set()
    while current_id is not None:
        key = str(current_id)
        if key in visited:
            break
        visited.add(key)
        current = by_id.get(key)
        if current is None:
            break
        parts.insert(0, current.name)
        if key == str(root_id):
            break
        current_id = _parent_id(current)
    return tuple(parts)


def _container_targets(window, root, include_root_set=False):
    """PublicationSets contenus dans un dossier visuel et ses descendants."""
    if root is None:
        return []

    root_id = getattr(root, "id", None)
    if root_id is None:
        return []

    descendant_ids = _descendant_ids(window, root_id)
    result = []
    seen = set()

    if include_root_set and hasattr(root, "items"):
        target = copy(root)
        target.publication_folder_parts = ()
        result.append(target)
        seen.add(str(root.id))

    for publication_set in getattr(window, "_carnets", []) or []:
        set_id = getattr(publication_set, "id", None)
        if set_id is None or str(set_id) in seen:
            continue
        parent_id = getattr(publication_set, "folder_id", None)
        if str(parent_id) not in descendant_ids:
            continue

        target = copy(publication_set)
        target.publication_folder_parts = _path_parts(
            window,
            publication_set,
            root_id,
        )
        result.append(target)
        seen.add(str(set_id))

    return result


def _folder_targets(window, folder):
    """Retourne les dossiers de publication sous un dossier visuel."""
    return _container_targets(window, folder, include_root_set=False)


def _set_targets(window, publication_set):
    """Retourne le dossier sélectionné et tous ses sous-dossiers publiables."""
    return _container_targets(
        window,
        publication_set,
        include_root_set=True,
    )
