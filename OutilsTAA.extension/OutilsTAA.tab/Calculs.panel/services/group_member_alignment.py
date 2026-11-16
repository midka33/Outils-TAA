# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Plan prudent d'écriture des membres homologues des groupes Revit.

Group.GetMemberIds() retourne un ordre utilisable pour retrouver les membres
correspondants d'occurrences du meme type (API Revit 2025).
Aucun groupe n'est degroupe, supprime, ni reconstruit.
"""

from common.exceptions import ValidationError
from calculation_diagnostics import element_id_value


def _members(group):
    getter = getattr(group, "GetMemberIds", None)
    if getter is None:
        return None
    return list(getter())


def _all_groups(document):
    try:
        from Autodesk.Revit.DB import FilteredElementCollector, Group
        return list(FilteredElementCollector(document).OfClass(Group).ToElements())
    except ImportError:
        # Double de test, jamais utilise dans Revit.
        return list(getattr(document, "groups", {}).values())


def _type_key(group):
    group_type = getattr(group, "GroupType", None)
    type_id = getattr(group_type, "Id", None)
    if type_id is None:
        type_id = group.GetTypeId()
    return element_id_value(type_id)


def build_uniform_member_plan(document, room_by_key, operations,
                              parameter_service, target_descriptor):
    """Prepare les ecritures complementaires sans modifier le modele.

    Retourne (extras, covered_ids). extras: (room, valeur_source, type_key).
    Les correspondances sont calculees par position dans GetMemberIds().
    Tout membre homologue manquant ou sans destination provoque un refus.
    """
    get_element = getattr(document, "GetElement", None)
    if get_element is None:
        return [], set()

    by_type = {}
    selected_by_id = {}
    for op in operations:
        room = room_by_key.get(op.room_key)
        if room is None:
            continue
        element_id = getattr(room, "Id", None)
        room_id = element_id_value(element_id)
        if room_id is not None:
            selected_by_id[str(room_id)] = op
        group_id = getattr(room, "GroupId", None)
        group_key = element_id_value(group_id)
        if group_key in (None, -1):
            continue
        group = get_element(group_id)
        if group is None:
            raise ValidationError("Groupe introuvable pour la piece '{}'.".format(op.room_key))
        ids = _members(group)
        if ids is None:
            # Compatibilite historique des doubles de tests sans Group API.
            # Dans Revit, GetMemberIds() est toujours disponible.
            continue
        key = _type_key(group)
        if key is None:
            raise ValidationError("Type de groupe introuvable.")
        positions = [i for i, value in enumerate(ids)
                     if element_id_value(value) == room_id]
        if len(positions) != 1:
            raise ValidationError(
                "Correspondance introuvable pour la piece '{}' dans son groupe."
                .format(op.room_key)
            )
        record = by_type.setdefault(key, {"positions": {}, "instances": {}})
        record["positions"].setdefault(positions[0], []).append(op.value)
        record["instances"][group_key] = group

    if not by_type:
        return [], set()

    for group in _all_groups(document):
        key = _type_key(group)
        if key in by_type:
            group_id = element_id_value(group.Id)
            by_type[key]["instances"][group_id] = group

    extras = []
    covered = set(selected_by_id)
    planned_extras = set()
    for type_key, record in by_type.items():
        positions = record["positions"]
        for group in record["instances"].values():
            ids = _members(group)
            if ids is None:
                raise ValidationError(
                    "Impossible de comparer les membres du type de groupe '{}'."
                    .format(type_key)
                )
            for position, raw_values in positions.items():
                if position >= len(ids):
                    raise ValidationError(
                        "Occurrences incompatibles du type de groupe '{}'."
                        .format(type_key)
                    )
                member_id = ids[position]
                identifier = str(element_id_value(member_id))
                covered.add(identifier)
                if identifier in selected_by_id or identifier in planned_extras:
                    continue
                room = get_element(member_id)
                if room is None:
                    raise ValidationError(
                        "Membre correspondant introuvable dans le type de groupe '{}'."
                        .format(type_key)
                    )
                parameter = parameter_service.get_parameter(room, target_descriptor)
                if parameter is None:
                    raise ValidationError(
                        "Le membre correspondant du type '{}' ne possede pas '{}'."
                        .format(type_key, target_descriptor.name)
                    )
                # Les conflits de valeurs entre instances sont resolus dans
                # le workflow par le choix explicite de l'utilisateur.
                extras.append((room, raw_values[0], type_key))
                planned_extras.add(identifier)

    return extras, covered
