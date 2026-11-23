# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre WPF unique pour les deux commandes, aucun dialogue d'étape."""

import os

from pyrevit import DB, forms, revit
from System.Data import DataTable
from System.Windows import Visibility
from common.logger import get_logger
from common.settings import JsonSettingsStore
from common.wpf_resources import load_resource_dictionary
from room_parameter_edit_service import (
    collect_rooms, room_label, parameter_options, prepare_changes,
    check_collisions, commit_changes,
)


LOGGER = get_logger("OutilsTAA.ParametresPieces")


def _settings_store():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return JsonSettingsStore(os.path.join(base, "OutilsTAA", "room_parameters.json"))


class RoomParametersWindow(forms.WPFWindow):
    SCOPES = ("Sélection actuelle", "Vue active", "Projet entier")
    NUMBER_OPERATIONS = ("Chiffres", "Lettres")
    TEXT_OPERATIONS = ("Ajouter au début", "Ajouter à la fin",
                       "Supprimer au début", "Supprimer à la fin")
    TEXT_CODES = ("add_start", "add_end", "remove_start", "remove_end")

    def __init__(self, initial_mode):
        xaml = os.path.join(os.path.dirname(__file__), "room_parameters.xaml")
        forms.WPFWindow.__init__(self, xaml)
        theme = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "resources", "ui", "taa_theme.xaml"))
        load_resource_dictionary(self, theme)
        self.changes = {}
        self.picked = []
        self.parameter_options = []
        self.table = None
        self.preview_signature = None
        self.last_report = None
        self.skipped_count = 0
        self.settings = _settings_store()
        for item in ("Numéroter", "Modifier le texte"):
            self.ModeCombo.Items.Add(item)
        for item in self.SCOPES:
            self.ScopeCombo.Items.Add(item)
        self.ScopeCombo.SelectedIndex = 0
        self.ModeCombo.SelectedIndex = 0 if initial_mode == "number" else 1
        self.load_parameters()
        self.update_mode()
        self.restore_preferences(initial_mode)

    def restore_preferences(self, initial_mode):
        try:
            values = self.settings.get(initial_mode, {})
            if not isinstance(values, dict):
                return
            index = values.get("operation", 0)
            if isinstance(index, int) and 0 <= index < self.OperationCombo.Items.Count:
                self.OperationCombo.SelectedIndex = index
            self.InputText.Text = values.get("input", self.InputText.Text)
            self.ExtraText.Text = values.get("extra", self.ExtraText.Text)
            self.AddOnce.IsChecked = bool(values.get("add_once", True))
            self.SharedValues.IsChecked = bool(values.get("allow_shared", False))
            scope = values.get("scope", self.SCOPES[0])
            if scope in self.SCOPES:
                self.ScopeCombo.SelectedIndex = self.SCOPES.index(scope)
        except Exception:
            LOGGER.exception("Préférences de paramètres non restaurées")

    def save_preferences(self):
        key = "number" if self.ModeCombo.SelectedIndex == 0 else "text"
        try:
            self.settings.set(key, {
                "operation": self.OperationCombo.SelectedIndex,
                "input": self.InputText.Text,
                "extra": self.ExtraText.Text,
                "add_once": bool(self.AddOnce.IsChecked),
                "allow_shared": bool(self.SharedValues.IsChecked),
                "scope": self.ScopeCombo.SelectedItem,
            })
        except Exception:
            LOGGER.exception("Préférences de paramètres non enregistrées")

    def load_parameters(self):
        self.parameter_options = parameter_options()
        for option in self.parameter_options:
            self.ParameterCombo.Items.Add(option)
        if self.parameter_options:
            self.ParameterCombo.SelectedIndex = 0

    def update_mode(self):
        numbering = self.ModeCombo.SelectedIndex == 0
        self.OperationCombo.Items.Clear()
        for option in (self.NUMBER_OPERATIONS if numbering else self.TEXT_OPERATIONS):
            self.OperationCombo.Items.Add(option)
        self.OperationCombo.SelectedIndex = 0
        self.OperationLabel.Text = "TYPE DE SÉQUENCE" if numbering else "OPÉRATION"
        self.InputLabel.Text = "VALEUR INITIALE" if numbering else "TEXTE À AJOUTER OU SUPPRIMER"
        self.ExtraLabel.Text = "PAS" if numbering else "SÉPARATEUR"
        self.InputText.Text = "001" if numbering else "BAT"
        self.ExtraText.Text = "1" if numbering else "-"
        self.SharedValues.Visibility = Visibility.Visible if numbering else Visibility.Collapsed
        self.AddOnce.Visibility = Visibility.Collapsed if numbering else Visibility.Visible
        self.SelectButton.IsEnabled = numbering
        self.ScopeCombo.IsEnabled = not numbering
        self.MessageText.Text = ""
        self.clear_preview()

    def ModeChanged(self, sender, args):
        if hasattr(self, "OperationCombo"):
            self.update_mode()

    def clear_preview(self):
        self.changes = {}
        self.preview_signature = None
        self.ConfirmCheck.IsChecked = False
        self.ApplyButton.IsEnabled = False
        self.PreviewGrid.ItemsSource = None
        self.CountText.Text = "0 pièce"

    def _signature(self):
        option = self.ParameterCombo.SelectedItem
        return (self.ModeCombo.SelectedIndex, option.Id if option else None,
                self.OperationCombo.SelectedIndex, self.InputText.Text, self.ExtraText.Text,
                self.ScopeCombo.SelectedIndex, bool(self.SharedValues.IsChecked),
                bool(self.AddOnce.IsChecked))

    def SelectRooms(self, sender, args):
        # Hide/Show sur la MÊME fenêtre ; aucune fenêtre de sélection additionnelle.
        self.picked = []
        seen = set()
        self.Hide()
        try:
            while True:
                room = revit.pick_element_by_category(
                    DB.BuiltInCategory.OST_Rooms,
                    message="Cliquez les pièces dans l'ordre ; Échap termine la sélection")
                if room is None:
                    break
                if room.UniqueId not in seen:
                    self.picked.append(room)
                    seen.add(room.UniqueId)
        except Exception as error:
            # L'annulation doit être distinguée d'une erreur inattendue.
            if "OperationCanceled" not in type(error).__name__:
                LOGGER.exception("Sélection de pièces interrompue par une erreur")
                self.MessageText.Text = "Erreur pendant la sélection : {}".format(error)
        finally:
            self.Show()
            self.Activate()
        self.refresh()

    def _table(self):
        table = DataTable("Modifications")
        for name, typ in (("Enabled", bool), ("RoomKey", str), ("RoomLabel", str), ("Before", str),
                          ("After", str), ("Status", str)):
            table.Columns.Add(name, typ)
        return table

    def refresh(self):
        self.clear_preview()
        selected = self.ParameterCombo.SelectedItem
        if selected is None:
            self.MessageText.Text = "Aucun paramètre texte modifiable disponible."
            return
        numbering = self.ModeCombo.SelectedIndex == 0
        try:
            rooms = self.picked if numbering else collect_rooms(self.ScopeCombo.SelectedItem)
            operation = (("digits" if self.OperationCombo.SelectedIndex == 0 else "letters")
                         if numbering else self.TEXT_CODES[self.OperationCombo.SelectedIndex])
            self.changes, skipped = prepare_changes(
                rooms, selected.Id, numbering, operation, self.InputText.Text,
                self.ExtraText.Text, bool(self.AddOnce.IsChecked))
            self.skipped_count = skipped
            table = self._table()
            for key, (room, parameter, before, after) in self.changes.items():
                row = table.NewRow()
                row["Enabled"], row["RoomLabel"] = True, room_label(room)
                row["RoomKey"] = key
                row["Before"], row["After"], row["Status"] = before, after, "Prêt"
                table.Rows.Add(row)
            if numbering:
                collisions = check_collisions(self.changes, selected.Id,
                                              bool(self.SharedValues.IsChecked))
                for row in table.Rows:
                    key = row["RoomKey"]
                    if key in collisions:
                        row["Status"] = "Doublon"
                        row["Enabled"] = False
            self.table = table
            self.preview_signature = self._signature()
            self.PreviewGrid.ItemsSource = table.DefaultView
            self.ApplyButton.IsEnabled = any(row["Status"] == "Prêt" for row in table.Rows)
            self.CountText.Text = "{} modification(s)".format(table.Rows.Count)
            self.MessageText.Text = "{} pièce(s) ignorée(s).".format(skipped)
        except Exception as error:
            LOGGER.exception("Échec de préparation des paramètres de pièces")
            self.MessageText.Text = "Aperçu impossible : {}".format(error)

    def RefreshPreview(self, sender, args):
        self.refresh()

    def ApplyChanges(self, sender, args):
        if self.table is None:
            self.MessageText.Text = "Actualisez l'aperçu avant validation."
            return
        if self.preview_signature != self._signature():
            self.MessageText.Text = "La configuration a changé : actualisez l'aperçu."
            return
        if not self.ConfirmCheck.IsChecked:
            self.MessageText.Text = "Cochez « Je confirme les valeurs » avant d'appliquer."
            return
        self.PreviewGrid.CommitEdit()
        selected = []
        for row in self.table.Rows:
            if not row["Enabled"] or row["Status"] != "Prêt":
                continue
            item = self.changes.get(row["RoomKey"])
            if item is not None:
                selected.append(item)
        if not selected:
            self.MessageText.Text = "Aucune modification admissible sélectionnée."
            return
        excluded_count = len(self.changes) - len(selected)
        if self.ModeCombo.SelectedIndex == 0:
            # Les lignes décochées restent inchangées : elles doivent compter
            # comme valeurs existantes pour le contrôle final des doublons.
            selected_keys = set(item[0].UniqueId for item in selected)
            filtered = {key: item for key, item in self.changes.items()
                        if key in selected_keys}
            collisions = check_collisions(
                filtered, self.ParameterCombo.SelectedItem.Id,
                bool(self.SharedValues.IsChecked))
            if collisions:
                self.MessageText.Text = "Doublons après exclusions : actualisez la sélection avant d'appliquer."
                return
        try:
            count = commit_changes(selected)
            LOGGER.info("Paramètres des pièces : %s écriture(s) validée(s)", count)
            self.last_report = {
                "updated": count, "excluded": excluded_count,
                "skipped": self.skipped_count,
                "mode": self.ModeCombo.SelectedIndex,
                "parameter": self.ParameterCombo.SelectedItem.Label,
            }
            self.FooterText.Text = "{} pièce(s) modifiée(s). Annulation possible dans Revit.".format(count)
            self.ReportText.Text = (
                "Rapport : {updated} modifiée(s), {excluded} exclue(s), "
                "{skipped} ignorée(s). Paramètre : {parameter}.".format(**self.last_report))
            self.save_preferences()
            self.refresh()
        except Exception as error:
            LOGGER.exception("Écriture des paramètres annulée")
            self.MessageText.Text = "Échec, aucune modification conservée : {}".format(error)

    def CloseWindow(self, sender, args):
        self.save_preferences()
        self.Close()


def launch(mode):
    if revit.doc is None or revit.doc.IsFamilyDocument or revit.doc.IsReadOnly:
        forms.alert("Ouvrez un projet Revit modifiable.", title="Paramètres des pièces")
        return
    RoomParametersWindow(mode).ShowDialog()
