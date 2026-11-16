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


def variant_group_key(room, group_value):
    """Sépare les totaux métier par scénario de variante Revit.

    Modèle principal et variantes principales : scénario de référence commun.
    Variantes secondaires : chacune possède son scénario indépendant.
    Les clés historiques du scénario principal restent inchangées.
    """
    from common.exceptions import ValidationError

    try:
        option = room.DesignOption
    except AttributeError:
        return group_value
    except Exception as error:
        raise ValidationError(
            "Variante de conception illisible pour une pièce : {}.".format(error)
        )
    if group_value is None or (isinstance(group_value, str) and not group_value.strip()):
        return group_value
    if option is None:
        return group_value
    try:
        if bool(option.IsPrimary):
            return group_value
        option_id = element_id_value(option.Id)
        if option_id is None:
            raise ValueError("identifiant manquant")
    except Exception as error:
        raise ValidationError(
            "Impossible de déterminer le scénario de variante : {}.".format(error)
        )
    # Marqueur explicite pour éviter toute collision avec une valeur métier.
    return ("TAA-VARIANTE-SECONDAIRE", str(option_id), group_value)


def variant_group_label(group_key, document=None):
    if not (
        isinstance(group_key, tuple)
        and len(group_key) == 3
        and group_key[0] == "TAA-VARIANTE-SECONDAIRE"
    ):
        return group_key
    option_name = group_key[1]
    if document is not None:
        try:
            from Autodesk.Revit.DB import ElementId
            option = document.GetElement(ElementId(int(group_key[1])))
            if option is not None:
                option_name = getattr(option, "Name", option_name)
        except (ImportError, AttributeError, ValueError, TypeError):
            pass
    return "{} — {}".format(group_key[2], option_name)



def shared_apartments_across_variants(result, document=None):
    """Retourne les appartements calculés dans plusieurs scénarios.

    Le diagnostic ne change jamais les sommes ni la liste des membres.
    Chaque entrée contient les totaux de chaque scénario pour informer
    l'utilisateur AVANT toute écriture dans le modèle.
    """
    by_apartment = {}
    for group_key, value in result.totals.items():
        if (
            isinstance(group_key, tuple)
            and len(group_key) == 3
            and group_key[0] == "TAA-VARIANTE-SECONDAIRE"
        ):
            apartment = group_key[2]
            scenario_key = ("secondary", group_key[1])
        else:
            apartment = group_key
            scenario_key = ("reference",)
        try:
            by_apartment.setdefault(apartment, []).append({
                "scenario_key": scenario_key,
                "label": (
                    str(group_key) + " — scénario de référence"
                    if scenario_key[0] == "reference"
                    else str(variant_group_label(group_key, document))
                ),
                "total": value,
            })
        except TypeError:
            # Les regroupements non hachables sont déjà rejetés par le moteur.
            continue

    duplicates = []
    for apartment, scenarios in by_apartment.items():
        if len(set(item["scenario_key"] for item in scenarios)) < 2:
            continue
        duplicates.append({
            "apartment": apartment,
            "scenarios": sorted(scenarios, key=lambda item: item["label"]),
        })
    return sorted(duplicates, key=lambda item: str(item["apartment"]))


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

    Ne depend pas de la vue active : le module lit les surfaces deja calculees par
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
    primary_names = [getattr(option, "Name", "(sans nom)")
                     for option in options if bool(getattr(option, "IsPrimary", False))]
    for option in sorted(options, key=lambda value: getattr(value, "Name", "")):
        option_id = element_id_value(option.Id)
        count = counts.get(option_id, 0)
        state = "principale" if bool(getattr(option, "IsPrimary", False)) else "secondaire"
        result.append("- {} ({}) : {} piece(s) incluse(s)".format(
            getattr(option, "Name", "(sans nom)"), state, count))
    result.append("- Modele principal : {} piece(s) incluse(s).".format(main_count))
    if main_count and primary_names:
        result.append(
            "Pour les pieces du modele principal, les limites peuvent dependre "
            "des variantes principales suivantes : {}.".format(
                ", ".join(sorted(primary_names))
            )
        )
    if unknown_count:
        result.append("- Attribution de variante non lisible : {} piece(s).".format(unknown_count))
    result.append(
        "Surfaces lues dans Revit : les pieces du modele principal peuvent "
        "dependre des variantes principales pour leurs limites; les vues ne "
        "determinent pas le perimetre de cette commande."
    )
    return result

def empty_result_explanation(prepared):
    """Diagnostic factuel si aucun total n'est calculé.

    Ne déduit jamais la cause d'une absence de résultat des seuls réglages
    du paramètre cible. La somme est calculée AVANT toute transaction.
    """
    skipped = getattr(getattr(prepared, "result", None), "skipped", []) or []
    counts = {}
    for item in skipped:
        reason = str(getattr(item, "reason", "other"))
        counts[reason] = counts.get(reason, 0) + 1

    request = prepared.request
    group_name = getattr(request.group_parameter, "name", "regroupement")
    source_name = getattr(request.source_parameter, "name", "source")
    lines = [
        "Aucune somme n'a pu être calculée sur {} pièce(s) retenue(s).".format(
            prepared.filtered_rooms
        )
    ]
    if counts.get("empty_group"):
        lines.append(
            "{} pièce(s) sans valeur dans '{}'."
            .format(counts["empty_group"], group_name)
        )
    if counts.get("non_numeric_source"):
        lines.append(
            "{} pièce(s) avec une valeur non numérique ou vide dans '{}'."
            .format(counts["non_numeric_source"], source_name)
        )
    if counts.get("invalid_group"):
        lines.append(
            "{} pièce(s) avec un regroupement inexploitable."
            .format(counts["invalid_group"])
        )
    if not skipped:
        lines.append("Aucune opération de calcul n'a été produite.")
    lines.append(
        "Vérifiez les valeurs de regroupement et de source dans les pièces. "
        "La gestion des groupes ne change pas le calcul des sommes et aucun "
        "paramètre n'a été modifié."
    )
    return "\n".join(lines)
