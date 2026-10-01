# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre principale — Étape 01 : détection des logements."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class HousingRow(object):
    def __init__(self, housing):
        self.Key = housing.key
        self.RoomCount = housing.room_count
        self.Levels = housing.levels_label


class PlansVenteWindow(forms.WPFWindow):

    def __init__(self, controller):
        self.controller = controller
        self._choices = []

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(current_dir, "plans_vente.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        self._load_theme()
        self._load_context()

    def _load_theme(self):
        panel_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        extension_dir = os.path.abspath(os.path.join(panel_dir, "..", ".."))
        resource_path = os.path.join(
            extension_dir,
            "resources",
            "ui",
            "taa_theme.xaml",
        )
        load_resource_dictionary(self, resource_path)

    def _load_context(self):
        self.StatusText.Text = "Lecture des pièces et paramètres..."
        context = self.controller.load_context()

        self.RoomCountText.Text = "{} pièce(s) détectée(s).".format(
            context.rooms_count
        )

        self._choices = self._build_parameter_choices(context.parameters)
        self.HousingParameterCombo.ItemsSource = self._choices

        if self._choices:
            self.HousingParameterCombo.SelectedIndex = 0
            self.AnalyzeButton.IsEnabled = True
            self.StatusText.Text = (
                "Choisissez le paramètre logement puis lancez l'analyse."
            )
        else:
            self.AnalyzeButton.IsEnabled = False
            self.StatusText.Text = (
                "Aucun paramètre texte n'a été trouvé sur les pièces."
            )

    @staticmethod
    def _build_parameter_choices(descriptors):
        descriptors = list(descriptors or [])
        name_counts = {}

        for descriptor in descriptors:
            key = descriptor.name.lower()
            name_counts[key] = name_counts.get(key, 0) + 1

        choices = []
        for descriptor in descriptors:
            label = descriptor.name
            if name_counts.get(descriptor.name.lower(), 0) > 1:
                label = "{} [{}]".format(
                    descriptor.name,
                    PlansVenteWindow._identity_label(descriptor),
                )
            choices.append(ParameterChoice(label, descriptor))

        return choices

    @staticmethod
    def _identity_label(descriptor):
        kind = getattr(descriptor, "identity_kind", "")
        if kind == "SHARED_GUID":
            return "partagé"
        if kind == "BUILT_IN":
            return "Revit"
        if kind == "DEFINITION":
            return "projet"
        return "nom"

    def Analyze_Click(self, sender, args):
        item = self.HousingParameterCombo.SelectedItem
        descriptor = getattr(item, "descriptor", None) if item is not None else None

        self.AnalyzeButton.IsEnabled = False
        try:
            result = self.controller.analyze(descriptor)
            self.HousingGrid.ItemsSource = [
                HousingRow(housing)
                for housing in result.housings
            ]

            self.HousingCountText.Text = "{} logement(s) détecté(s).".format(
                result.housing_count
            )

            message = (
                "{} logement(s), {} pièce(s) affectée(s)."
            ).format(
                result.housing_count,
                result.room_count,
            )
            if result.empty_value_count:
                message += " {} pièce(s) sans valeur ignorée(s).".format(
                    result.empty_value_count
                )
            if result.skipped_room_count:
                message += " {} élément(s) invalide(s) ignoré(s).".format(
                    result.skipped_room_count
                )

            self.StatusText.Text = message
        except Exception as error:
            self.StatusText.Text = "Erreur pendant l'analyse."
            forms.alert(
                str(error),
                title="Plans de vente — Analyse",
                warn_icon=True,
            )
        finally:
            self.AnalyzeButton.IsEnabled = bool(self._choices)

    def Close_Click(self, sender, args):
        self.Close()
