# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Lanceur commun pour Cotation et Etiquetage (Revit 2025.4)."""

from pyrevit import forms, revit, script
from Autodesk.Revit import DB

from annotations_service import AnnotationService, safe_name, room_value
from crash_trace import TRACE_PATH
from apartment_scope import (parameter_candidates, apartment_values,
                             available_buildings, filter_apartment,
                             MAX_APARTMENT_ROOMS)


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
    diagnostic_room_uids = None
    chosen_scope = "room"
    apartment_description = ""
    if kind == "dims":
        # Conserver le mode diagnostic une piece APRES CRASH REVIT.
        # Elargir uniquement a UN appartement, UNE vue, sans groupe,
        # avec au maximum 12 pieces et liste explicite pre-confirmee.
        if len(views) != 1:
            chosen_view = _choose_one(
                [(v, safe_name(v, "Vue")) for v in views],
                "Diagnostic securise : choisir UNE vue")
            if chosen_view is None:
                return
            views = [chosen_view.value]
        test_rooms = service._rooms(views[0])
        scope = _choose_one([
            ("room", "Une piece (diagnostic securise)"),
            ("apartment", "Un appartement dans cette vue (beta, 12 pieces max.)"),
        ], "Cotation beta : choisir le perimetre")
        if scope is None:
            return
        chosen_scope = scope.value
        if chosen_scope == "room":
            room_candidates = [
                room for room in test_rooms
                if room.GroupId == DB.ElementId.InvalidElementId
            ]
            chosen_room = _choose_one([
                (str(room.UniqueId), "{} - {}".format(
                    room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                    room_value(room, DB.BuiltInParameter.ROOM_NAME, "Piece")))
                for room in room_candidates
            ], "Diagnostic securise : choisir UNE piece hors groupe")
            if chosen_room is None:
                return
            diagnostic_room_uid = chosen_room.value
        else:
            # Ne jamais deviner le numero de logement a partir du numero
            # de piece. Choix explicite du parametre d'instance Revit.
            candidate_names = parameter_candidates(test_rooms)
            if not candidate_names:
                forms.alert(
                    "Aucun parametre d'instance partage entre plusieurs "
                    "pieces visibles. Renseigner un identifiant de "
                    "logement sur chaque piece ou choisir UNE piece.",
                    title=title)
                return
            chosen_param = _choose_one([
                (name, name) for name in candidate_names
            ], "Choisir le PARAMETRE identifiant l'appartement")
            if chosen_param is None:
                return
            apartment_parameter = chosen_param.value
            groups = apartment_values(test_rooms, apartment_parameter)
            chosen_value = _choose_one([
                (value, "{} ({} pieces visibles)".format(value, len(items)))
                for value, items in groups
            ], "Choisir UN appartement : {}".format(apartment_parameter))
            if chosen_value is None:
                return
            apartment_value = chosen_value.value

            building_parameter = None
            building_value = None
            apartment_candidates = [
                room for room in test_rooms
                if str(room.UniqueId) in set(
                    str(item.UniqueId) for value, items in groups
                    if value == apartment_value for item in items)
            ]
            building_names = [
                name for name in parameter_candidates(apartment_candidates)
                if name != apartment_parameter and any(
                    marker in name.lower() for marker in
                    ("batiment", "bâtiment", "immeuble", "building", "bloc"))
                and len(available_buildings(apartment_candidates, name)) > 1
            ]
            if building_names:
                chosen_building_param = _choose_one([
                    (name, name) for name in building_names
                ], "Plusieurs batiments pour cet identifiant : "
                   "choisir le parametre de BATIMENT")
                if chosen_building_param is None:
                    return
                building_parameter = chosen_building_param.value
                chosen_building = _choose_one([
                    (value, value) for value in
                    available_buildings(apartment_candidates, building_parameter)
                ], "Choisir le batiment de l'appartement")
                if chosen_building is None:
                    return
                building_value = chosen_building.value

            try:
                selected_rooms = filter_apartment(
                    test_rooms, apartment_parameter, apartment_value,
                    building_parameter=building_parameter,
                    building_value=building_value,
                    max_rooms=MAX_APARTMENT_ROOMS)
            except ValueError as exc:
                forms.alert(str(exc), title=title)
                return
            grouped_rooms = [
                room for room in selected_rooms
                if room.GroupId != DB.ElementId.InvalidElementId
            ]
            if grouped_rooms:
                forms.alert(
                    "Cet appartement contient {} piece(s) dans un "
                    "groupe de modele. La cotation par appartement ne "
                    "prend pas encore en charge les groupes ; aucune "
                    "annotation ne sera creee.".format(len(grouped_rooms)),
                    title=title)
                return
            diagnostic_room_uids = [str(room.UniqueId)
                                    for room in selected_rooms]
            room_labels = [
                "{} - {}".format(
                    room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                    room_value(room, DB.BuiltInParameter.ROOM_NAME, "Piece"))
                for room in selected_rooms
            ]
            apartment_description = (
                "Parametre : {} = {}{}\n"
                "Vue : {}\n"
                "Pieces visibles retenues ({} / {} maximum) :\n - {}"
            ).format(
                apartment_parameter, apartment_value,
                (" ; {} = {}".format(building_parameter, building_value)
                 if building_parameter else ""),
                safe_name(views[0], "Vue"), len(selected_rooms),
                MAX_APARTMENT_ROOMS, "\n - ".join(room_labels))
            # Le choix du parametre peut etre erroné (ex. Phase, Niveau) :
            # faire verifier la liste de toutes les pieces par l'utilisateur.
            if not forms.alert(
                    "VERIFIER LE PERIMETRE DE L'APPARTEMENT\n\n"
                    + apartment_description
                    + "\n\nCes pieces sont-elles exactement celles "
                      "de cet appartement ?",
                    title=title, yes=True, no=True):
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
            [(x.UniqueId, safe_name(x, "Ligne")) for x in styles],
            "Style des petites lignes de reference 2D")
        if picked_style is None:
            return
        style = doc.GetElement(picked_style.value)
        if style is None:
            forms.alert("Style de ligne indisponible.", title=title)
            return

    if kind == "dims":
        if chosen_scope == "apartment":
            question = (
                "MODE BETA APPARTEMENT APRES CRASH REVIT\n"
                "{}\n\n"
                "Chaque piece sera traitee dans sa propre transaction.\n"
                "Le traitement s'arrete au premier echec technique.\n"
                "AUCUN groupe et AUCUNE autre vue ne seront modifies.\n"
                "Tester UNIQUEMENT sur une COPIE du projet Revit, "
                "Revit enregistre et autres fichiers synchronises.\n"
                "Journal persistant : {}\n"
                "Lancer la cotation des {} pieces ?"
            ).format(apartment_description, TRACE_PATH,
                     len(diagnostic_room_uids))
        else:
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
        diagnostic_room_uid=diagnostic_room_uid,
        diagnostic_room_uids=diagnostic_room_uids)
    out = script.get_output()
    out.print_md("## {} - version beta".format(title))
    out.print_md("**{} annotation(s) creee(s) dans {} vue(s).**".format(
        count, len(views)))
    for line in report:
        out.print_md("- {}".format(str(line).replace("|", "/")))
    forms.alert("{} annotation(s) creee(s).\nConsulter le rapport pyRevit.".format(count),
                title=title)
