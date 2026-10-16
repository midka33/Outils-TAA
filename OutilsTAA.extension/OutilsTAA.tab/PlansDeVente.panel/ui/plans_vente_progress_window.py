# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Fenêtre synchrone de progression de la création des plans de vente."""

import os

from pyrevit import forms
from System import Action
from System.Windows.Threading import DispatcherPriority

from taa_ui_theme import apply_theme


class PlansVenteProgressWindow(forms.WPFWindow):
    def __init__(self, owner, total):
        self._allow_close = False
        self._total = max(1, int(total or 0))
        forms.WPFWindow.__init__(
            self,
            os.path.join(
                os.path.dirname(__file__),
                "plans_vente_progress.xaml",
            ),
        )
        apply_theme(self)
        self.Owner = owner

    def _flush_ui(self):
        self.UpdateLayout()
        self.Dispatcher.Invoke(
            DispatcherPriority.Loaded,
            Action(lambda: None),
        )

    def update(
        self,
        current,
        housing_key="—",
        phase="Création",
        message="",
        item_label="Revit travaille…",
    ):
        current = max(0, min(int(current or 0), self._total))
        percent = int(round(100.0 * current / float(self._total)))
        if current < self._total:
            percent = min(percent, 99)

        self.ProgressBar.Value = percent
        self.PercentText.Text = "{} %".format(percent)
        self.HousingText.Text = housing_key or "—"
        self.UnitsText.Text = "{} / {}".format(current, self._total)
        self.PhaseText.Text = phase
        self.ItemText.Text = item_label
        self.StatusText.Text = message or "{} en cours…".format(phase)

        active = "prepare"
        phase_lower = (phase or "").lower()
        if "création" in phase_lower:
            active = "create"
        elif "assemblage" in phase_lower:
            active = "assemble"
        elif "final" in phase_lower:
            active = "finalize"

        for key, control in (
            ("prepare", self.PrepareStep),
            ("create", self.CreateStep),
            ("assemble", self.AssembleStep),
            ("finalize", self.FinalizeStep),
        ):
            control.Opacity = 1.0 if key == active else 0.45

        self._flush_ui()

    def finish(self, created, skipped, failures):
        self.ProgressBar.Value = 100
        self.PercentText.Text = "100 %"
        self.UnitsText.Text = "{} / {}".format(self._total, self._total)
        self.PhaseText.Text = "Finalisation"
        self.HousingText.Text = "—"
        self.ItemText.Text = "Rapport de création"
        self.StatusText.Text = (
            "{} créé(s), {} ignoré(s), {} échec(s)."
        ).format(created, skipped, failures)

        for control in (
            self.PrepareStep,
            self.CreateStep,
            self.AssembleStep,
        ):
            control.Opacity = 0.45
        self.FinalizeStep.Opacity = 1.0
        self._flush_ui()

    def Window_Closing(self, sender, args):
        args.Cancel = not self._allow_close

    def close_progress(self):
        self._allow_close = True
        self.Close()


class PlansVenteProgressSession(object):
    """Gère l'ouverture, le verrouillage de la fenêtre principale et la fermeture."""

    def __init__(self, owner, total):
        self.owner = owner
        self.total = max(1, int(total or 0))
        self.window = None
        self.was_enabled = True

    def __enter__(self):
        self.was_enabled = self.owner.IsEnabled
        self.window = PlansVenteProgressWindow(
            self.owner,
            self.total,
        )
        self.owner.IsEnabled = False
        self.window.Show()
        self.window.update(
            0,
            phase="Préparation",
            message="Préparation de la création des plans de vente…",
            item_label="Analyse du lot",
        )
        return self.window

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if self.window is not None:
                self.window.close_progress()
        finally:
            self.owner.IsEnabled = self.was_enabled
        return False
