# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Point d'entrée pyRevit du module Plans de vente."""

__title__ = "Plans de\nvente"
__doc__ = (
    "Détecte les logements et prépare vues, nomenclatures, repérage, "
    "étiquettes, cotations et feuilles des plans de vente."
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

# pyRevit peut conserver des modules Python dans le moteur entre deux reloads
# d'extension. On force le rechargement du service d'étiquettes pour garantir
# que le code exécuté correspond au fichier présent sur disque.
try:
    from importlib import reload as _reload_module
except ImportError:
    _reload_module = reload

import room_tag_service as _room_tag_service
_room_tag_service = _reload_module(_room_tag_service)
RoomTagService = _room_tag_service.RoomTagService

import plans_vente.dimension_geometry as _dimension_geometry
_dimension_geometry = _reload_module(_dimension_geometry)
import plans_vente.dimension_positioning as _dimension_positioning
_dimension_positioning = _reload_module(_dimension_positioning)
import dimension_service as _dimension_service
_dimension_service = _reload_module(_dimension_service)
DimensionService = _dimension_service.DimensionService

from schedule_service import ScheduleService

import sheet_assembly_service as _sheet_assembly_service
_sheet_assembly_service = _reload_module(_sheet_assembly_service)
SheetAssemblyService = _sheet_assembly_service.SheetAssemblyService

import full_generation_service as _full_generation_service
_full_generation_service = _reload_module(_full_generation_service)
FullGenerationService = _full_generation_service.FullGenerationService

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
    dimension_service = DimensionService(document)
    sheet_assembly_service = SheetAssemblyService(document)
    location_plan_service = LocationPlanService(
        document,
        plan_view_service,
        crop_geometry_service,
    )
    full_generation_service = FullGenerationService(
        document=document,
        prototype_view_service=prototype_view_service,
        schedule_service=schedule_service,
        location_plan_service=location_plan_service,
        room_tag_service=room_tag_service,
        dimension_service=dimension_service,
        sheet_assembly_service=sheet_assembly_service,
    )

    controller = PlansVenteController(
        analysis_service=analysis_service,
        prototype_view_service=prototype_view_service,
        schedule_service=schedule_service,
        location_plan_service=location_plan_service,
        room_tag_service=room_tag_service,
        dimension_service=dimension_service,
        sheet_assembly_service=sheet_assembly_service,
        full_generation_service=full_generation_service,
    )

    window = PlansVenteWindow(controller)
    window.ShowDialog()


if __name__ == "__main__":
    main()
