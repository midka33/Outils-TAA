# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Renommage de paramètres de pièces et de notes textuelles Revit."""

from pyrevit import DB, revit
from room_parameter_edit_service import (
    collect_rooms, id_value, parameter_of, ParameterOption, room_label,
)
from room_parameters.text_transform_engine import transform
from room_parameters.format_engine import format_value, parameter_token


def _family_instances(scope):
    doc = revit.doc
    if scope == "Sélection actuelle":
        candidates = [doc.GetElement(element_id)
                      for element_id in revit.uidoc.Selection.GetElementIds()]
    else:
        if scope == "Vue active":
            if not DB.FilteredElementCollector.IsViewValidForElementIteration(doc, doc.ActiveView.Id):
                raise ValueError("La vue active ne permet pas de collecter les familles.")
            collector = DB.FilteredElementCollector(doc, doc.ActiveView.Id)
        else:
            collector = DB.FilteredElementCollector(doc)
        try:
            candidates = list(collector.OfClass(DB.FamilyInstance).ToElements())
        finally:
            collector.Dispose()
    return [item for item in candidates if isinstance(item, DB.FamilyInstance)
            and item.Symbol is not None and item.GroupId == DB.ElementId.InvalidElementId]


def collect_targets(category, scope, family_level="instance"):
    if category == "Pièces":
        items = [item for item in collect_rooms(scope)
                 if item.GroupId == DB.ElementId.InvalidElementId]
    elif category == "Textes":
        if scope == "Sélection actuelle":
            items = [revit.doc.GetElement(element_id)
                     for element_id in revit.uidoc.Selection.GetElementIds()]
        else:
            if scope == "Vue active":
                if not DB.FilteredElementCollector.IsViewValidForElementIteration(revit.doc, revit.doc.ActiveView.Id):
                    raise ValueError("La vue active ne permet pas de collecter les textes.")
                collector = DB.FilteredElementCollector(revit.doc, revit.doc.ActiveView.Id)
            else:
                collector = DB.FilteredElementCollector(revit.doc)
            try:
                items = list(collector.OfClass(DB.TextNote).ToElements())
            finally:
                collector.Dispose()
        items = [item for item in items if isinstance(item, DB.TextNote)
                 and item.GroupId == DB.ElementId.InvalidElementId]
    elif category == "Familles":
        instances = _family_instances(scope)
        items = [instance.Symbol for instance in instances] if family_level == "type" else instances
    else:
        raise ValueError("Catégorie inconnue.")
    return sorted({item.UniqueId: item for item in items}.values(),
                  key=lambda item: id_value(item.Id))


def target_label(element):
    if isinstance(element, DB.TextNote):
        return "{} (ID {})".format((element.Text or "").replace("\r", " ").replace("\n", " ")[:100], id_value(element.Id))
    if isinstance(element, DB.Architecture.Room):
        return room_label(element)
    if isinstance(element, DB.FamilyInstance):
        return "{} — {} (ID {})".format(element.Symbol.Family.Name,
                                       element.Symbol.Name, id_value(element.Id))
    if isinstance(element, DB.FamilySymbol):
        return "{} — Type : {} (ID {})".format(element.Family.Name,
                                              element.Name, id_value(element.Id))
    return "Élément ID {}".format(id_value(element.Id))


def writable_text_parameters(elements):
    found = {}
    for element in elements:
        number = (element.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER)
                  if isinstance(element, DB.Architecture.Room) else None)
        for parameter in element.Parameters:
            if parameter.StorageType != DB.StorageType.String or parameter.IsReadOnly:
                continue
            if number is not None and parameter.Id == number.Id:
                continue
            key = id_value(parameter.Id)
            if key not in found:
                found[key] = ParameterOption(parameter)
    return sorted(found.values(), key=lambda option: option.Label.lower())


