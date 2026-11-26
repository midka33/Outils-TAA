# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Deux étapes WPF pour le renommage ; une transaction au dernier écran."""

import os
import clr
clr.AddReference("System.Data")

from pyrevit import forms, revit
from System.Data import DataTable
from System.Windows import Visibility
from System.Windows.Input import Keyboard
from common.logger import get_logger
from common.wpf_resources import load_resource_dictionary
from text_rename_service import (
    collect_targets, target_label, writable_text_parameters, readable_parameters,
    prepare_text_renames, commit_text_renames,
)
from room_parameter_edit_service import parameter_of


LOGGER = get_logger("OutilsTAA.Renommage")
UI_DIR = os.path.dirname(__file__)
THEME = os.path.abspath(os.path.join(UI_DIR, "..", "..", "..", "resources", "ui", "taa_theme.xaml"))


def _rows(columns, items):
    table = DataTable("Sélection")
    for name, kind in columns:
        table.Columns.Add(name, kind)
    for item in items:
        row = table.NewRow()
        for name, value in item.items():
            row[name] = value
        table.Rows.Add(row)
    return table


def _parameter_display(element, parameter_id):
    """Valeur visible, indépendante de l'identifiant technique de l'objet."""
    parameter = parameter_of(element, parameter_id)
    if parameter is None:
        return "(paramètre absent)"
    return parameter.AsString() or "(vide)"


class RenameSelectionWindow(forms.WPFWindow):
    SCOPES = ("Sélection actuelle", "Vue active", "Projet entier")

    def __init__(self):
        self._ready = False
        forms.WPFWindow.__init__(self, os.path.join(UI_DIR, "rename_selection.xaml"))
        load_resource_dictionary(self, THEME)
        self.elements = []
        self.parameter_id = None
        self.selection = []
        self.category = "Pièces"
        self.level = "instance"
        self.CategoryCombo.Items.Add("Pièces")
        self.CategoryCombo.Items.Add("Familles")
        self.LevelCombo.Items.Add("Instance")
        self.LevelCombo.Items.Add("Type")
        for scope in self.SCOPES:
            self.ScopeCombo.Items.Add(scope)
        self.CategoryCombo.SelectedIndex = 0
        self.LevelCombo.SelectedIndex = 0
        self.ScopeCombo.SelectedIndex = 0
        self._ready = True
        self.reload_targets()

    def ScopeChanged(self, sender, args):
        if self._ready:
            self.reload_targets()

    def reload_targets(self):
        self.category = self.CategoryCombo.SelectedItem or "Pièces"
        self.level = "type" if self.LevelCombo.SelectedIndex == 1 else "instance"
        self.LevelCombo.IsEnabled = self.category == "Familles"
        self.ContinueButton.IsEnabled = False
        self.ParameterCombo.Items.Clear()
        self.SelectionMessage.Text = ""
        try:
            self.elements = collect_targets(self.category, self.ScopeCombo.SelectedItem, self.level)
            table = _rows((("Enabled", bool), ("Key", str), ("Label", str)),
                          ({"Enabled": True, "Key": obj.UniqueId, "Label": target_label(obj)}
                           for obj in self.elements))
            self.table = table
            self.ObjectsGrid.ItemsSource = table.DefaultView
            options = writable_text_parameters(self.elements)
            for option in options:
                self.ParameterCombo.Items.Add(option)
            if options:
                preferred = next((i for i, option in enumerate(options)
                                  if option.Label.split(" [ID ")[0].strip().lower() == "n° appartement"), 0)
                self.ParameterCombo.SelectedIndex = preferred
            self.ContinueButton.IsEnabled = bool(self.elements and options)
            self.FoundText.Text = "{} élément(s)".format(len(self.elements))
            if self.category == "Familles" and self.level == "type":
                self.SelectionMessage.Text = "Attention : modifier un type affecte toutes ses occurrences dans le projet."
            elif not self.elements:
                self.SelectionMessage.Text = "Aucun élément trouvé pour ce périmètre."
        except Exception as error:
            LOGGER.exception("Collecte de renommage impossible")
            self.elements = []
            self.ObjectsGrid.ItemsSource = None
            self.FoundText.Text = "0 élément"
            self.SelectionMessage.Text = "Collecte impossible : {}".format(error)

    def ContinueSelection(self, sender, args):
        option = self.ParameterCombo.SelectedItem
        if option is None:
            self.SelectionMessage.Text = "Choisissez un paramètre de destination."
            return
        self.ObjectsGrid.CommitEdit()
        self.selection = [element for element in self.elements
                          if any(row["Key"] == element.UniqueId and row["Enabled"]
                                 for row in self.table.Rows)]
        if not self.selection:
            self.SelectionMessage.Text = "Cochez au moins un élément."
            return
        self.parameter_id = option.Id
        self.parameter_label = option.Label
        self.DialogResult = True
        self.Close()

    def CancelSelection(self, sender, args):
        self.DialogResult = False
        self.Close()


