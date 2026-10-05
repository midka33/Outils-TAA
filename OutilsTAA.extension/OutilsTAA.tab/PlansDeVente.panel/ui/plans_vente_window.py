# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre principale — détection des logements et prototype de contour optimisé."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from plans_vente.view_grouping import normalize_scale


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class HousingRow(object):
    def __init__(self, housing):
        self.Housing = housing
        self.Key = housing.key
        self.RoomCount = housing.room_count
        self.Levels = housing.levels_label


class SourceViewChoice(object):
    def __init__(self, candidate):
        self.Candidate = candidate
        self.Label = candidate.label


class PlansVenteWindow(forms.WPFWindow):

    def __init__(self, controller):
        self.controller = controller
        self._choices = []
        self._housing_rows = []
        self._source_view_choices = []

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(current_dir, "plans_vente.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        self._load_theme()
        self._load_context()
        self._clear_prototype_selection()

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
            self._housing_rows = [
                HousingRow(housing)
                for housing in result.housings
            ]
            self.HousingGrid.ItemsSource = self._housing_rows

            self.HousingCountText.Text = "{} logement(s) détecté(s).".format(
                result.housing_count
            )

            message = "{} logement(s), {} pièce(s) affectée(s).".format(
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
            self._clear_prototype_selection()
        except Exception as error:
            self.StatusText.Text = "Erreur pendant l'analyse."
            forms.alert(
                str(error),
                title="Plans de vente — Analyse",
                warn_icon=True,
            )
        finally:
            self.AnalyzeButton.IsEnabled = bool(self._choices)

    def HousingSelectionChanged(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        if housing is None:
            self._clear_prototype_selection()
            return

        try:
            candidates = self.controller.source_views_for_housing(housing)
        except Exception as error:
            self._clear_prototype_selection()
            self.PrototypeInfoText.Text = str(error)
            return

        self._source_view_choices = [
            SourceViewChoice(candidate)
            for candidate in candidates
        ]
        self.SourceViewCombo.ItemsSource = self._source_view_choices
        self.SourceViewCombo.SelectedIndex = 0 if self._source_view_choices else -1
        self.CreatePrototypeButton.IsEnabled = bool(self._source_view_choices)

        if self._source_view_choices:
            self.PrototypeInfoText.Text = (
                "Le prototype crée une vue dépendante avec un contour optimisé "
                "à partir de l'union réelle des pièces du logement."
            )
        else:
            self.PrototypeInfoText.Text = (
                "Aucune vue plan principale duplicable n'a été trouvée pour ce niveau."
            )

    def SourceViewChanged(self, sender, args):
        item = self.SourceViewCombo.SelectedItem
        candidate = getattr(item, "Candidate", None) if item is not None else None
        if candidate is not None and getattr(candidate, "scale", 0):
            self.TargetScaleTextBox.Text = str(candidate.scale)

        self.CreatePrototypeButton.IsEnabled = (
            self.HousingGrid.SelectedItem is not None
            and candidate is not None
        )

    def CreatePrototype_Click(self, sender, args):
        row = self.HousingGrid.SelectedItem
        housing = getattr(row, "Housing", None) if row is not None else None
        view_item = self.SourceViewCombo.SelectedItem
        candidate = (
            getattr(view_item, "Candidate", None)
            if view_item is not None
            else None
        )

        if housing is None or candidate is None:
            forms.alert(
                "Sélectionnez un logement et une vue source.",
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
            return

        try:
            margin_mm = self._parse_margin_mm()
            target_scale = self._parse_target_scale()
        except Exception as error:
            forms.alert(
                str(error),
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
            return

        confirmed = forms.alert(
            (
                "Créer une vue dépendante réelle pour le logement « {} » ?\n\n"
                "Vue source : {}\n"
                "Échelle : 1:{}\n"
                "Marge de crop : {} mm\n"
                "Contour : union optimisée des pièces\n\n"
                "Cette opération ajoute une vue au projet mais ne supprime rien."
            ).format(
                housing.key,
                candidate.name,
                target_scale,
                self._format_number(margin_mm),
            ),
            title="Plans de vente — Prototype contour optimisé",
            yes=True,
            no=True,
        )
        if not confirmed:
            return

        self.CreatePrototypeButton.IsEnabled = False
        try:
            result = self.controller.create_view_prototype(
                housing=housing,
                source_view_unique_id=candidate.unique_id,
                margin_mm=margin_mm,
                target_scale=target_scale,
            )

            status = "Vue prototype créée : {} — {}.".format(
                result.view_name,
                result.crop_mode,
            )
            if result.warning:
                status += " Avertissement : {}".format(result.warning)
            self.StatusText.Text = status

            message = (
                "Vue dépendante créée avec succès.\n\n"
                "Nom : {}\n"
                "Vue source : {}\n"
                "Vue principale PDV : {}\n"
                "Échelle : 1:{}\n"
                "Logement : {}\n"
                "Crop : {}"
            ).format(
                result.view_name,
                result.source_view_name,
                result.master_view_name,
                result.target_scale,
                result.housing_key,
                result.crop_mode,
            )

            if result.warning:
                message += "\n\nAvertissement :\n{}".format(result.warning)

            forms.alert(
                message,
                title="Plans de vente — Prototype",
                warn_icon=bool(result.warning),
            )
        except Exception as error:
            self.StatusText.Text = "Échec du prototype contour optimisé."
            forms.alert(
                str(error),
                title="Plans de vente — Prototype",
                warn_icon=True,
            )
        finally:
            self.CreatePrototypeButton.IsEnabled = (
                self.HousingGrid.SelectedItem is not None
                and self.SourceViewCombo.SelectedItem is not None
            )

    def _clear_prototype_selection(self):
        self._source_view_choices = []
        self.SourceViewCombo.ItemsSource = []
        self.SourceViewCombo.SelectedIndex = -1
        self.TargetScaleTextBox.Text = "50"
        self.CreatePrototypeButton.IsEnabled = False
        self.PrototypeInfoText.Text = (
            "Sélectionnez d'abord un logement dans le tableau."
        )

    def _parse_target_scale(self):
        raw = (self.TargetScaleTextBox.Text or "").strip()
        return normalize_scale(raw)

    def _parse_margin_mm(self):
        raw = (self.CropMarginTextBox.Text or "").strip().replace(",", ".")
        if not raw:
            raise ValueError("Saisissez une marge de crop.")
        try:
            value = float(raw)
        except Exception:
            raise ValueError("La marge de crop doit être un nombre.")
        if value < 0:
            raise ValueError("La marge de crop ne peut pas être négative.")
        return value

    @staticmethod
    def _format_number(value):
        if float(value).is_integer():
            return str(int(value))
        return str(value)

    def Close_Click(self, sender, args):
        self.Close()
