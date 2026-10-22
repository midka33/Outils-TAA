# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Lanceur commun pour Cotation et Etiquetage (Revit 2025.4)."""

from pyrevit import forms, revit, script
from Autodesk.Revit import DB

from annotations_service import AnnotationService


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
        view.Name, view.Scale, view.GenLevel.Name)) for view in candidates]
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

    types = service.list_types(kind)
    picked = _choose_one([(x.unique_id, x.label) for x in types],
                         "{} - type Revit".format(title))
    if picked is None:
        return

    style = None
    if kind == "dims":
        styles = service.line_styles()
        picked_style = _choose_one(
            [(x.UniqueId, x.Name) for x in styles],
            "Style des petites lignes de reference 2D")
        if picked_style is None:
            return
        style = doc.GetElement(picked_style.value)
        if style is None:
            forms.alert("Style de ligne indisponible.", title=title)
            return

    question = ("Appliquer {} dans {} vue(s) ?\n"
                "Les groupes existants seront conserves ; "
                "les groupes de details attaches seront testes.\n"
                "Une operation de groupe refusee par Revit sera annulee."
                .format(title.lower(), len(views)))
    if not forms.alert(question, title=title, yes=True, no=True):
        return

    count, report = service.run(kind, views, picked.value, style)
    out = script.get_output()
    out.print_md("## {} - version beta".format(title))
    out.print_md("**{} annotation(s) creee(s) dans {} vue(s).**".format(
        count, len(views)))
    for line in report:
        out.print_md("- {}".format(str(line).replace("|", "/")))
    forms.alert("{} annotation(s) creee(s).\nConsulter le rapport pyRevit.".format(count),
                title=title)
