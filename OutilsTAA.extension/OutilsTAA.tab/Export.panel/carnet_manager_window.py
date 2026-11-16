# -*- coding: utf-8 -*-
"""Fenêtre de création des dossiers de publication Export."""

import os
from pyrevit import forms
from taa_ui_theme import apply_theme
from System.Windows import Visibility


class CarnetManagerWindow(forms.WPFWindow):
    """Permet de préparer des dossiers de publication contenant des mises en page."""
    def __init__(self, controller, owner=None, target_folder_id=None,
                 dynamic_only=False):
        self.controller = controller
        self._dynamic_only = bool(dynamic_only)
        self._dynamic_ready = False
        self.target_folder_id = target_folder_id or "default"
        self.result = []
        self.current_items = []
        self.parameter_carnets = []
        self.rows = []
        xaml_path = os.path.join(os.path.dirname(__file__), "carnet_manager.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        apply_theme(self)
        if owner is not None:
            self.Owner = owner
        self._load_parameters()
        self._load_dynamic_parameters()
        if self._dynamic_only:
            self.CreationModePanel.Visibility = Visibility.Collapsed
            self.ModeDynamic.IsChecked = True
            self.Title = "Créer un dossier automatique — Outils TAA"
            self.CreationDialogTitle.Text = "Créer un dossier automatique"
            self.CreationDialogSubtitle.Text = "Sélection dynamique depuis les paramètres des mises en page Revit"
            self.Height = 590
            self.MinHeight = 520
        self._update_mode()
        self._dynamic_ready = True
        self._refresh_dynamic_preview()

    def _load_parameters(self):
        context = self.controller.get_context()
        self.ParameterCombo.ItemsSource = context["parameters"]
        if self.ParameterCombo.Items.Count:
            self.ParameterCombo.SelectedIndex = 0
        else:
            self.ParameterInfo.Text = "Aucun paramètre de feuille disponible."
            self.ParameterCombo.IsEnabled = False

    def _load_dynamic_parameters(self):
        parameters = list(self.controller.get_context().get("parameters") or [])
        self.DynamicParameterCombo.ItemsSource = parameters
        self.DynamicGroupCombo.ItemsSource = parameters
        if parameters:
            self.DynamicParameterCombo.SelectedIndex = 0
            self.DynamicGroupCombo.SelectedIndex = 0

    def DynamicParameter_Changed(self, sender, args):
        name = self.DynamicParameterCombo.SelectedItem
        self.DynamicValueCombo.ItemsSource = (
            self.controller.parameter_service.get_parameter_values(
                self.controller.export_service.get_sheets(), name)
            if name else [])
        if self.DynamicValueCombo.Items.Count:
            self.DynamicValueCombo.SelectedIndex = 0
        self._refresh_dynamic_preview()

    def DynamicValue_Changed(self, sender, args):
        self._refresh_dynamic_preview()

    def DynamicGroup_Changed(self, sender, args):
        self.DynamicGroupCombo.IsEnabled = bool(self.DynamicGroupCheck.IsChecked)
        self._refresh_dynamic_preview()

    def _refresh_dynamic_preview(self):
        if not getattr(self, "_dynamic_ready", False):
            return
        if not (self._dynamic_only or self.ModeDynamic.IsChecked):
            return

        parameter = self.DynamicParameterCombo.SelectedItem
        value = self.DynamicValueCombo.SelectedItem
        grouping = bool(self.DynamicGroupCheck.IsChecked)
        group_parameter = self.DynamicGroupCombo.SelectedItem if grouping else None
        self.DynamicPreviewGroups.ItemsSource = []
        self.DynamicPreviewGroups.Visibility = (
            Visibility.Visible if grouping else Visibility.Collapsed)
        self.AddButton.IsEnabled = False

        if not parameter or value is None:
            self.DynamicPreviewSummary.Text = (
                "Choisissez un paramètre de feuille et une valeur.")
            return
        if grouping and not group_parameter:
            self.DynamicPreviewSummary.Text = (
                "Choisissez le paramètre des sous-dossiers.")
            return
        try:
            result = self.controller.preview_dynamic(
                parameter, value, group_parameter)
        except Exception as exc:
            self.DynamicPreviewSummary.Text = (
                "Aperçu impossible : {}".format(exc))
            return

        count = result["sheet_count"]
        groups = result["group_count"]
        self.DynamicPreviewSummary.Text = (
            "{0} feuille(s) correspondante(s) • "
            "{1} sous-dossier(s) à créer".format(count, groups)
        )
        if grouping:
            self.DynamicPreviewGroups.ItemsSource = [
                "{0} — {1} feuille(s)".format(name, count)
                for name, count in result["groups"]
            ]
        self.AddButton.IsEnabled = True

    def _load_parameter_carnets(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            self.parameter_carnets = []
            self._set_rows([])
            return
        self.parameter_carnets = self.controller.create_from_parameter(parameter_name)
        self._set_rows(self.parameter_carnets)
        total = sum(len(c.items) for c in self.parameter_carnets)
        self.ParameterInfo.Text = (
            "{0} dossier(s) détecté(s) • {1} feuille(s) répartie(s). "
            "Cochez uniquement les dossiers à ajouter."
        ).format(len(self.parameter_carnets), total)

    def _set_rows(self, carnets):
        self.rows = [_CarnetManagerRow(carnet) for carnet in carnets]
        self.CarnetsGrid.ItemsSource = self.rows
        self._update_selection_info()

    def _update_selection_info(self):
        selected = [row for row in self.rows if row.IsSelected]
        self.SelectionInfo.Text = "{0} dossier(s) sélectionné(s).".format(len(selected))

    def SelectionChanged_Click(self, sender, args):
        self._update_selection_info()

    def _update_mode(self):
        self.DynamicPanel.Visibility = Visibility.Collapsed
        self.DynamicPreviewPanel.Visibility = Visibility.Collapsed
        self.CarnetsGrid.Visibility = Visibility.Visible
        self.SelectionInfo.Visibility = Visibility.Visible
        self.AddButton.IsEnabled = True
        if self.ModeParameter.IsChecked and not self._dynamic_only:
            self.ParameterPanel.Visibility = Visibility.Visible
            self.ManualPanel.Visibility = Visibility.Collapsed
            self.AddButton.Content = "Ajouter les dossiers sélectionnés"
            self._load_parameter_carnets()
        elif self._dynamic_only or self.ModeDynamic.IsChecked:
            self.ParameterPanel.Visibility = Visibility.Collapsed
            self.ManualPanel.Visibility = Visibility.Collapsed
            self.DynamicPanel.Visibility = Visibility.Visible
            self.DynamicPreviewPanel.Visibility = Visibility.Visible
            self.CarnetsGrid.Visibility = Visibility.Collapsed
            self.SelectionInfo.Visibility = Visibility.Collapsed
            self.AddButton.Content = "Créer le dossier automatique"
            self._set_rows([])
            self._refresh_dynamic_preview()
        elif self.ModeManual.IsChecked:
            self.ParameterPanel.Visibility = Visibility.Collapsed
            self.ManualPanel.Visibility = Visibility.Visible
            self.PersistentCheckBox.IsChecked = True
            self.AddButton.Content = "Ajouter le dossier"
            self._set_rows([])
        else:
            self.ParameterPanel.Visibility = Visibility.Collapsed
            self.ManualPanel.Visibility = Visibility.Visible
            self.PersistentCheckBox.IsChecked = False
            self.AddButton.Content = "Ajouter le dossier temporaire"
            self._set_rows([])

    def Mode_Checked(self, sender, args):
        self._update_mode()

    def Parameter_SelectionChanged(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._load_parameter_carnets()

    def RefreshParameter_Click(self, sender, args):
        self._load_parameter_carnets()

    def SelectSheets_Click(self, sender, args):
        sheets = self.controller.export_service.get_sheets()
        selected = forms.SelectFromList.show(
            sheets, title="Sélectionner les feuilles", multiselect=True,
            name_attr="SheetNumber", description_attr="Name"
        )
        self.current_items = (
            self.controller.export_service.build_publication_items(selected)
            if selected else []
        )
        self.ManualSelectionInfo.Text = (
            "{0} feuille(s) sélectionnée(s).".format(len(self.current_items))
            if self.current_items else "Aucune feuille sélectionnée."
        )

    def Add_Click(self, sender, args):
        if self._dynamic_only or self.ModeDynamic.IsChecked:
            name = (self.DynamicNameTextBox.Text or "").strip()
            param = self.DynamicParameterCombo.SelectedItem
            value = self.DynamicValueCombo.SelectedItem
            group = (self.DynamicGroupCombo.SelectedItem
                     if self.DynamicGroupCheck.IsChecked else None)
            if not name or not param or value is None:
                forms.alert("Renseignez le nom, le paramètre et sa valeur.",
                            title="Export")
                return
            if self.DynamicGroupCheck.IsChecked and not group:
                forms.alert("Choisissez le paramètre des sous-dossiers.",
                            title="Export")
                return
            try:
                obj = self.controller.create_dynamic_persistent(
                    name, param, value, group, self.target_folder_id)
            except Exception as exc:
                owner = getattr(self, "Owner", None)
                handler = getattr(owner, "_show_storage_error", None)
                if handler is not None and handler(
                        exc, "créer le dossier automatique"):
                    return
                forms.alert("Création impossible : {}".format(exc), title="Export")
                return
            self.result = [obj]
            self.Close()
            return

        if self.ModeParameter.IsChecked:
            selected = [row.publication_set for row in self.rows if row.IsSelected]
            if not selected:
                forms.alert("Cochez au moins un dossier à ajouter.", title="Export")
                return
            persisted = []
            try:
                for carnet in selected:
                    # Le dossier sélectionné dans l'arborescence devient le parent réel.
                    carnet.folder_id = self.target_folder_id
                    persisted.append(self.controller.save_persistent(carnet))
            except Exception as exc:
                owner = getattr(self, "Owner", None)
                handler = getattr(owner, "_show_storage_error", None)
                if handler is not None and handler(
                        exc,
                        "enregistrer les dossiers sélectionnés"):
                    return
                forms.alert(
                    "Impossible d'enregistrer les dossiers sélectionnés.\n\n{0}"
                    .format(exc),
                    title="Export",
                )
                return
            self.result = persisted
            self.Close()
            return

        if not self.current_items:
            forms.alert("Sélectionnez au moins une feuille.", title="Export")
            return
        name = self.CarnetNameTextBox.Text
        if not name or not name.strip():
            forms.alert("Saisissez un nom de dossier.", title="Export")
            return

        if self.ModeManual.IsChecked and self.PersistentCheckBox.IsChecked:
            carnet = self.controller.create_manual_persistent(name.strip(), self.current_items)
            carnet.folder_id = self.target_folder_id
            try:
                self.controller.save_persistent(carnet)
            except Exception as exc:
                owner = getattr(self, "Owner", None)
                handler = getattr(owner, "_show_storage_error", None)
                if handler is not None and handler(
                        exc,
                        "enregistrer le dossier de publication"):
                    return
                forms.alert(
                    "Impossible d'enregistrer le dossier.\n\n{0}"
                    .format(exc),
                    title="Export",
                )
                return
        else:
            carnet = self.controller.create_manual_temporary(name.strip(), self.current_items)
            carnet.folder_id = self.target_folder_id
        self.result = [carnet]
        self.Close()

    def Cancel_Click(self, sender, args):
        self.result = []
        self.Close()


class _CarnetManagerRow(object):
    """Ligne cochable de la liste des dossiers détectés."""
    def __init__(self, publication_set):
        self.publication_set = publication_set
        self.IsSelected = False
        self.Name = publication_set.name
        self.Count = len(publication_set.items)
