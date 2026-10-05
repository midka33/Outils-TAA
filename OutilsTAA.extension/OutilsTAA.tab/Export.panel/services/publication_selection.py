# -*- coding: utf-8 -*-
"""Construit un périmètre de publication à partir des nœuds sélectionnés."""

from copy import copy


def _set_key(carnet):
    """Distingue aussi les carnets temporaires dépourvus d'identifiant."""
    value = getattr(carnet, "id", None)
    return ("id", str(value)) if value is not None else ("session", id(carnet))


def publication_targets(tags, folder_targets):
    """Regroupe les feuilles par carnet, dans leur ordre métier, sans modifier la source.

    Les tags sont fournis dans l'ordre de l'arbre (parents avant descendants).
    Un dossier ou carnet sélectionné inclut son contenu entier. Les doublons
    sont éliminés par carnet ; une feuille dans deux carnets reste deux livrables.
    """
    tags = list(tags or [])
    complete, expanded = {}, {}
    for index, tag in enumerate(tags):
        if tag[0] == "FOLDER":
            expanded[index] = list(folder_targets(tag[1]))
            for target in expanded[index]:
                complete.setdefault(_set_key(target), target)
    for tag in tags:
        if tag[0] == "CARNET":
            complete.setdefault(_set_key(tag[1]), tag[1])

    ordered, parents, selected_items = [], {}, {}
    for index, tag in enumerate(tags):
        candidates = (expanded[index] if tag[0] == "FOLDER" else
                      [tag[1]] if tag[0] == "CARNET" else
                      [tag[2]] if tag[0] == "SHEET" else [])
        for parent in candidates:
            key = _set_key(parent)
            if key not in parents:
                ordered.append(key)
                parents[key] = parent
                selected_items[key] = set()
            if tag[0] == "SHEET":
                selected_items[key].add(tag[1].unique_id)

    result = []
    for key in ordered:
        parent = complete.get(key, parents[key])
        target = copy(parent)
        target.items = [item for item in parent.items or []
                        if key in complete or item.unique_id in selected_items[key]]
        result.append(target)
    return result
