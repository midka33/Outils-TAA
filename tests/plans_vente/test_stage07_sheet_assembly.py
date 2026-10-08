# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

import pytest

from plans_vente.sheet_layout import default_sheet_anchors
from plans_vente.sheet_template import (
    TEMPLATE_MAIN_VIEW_NAME,
    TEMPLATE_LOCATION_VIEW_NAME,
    TEMPLATE_INTERIOR_SCHEDULE_NAME,
    TEMPLATE_EXTERIOR_SCHEDULE_NAME,
    required_placeholder_names,
)


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "sheet_assembly_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"
SCRIPT = PANEL / "PlansDeVente.pushbutton" / "script.py"
DOC = ROOT / "docs" / "20_Plans_de_Vente.md"


def test_default_sheet_anchors_are_inside_sheet_and_separated():
    anchors = default_sheet_anchors(0.0, 0.0, 10.0, 7.0)

    assert set(anchors) == {
        "main_view",
        "location_view",
        "interior_schedule",
        "exterior_schedule",
    }
    assert anchors["main_view"].x == pytest.approx(3.8)
    assert anchors["main_view"].y == pytest.approx(4.06)
    assert anchors["location_view"].x == pytest.approx(7.9)
    assert anchors["location_view"].y == pytest.approx(5.11)
    assert anchors["interior_schedule"].y > anchors["exterior_schedule"].y

    for anchor in anchors.values():
        assert 0.0 < anchor.x < 10.0
        assert 0.0 < anchor.y < 7.0


def test_default_sheet_anchors_reject_invalid_outline():
    with pytest.raises(ValueError):
        default_sheet_anchors(1.0, 0.0, 1.0, 7.0)


def test_stage07_service_uses_native_revit_sheet_placement_api():
    text = SERVICE.read_text(encoding="utf-8")
    ast.parse(text)

    assert 'SHEET_ASSEMBLY_BUILD = "stage07b-sheet-template-layout-v2"' in text
    assert "ViewSheet.Create" in text
    assert "Viewport.Create" in text
    assert "ScheduleSheetInstance.Create" in text
    assert "viewport.GetBoxCenter()" in text
    assert "instance.Point" in text
    assert "layout.title_block_type.Id" in text
    assert "viewport.ChangeTypeId(viewport_type_id)" in text


def test_stage07b_template_contract_is_explicit():
    names = required_placeholder_names()

    assert names == {
        "main_view": "PDV_MODELE_VUE",
        "location_view": "PDV_MODELE_REPERAGE",
        "interior_schedule": "PDV_MODELE_NOM_INT",
        "exterior_schedule": "PDV_MODELE_NOM_EXT",
    }
    assert TEMPLATE_MAIN_VIEW_NAME == "PDV_MODELE_VUE"
    assert TEMPLATE_LOCATION_VIEW_NAME == "PDV_MODELE_REPERAGE"
    assert TEMPLATE_INTERIOR_SCHEDULE_NAME == "PDV_MODELE_NOM_INT"
    assert TEMPLATE_EXTERIOR_SCHEDULE_NAME == "PDV_MODELE_NOM_EXT"


def test_stage07b_service_filters_only_complete_template_sheets():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def list_sheet_templates(" in text
    assert "def _template_layout(" in text
    assert "sheet.GetAllViewports()" in text
    assert "ScheduleSheetInstance" in text
    assert "required_placeholder_names()" in text
    assert "La feuille modèle doit contenir exactement un cartouche." in text


def test_stage07_service_discovers_existing_generated_artifacts():
    text = SERVICE.read_text(encoding="utf-8")

    assert 'name.startswith("PDV PROTO - {} - ".format(housing_key))' in text
    assert "location_view_name(housing.key)" in text
    assert 'schedule_name(housing.key, "INT")' in text
    assert 'schedule_name(housing.key, "EXT")' in text
    assert "La mise à jour sera traitée à l'Étape 08." in text


def test_stage07_controller_and_entrypoint_wire_service_outside_ui():
    controller = CONTROLLER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "self.sheet_assembly_service = sheet_assembly_service" in controller
    assert "def sheet_templates(" in controller
    assert "def sheet_assembly_readiness(" in controller
    assert "def create_sheet_from_template(" in controller
    assert "def sheet_assembly_build_id(" in controller

    assert "from sheet_assembly_service import SheetAssemblyService" in script
    assert "sheet_assembly_service = SheetAssemblyService(document)" in script
    assert "sheet_assembly_service=sheet_assembly_service" in script


def test_stage07_ui_exposes_sheet_template_and_create_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    assert "Étape 07B — Feuille modèle" in xaml
    for name in (
        "SheetInfoText",
        "SheetTemplateCombo",
        "CreateSheetButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'SelectionChanged="SheetTemplateChanged"' in xaml
    assert 'Click="CreateSheet_Click"' in xaml
    assert "def CreateSheet_Click(" in window
    assert "def _load_sheet_templates(" in window
    assert "def _load_sheet_readiness(" in window
    assert "create_sheet_from_template(" in window


def test_stage07_documentation_is_opened():
    text = DOC.read_text(encoding="utf-8")
    assert "Étape 06 — Cotations V1 : VALIDÉE." in text
    assert "## Ouverture Étape 07 — Assemblage de la feuille" in text
    assert "Prototype 07A : VALIDÉ TECHNIQUEMENT" in text
    assert "### Prototype 07B — Feuille modèle" in text
    assert "PDV_MODELE_VUE" in text
    assert "PDV_MODELE_REPERAGE" in text
    assert "PDV_MODELE_NOM_INT" in text
    assert "PDV_MODELE_NOM_EXT" in text
    assert "feature/plans-de-vente-stage07-sheet-assembly" in text



def test_stage07b_result_reports_template_sheet():
    text = SERVICE.read_text(encoding="utf-8")

    assert "template_sheet_label" in text
    assert "result.template_sheet_label" in WINDOW.read_text(encoding="utf-8")
    assert "stage07b-sheet-template-layout-v2" in text
