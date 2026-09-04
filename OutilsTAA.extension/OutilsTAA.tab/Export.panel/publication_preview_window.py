# -*- coding: utf-8 -*-
"""Fenêtre de confirmation avant publication."""

import os
import subprocess

from pyrevit import forms


class PublicationPreviewWindow(forms.WPFWindow):
    """Affiche les livrables prévus et demande une confirmation explicite."""

    def __init__(self, preview, owner=None):
        self.preview = preview or {}
        self.confirmed = False
        xaml_path = os.path.join(os.path.dirname(__file__), "publication_preview.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        self._set_owner(owner)
        self._load()

    def _set_owner(self, owner):
        if owner is not None:
            try:
                self.Owner = owner
            except Exception:
                pass

    def _load(self):
        rows = self.preview.get("rows", [])
        errors = self.preview.get("errors", [])
        warnings = self.preview.get("warnings", [])
        directory = self.preview.get("directory", "")
        self.PreviewGrid.ItemsSource = rows
        self.SummaryText.Text = "{} livrable(s) seront générés.".format(len(rows))
        self.DestinationText.Text = "Destination : {}".format(directory or "—")
        self.WarningText.Text = ""
        if errors:
            self.ErrorText.Text = "ERREURS BLOQUANTES\n• " + "\n• ".join(errors)
        else:
            self.ErrorText.Text = ""
        if warnings:
            self.WarningText.Text = "AVERTISSEMENTS\n• " + "\n• ".join(warnings)
        self.ConfirmButton.IsEnabled = not bool(errors) and bool(rows)

    def Confirm_Click(self, sender, args):
        self.confirmed = True
        self.Close()

    def Cancel_Click(self, sender, args):
        self.confirmed = False
        self.Close()

    def OpenFolder_Click(self, sender, args):
        directory = self.preview.get("directory", "")
        if not directory or not os.path.isdir(directory):
            forms.alert("Le dossier de destination n'existe pas encore.", title="Aperçu")
            return
        try:
            subprocess.Popen(["explorer.exe", directory])
        except Exception as exc:
            forms.alert("Impossible d'ouvrir le dossier : {0}".format(exc), title="Aperçu")
