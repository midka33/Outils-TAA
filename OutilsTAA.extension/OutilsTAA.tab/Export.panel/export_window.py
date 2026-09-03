# -*- coding: utf-8 -*-
"""Fenêtre WPF du module Export."""

import os

from pyrevit import forms
from System.Windows import Visibility


class PreviewRow(object):
    """Ligne d'aperçu affichée dans le DataGrid WPF."""

    def __init__(self, name, count, status="Prêt"):
        self.Name = name
        self.Count = count
        self.Status = status


class ExportWindow(forms.WPFWindow):
    """Interface de création et de gestion des carnets Export."""

    def __init__(self, controller, repository):
        self.controller = controller
        self.repository = repository
        self.current_items = []
        self.current_persistent = None

        xaml_path = os.path.join(os.path.dirname(__file__), "ui.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._load_context()

    def _load_context(self):
        context = self.controller.get_context()
        self.ParameterCombo.ItemsSource = context["parameters"]
        if self.ParameterCombo.Items.Count:
            self.ParameterCombo.SelectedIndex = 0
        self._refresh_persistent_carnets()
        self._update_mode()

    def _refresh_persistent_carnets(self):
        rows = []
        for publication_set in self.controller.list_persistent():
            resolution = self.controller.resolve_persistent(publication_set)
            rows.append(_CarnetListEntry(publication_set, resolution.missing_count))
        self.PersistentCarnetsList.ItemsSource = rows

    def _update_mode(self):
        if self.ModeParameter.IsChecked:
            self.ManualPanel.Visibility = Visibility.Collapsed
            self.CreateButton.Content = "Créer les carnets"
            self._update_parameter_preview()
        else:
            self.ManualPanel.Visibility = Visibility.Visible
            self.CreateButton.Content = (
                "Enregistrer le carnet"
                if self.ModeManual.IsChecked
                else "Utiliser la sélection"
            )
            self._show_manual_selection()

    def _update_parameter_preview(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            self.ParameterInfo.Text = "Aucun paramètre disponible."
            self.PreviewGrid.ItemsSource = []
            return

        preview = self.controller.get_parameter_preview(parameter_name)
        self.ParameterInfo.Text = (
            "{0} feuille(s) • {1} carnet(s) détecté(s) • "
            "{2} feuille(s) affectée(s)."
        ).format(
            preview["sheet_count"],
            preview["carnet_count"],
            preview["assigned_sheet_count"]
        )

        self.PreviewGrid.ItemsSource = [
            PreviewRow(item["value"], item["count"])
            for item in preview["values"]
        ]
        self.MissingInfo.Visibility = Visibility.Collapsed

    def _show_manual_selection(self):
        if not self.current_items:
            self.ManualSelectionInfo.Text = "Aucune sélection."
            self.PreviewGrid.ItemsSource = []
            return

        self.ManualSelectionInfo.Text = "{0} feuille(s) sélectionnée(s).".format(
            len(self.current_items)
        )
        self.PreviewGrid.ItemsSource = [
            PreviewRow(item.sheet_number, 1, item.sheet_name)
            for item in self.current_items
        ]

    def ParameterCombo_SelectionChanged(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._update_parameter_preview()

    def Mode_Checked(self, sender, args):
        self._update_mode()

    def SelectSheets_Click(self, sender, args):
        sheets = self.controller.export_service.get_sheets()
        selected = forms.SelectFromList.show(
            sheets,
            title="Sélectionner les feuilles",
            multiselect=True,
            name_attr="SheetNumber",
            description_attr="Name"
        )
        self.current_items = (
            self.controller.export_service.build_publication_items(selected)
            if selected else []
        )
        self._show_manual_selection()

    def PersistentCarnet_SelectionChanged(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        self.current_persistent = entry.publication_set if entry else None
        if self.current_persistent is None:
            return

        resolution = self.controller.resolve_persistent(self.current_persistent)
        self.PreviewGrid.ItemsSource = [
            PreviewRow(item.sheet_number, 1, item.sheet_name)
            for item in resolution.items
        ]

        if resolution.missing_count:
            self.MissingInfo.Visibility = Visibility.Visible
            self.MissingInfo.Text = (
                "ATTENTION : {0} élément(s) du carnet sont introuvables "
                "dans le document courant. Ils ne seront pas publiés."
            ).format(resolution.missing_count)
        else:
            self.MissingInfo.Visibility = Visibility.Collapsed

    def Create_Click(self, sender, args):
        if self.ModeParameter.IsChecked:
            self._create_parameter_carnets()
            return

        if not self.current_items:
            forms.alert("Sélectionnez au moins une feuille.", title="Export")
            return

        name = self.CarnetNameTextBox.Text
        if not name or not name.strip():
            forms.alert("Saisissez un nom de carnet.", title="Export")
            return

        if self.ModeManual.IsChecked and self.PersistentCheckBox.IsChecked:
            self.controller.create_manual_persistent(name, self.current_items)
            self._refresh_persistent_carnets()
            forms.alert("Carnet enregistré.", title="Export")
        else:
            self.controller.create_manual_temporary(name, self.current_items)
            forms.alert("Carnet temporaire préparé pour la session.", title="Export")

    def _create_parameter_carnets(self):
        parameter_name = self.ParameterCombo.SelectedItem
        if not parameter_name:
            forms.alert("Aucun paramètre sélectionné.", title="Export")
            return

        carnets = self.controller.create_from_parameter(parameter_name)
        self.PreviewGrid.ItemsSource = [
            PreviewRow(carnet.name, len(carnet.items))
            for carnet in carnets
        ]
        forms.alert(
            "{0} carnet(s) préparé(s) à partir de « {1} ».".format(
                len(carnets), parameter_name
            ),
            title="Export"
        )

    def DeleteCarnet_Click(self, sender, args):
        entry = self.PersistentCarnetsList.SelectedItem
        if entry is None:
            return

        confirmed = forms.alert(
            "Supprimer le carnet « {0} » ?".format(entry.publication_set.name),
            title="Export",
            yes=True,
            no=True
        )
        if not confirmed:
            return

        self.repository.delete(entry.publication_set.id)
        self.current_persistent = None
        self._refresh_persistent_carnets()
        self.PreviewGrid.ItemsSource = []
        self.MissingInfo.Visibility = Visibility.Collapsed

    def Close_Click(self, sender, args):
        self.Close()


class _CarnetListEntry(object):
    """Objet d'affichage d'un carnet persistant."""

    def __init__(self, publication_set, missing_count):
        self.publication_set = publication_set
        self.DisplayName = "{0} — {1}".format(
            publication_set.name,
            "ATTENTION : {0} manquant(s)".format(missing_count)
            if missing_count
            else "{0} feuille(s)".format(len(publication_set.items))
        )
