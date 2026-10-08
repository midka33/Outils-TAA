# -*- coding: utf-8 -*-
"""Affichage synchrone de la progression ; les appels Revit restent sur leur thread."""

from __future__ import unicode_literals

import os
import logging

from pyrevit import forms
from System import Action
from System.Windows.Threading import DispatcherPriority
from taa_ui_theme import apply_theme
from publication_progress import PublicationProgress


class PublicationProgressWindow(forms.WPFWindow):
    """Fenêtre possédée par Export, sans annulation native ni minuterie."""

    def __init__(self, owner, has_pdf=True):
        self._allow_close = False
        forms.WPFWindow.__init__(self, os.path.join(
            os.path.dirname(__file__), "publication_progress.xaml"))
        apply_theme(self)
        self.Owner = owner
        if not has_pdf:
            self.Title = "Publication en cours"
            self.HeadingText.Text = "Publication en cours"

    def update(self, state):
        self.ProgressBar.Value = state["percent"]
        self.PercentText.Text = "{0} %".format(state["percent"])
        self.CarnetText.Text = state["carnet_name"]
        self.ItemText.Text = state["item_label"]
        detail_total = int(state.get("detail_total", 0) or 0)
        detail_label = state.get("detail_label", "unités")
        if detail_total > 0 and detail_label == "progression Revit":
            # Position/UpperRange sert au calcul de la barre mais n'est pas
            # une information métier (ce n'est pas un nombre de feuilles).
            self.UnitsLabelText.Text = "Avancement :"
            self.UnitsText.Text = "Revit travaille…"
        elif detail_total > 0:
            self.UnitsLabelText.Text = (
                "Mises en page :"
                if detail_label == "mises en page"
                else "Avancement :"
            )
            self.UnitsText.Text = "{0} / {1}".format(
                state.get("detail_current", 0),
                detail_total,
            )
        else:
            self.UnitsLabelText.Text = "Avancement :"
            self.UnitsText.Text = "{0} / {1} étapes".format(
                state["current"], state["total"]
            )
        self.PhaseText.Text = state["phase"]
        self.StatusText.Text = state["message"]
        phase_key = state["phase_key"]
        if phase_key in ("pdf", "dwg"):
            active = "export"
        elif phase_key in ("pdf_delivery", "dwg_delivery"):
            active = "delivery"
        else:
            active = phase_key
        for key, control in (("prepare", self.PrepareStep), ("export", self.ExportStep),
                             ("delivery", self.DeliveryStep), ("finalize", self.FinalizeStep)):
            control.Opacity = 1.0 if key == active else 0.45
        self.UpdateLayout()
        # Loaded est après layout/render, avant Input. Ne pas utiliser Send
        # (appel immédiat sur ce thread) ni une boucle DoEvents non bornée.
        self.Dispatcher.Invoke(DispatcherPriority.Loaded, Action(lambda: None))

    def Window_Closing(self, sender, args):
        args.Cancel = not self._allow_close

    def close_progress(self):
        self._allow_close = True
        self.Close()


class PublicationProgressSession(object):
    """Propriétaire unique du cycle ouvrir/restaurer/fermer, même sur exception."""

    def __init__(self, owner, targets):
        self.owner = owner
        self.targets = targets
        self.window = None
        self.progress = None

    def __enter__(self):
        if getattr(self.owner, "_publication_in_progress", False):
            raise RuntimeError("Une publication est déjà en cours.")
        self.was_enabled = self.owner.IsEnabled
        self.owner._publication_in_progress = True
        try:
            settings = [self.owner._resolve_settings(target) for target in self.targets]
            self.window = PublicationProgressWindow(
                self.owner, has_pdf=any(value.pdf_enabled for value in settings))
            self.progress = PublicationProgress(self.targets, settings, self.window.update)
            self.owner.IsEnabled = False
            self.window.Show()
            self.progress.start()
            return self.progress
        except Exception:
            self._close_after_error()
            raise

    def _close_after_error(self):
        """Préserve l'exception d'origine si le nettoyage échoue aussi."""
        try:
            self._close()
        except Exception:
            logging.getLogger("OutilsTAA").exception("Échec de fermeture de la progression")

    def _close(self):
        try:
            if self.window is not None:
                self.window.close_progress()
        finally:
            self.owner.IsEnabled = self.was_enabled
            self.owner._publication_in_progress = False

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is not None:
                self.progress.interrupt()
        finally:
            if exc_type is not None:
                self._close_after_error()
            else:
                self._close()
        return False
