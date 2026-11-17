# -*- coding: utf-8 -*-
"""À propos : affiche la version centrale de la suite, sans dépendre de Git."""
import os

from pyrevit import forms
from taa_ui_theme import apply_theme
from lib.common.taa_version import (
    read_version, display_version, display_release, display_status
)


class AboutWindow(forms.WPFWindow):
    def __init__(self, owner=None):
        xaml_path = os.path.join(os.path.dirname(__file__), "about_window.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        apply_theme(self)
        if owner is not None:
            self.Owner = owner

        version = read_version()
        self.AboutVersionText.Text = "Version Outils TAA : {}".format(
            display_version(version))
        self.AboutReleaseText.Text = display_release(version)
        self.AboutStatusText.Text = display_status(version)

    def Close_Click(self, sender, args):
        self.Close()