class RenameEditorWindow(forms.WPFWindow):
    MODES = ("Ajouter", "Supprimer", "Remplacer", "Formater")
    ADD_CODES = ("add_start", "add_end")
    REMOVE_CODES = ("remove_start", "remove_end")

    def __init__(self, selection):
        self.context = selection
        self.elements = list(selection.selection)
        self.parameter_id = selection.parameter_id
        forms.WPFWindow.__init__(self, os.path.join(UI_DIR, "rename_editor.xaml"))
        load_resource_dictionary(self, THEME)
        self.changes = {}
        self.preview_signature = None
        self._ready = False
        self.ContextText.Text = "{} — {} — {}".format(selection.category,
            "Types" if selection.level == "type" else "Instances",
            selection.parameter_label)
        parameter_name = selection.parameter_label.split(" [ID ")[0]
        self.ObjectsGrid.Columns[1].Header = parameter_name
        self.PreviewGrid.Columns[0].Header = parameter_name
        table = _rows((("Enabled", bool), ("Key", str), ("Label", str)),
                      ({"Enabled": True, "Key": obj.UniqueId,
                        "Label": _parameter_display(obj, self.parameter_id)}
                       for obj in self.elements))
        self.table = table
        self.ObjectsGrid.ItemsSource = table.DefaultView
        for option in readable_parameters(self.elements):
            self.FormatParameterCombo.Items.Add(option)
        if self.FormatParameterCombo.Items.Count:
            self.FormatParameterCombo.SelectedIndex = 0
        self.InsertParameterButton.IsEnabled = self.FormatParameterCombo.Items.Count > 0
        for mode in self.MODES:
            self.ModeCombo.Items.Add(mode)
        self.ModeCombo.SelectedIndex = 0
        self._ready = True
        self.ModeChanged(None, None)
        self.ContentRendered += self._focus_input

    def _focus_input(self, sender, args):
        self.InputText.Focus()
        Keyboard.Focus(self.InputText)

    def ModeChanged(self, sender, args):
        if not self._ready:
            return
        mode = self.ModeCombo.SelectedIndex
        self.OperationCombo.Items.Clear()
        if mode == 0:
            labels = ("Au début", "À la fin")
            self.OperationLabel.Text = "POSITION DE L'AJOUT"
            self.InputLabel.Text = "TEXTE À AJOUTER"
            self.ExtraLabel.Text = "SÉPARATEUR"
            self.InputText.Text, self.ExtraText.Text = "BAT", "-"
        elif mode == 1:
            labels = ("Au début", "À la fin")
            self.OperationLabel.Text = "POSITION DE LA SUPPRESSION"
            self.InputLabel.Text = "TEXTE À SUPPRIMER"
            self.ExtraLabel.Text = "SÉPARATEUR"
            self.InputText.Text, self.ExtraText.Text = "BAT", "-"
        elif mode == 2:
            labels = ("Remplacer toutes les occurrences",)
            self.OperationLabel.Text = "REMPLACEMENT LITTÉRAL"
            self.InputLabel.Text, self.ExtraLabel.Text = "RECHERCHER", "REMPLACER PAR"
            self.InputText.Text, self.ExtraText.Text = "BAT", "LOG"
        else:
            labels = ("Format personnalisé",)
            self.OperationLabel.Text = "MODÈLE"
            self.InputLabel.Text, self.ExtraLabel.Text = "FORMAT", "NON UTILISÉ"
            self.InputText.Text, self.ExtraText.Text = "{famille}-{valeur}-{index}", ""
        for label in labels:
            self.OperationCombo.Items.Add(label)
        self.OperationCombo.SelectedIndex = 0
        self.ExtraText.IsEnabled = mode != 3
        self.AddOnce.Visibility = Visibility.Visible if mode == 0 else Visibility.Collapsed
        self.FormatFields.Visibility = Visibility.Visible if mode == 3 else Visibility.Collapsed
        self.clear_preview()

    def InsertFormatParameter(self, sender, args):
        option = self.FormatParameterCombo.SelectedItem
        if option is None or self.ModeCombo.SelectedIndex != 3:
            return
        self.InputText.SelectedText = "{" + option.Token + "}"
        self.InputText.Focus()
        Keyboard.Focus(self.InputText)
        self.clear_preview()

    def InputsChanged(self, sender, args):
        if self._ready:
            self.clear_preview()

    def _included(self):
        self.ObjectsGrid.CommitEdit()
        included = set(row["Key"] for row in self.table.Rows if row["Enabled"])
        return [element for element in self.elements if element.UniqueId in included]

    def _operation(self):
        mode = self.ModeCombo.SelectedIndex
        if mode == 0:
            return self.ADD_CODES[self.OperationCombo.SelectedIndex]
        if mode == 1:
            return self.REMOVE_CODES[self.OperationCombo.SelectedIndex]
        return "replace" if mode == 2 else "format"

    def _signature(self):
        return (tuple(item.UniqueId for item in self._included()), self.ModeCombo.SelectedIndex,
                self.OperationCombo.SelectedIndex, self.InputText.Text, self.ExtraText.Text,
                bool(self.AddOnce.IsChecked))

    def clear_preview(self):
        self.changes = {}
        self.preview_signature = None
        self.ApplyButton.IsEnabled = False
        self.ConfirmCheck.IsChecked = False
        self.PreviewGrid.ItemsSource = None
        self.CountText.Text = "0 modification"

    def RefreshPreview(self, sender, args):
        self.clear_preview()
        try:
            elements = self._included()
            self.changes, skipped = prepare_text_renames(
                elements, self.parameter_id, self._operation(),
                self.InputText.Text, self.ExtraText.Text, bool(self.AddOnce.IsChecked))
            table = _rows((("Label", str), ("Before", str), ("After", str), ("Status", str)),
                          ({"Label": item[2] or "(vide)", "Before": item[2],
                            "After": item[3], "Status": "Prêt"}
                           for item in self.changes.values()))
            self.PreviewGrid.ItemsSource = table.DefaultView
            self.preview_signature = self._signature()
            self.ApplyButton.IsEnabled = bool(self.changes)
            self.CountText.Text = "{} modification(s)".format(len(self.changes))
            self.MessageText.Text = "{} élément(s) sans changement ou non modifiables.".format(skipped)
        except Exception as error:
            LOGGER.exception("Aperçu de renommage impossible")
            self.MessageText.Text = "Aperçu impossible : {}".format(error)

    def ApplyChanges(self, sender, args):
        if self.preview_signature is None or self.preview_signature != self._signature():
            self.MessageText.Text = "La sélection ou les paramètres ont changé : actualisez l'aperçu."
            return
        if not self.ConfirmCheck.IsChecked:
            self.MessageText.Text = "Cochez « Je confirme les valeurs »."
            return
        try:
            count = commit_text_renames(list(self.changes.values()))
            LOGGER.info("Renommage : %s paramètre(s) modifié(s)", count)
            self.MessageText.Text = "{} modification(s) validée(s). Annulation possible dans Revit.".format(count)
            self.clear_preview()
        except Exception as error:
            LOGGER.exception("Écriture de renommage annulée")
            self.MessageText.Text = "Aucune modification conservée : {}".format(error)

    def CloseWindow(self, sender, args):
        self.Close()


def launch_rename():
    if revit.doc is None or revit.doc.IsFamilyDocument or revit.doc.IsReadOnly:
        forms.alert("Ouvrez un projet Revit modifiable.", title="Renommage multiple")
        return
    selection = RenameSelectionWindow()
    if selection.ShowDialog():
        RenameEditorWindow(selection).ShowDialog()
