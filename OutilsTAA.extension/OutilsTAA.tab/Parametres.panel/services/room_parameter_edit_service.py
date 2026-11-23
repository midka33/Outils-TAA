# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Accès Revit et mutations des paramètres : propriétaire métier unique."""

from pyrevit import DB, revit
from room_parameters.numbering_engine import parse_sequence, proposed_assignments
from room_parameters.text_transform_engine import transform
from room_parameters.duplicate_checker import detect_collisions


def id_value(element_id):
    return element_id.Value if hasattr(element_id, "Value") else element_id.IntegerValue


def collect_rooms(scope):
    doc = revit.doc
    if scope == "Sélection actuelle":
        elements = [doc.GetElement(element_id) for element_id in revit.uidoc.Selection.GetElementIds()]
        found = []
        for element in elements:
            if isinstance(element, DB.Architecture.Room):
                found.append(element)
            elif isinstance(element, DB.Architecture.RoomTag):
                if not element.IsTaggingLink and element.Room is not None:
                    found.append(element.Room)
    else:
        if scope == "Vue active":
            if not DB.FilteredElementCollector.IsViewValidForElementIteration(doc, doc.ActiveView.Id):
                raise ValueError("La vue active ne permet pas de collecter les pièces.")
            collector = DB.FilteredElementCollector(doc, doc.ActiveView.Id)
        else:
            collector = DB.FilteredElementCollector(doc)
        try:
            found = list(collector.OfCategory(DB.BuiltInCategory.OST_Rooms)
                         .WhereElementIsNotElementType().ToElements())
        finally:
            collector.Dispose()
    return sorted({room.UniqueId: room for room in found
                   if isinstance(room, DB.Architecture.Room)}.values(),
                  key=lambda room: id_value(room.Id))


def room_label(room):
    number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER)
    name = room.get_Parameter(DB.BuiltInParameter.ROOM_NAME)
    return "{} — {} (ID {})".format(number.AsString() if number else "",
                                  name.AsString() if name else "", id_value(room.Id))


class ParameterOption(object):
    def __init__(self, parameter):
        self.Id = id_value(parameter.Id)
        self.Label = "{} [ID {}]".format(parameter.Definition.Name, self.Id)


def parameter_of(room, parameter_id):
    for parameter in room.Parameters:
        if id_value(parameter.Id) == parameter_id:
            return parameter
    return None


def parameter_options():
    found = {}
    for room in collect_rooms("Projet entier"):
        if room.GroupId != DB.ElementId.InvalidElementId:
            continue
        number = room.get_Parameter(DB.BuiltInParameter.ROOM_NUMBER)
        for parameter in room.Parameters:
            if parameter.StorageType != DB.StorageType.String or parameter.IsReadOnly:
                continue
            if number is not None and parameter.Id == number.Id:
                continue
            key = id_value(parameter.Id)
            if key not in found:
                found[key] = ParameterOption(parameter)
    return sorted(found.values(), key=lambda item: item.Label.lower())


def prepare_changes(rooms, parameter_id, numbering, operation, input_text,
                    extra_text, add_once=False):
    """Retourne (changements par UniqueId, nombre ignoré), sans écriture."""
    if numbering:
        spec = parse_sequence(input_text, operation, int(extra_text))
        proposals = dict(proposed_assignments([room.UniqueId for room in rooms], spec))
    changes = {}
    skipped = 0
    for room in rooms:
        if room.GroupId != DB.ElementId.InvalidElementId:
            skipped += 1
            continue
        parameter = parameter_of(room, parameter_id)
        if parameter is None or parameter.IsReadOnly or parameter.StorageType != DB.StorageType.String:
            skipped += 1
            continue
        before = parameter.AsString() or ""
        after = (proposals[room.UniqueId] if numbering else
                 transform(before, operation, input_text, extra_text, add_once))
        if before == after:
            skipped += 1
            continue
        changes[room.UniqueId] = (room, parameter, before, after)
    return changes, skipped


def check_collisions(changes, parameter_id, allow_shared=False):
    existing = []
    for room in collect_rooms("Projet entier"):
        parameter = parameter_of(room, parameter_id)
        if parameter is not None:
            existing.append((room.UniqueId, parameter.AsString() or ""))
    return detect_collisions([(key, item[3]) for key, item in changes.items()],
                             existing, allow_shared)


def commit_changes(changes):
    """Une transaction pour le lot ; toute écriture refusée déclenche rollback."""
    transaction = DB.Transaction(revit.doc, "TAA — Paramètres des pièces")
    try:
        if transaction.Start() != DB.TransactionStatus.Started:
            raise RuntimeError("Transaction non démarrée.")
        for room, parameter, before, after in changes:
            if room.GroupId != DB.ElementId.InvalidElementId or parameter.IsReadOnly:
                raise RuntimeError("Une pièce est devenue non modifiable.")
            if (parameter.AsString() or "") != before:
                raise RuntimeError("Une valeur a changé depuis l'aperçu.")
            if not parameter.Set(after) or parameter.AsString() != after:
                raise RuntimeError("Écriture refusée : {}".format(room_label(room)))
        if transaction.Commit() != DB.TransactionStatus.Committed:
            raise RuntimeError("Transaction non validée par Revit.")
        return len(changes)
    except Exception:
        if transaction.GetStatus() == DB.TransactionStatus.Started:
            transaction.RollBack()
        raise
    finally:
        transaction.Dispose()
