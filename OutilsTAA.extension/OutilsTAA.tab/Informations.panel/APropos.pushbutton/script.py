# -*- coding: utf-8 -*-
"""Commande autonome de ruban : À propos de la suite Outils TAA.

Aucun document Revit ni configuration de publication n'est nécessaire.
Le dialogue WPF est partagé avec la commande À propos d'Export.
"""
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
TAB_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
EXTENSION_DIR = os.path.abspath(os.path.join(TAB_DIR, ".."))
EXPORT_PANEL_DIR = os.path.join(TAB_DIR, "Export.panel")
EXPORT_SERVICES_DIR = os.path.join(EXPORT_PANEL_DIR, "services")

for path in (EXTENSION_DIR, EXPORT_SERVICES_DIR, EXPORT_PANEL_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from about_window import AboutWindow

AboutWindow().ShowDialog()
