# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Une seule fenêtre de validation et de résolution pour Calculs des pièces."""

import os

from pyrevit import forms
from System.Windows import Visibility
from System.Windows.Controls import ComboBox, TextBlock

from common.wpf_resources import load_resource_dictionary


class ReviewChoice(object):
    def __init__(self, label, value):
        self.label = label
        self.value = value


class CalculationReviewWindow(forms.WPFWindow):

    def __init__(self, prepared, format_value, owner=None,
                 uniform_guidance=None):
        xaml_path = os.path.join(os.path.dirname(__file__), "calculation_review.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        if owner is not None:
            self.Owner = owner
        panel_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        extension_dir = os.path.abspath(os.path.join(panel_dir, "..", ".."))
        load_resource_dictionary(
            self, os.path.join(extension_dir, "resources", "ui", "taa_theme.xaml")
        )

        self.prepared = prepared
        self.format_value = format_value
        self.uniform_guidance = uniform_guidance
        self._uniform_combos = {}
        self._conflicts = list(prepared.group_conflicts)
        request = prepared.request
        mode = getattr(request, "variant_mode", "separate")
        self.SummaryText.Text = (
            "{} pièces • {} totaux • Destination : {}".format(
                len(prepared.operations),
                prepared.result.group_count,
                request.target_parameter.name,
            )
        )
        count = len(prepared.shared_variant_apartments)
        if mode == "combine":
            self.VariantsText.Text = (
                "Variantes additionnées. Risque de double comptage de solutions "
                "alternatives. Le total sera écrit dans chaque pièce du même "
                "appartement."
            )
        elif count:
            self.VariantsText.Text = (
                "{} appartement(s) dans plusieurs variantes : "
                "les surfaces restent séparées.".format(count)
            )
        else:
            self.VariantsText.Text = "Surfaces séparées par variante."
        self.WarningText.Text = ""
        if prepared.warnings:
            # Les détails restent dans le rapport facultatif ; les risques
            # non déjà couverts par le choix de groupes sont visibles ici.
            other_warnings = [
                str(message) for message in prepared.warnings
                if "aligné par type de groupe" not in str(message)
            ]
            if other_warnings:
                warning = other_warnings[0]
                self.WarningText.Text = (
                    "Attention : " + warning[:180]
                    + ("…" if len(warning) > 180 else "")
                )
                self.WarningText.ToolTip = "\n".join(other_warnings)
        self.ErrorText.Text = ""

        self._requested_group_mode = getattr(request, "group_mode", "auto")
        self._automatic_uniform = False
        self.UniformChoices.Visibility = Visibility.Collapsed
        self.GroupModeCombo.Visibility = Visibility.Collapsed
        if not self._conflicts:
            self.GroupSection.Visibility = Visibility.Collapsed
        elif self._requested_group_mode == "vary":
            self.GroupSection.Visibility = Visibility.Collapsed
        elif (all(item["uniform_safe"] for item in self._conflicts)
              and not getattr(prepared, "uniform_plan_error", None)):
            self._automatic_uniform = True
            self.GroupHint.Text = (
                "Choisissez une valeur commune par type de groupe. "
                "Si Revit ne peut pas conserver son alignement, le parametre "
                "autorisera durablement des valeurs differentes."
            )
            self._build_uniform_choices()
        else:
            self.GroupSection.Visibility = Visibility.Collapsed
            self.WarningText.Text += (
                "\nLes groupes ne peuvent pas etre uniformises sans risque : "
                "les surfaces seront ecrites individuellement et le parametre "
                "autorisera durablement des valeurs differentes entre groupes."
            )

    def GroupMode_Changed(self, sender, args):
        if not hasattr(self, "_conflicts"):
            return
        selected = getattr(self.GroupModeCombo.SelectedItem, "value", None)
        self.UniformChoices.Visibility = (
            Visibility.Visible if selected == "uniform"
            else Visibility.Collapsed
        )
        if selected == "uniform":
            extra_count = len(getattr(self.prepared, "uniform_extra_members", []))
            if extra_count:
                self.GroupHint.Text = (
                    "{} membre(s) de groupes homologues seront aussi "
                    "modifiés, y compris hors du filtre.".format(extra_count)
                )
        if selected != "uniform" or self._uniform_combos:
            return
        self._build_uniform_choices()

    def _build_uniform_choices(self):
        self.UniformChoices.Visibility = Visibility.Visible
        if self._uniform_combos:
            return
        for conflict in self._conflicts:
            title = TextBlock()
            title.Text = "Type de groupe : {}".format(conflict["name"])
            title.Margin = self._thickness(0, 8, 0, 4)
            self.UniformChoices.Children.Add(title)
            control = ComboBox()
            control.DisplayMemberPath = "label"
            control.Style = self.FindResource("TAAComboBox")
            control.ItemsSource = [
                ReviewChoice(
                    "{} — {}".format(
                        item["name"],
                        self.format_value(item["value"], self.prepared.request),
                    ),
                    item["value"],
                ) for item in conflict["candidates"]
            ]
            control.SelectedIndex = -1
            self.UniformChoices.Children.Add(control)
            self._uniform_combos[conflict["type_key"]] = control

    @staticmethod
    def _thickness(left, top, right, bottom):
        from System.Windows import Thickness
        return Thickness(left, top, right, bottom)

    def Confirm_Click(self, sender, args):
        prepared = self.prepared
        mode = getattr(prepared.request, "variant_mode", "separate")
        group_mode = getattr(prepared, "group_mode", "restore")
        selected_values = {}
        if self._conflicts:
            if self._requested_group_mode == "vary":
                group_mode = "vary"
            elif self._automatic_uniform:
                group_mode = "uniform"
                for conflict in self._conflicts:
                    combo = self._uniform_combos.get(conflict["type_key"])
                    choice = getattr(combo, "SelectedItem", None)
                    if choice is None:
                        self.ErrorText.Text = (
                            "Choisissez une valeur pour chaque type de groupe."
                        )
                        return
                    selected_values[conflict["type_key"]] = choice.value
            else:
                # Les types incompatibles sont traites sans uniformisation.
                group_mode = "vary"
        if group_mode == "uniform" and self.uniform_guidance is not None:
            try:
                notice = self.uniform_guidance(prepared, selected_values)
            except Exception as error:
                self.ErrorText.Text = (
                    "Verification du changement de parametre impossible : {}."
                    .format(error)
                )
                return
            if notice:
                # Le notice n'est plus bloquant : la gestion des groupes est
                # automatique et l'utilisateur en a ete informe dans l'accueil.
                self.WarningText.Text = notice

        # Les décisions sont posées ensemble, au dernier clic seulement.
        prepared.group_mode = group_mode
        prepared.uniform_values = selected_values
        prepared.variant_separation_confirmed = (mode == "separate")
        prepared.variant_combination_confirmed = (mode == "combine")
        self.DialogResult = True

    def Cancel_Click(self, sender, args):
        self.DialogResult = False


def review_taa(prepared, format_value, owner, uniform_guidance=None):
    return bool(CalculationReviewWindow(
        prepared, format_value, owner=owner,
        uniform_guidance=uniform_guidance,
    ).ShowDialog())
