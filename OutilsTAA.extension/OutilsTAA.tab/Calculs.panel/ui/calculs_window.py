# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre principale de Calculs des pièces."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary
from calculation.group_alignment import GroupAlignmentResolution
from calculation_report_window import CalculationReportWindow
from group_value_selection_window import GroupValueSelectionWindow


class ParameterChoice(object):
    def __init__(self, label, descriptor):
        self.label = label
        self.descriptor = descriptor


class CalculsWindow(forms.WPFWindow):

    def __init__(self, controller):
        self.controller = controller
        self._loading = True
        self._context = None
        self._group_choices = []
        self._source_choices = []
        self._target_choices = []
        self._filter_choices = []

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
        )

    def Calculate_Click(self, sender, args):
        self.CalculateButton.IsEnabled = False
        self.ProgressBar.Value = 0

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
                    "Aucun résultat écrivable n'a été produit. "
                    "Vérifiez le regroupement et le paramètre source.",
                    title="Calculs des pièces",
                    warn_icon=True,
                )
                self.StatusText.Text = "Aucun résultat à écrire."
                return

            group_resolution = None
            alignment_analysis = self.controller.analyze_group_alignment(
                prepared
            )
            if (
                alignment_analysis is not None
                and alignment_analysis.has_conflicts
            ):
                group_resolution = self._resolve_group_conflicts(
                    alignment_analysis,
                    request.target_parameter.name,
                )
                if group_resolution is None:
                    self.StatusText.Text = (
                        "Calcul annulé : divergences entre groupes."
                    )
                    return

            message = (
                "{0} pièce(s) analysée(s)\n"
                "{1} pièce(s) après filtre\n"
                "{2} groupe(s)\n"
                "{3} écriture(s) prévues\n\n"
            ).format(
                prepared.total_rooms,
                prepared.filtered_rooms,
                prepared.result.group_count,
                len(prepared.operations),
            )

            if prepared.warnings:
                message += "Avertissements :\n"
                for warning in prepared.warnings:
                    message += "- {}\n".format(warning)
                message += "\n"

            message += "Écrire ces résultats dans « {} » ?".format(
                request.target_parameter.name
            )

            confirmed = forms.alert(
                message,
                title="Calculs des pièces — Confirmation",
                yes=True,
                no=True,
            )
            if not confirmed:
                self.StatusText.Text = "Calcul annulé avant écriture."
                return

            self.controller.save_settings(request)
            self.StatusText.Text = "Écriture dans Revit..."

            report = self.controller.execute(
                prepared,
                progress=self._write_progress,
                group_resolution=group_resolution,
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

            CalculationReportWindow(
                prepared,
                report,
                owner=self,
            ).ShowDialog()

        except Exception as error:
            self.StatusText.Text = "Erreur : {}".format(error)
            forms.alert(
                str(error),
                title="Calculs des pièces — Erreur",
                warn_icon=True,
            )
        finally:
            self.CalculateButton.IsEnabled = True

    def _resolve_group_conflicts(self, analysis, target_name):
        exact_label = (
            "Conserver les résultats exacts et laisser le paramètre varier"
        )
        aligned_label = (
            "Conserver l'alignement et choisir les valeurs"
        )
        cancel_label = "Annuler"

        message = (
            "{} divergence(s) ont été détectée(s) entre des occurrences "
            "d'un même type de groupe pour le paramètre « {} ».\n\n"
            "Vous pouvez conserver les résultats calculés exacts, ce qui "
            "laissera durablement le paramètre en mode valeurs variables, "
            "ou conserver l'alignement et choisir la valeur à appliquer "
            "pour chaque membre concerné."
        ).format(
            analysis.conflict_count,
            target_name,
        )

        choice = forms.alert(
            message,
            title="Calculs des pièces — Groupes différents",
            options=[
                exact_label,
                aligned_label,
                cancel_label,
            ],
            warn_icon=True,
        )

        if choice == exact_label:
            return GroupAlignmentResolution.keep_variable()

        if choice == aligned_label:
            window = GroupValueSelectionWindow(
                analysis,
                owner=self,
            )
            window.ShowDialog()

            if window.selections is None:
                return None

            return GroupAlignmentResolution.align_selected(
                window.selections
            )

        return None

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

    def Close_Click(self, sender, args):
        self.Close()
