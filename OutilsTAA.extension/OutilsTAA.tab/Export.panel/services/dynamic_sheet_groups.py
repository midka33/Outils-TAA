# -*- coding: utf-8 -*-
"""Résolution non destructive des dossiers dynamiques Export (Revit 2025)."""
import hashlib

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource


def read_parameter(sheet, name):
    """Lecture identique au filtre de feuilles ; aucune mutation du RVT."""
    if not name:
        raise ValueError("Le paramètre de classement n'est pas défini.")
    try:
        candidates = sheet.GetParameters(name)
        if candidates is not None and len(candidates) > 1:
            raise ValueError("Paramètre ambigu (plusieurs définitions) : {}".format(name))
    except (AttributeError, TypeError):
        pass
    except ValueError:
        raise
    except Exception:
        pass
    try:
        p = sheet.LookupParameter(name)
        if p is None:
            return None
        value = p.AsString() or p.AsValueString()
        return str(value).strip() if value is not None else ""
    except Exception:
        return None



def group_identifier(parent_id, group_key):
    """Identifiant stable d'un groupe, y compris lorsque sa valeur est vide."""
    token = hashlib.sha1(
        ("vide" if group_key is None else "valeur:" + group_key).encode(
            "utf-8")).hexdigest()[:16]
    return "dyn-{}-{}".format(parent_id, token)


def resolve_dynamic(publication_set, sheets):
    """Retourne (feuilles directes, sous-dossiers virtuels) sans écrire le JSON.

    Un paramètre indisponible sur toutes les feuilles bloque l'opération pour
    éviter d'interpréter une lecture impossible comme un résultat vide.
    """
    source = publication_set.source
    if source is None or source.mode != PublicationSource.DYNAMIC:
        return (list(publication_set.items or []), [])
    if not source.parameter_name or source.parameter_value is None:
        raise ValueError("Règle de sélection dynamique incomplète.")
    all_sheets = list(sheets or [])
    main_values = [(sheet, read_parameter(sheet, source.parameter_name))
                   for sheet in all_sheets]
    if all_sheets and all(v is None for _, v in main_values):
        raise ValueError("Paramètre introuvable : {}".format(source.parameter_name))
    matched = [sheet for sheet, value in main_values
               if value is not None and value == source.parameter_value]
    groups = {}
    if source.group_parameter:
        raw_groups = [(sheet, read_parameter(sheet, source.group_parameter))
                      for sheet in matched]
        if matched and all(value is None for _, value in raw_groups):
            raise ValueError("Paramètre de sous-dossier introuvable : {}".format(
                source.group_parameter))
        for sheet, value in raw_groups:
            key = value if value else None
            groups.setdefault(key, []).append(sheet)
    else:
        groups[None] = matched

    def items(values):
        result = []
        for sheet in sorted(values, key=lambda v: (
                str(v.SheetNumber or "").lower(), str(v.Name or "").lower())):
            result.append(PublicationItem(
                str(sheet.UniqueId), sheet.Id.IntegerValue, "SHEET",
                sheet.SheetNumber, sheet.Name))
        return result

    if not source.group_parameter:
        return (items(matched), [])

    result = []
    frozen_ids = set(str(value) for value in (
        getattr(source, "frozen_group_ids", None) or []))
    for idx, key in enumerate(sorted(
            groups, key=lambda value: (value is None, (value or "").lower()))):
        group_id = group_identifier(publication_set.id, key)
        # Un groupe figé reste dans le JSON comme dossier manuel. Ne pas
        # le recréer ou y ajouter de feuilles après changement de Revit.
        if str(group_id) in frozen_ids:
            continue
        child = PublicationSet(
            name=key if key is not None else "Sans valeur",
            items=items(groups[key]), source=PublicationSource(
                PublicationSource.MANUAL),
            set_id=group_id, persistent=False, folder_id=publication_set.id)
        child.tree_order = idx
        child.sort_order = idx
        child.dynamic_virtual = True
        child.dynamic_group_key = key
        result.append(child)
    return ([], result)
