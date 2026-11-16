# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre principale de Calculs des pièces."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from calculation_report_window import CalculationReportWindow
from calculation_review_window import review_taa
from calculation_diagnostics import empty_result_explanation


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class CalculsWindow(forms.WPFWindow):

    def __init__(self, controller):
        self.controller = controller
        self._loading = True
        self._context = None
        self._last_report = None
        self._last_prepared = None
        self._group_choices = []
        self._source_choices = []
        self._target_choices = []
        self._filter_choices = []
        self._variant_choices = [
            ParameterChoice("Surfaces séparées par variante (défaut)", "separate"),
            ParameterChoice("Additionner toutes les surfaces des variantes", "combine"),
        ]
        self._group_mode_choices = [
            ParameterChoice("Automatique — conserver les réglages (défaut)", "auto"),
            ParameterChoice("Autoriser des valeurs différentes entre groupes", "vary"),
            ParameterChoice("Conserver une valeur commune entre groupes", "uniform"),
        ]

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(current_dir, "calculs_ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        self._load_theme()
        self._load_context()
        self._restore_settings()
        self._loading = False
        self._update_filter_state()
        self._update_unit_state()

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
        self.StatusText.Text = "Lecture des paramètres des pièces..."
        self._context = self.controller.load_context()

        self.SourceCountText.Text = "{} pièce(s) détectée(s).".format(
            self._context.rooms_count
        )

        self._group_choices = self._build_choices(
            self._context.all_parameters
        )
        self._source_choices = self._build_choices(
            self._context.numeric_parameters
        )
        self._target_choices = self._build_choices(
            self._context.target_parameters
        )
        self._filter_choices = [
            ParameterChoice("Aucun filtre", None)
        ] + self._build_choices(self._context.all_parameters)

        self.GroupParameterCombo.ItemsSource = self._group_choices
        self.SourceParameterCombo.ItemsSource = self._source_choices
        self.TargetParameterCombo.ItemsSource = self._target_choices
        self.FilterParameterCombo.ItemsSource = self._filter_choices
        self.VariantModeCombo.ItemsSource = self._variant_choices
        self.VariantModeCombo.SelectedIndex = 0
        self.GroupModeCombo.ItemsSource = self._group_mode_choices
        self.GroupModeCombo.SelectedIndex = 0

        if self._filter_choices:
            self.FilterParameterCombo.SelectedIndex = 0

        self.StatusText.Text = "Prêt."

    def _build_choices(self, descriptors):
        descriptors = list(descriptors or [])
        counts = {}
        for descriptor in descriptors:
            key = descriptor.name.lower()
            counts[key] = counts.get(key, 0) + 1

        choices = []
        for descriptor in descriptors:
            label = descriptor.name
            if counts.get(descriptor.name.lower(), 0) > 1:
                label = "{} [{}]".format(
                    descriptor.name,
                    self._identity_label(descriptor),
                )
            choices.append(ParameterChoice(label, descriptor))
        return choices

    @staticmethod
    def _identity_label(descriptor):
        kind = descriptor.identity_kind
        if kind == "SHARED_GUID":
            return "partagé"
        if kind == "BUILT_IN":
            return "Revit"
        if kind == "DEFINITION":
            return "projet"
        return "nom"

    def _restore_settings(self):
        data = self.controller.load_settings() or {}

        self._select_saved(
            self.GroupParameterCombo,
            self._group_choices,
            data.get("group_parameter"),
        )
        self._select_saved(
            self.SourceParameterCombo,
            self._source_choices,
            data.get("source_parameter"),
        )
        self._select_saved(
            self.TargetParameterCombo,
            self._target_choices,
            data.get("target_parameter"),
        )
        self._select_saved(
            self.FilterParameterCombo,
            self._filter_choices,
            data.get("filter_parameter"),
        )

        self.FilterValueTextBox.Text = data.get("filter_value") or ""
        self._refresh_unit_options(
            selected_type_id=data.get("output_unit_type_id")
        )
        self._update_unit_state()

    def _select_saved(self, combo, choices, saved_data):
        descriptors = [
            choice.descriptor
            for choice in choices
            if choice.descriptor is not None
        ]
        descriptor = self.controller.match_saved_descriptor(
            saved_data,
            descriptors,
        )
        if descriptor is None:
            return

        for index, choice in enumerate(choices):
            if (
                choice.descriptor is not None
                and choice.descriptor.identity_key == descriptor.identity_key
            ):
                combo.SelectedIndex = index
                return

    def _refresh_unit_options(self, selected_type_id=None):
        source = self._selected_descriptor(self.SourceParameterCombo)
        options = self.controller.unit_options(source)
        self.UnitCombo.ItemsSource = options
        self.UnitCombo.SelectedIndex = 0

        if selected_type_id:
            for index, option in enumerate(options):
                if option.type_id == selected_type_id:
                    self.UnitCombo.SelectedIndex = index
                    break

    @staticmethod
    def _selected_descriptor(combo):
        item = combo.SelectedItem
        return getattr(item, "descriptor", None) if item is not None else None

    def _selected_unit_type_id(self):
        option = self.UnitCombo.SelectedItem
        return getattr(option, "type_id", None) if option is not None else None

    def _create_request(self):
        group = self._selected_descriptor(self.GroupParameterCombo)
        source = self._selected_descriptor(self.SourceParameterCombo)
        target = self._selected_descriptor(self.TargetParameterCombo)
        filter_parameter = self._selected_descriptor(
            self.FilterParameterCombo
        )

        missing = []
        if group is None:
            missing.append("paramètre de regroupement")
        if source is None:
            missing.append("paramètre à additionner")
        if target is None:
            missing.append("paramètre destination")
        if missing:
            raise ValueError(
                "Sélectionnez : {}.".format(", ".join(missing))
            )

        filter_value = (self.FilterValueTextBox.Text or "").strip()
        if filter_parameter is not None and not filter_value:
            raise ValueError(
                "Saisissez la valeur exacte du filtre ou choisissez « Aucun filtre »."
            )

        return self.controller.create_request(
            group_parameter=group,
            source_parameter=source,
            target_parameter=target,
            filter_parameter=filter_parameter,
            filter_value=filter_value,
            output_unit_type_id=self._selected_unit_type_id(),
            variant_mode=self.VariantModeCombo.SelectedItem.descriptor,
            group_mode=self.GroupModeCombo.SelectedItem.descriptor,
        )

    def Calculate_Click(self, sender, args):
        self.CalculateButton.IsEnabled = False
        self.ProgressBar.Value = 0
        self.ReportButton.IsEnabled = False
        self._last_report = None
        self._last_prepared = None

        try:
            request = self._create_request()
            self.StatusText.Text = "Calcul en cours..."

            prepared = self.controller.prepare(
                request,
                progress=self._calculation_progress,
            )

            if prepared.filtered_rooms == 0:
                forms.alert(
                    "Aucune pièce ne correspond au filtre.",
                    title="Calculs des pièces",
                    warn_icon=True,
                )
                self.StatusText.Text = "Aucune pièce à calculer."
                return

            if not prepared.operations:
                forms.alert(
                    empty_result_explanation(prepared),
                    title="Calculs des pièces",
                    warn_icon=True,
                )
                self.StatusText.Text = "Aucun total calculé ; aucune écriture."
                return

            # Un seul dialogue WPF TAA : variantes, conflits de groupes
            # et validation finale sont traités dans la même fenêtre.
            if not review_taa(prepared, self._format_group_value, owner=self,
                uniform_guidance=self.controller.uniform_manual_guidance,
            ):
                self.StatusText.Text = "Calcul annulé avant écriture."
                return

            self.controller.save_settings(request)
            self.StatusText.Text = "Écriture dans Revit..."

            report = self.controller.execute(
                prepared,
                progress=self._write_progress,
            )
            self.ProgressBar.Value = 100

            if report.transaction_error:
                self.StatusText.Text = "Échec de la transaction."
            elif report.failed_count:
                self.StatusText.Text = (
                    "{} écriture(s) réussie(s), {} échec(s).".format(
                        report.success_count,
                        report.failed_count,
                    )
                )
            else:
                self.StatusText.Text = (
                    "{} valeur(s) écrite(s) avec succès.".format(
                        report.success_count
                    )
                )

            self._last_prepared = prepared
            self._last_report = report
            self.ReportButton.IsEnabled = True
            if report.transaction_error or report.failed_count:
                self.Report_Click(None, None)
            elif report.skipped:
                self.StatusText.Text += " {} pièce(s) ignorée(s).".format(
                    len(report.skipped)
                )

        except Exception as error:
            self.StatusText.Text = "Erreur : {}".format(error)
            forms.alert(
                str(error),
                title="Calculs des pièces — Erreur",
                warn_icon=True,
            )
        finally:
            self.CalculateButton.IsEnabled = True

    @staticmethod
    def _format_group_value(value, request):
        # Les surfaces Revit sont internes (pieds carres); afficher m2
        # uniquement si la source est bien un parametre d'aire.
        data_type = str(getattr(request.source_parameter, "data_type_id", "") or "")
        if "area" in data_type.lower():
            try:
                from Autodesk.Revit.DB import UnitUtils, UnitTypeId
                area_m2 = UnitUtils.ConvertFromInternalUnits(
                    float(value), UnitTypeId.SquareMeters
                )
                return "{:.3f} m²".format(area_m2)
            except (ImportError, AttributeError, TypeError, ValueError):
                pass
        return "{} (unites internes Revit si Double)".format(value)

    def _calculation_progress(self, current, total):
        if total:
            self.ProgressBar.Value = min(
                55,
                (current / float(total)) * 55,
            )

    def _write_progress(self, current, total):
        if total:
            self.ProgressBar.Value = 55 + min(
                40,
                (current / float(total)) * 40,
            )

    def FilterParameterChanged(self, sender, args):
        if self._loading:
            return
        self._update_filter_state()

    def _update_filter_state(self):
        descriptor = self._selected_descriptor(self.FilterParameterCombo)
        self.FilterValueTextBox.IsEnabled = descriptor is not None
        if descriptor is None:
            self.FilterValueTextBox.Text = ""

    def SourceParameterChanged(self, sender, args):
        if self._loading:
            return
        self._refresh_unit_options()
        self._update_unit_state()

    def TargetParameterChanged(self, sender, args):
        if self._loading:
            return
        self._update_unit_state()

    def _update_unit_state(self):
        source = self._selected_descriptor(self.SourceParameterCombo)
        target = self._selected_descriptor(self.TargetParameterCombo)

        manual_units_are_useful = (
            source is not None
            and source.storage_type == "Double"
            and target is not None
            and target.storage_type in ("Integer", "String")
        )

        self.UnitCombo.IsEnabled = manual_units_are_useful
        if not manual_units_are_useful and self.UnitCombo.Items.Count:
            self.UnitCombo.SelectedIndex = 0

    def Report_Click(self, sender, args):
        if self._last_report is None or self._last_prepared is None:
            return
        CalculationReportWindow(
            self._last_prepared, self._last_report, owner=self
        ).ShowDialog()

    def Close_Click(self, sender, args):
        self.Close()
