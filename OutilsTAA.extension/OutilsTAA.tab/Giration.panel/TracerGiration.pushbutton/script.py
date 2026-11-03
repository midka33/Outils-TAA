# -*- coding: utf-8 -*-
"""
Point d'entrée pour le module Giration des véhicules.

Ce script est exécuté par pyRevit lorsque l'utilisateur clique sur le bouton
"Tracer Giration" dans l'onglet Outils TAA.
"""

import os
import sys

# Configuration des chemins pour l'import
CURRENT_DIR = os.path.dirname(__file__)
EXTENSION_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
PANEL_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
MODEL_DIR = os.path.join(PANEL_DIR, "models")
SERVICE_DIR = os.path.join(PANEL_DIR, "services")
UI_DIR = os.path.join(PANEL_DIR, "ui")
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")

# Ajout des chemins au sys.path
for path in (EXTENSION_DIR, LIB_DIR, PANEL_DIR, MODEL_DIR, SERVICE_DIR, UI_DIR):
    if path not in sys.path:
        sys.path.append(path)

from pyrevit import revit, forms
from lib.common import logger

# Import du module de giration
try:
    from giration_main_window import GirationMainWindow
    from giration_controller import GirationController
    GIRATION_AVAILABLE = True
except ImportError as e:
    logger.get_logger().error(f"Erreur de chargement du module Giration: {e}")
    GIRATION_AVAILABLE = False


def main():
    """
    Fonction principale exécutée lors du clic sur le bouton.
    """
    if not GIRATION_AVAILABLE:
        forms.alert(
            "Le module Giration des véhicules n'est pas disponible. "
            "Vérifiez que tous les fichiers sont correctement installés.",
            title="Erreur - Giration"
        )
        return
    
    # Vérifier que nous sommes dans un document Revit
    if not revit.doc:
        forms.alert(
            "Aucun document Revit actif. Ouvrez un projet Revit pour utiliser cet outil.",
            title="Giration - Erreur"
        )
        return
    
    # Créer le contrôleur
    try:
        controller = GirationController(revit.doc)
    except Exception as e:
        logger.get_logger().exception("Erreur lors de la création du contrôleur Giration")
        forms.alert(
            f"Erreur lors de l'initialisation: {e}",
            title="Giration - Erreur"
        )
        return
    
    # Ouvrir la fenêtre principale
    try:
        window = GirationMainWindow(controller)
        window.ShowDialog()
    except Exception as e:
        logger.get_logger().exception("Erreur lors de l'ouverture de la fenêtre Giration")
        forms.alert(
            f"Erreur lors de l'ouverture de la fenêtre: {e}",
            title="Giration - Erreur"
        )


if __name__ == "__main__":
    main()
