# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre de rapport de Calculs des pièces."""

import os

from pyrevit import forms

from common.wpf_resources import load_resource_dictionary


class CalculationReportWindow(forms.WPFWindow):

    def __init__(self, prepared, report, owner=None):
        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(current_dir, "calculation_report.xaml")
        forms.WPFWindow.__init__(self, xaml_path)

        if owner is not None:
            self.Owner = owner

        self._load_theme()
        self._render(prepared, report)

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

    def _render(self, prepared, report):
        self.SummaryText.Text = (
            "{} pièces projet • {} après filtre • {} groupes".format(
                prepared.total_rooms,
                prepared.filtered_rooms,
                prepared.result.group_count,
            )
        )
        self.CountsText.Text = (
            "{} écriture(s) réussie(s) • {} échec(s) • "
            "{} pièce(s) ignorée(s) pendant le calcul".format(
                report.success_count,
                report.failed_count,
                len(report.skipped),
            )
        )

        lines = []

        if report.transaction_error:
            lines.append("ERREUR TRANSACTION")
            lines.append(report.transaction_error)
            lines.append("")

        if report.warnings:
            lines.append("AVERTISSEMENTS")
            for warning in report.warnings:
                lines.append("- " + str(warning))
            lines.append("")

        if report.failed_results:
            lines.append("ÉCHECS D'ÉCRITURE")
            for item in report.failed_results:
                lines.append(
                    "- {} • groupe {} : {}".format(
                        item.room_key,
                        item.group_value,
                        item.message,
                    )
                )
            lines.append("")

        if report.skipped:
            lines.append("PIÈCES IGNORÉES PENDANT LE CALCUL")
            for item in report.skipped:
                lines.append("- {} : {}".format(item.room_key, item.reason))
            lines.append("")

        if not lines:
            lines.append("Aucune anomalie détectée.")

        self.DetailsText.Text = "
".join(lines)

    def Close_Click(self, sender, args):
        self.Close()
