# -*- coding: utf-8 -*-
"""Suppression explicite des dossiers sélectionnés, sans accès Revit."""


def deletion_targets(tags):
    """Déduplique les conteneurs ; les mises en page ne sont pas supprimées ici."""
    result, seen = [], set()
    for tag in tags:
        if tag[0] not in ("CARNET", "FOLDER"):
            continue
        key = (tag[0], str(tag[1].id))
        if key not in seen:
            result.append(tag)
            seen.add(key)
    return result


def _parent_id(value):
    if value is None:
        return None
    if hasattr(value, "parent_id"):
        return getattr(value, "parent_id", None)
    return getattr(value, "folder_id", None)


def delete_selected(targets, controller, repository, session_carnets, folders):
    """Supprime les descendants avant leurs parents, quel que soit le type interne."""
    remaining = list(session_carnets)
    blocked = []

    persistent_sets = []
    try:
        persistent_sets = list(repository.list_all())
    except Exception:
        persistent_sets = []

    by_id = {}
    for value in list(folders or []) + persistent_sets + list(session_carnets or []):
        value_id = getattr(value, "id", None)
        if value_id is not None:
            by_id[str(value_id)] = value

    def depth(tag):
        value = tag[1]
        seen = set()
        count = 0
        current = value
        while current is not None:
            key = str(getattr(current, "id", ""))
            if key in seen:
                break
            seen.add(key)
            count += 1
            parent_id = _parent_id(current)
            current = (
                by_id.get(str(parent_id))
                if parent_id is not None else None
            )
        return count

    ordered = sorted(
        list(targets or []),
        key=depth,
        reverse=True,
    )

    for kind, value in ordered:
        try:
            if kind == "CARNET":
                if value.persistent:
                    if not repository.delete(value.id):
                        blocked.append(
                            value.name
                            + " : dossier non vide ou indisponible"
                        )
                else:
                    remaining = [
                        item for item in remaining
                        if item.id != value.id
                    ]
            elif str(value.id) == "default":
                blocked.append("Général : dossier protégé")
            elif not controller.delete_folder(value.id):
                blocked.append(
                    value.name
                    + " : dossier non vide ou indisponible"
                )
        except Exception as exc:
            blocked.append(
                "{0} : {1}".format(value.name, exc)
            )

    return remaining, blocked
