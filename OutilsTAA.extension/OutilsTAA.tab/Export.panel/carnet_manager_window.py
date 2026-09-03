# -*- coding: utf-8 -*-
"""Fenêtre de gestion et d'ajout des carnets Export."""

import os
from pyrevit import forms
from System.Windows import Visibility


class CarnetManagerWindow(forms.WPFWindow):
    """Permet de préparer plusieurs carnets puis de les ajouter à la liste."""
    def __init__(self, controller, owner=None):
        self.controller = controller
        self.result = []
        self.current_items = []
        self.parameter_carnets = []
        self.rows = []
        xaml_path = os.path.join(os.path.dirname(__file__), "carnet_manager.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        if owner is not None:
            self.Owner = owner
        self._load_parameters()
        self._update_mode()

    def _load_parameters(self):
        context = self.controller.get_context()
        self.ParameterCombo.ItemsSource = context["parameters"]
        if self.ParameterCombo.Items.Count:
            self.ParameterCombo.SelectedIndex = 0
        else:
            self.ParameterInfo.Text = "Aucun paramètre de feuille disponible."
            self.ParameterCombo.IsEnabled = False

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
            "{0} carnet(s) détecté(s) • {1} feuille(s) répartie(s). "
            "Cochez uniquement les carnets à ajouter."
        ).format(len(self.parameter_carnets), total)

    def _set_rows(self, carnets):
        self.rows = [_CarnetManagerRow(carnet) for carnet in carnets]
        self.CarnetsGrid.ItemsSource = self.rows
        self._update_selection_info()

    def _update_selection_info(self):
        selected = [row for row in self.rows if row.IsSelected]
        self.SelectionInfo.Text = "{0} carnet(s) sélectionné(s).".format(len(selected))

    def SelectionChanged_Click(self, sender, args):
        self._update_selection_info()

    def _update_mode(self):
        if self.ModeParameter.IsChecked:
            self.ParameterPanel.Visibility = Visibility.Visible
            self.ManualPanel.Visibility = Visibility.Collapsed
            self.AddButton.Content = "Ajouter les carnets sélectionnés"
            self._load_parameter_carnets()
        elif self.ModeManual.IsChecked:
            self.ParameterPanel.Visibility = Visibility.Collapsed
            self.ManualPanel.Visibility = Visibility.Visible
            self.PersistentCheckBox.IsChecked = True
            self.AddButton.Content = "Ajouter le carnet"
            self._set_rows([])
        else:
            self.ParameterPanel.Visibility = Visibility.Collapsed
            self.ManualPanel.Visibility = Visibility.Visible
            self.PersistentCheckBox.IsChecked = False
            self.AddButton.Content = "Ajouter le carnet temporaire"
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
        if self.ModeParameter.IsChecked:
            selected = [row.publication_set for row in self.rows if row.IsSelected]
            if not selected:
                forms.alert("Cochez au moins un carnet à ajouter.", title="Export")
                return

            # Les carnets créés par paramètre sont désormais persistants.
            # Ils restent donc disponibles à la prochaine ouverture d'Export.
            persisted = []
            try:
                for carnet in selected:
                    persisted.append(self.controller.save_persistent(carnet))
            except Exception as exc:
                forms.alert(
                    "Impossible d'enregistrer les carnets sélectionnés.\n\n{0}".format(exc),
                    title="Export"
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
            forms.alert("Saisissez un nom de carnet.", title="Export")
            return

        if self.ModeManual.IsChecked and self.PersistentCheckBox.IsChecked:
            carnet = self.controller.create_manual_persistent(name.strip(), self.current_items)
        else:
            carnet = self.controller.create_manual_temporary(name.strip(), self.current_items)
        self.result = [carnet]
        self.Close()

    def Cancel_Click(self, sender, args):
        self.result = []
        self.Close()


class _CarnetManagerRow(object):
    """Ligne cochable de la liste des carnets détectés."""
    def __init__(self, publication_set):
        self.publication_set = publication_set
        self.IsSelected = False
        self.Name = publication_set.name
        self.Count = len(publication_set.items)
