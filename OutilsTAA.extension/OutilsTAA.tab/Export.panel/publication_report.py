# -*- coding: utf-8 -*-
"""Fenêtre WPF du rapport de publication."""

import os

from pyrevit import forms


class PublicationReportRow(object):
    """Ligne affichée dans le rapport de publication."""

    def __init__(self, carnet, result, path=None):
        self.Carnet = carnet or "—"
        self.Format = result.get("format", "—")
        self.Mode = "Combiné" if result.get("mode") == "combined" else "Séparé"
        self.Status = "OK" if result.get("success") else "ERREUR"
        self.Count = result.get("count", 0)
        self.Path = path or result.get("file") or result.get("directory") or "—"

        details = []
        for warning in result.get("warnings", []):
            details.append("AVERTISSEMENT : " + warning)
        for error in result.get("errors", []):
            details.append("ERREUR : " + error)
        self.Details = " | ".join(details) if details else "Export terminé."


class PublicationReportWindow(forms.WPFWindow):
    """Affiche le résultat détaillé d'une publication."""

    def __init__(self, report, owner=None):
        xaml_path = os.path.join(
            os.path.dirname(__file__),
            "publication_report.xaml"
        )
        forms.WPFWindow.__init__(self, xaml_path)

        if owner is not None:
            self.Owner = owner

        self.report = report or {}
        self.output_directory = self.report.get("output_directory") or ""

        rows = []
        carnet = self.report.get("carnet")
        for result in self.report.get("results", []):
            files = result.get("files") or []
            if files:
                for file_path in files:
                    rows.append(PublicationReportRow(carnet, result, file_path))
            else:
                rows.append(PublicationReportRow(carnet, result))

        self.ReportGrid.ItemsSource = rows

        success = bool(self.report.get("success"))
        status = "Publication terminée" if success else "Publication terminée avec erreurs"
        self.SummaryText.Text = "{0} — carnet : {1}".format(
            status,
            carnet or "inconnu"
        )
        self.DestinationText.Text = (
            "Destination : {0}".format(self.output_directory)
            if self.output_directory
            else "Destination non renseignée."
        )

        warnings = self.report.get("warnings", [])
        errors = self.report.get("errors", [])
        self.WarningsText.Text = ""
        if warnings:
            self.WarningsText.Text += "{0} avertissement(s). ".format(len(warnings))
        if errors:
            self.WarningsText.Text += "{0} erreur(s).".format(len(errors))

    def OpenFolder_Click(self, sender, args):
        """Ouvre le dossier de publication dans l'explorateur Windows."""
        if not self.output_directory or not os.path.isdir(self.output_directory):
            forms.alert(
                "Le dossier de publication n'est pas accessible.",
                title="Rapport de publication"
            )
            return
        try:
            os.startfile(self.output_directory)
        except Exception as exc:
            forms.alert(
                "Impossible d'ouvrir le dossier :\n{0}".format(exc),
                title="Rapport de publication"
            )

    def Close_Click(self, sender, args):
        self.Close()
