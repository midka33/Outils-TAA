# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Point d'entrée pyRevit du module Plans de vente."""

__title__ = "Plans de\nvente"
__doc__ = (
    "Détecte les logements et prépare vues, nomenclatures, repérage "
    "et étiquettes de pièces des plans de vente."
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
from crop_geometry_service import CropGeometryService
from housing_analysis_service import HousingAnalysisService
from location_plan_service import LocationPlanService
from plan_view_service import PlanViewService
from plans_vente_controller import PlansVenteController
from prototype_view_service import PrototypeViewService
from room_collector_service import RoomCollectorService
from room_parameter_service import RoomParameterService
from room_tag_service import RoomTagService
from schedule_service import ScheduleService
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

    plan_view_service = PlanViewService(document)
    crop_geometry_service = CropGeometryService(document)
    prototype_view_service = PrototypeViewService(
        document=document,
        plan_view_service=plan_view_service,
        crop_geometry_service=crop_geometry_service,
    )

    schedule_service = ScheduleService(document)
    room_tag_service = RoomTagService(document)
    location_plan_service = LocationPlanService(
        document,
        plan_view_service,
        crop_geometry_service,
    )

    controller = PlansVenteController(
        analysis_service=analysis_service,
        prototype_view_service=prototype_view_service,
        schedule_service=schedule_service,
        location_plan_service=location_plan_service,
        room_tag_service=room_tag_service,
    )

    window = PlansVenteWindow(controller)
    window.ShowDialog()


if __name__ == "__main__":
    main()
