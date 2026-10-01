# -*- coding: utf-8 -*-
"""Suppression explicite des carnets et dossiers sélectionnés, sans accès Revit."""


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


def delete_selected(targets, controller, repository, session_carnets, folders):
    """Supprime les enfants sélectionnés avant leurs parents ; conserve les autres."""
    remaining = list(session_carnets)
    blocked = []
    by_id = dict((str(f.id), f) for f in folders)

    def depth(tag):
        value, seen = tag[1], set()
        while value is not None and str(value.id) not in seen:
            seen.add(str(value.id))
            value = by_id.get(str(value.parent_id))
        return len(seen)

    carnets = [t for t in targets if t[0] == "CARNET"]
    directories = sorted([t for t in targets if t[0] == "FOLDER"], key=depth, reverse=True)
    for kind, value in carnets + directories:
        try:
            if kind == "CARNET":
                if value.persistent:
                    repository.delete(value.id)
                else:
                    remaining = [c for c in remaining if c.id != value.id]
            elif str(value.id) == "default":
                blocked.append("Général : dossier protégé")
            elif any(c.folder_id == value.id for c in remaining):
                blocked.append(value.name + " : contient un carnet de session")
            elif not controller.delete_folder(value.id):
                blocked.append(value.name + " : dossier non vide ou indisponible")
        except Exception as exc:
            blocked.append("{0} : {1}".format(value.name, exc))
    return remaining, blocked
