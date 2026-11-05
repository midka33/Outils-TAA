# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Perimetre de recette d'un SEUL appartement dans UNE vue Revit.

Helpers purs : pas d'appel a Revit ni de mutation de modele.
Les donnees proviennent seulement des parametres d'INSTANCE des pieces
visibles dans la vue. Une correspondance exacte est obligatoire.
"""

MAX_APARTMENT_ROOMS = 12


def normalize(value):
    return "" if value is None else str(value).strip()


def _read_value(parameter):
    """Lit texte et entiers sans convertir de valeur absente en '0'."""
    try:
        value = parameter.AsString()
        if value is not None:
            return normalize(value)
    except Exception:
        pass
    try:
        storage = str(parameter.StorageType)
    except Exception:
        storage = ""
    if storage.endswith("Integer"):
        try:
            return normalize(parameter.AsInteger())
        except Exception:
            pass
    try:
        value = parameter.AsValueString()
        return normalize(value)
    except Exception:
        return ""


def room_parameters(room):
    """Noms de parametres d'instance renseignes sans identite ambiguë."""
    values = {}
    ambiguous = set()
    try:
        parameters = room.Parameters
    except Exception:
        return values
    try:
        iterator = iter(parameters)
    except Exception:
        return values
    for parameter in iterator:
        try:
            name = normalize(parameter.Definition.Name)
            value = _read_value(parameter)
        except Exception:
            continue
        if not name or not value or name in ambiguous:
            continue
        if name in values and values[name] != value:
            # Le nom ne suffit plus pour choisir un parametre de facon
            # non ambiguë : cette valeur ne peut pas servir au filtrage.
            ambiguous.add(name)
            values.pop(name, None)
        else:
            values[name] = value
    return values


def parameter_candidates(rooms):
    """Noms dont une valeur non vide est partagee par au moins deux pieces."""
    histogram = {}
    for room in rooms or ():
        for name, value in room_parameters(room).items():
            histogram.setdefault(name, {}).setdefault(value, 0)
            histogram[name][value] += 1

    def priority(name):
        label = name.lower()
        return (0 if any(token in label for token in (
            "appart", "logement", "housing", "lot", "unit", "unite"))
            else 1, label)

    return sorted(
        (name for name, counts in histogram.items()
         if max(counts.values()) >= 2),
        key=priority)


def apartment_values(rooms, apartment_parameter):
    """Liste des identifiants et nombre de pieces visibles qui les partagent."""
    grouped = {}
    for room in rooms or ():
        value = room_parameters(room).get(apartment_parameter, "")
        if value:
            grouped.setdefault(value, []).append(room)
    return sorted(
        ((value, items) for value, items in grouped.items()
         if len(items) >= 2),
        key=lambda item: (item[0].lower(), item[0]))


def filter_apartment(rooms, apartment_parameter, apartment_value,
                     building_parameter=None, building_value=None,
                     max_rooms=MAX_APARTMENT_ROOMS):
    """Filtrage strict par identifiant et batiment si fourni.

    Ne renvoie jamais des pieces de groupes ou une selection trop large.
    Le lanceur affiche la liste des pieces avant toute transaction.
    """
    key = normalize(apartment_parameter)
    value = normalize(apartment_value)
    building = normalize(building_parameter)
    building_key = normalize(building_value)
    if not key or not value:
        raise ValueError("Identifiant appartement ou valeur vide.")
    if building and (not building_key or building == key):
        raise ValueError("Choisir une valeur de batiment et un parametre distinct.")
    if not building and building_key:
        raise ValueError("Valeur de batiment sans parametre.")
    selected = []
    for room in rooms or ():
        values = room_parameters(room)
        if values.get(key, "") != value:
            continue
        if building and values.get(building, "") != building_key:
            continue
        selected.append(room)
    if len(selected) < 2:
        raise ValueError(
            "L'appartement doit contenir au moins 2 pieces visibles "
            "dans cette vue ({} trouvee(s)).".format(len(selected)))
    if len(selected) > int(max_rooms):
        raise ValueError(
            "{} pieces trouvees : limite de securite de {} pieces. "
            "Choisir un appartement plus petit ou ajouter un filtre "
            "batiment.".format(len(selected), max_rooms))
    return selected


def available_buildings(rooms, building_parameter):
    result = set()
    for room in rooms or ():
        value = room_parameters(room).get(building_parameter, "")
        if value:
            result.add(value)
    return sorted(result, key=lambda item: (item.lower(), item))
