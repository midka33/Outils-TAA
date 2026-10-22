# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Lanceur commun pour Cotation et Etiquetage (Revit 2025.4)."""

from pyrevit import forms, revit, script
from Autodesk.Revit import DB

from annotations_service import AnnotationService, safe_name, room_value
from crash_trace import TRACE_PATH


class Choice(object):
    def __init__(self, value, label):
        self.value = value
        self.name = label

    def __str__(self):
        return self.name


def _choose_one(items, title):
    choices = [Choice(value, label) for value, label in items]
    if not choices:
        forms.alert("Aucune option compatible disponible.", title=title)
        return None
    return forms.SelectFromList.show(
        choices, title=title, name_attr="name", multiselect=False,
        button_name="Choisir")


def _select_views(service):
    candidates = service.list_views()
    chosen_ids = set(str(x) for x in revit.uidoc.Selection.GetElementIds())
    selected = [v for v in candidates if str(v.Id) in chosen_ids]
    if selected:
        return selected

    active = revit.active_view
    options = [Choice(view, "{} — 1:{} ({})".format(
        safe_name(view, "Vue"), view.Scale, safe_name(view.GenLevel, "Niveau"))) for view in candidates]
    defaults = [choice for choice in options
                if active and choice.value.Id == active.Id]
    chosen = forms.SelectFromList.show(
        options, title="Selectionner les vues a traiter",
        name_attr="name", multiselect=True,
        default=defaults, button_name="Traiter les vues")
    return [choice.value for choice in (chosen or [])]


def run(kind):
    title = "Etiquetage automatique" if kind == "tags" else "Cotation automatique"
    doc = revit.doc
    if not doc:
        forms.alert("Ouvrir un projet Revit.", title=title)
        return
    if doc.IsFamilyDocument:
        forms.alert("Ce module fonctionne sur un projet Revit, pas une famille.",
                    title=title)
        return

    service = AnnotationService(doc)
    views = _select_views(service)
    if not views:
        return

    diagnostic_room_uid = None
    if kind == "dims":
        # Apres crash complet : pas de traitement de masse ni groupe.
        # Selectionner explicitement une seule vue et une seule piece.
        if len(views) != 1:
            chosen_view = _choose_one(
                [(v, safe_name(v, "Vue")) for v in views],
                "Diagnostic crash - choisir UNE vue")
            if chosen_view is None:
                return
            views = [chosen_view.value]
        test_rooms = [
            room for room in service._rooms(views[0])
            if room.GroupId == DB.ElementId.InvalidElementId
        ]
        chosen_room = _choose_one([
            (str(room.UniqueId), "{} - {}".format(
                room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                room_value(room, DB.BuiltInParameter.ROOM_NAME, "Piece")))
            for room in test_rooms
        ], "Diagnostic securise : choisir UNE piece hors groupe")
        if chosen_room is None:
            return
        diagnostic_room_uid = chosen_room.value

    types = service.list_types(kind)
    picked = _choose_one([(x.unique_id, x.label) for x in types],
                         "{} - type Revit".format(title))
    if picked is None:
        return

    style = None
    if kind == "dims":
        styles = service.line_styles()
        picked_style = _choose_one(
            [(x.UniqueId, safe_name(x, "Ligne")) for x in styles],
            "Style des petites lignes de reference 2D")
        if picked_style is None:
            return
        style = doc.GetElement(picked_style.value)
        if style is None:
            forms.alert("Style de ligne indisponible.", title=title)
            return

    if kind == "dims":
        question = ("MODE DIAGNOSTIC APRES CRASH REVIT\n"
                    "Une seule piece hors groupe sera traitee.\n"
                    "Ne pas executer sur la maquette de production.\n"
                    "Journal persistant : {}\n"
                    "Lancer cet essai ?".format(TRACE_PATH))
    else:
        question = "Appliquer {} dans {} vue(s) ?".format(
            title.lower(), len(views))
    if not forms.alert(question, title=title, yes=True, no=True):
        return

    count, report = service.run(
        kind, views, picked.value, style,
        diagnostic_room_uid=diagnostic_room_uid)
    out = script.get_output()
    out.print_md("## {} - version beta".format(title))
    out.print_md("**{} annotation(s) creee(s) dans {} vue(s).**".format(
        count, len(views)))
    for line in report:
        out.print_md("- {}".format(str(line).replace("|", "/")))
    forms.alert("{} annotation(s) creee(s).\nConsulter le rapport pyRevit.".format(count),
                title=title)
