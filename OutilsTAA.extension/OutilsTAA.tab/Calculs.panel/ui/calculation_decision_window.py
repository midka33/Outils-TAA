# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Dialogue TAA de choix ou de confirmation pour Calculs des pièces."""

import os

from pyrevit import forms
from System.Windows import Visibility
from common.wpf_resources import load_resource_dictionary


class DialogChoice(object):
    def __init__(self, label, value):
        self.label = label
        self.value = value


class CalculationDecisionWindow(forms.WPFWindow):
    def __init__(self, heading, details, options=None,
                 owner=None, confirm_label="Continuer"):
        xaml_path = os.path.join(os.path.dirname(__file__), "calculation_decision.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        if owner is not None:
            self.Owner = owner

        panel_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        extension_dir = os.path.abspath(os.path.join(panel_dir, "..", ".."))
        load_resource_dictionary(
            self, os.path.join(extension_dir, "resources", "ui", "taa_theme.xaml")
        )
        self.HeadingText.Text = heading
        self.DetailsText.Text = details or ""
        self.ConfirmButton.Content = confirm_label
        self._options = (
            [DialogChoice(label, value) for label, value in options]
            if options is not None else None
        )
        self.selected_value = None
        if self._options is None:
            self.OptionsPanel.Visibility = Visibility.Collapsed
            self.ConfirmButton.IsEnabled = True
            self.Height = 320
        else:
            self.ChoicesList.ItemsSource = self._options
            self.ChoicesList.SelectedIndex = -1
            self.ConfirmButton.IsEnabled = False

    def Choice_Changed(self, sender, args):
        if hasattr(self, "ConfirmButton") and self._options is not None:
            self.ConfirmButton.IsEnabled = self.ChoicesList.SelectedItem is not None

    def Confirm_Click(self, sender, args):
        if self._options is not None:
            item = self.ChoicesList.SelectedItem
            if item is None:
                return
            self.selected_value = item.value
        self.DialogResult = True

    def Cancel_Click(self, sender, args):
        self.DialogResult = False


def choose_taa(heading, details, choices, owner):
    dialog = CalculationDecisionWindow(
        heading, details, options=choices, owner=owner,
        confirm_label="Valider le choix"
    )
    if dialog.ShowDialog():
        return dialog.selected_value
    return None


def confirm_taa(heading, details, owner):
    dialog = CalculationDecisionWindow(
        heading, details, owner=owner,
        confirm_label="Confirmer l'écriture"
    )
    return bool(dialog.ShowDialog())
