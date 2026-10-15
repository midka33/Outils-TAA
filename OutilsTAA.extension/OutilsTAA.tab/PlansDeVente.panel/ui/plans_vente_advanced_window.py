# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre Options avancées — Plans de vente Étape 09."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from plans_vente.sheet_fit import parse_allowed_scales


class PlansVenteAdvancedWindow(forms.WPFWindow):

    DEFAULTS = {
        "skip_existing": True,
        "crop_margin_mm": 500.0,
        "auto_scale": True,
        "allowed_scales": [50, 75, 100, 125, 150],
        "detailed_report": True,
        "log_warnings": True,
        "building_parameter_name": "",
        "typology_parameter_name": "",
    }

    def __init__(
        self,
        parameter_choices,
        active_descriptor,
        settings=None,
        owner=None,
    ):
        self.accepted = False
        self.parameter_choices = list(parameter_choices or [])
        self.active_descriptor = active_descriptor
        self.settings = dict(self.DEFAULTS)
        self.settings.update(dict(settings or {}))

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(
            current_dir,
            "plans_vente_advanced.xaml",
        )
        forms.WPFWindow.__init__(self, xaml_path)

        if owner is not None:
            try:
                self.Owner = owner
            except Exception:
                pass

        self._load_theme()
        self._load_values()

    def _load_theme(self):
        panel_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        extension_dir = os.path.abspath(
            os.path.join(panel_dir, "..", "..")
        )
        resource_path = os.path.join(
            extension_dir,
            "resources",
            "ui",
            "taa_theme.xaml",
        )
        load_resource_dictionary(self, resource_path)

    def _load_values(self):
        self.HousingParameterCombo.ItemsSource = self.parameter_choices
        self.HousingParameterCombo.SelectedIndex = (
            self._descriptor_index(self.active_descriptor)
        )

        self.BuildingParameterCombo.ItemsSource = self.parameter_choices
        self.BuildingParameterCombo.SelectedIndex = self._parameter_name_index(
            self.settings.get("building_parameter_name", "")
        )
        self.TypologyParameterCombo.ItemsSource = self.parameter_choices
        self.TypologyParameterCombo.SelectedIndex = self._parameter_name_index(
            self.settings.get("typology_parameter_name", "")
        )

        self.BatchModeCombo.ItemsSource = ["Par lot"]
        self.BatchModeCombo.SelectedIndex = 0

        self.SkipExistingCheckBox.IsChecked = bool(
            self.settings.get("skip_existing", True)
        )
        self.CropMarginTextBox.Text = self._format_number(
            self.settings.get("crop_margin_mm", 500.0)
        )
        self.AutoScaleCheckBox.IsChecked = bool(
            self.settings.get("auto_scale", True)
        )
        self.AllowedScalesTextBox.Text = ", ".join(
            str(value)
            for value in self.settings.get(
                "allowed_scales",
                [50, 75, 100, 125, 150],
            )
        )
        self.DetailedReportCheckBox.IsChecked = bool(
            self.settings.get("detailed_report", True)
        )
        self.LogWarningsCheckBox.IsChecked = bool(
            self.settings.get("log_warnings", True)
        )

    def _descriptor_index(self, descriptor):
        if not self.parameter_choices:
            return -1

        target_key = getattr(descriptor, "identity_key", None)
        for index, choice in enumerate(self.parameter_choices):
            candidate = getattr(choice, "descriptor", None)
            if candidate is descriptor:
                return index
            if (
                target_key
                and getattr(candidate, "identity_key", None) == target_key
            ):
                return index
        return 0

    def _parameter_name_index(self, name):
        target = str(name or "").strip().lower()
        if not target:
            return -1
        for index, choice in enumerate(self.parameter_choices):
            descriptor = getattr(choice, "descriptor", None)
            candidate = str(
                getattr(descriptor, "name", "") or ""
            ).strip().lower()
            if candidate == target:
                return index
        return -1

    @staticmethod
    def _selected_parameter_name(combo):
        item = combo.SelectedItem
        descriptor = (
            getattr(item, "descriptor", None)
            if item is not None
            else None
        )
        return str(
            getattr(descriptor, "name", "") or ""
        ).strip()

    def Reset_Click(self, sender, args):
        self.settings = dict(self.DEFAULTS)
        self._load_values()

    def Cancel_Click(self, sender, args):
        self.accepted = False
        self.Close()

    def Save_Click(self, sender, args):
        item = self.HousingParameterCombo.SelectedItem
        descriptor = (
            getattr(item, "descriptor", None)
            if item is not None
            else None
        )
        if descriptor is None:
            forms.alert(
                "Sélectionnez le paramètre identifiant les logements.",
                title="Plans de vente — Options avancées",
                warn_icon=True,
            )
            return

        try:
            margin = float(
                str(self.CropMarginTextBox.Text or "")
                .strip()
                .replace(",", ".")
            )
        except Exception:
            margin = 0.0
        if margin <= 0.0:
            forms.alert(
                "La marge de crop doit être un nombre positif.",
                title="Plans de vente — Options avancées",
                warn_icon=True,
            )
            return

        auto_scale = bool(self.AutoScaleCheckBox.IsChecked)
        try:
            scales = parse_allowed_scales(
                self.AllowedScalesTextBox.Text
            )
        except Exception as error:
            forms.alert(
                str(error),
                title="Plans de vente — Options avancées",
                warn_icon=True,
            )
            return

        self.active_descriptor = descriptor
        self.settings = {
            "skip_existing": bool(
                self.SkipExistingCheckBox.IsChecked
            ),
            "crop_margin_mm": float(margin),
            "auto_scale": auto_scale,
            "allowed_scales": list(scales),
            "detailed_report": bool(
                self.DetailedReportCheckBox.IsChecked
            ),
            "log_warnings": bool(
                self.LogWarningsCheckBox.IsChecked
            ),
            "building_parameter_name": self._selected_parameter_name(
                self.BuildingParameterCombo
            ),
            "typology_parameter_name": self._selected_parameter_name(
                self.TypologyParameterCombo
            ),
        }
        self.accepted = True
        self.Close()

    @staticmethod
    def _format_number(value):
        try:
            number = float(value)
        except Exception:
            return str(value or "")
        if abs(number - int(number)) < 1e-9:
            return str(int(number))
        return ("{:.2f}".format(number)).rstrip("0").rstrip(".")
