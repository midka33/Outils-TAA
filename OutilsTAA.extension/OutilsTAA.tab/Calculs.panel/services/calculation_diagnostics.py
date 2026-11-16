# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Diagnostics de groupes et de variantes, sans modification du modele."""


def element_id_value(element_id):
    if element_id is None:
        return None
    for attr in ("Value", "IntegerValue"):
        value = getattr(element_id, attr, None)
        if value is not None:
            return value
    try:
        return int(element_id)
    except (TypeError, ValueError):
        return None


def group_conflicts(document, room_by_key, operations):
    """Conflits entre valeurs calculees pour les occurrences d'un type de groupe.

    Une uniformisation n'est permise que si chaque occurrence a une seule
    valeur calculee; sinon, on risquerait d'ecraser des appartements distincts.
    """
    by_type = {}
    get_element = getattr(document, "GetElement", None)
    if get_element is None:
        return []

    for op in operations:
        room = room_by_key.get(op.room_key)
        group_id = getattr(room, "GroupId", None)
        instance_id = element_id_value(group_id)
        if instance_id is None or instance_id == -1:
            continue
        group = get_element(group_id)
        if group is None:
            continue
        type_id = getattr(getattr(group, "GroupType", None), "Id", None)
        if type_id is None:
            type_id = group.GetTypeId()
        type_key = element_id_value(type_id)
        if type_key is None:
            continue
        group_type = getattr(group, "GroupType", None)
        type_name = getattr(group_type, "Name", None) or str(type_key)
        item = by_type.setdefault(type_key, {
            "type_key": type_key, "name": type_name, "instances": {}
        })
        instance = item["instances"].setdefault(instance_id, {
            "name": getattr(group, "Name", None) or str(instance_id),
            "values": [], "room_keys": [],
        })
        instance["values"].append(op.value)
        instance["room_keys"].append(op.room_key)

    conflicts = []
    for type_key, item in sorted(by_type.items(), key=lambda pair: str(pair[0])):
        unique_values = set()
        candidates = []
        uniform_safe = True
        for instance_id, instance in sorted(item["instances"].items(),
                                            key=lambda pair: str(pair[0])):
            local_values = set(instance["values"])
            unique_values.update(local_values)
            if len(local_values) != 1:
                uniform_safe = False
                continue
            candidates.append({
                "instance_id": instance_id,
                "name": instance["name"],
                "value": instance["values"][0],
            })
        if len(unique_values) > 1:
            conflicts.append({
                "type_key": type_key,
                "name": item["name"],
                "candidates": candidates,
                "uniform_safe": uniform_safe,
                "room_keys": [
                    key for instance in item["instances"].values()
                    for key in instance["room_keys"]
                ],
            })
    return conflicts


def design_option_summary(document, rooms):
    """Decrit les options du projet et la provenance des surfaces des pieces.

    N'utilise pas ActiveView: le module lit les surfaces deja calculees par
    Revit pour chaque piece, quelle que soit sa vue d'affichage.
    """
    try:
        from Autodesk.Revit.DB import FilteredElementCollector, DesignOption
        options = list(FilteredElementCollector(document)
                       .OfClass(DesignOption).ToElements())
    except (ImportError, AttributeError):
        return []
    if not options:
        return []

    option_by_id = {}
    for option in options:
        option_id = element_id_value(option.Id)
        if option_id is not None:
            option_by_id[option_id] = option
    counts = {}
    main_count = 0
    unknown_count = 0
    for room in rooms:
        try:
            option = room.DesignOption
        except Exception:
            unknown_count += 1
            continue
        if option is None:
            main_count += 1
            continue
        option_id = element_id_value(getattr(option, "Id", None))
        if option_id is None:
            unknown_count += 1
        else:
            counts[option_id] = counts.get(option_id, 0) + 1

    result = ["Variantes de conception detectees dans le projet :"]
    for option in sorted(options, key=lambda value: getattr(value, "Name", "")):
        option_id = element_id_value(option.Id)
        count = counts.get(option_id, 0)
        state = "principale" if bool(getattr(option, "IsPrimary", False)) else "secondaire"
        result.append("- {} ({}) : {} piece(s) incluse(s)".format(
            getattr(option, "Name", "(sans nom)"), state, count))
    result.append("- Modele principal : {} piece(s) incluse(s).".format(main_count))
    if unknown_count:
        result.append("- Attribution de variante non lisible : {} piece(s).".format(unknown_count))
    result.append(
        "Surfaces lues dans Revit : les pieces du modele principal peuvent "
        "dependre des variantes principales pour leurs limites; les vues ne "
        "determinent pas le perimetre de cette commande."
    )
    return result
