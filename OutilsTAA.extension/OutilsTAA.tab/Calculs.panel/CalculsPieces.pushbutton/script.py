# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Point d'entrée pyRevit de Calculs des pièces."""

__title__ = "Calculs\ndes pièces"
__doc__ = (
    "Regroupe les pièces du projet, additionne un paramètre et écrit "
    "le total dans un paramètre de destination."
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

from calculation.room_calculator import RoomCalculator
from calculation.room_filter import RoomFilter

from calculation_controller import CalculationController
from calculation_settings_service import CalculationSettingsService
from room_calculation_workflow import RoomCalculationWorkflow
from room_collector_service import RoomCollectorService
from room_parameter_service import RoomParameterService
from room_parameter_validator import RoomParameterValidator
from room_unit_service import RoomUnitService
from room_writer import RoomWriter
from calculs_window import CalculsWindow


def main():
    try:
        from pyrevit import forms, revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    document = revit.doc
    if document is None:
        forms.alert(
            "Ouvrez un projet Revit avant de lancer Calculs des pièces.",
            title="Calculs des pièces",
            warn_icon=True,
        )
        return

    collector_service = RoomCollectorService(document)
    parameter_service = RoomParameterService()
    parameter_validator = RoomParameterValidator()
    unit_service = RoomUnitService()
    writer = RoomWriter(parameter_service, unit_service)

    workflow = RoomCalculationWorkflow(
        document=document,
        collector_service=collector_service,
        parameter_service=parameter_service,
        parameter_validator=parameter_validator,
        room_filter=RoomFilter(),
        calculator=RoomCalculator(),
        writer=writer,
    )

    settings_service = CalculationSettingsService()

    controller = CalculationController(
        collector_service=collector_service,
        parameter_service=parameter_service,
        parameter_validator=parameter_validator,
        unit_service=unit_service,
        workflow=workflow,
        settings_service=settings_service,
    )

    window = CalculsWindow(controller)
    window.ShowDialog()


if __name__ == "__main__":
    main()