def readable_parameters(elements):
    """Sources de formatage lisibles (texte, nombres, références Revit)."""
    found = {}
    for element in elements:
        for parameter in element.Parameters:
            if parameter.StorageType not in (DB.StorageType.String, DB.StorageType.Integer,
                                             DB.StorageType.Double, DB.StorageType.ElementId):
                continue
            key = id_value(parameter.Id)
            if key not in found:
                option = ParameterOption(parameter)
                option.Token = parameter_token(key)
                found[key] = option
    return sorted(found.values(), key=lambda option: option.Label.lower())


def parameter_display_value(parameter):
    if parameter.StorageType == DB.StorageType.String:
        return parameter.AsString() or ""
    display = parameter.AsValueString()
    if display:
        return display
    if parameter.StorageType == DB.StorageType.Integer:
        return str(parameter.AsInteger())
    if parameter.StorageType == DB.StorageType.Double:
        return str(parameter.AsDouble())
    if parameter.StorageType == DB.StorageType.ElementId:
        return str(id_value(parameter.AsElementId()))
    return ""


def prepare_text_renames(elements, parameter_id, operation, before_text, after_text,
                         add_once=False, format_aliases=None):
    """Constitue l'aperçu ; chaque type de famille n'apparaît qu'une seule fois."""
    changes = {}
    skipped = 0
    for index, element in enumerate(elements, 1):
        is_text_note = isinstance(element, DB.TextNote)
        parameter = None if is_text_note else parameter_of(element, parameter_id)
        if not is_text_note and (parameter is None or parameter.IsReadOnly
                                 or parameter.StorageType != DB.StorageType.String):
            skipped += 1
            continue
        before = (element.Text or "") if is_text_note else (parameter.AsString() or "")
        if operation == "format":
            family_name = (element.Symbol.Family.Name if isinstance(element, DB.FamilyInstance)
                           else element.Family.Name if isinstance(element, DB.FamilySymbol) else "")
            param_values = {}
            for candidate in element.Parameters:
                if candidate.StorageType in (DB.StorageType.String, DB.StorageType.Integer,
                                             DB.StorageType.Double, DB.StorageType.ElementId):
                    key = parameter_token(id_value(candidate.Id))
                    param_values[key] = parameter_display_value(candidate)
            after = format_value(before, before_text, index, family_name,
                                 param_values, format_aliases)
        else:
            after = transform(before, operation, before_text, after_text, add_once)
        if before == after:
            skipped += 1
            continue
        changes[element.UniqueId] = (element, parameter, before, after)
    return changes, skipped


def commit_text_renames(changes):
    """Écriture atomique après relecture de toutes les valeurs sources."""
    transaction = DB.Transaction(revit.doc, "TAA — Renommage multiple")
    try:
        if transaction.Start() != DB.TransactionStatus.Started:
            raise RuntimeError("Transaction non démarrée.")
        for element, parameter, before, after in changes:
            if isinstance(element, DB.TextNote):
                if (element.Text or "") != before or element.GroupId != DB.ElementId.InvalidElementId:
                    raise RuntimeError("Texte devenu indisponible ou modifié depuis l'aperçu.")
                # Revit peut réinitialiser les mises en forme locales lors d'un changement de Text.
                element.Text = after
                if element.Text != after:
                    raise RuntimeError("Écriture du texte refusée.")
                continue
            if parameter.IsReadOnly or (parameter.AsString() or "") != before:
                raise RuntimeError("Paramètre devenu non modifiable ou modifié depuis l'aperçu.")
            if isinstance(element, DB.FamilyInstance) and element.GroupId != DB.ElementId.InvalidElementId:
                raise RuntimeError("Une instance appartient désormais à un groupe.")
            if isinstance(element, DB.Architecture.Room) and element.GroupId != DB.ElementId.InvalidElementId:
                raise RuntimeError("Une pièce appartient désormais à un groupe.")
            if not parameter.Set(after) or parameter.AsString() != after:
                raise RuntimeError("Écriture refusée : {}".format(target_label(element)))
        if transaction.Commit() != DB.TransactionStatus.Committed:
            raise RuntimeError("Transaction non validée.")
        return len(changes)
    except Exception:
        if transaction.GetStatus() == DB.TransactionStatus.Started:
            transaction.RollBack()
        raise
    finally:
        transaction.Dispose()
