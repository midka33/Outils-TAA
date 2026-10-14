# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from pyrevit import forms
from common.wpf_resources import load_resource_dictionary


class AdvancedOptionsWindow(forms.WPFWindow):
    def __init__(self, owner, parameter_choices, active_descriptor, options):
        self.accepted = False
        self.options = dict(options or {})
        self.selected_descriptor = active_descriptor

        xaml_path = os.path.join(os.path.dirname(__file__), "advanced_options.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        try:
            self.Owner = owner
        except Exception:
            pass
        self._load_theme()
        self._load_values(parameter_choices, active_descriptor)

    def _load_theme(self):
        panel_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        extension_dir = os.path.abspath(os.path.join(panel_dir, "..", ".."))
        resource_path = os.path.join(
            extension_dir, "resources", "ui", "taa_theme.xaml"
        )
        load_resource_dictionary(self, resource_path)

    def _load_values(self, parameter_choices, active_descriptor):
        choices = list(parameter_choices or [])
        self.HousingParameterCombo.ItemsSource = choices
        selected = -1
        for index, choice in enumerate(choices):
            if getattr(choice, "descriptor", None) is active_descriptor:
                selected = index
                break
        if selected < 0 and choices:
            selected = 0
        self.HousingParameterCombo.SelectedIndex = selected

        self.OnlyWithoutExistingCheck.IsChecked = bool(
            self.options.get("only_without_existing", True)
        )
        self.CropMarginTextBox.Text = str(
            self.options.get("crop_margin_mm", 500.0)
        )
        self.AutoScaleCheck.IsChecked = bool(
            self.options.get("auto_scale_on_collision", True)
        )
        self.AllowedScalesTextBox.Text = self.options.get(
            "allowed_scales", "50, 75, 100, 125, 150"
        )
        self.DetailedReportCheck.IsChecked = bool(
            self.options.get("detailed_report", True)
        )
        self.LogWarningsCheck.IsChecked = bool(
            self.options.get("log_warnings", True)
        )

    def Apply_Click(self, sender, args):
        try:
            margin = float(
                (self.CropMarginTextBox.Text or "500").replace(",", ".")
            )
            if margin < 0:
                raise ValueError()
        except Exception:
            forms.alert(
                "La marge de crop doit être un nombre positif.",
                title="Plans de vente — Options avancées",
                warn_icon=True,
            )
            return

        choice = self.HousingParameterCombo.SelectedItem
        self.selected_descriptor = getattr(choice, "descriptor", None)
        self.options = {
            "only_without_existing": bool(self.OnlyWithoutExistingCheck.IsChecked),
            "crop_margin_mm": margin,
            "auto_scale_on_collision": bool(self.AutoScaleCheck.IsChecked),
            "allowed_scales": self.AllowedScalesTextBox.Text or "50, 75, 100, 125, 150",
            "detailed_report": bool(self.DetailedReportCheck.IsChecked),
            "log_warnings": bool(self.LogWarningsCheck.IsChecked),
        }
        self.accepted = True
        self.Close()

    def Cancel_Click(self, sender, args):
        self.accepted = False
        self.Close()
