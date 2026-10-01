# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Point d'entrée pyRevit du module Plans de vente."""

__title__ = "Plans de\nvente"
__doc__ = (
    "Détecte les logements du projet à partir d'un paramètre texte de pièce. "
    "Étape 01 du module Plans de vente Outils TAA."
)

import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PANEL_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
EXTENSION_DIR = os.path.abspath(os.path.join(PANEL_DIR, "..", ".."))
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")
SERVICE_DIR = os.path.join(PANEL_DIR, "services")
UI_DIR = os.path.join(PANEL_DIR, "ui")

for path in (LIB_DIR, PANEL_DIR, SERVICE_DIR, UI_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from plans_vente.housing_grouper import HousingGrouper
from housing_analysis_service import HousingAnalysisService
from plans_vente_controller import PlansVenteController
from room_collector_service import RoomCollectorService
from room_parameter_service import RoomParameterService
from plans_vente_window import PlansVenteWindow


def main():
    try:
        from pyrevit import forms, revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    document = revit.doc
    if document is None:
        forms.alert(
            "Ouvrez un projet Revit avant de lancer Plans de vente.",
            title="Plans de vente",
            warn_icon=True,
        )
        return

    collector_service = RoomCollectorService(document)
    parameter_service = RoomParameterService()
    analysis_service = HousingAnalysisService(
        collector_service=collector_service,
        parameter_service=parameter_service,
        grouper=HousingGrouper(),
    )
    controller = PlansVenteController(analysis_service)

    window = PlansVenteWindow(controller)
    window.ShowDialog()


if __name__ == "__main__":
    main()
