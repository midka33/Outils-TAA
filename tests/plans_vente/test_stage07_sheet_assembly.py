# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

import pytest

from plans_vente.sheet_layout import default_sheet_anchors


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

    assert 'SHEET_ASSEMBLY_BUILD = "stage07c-auto-fit-main-view-v5"' in text
    assert "ViewSheet.Create" in text
    assert "Viewport.Create" in text
    assert "ScheduleSheetInstance.Create" in text
    assert "viewport.GetBoxCenter()" in text
    assert "instance.Point" in text
    assert "layout.title_block_type.Id" in text
    assert "viewport.ChangeTypeId(viewport_type_id)" in text


def test_stage07b_template_roles_are_selected_by_user_not_magic_names():
    text = SERVICE.read_text(encoding="utf-8")

    assert "class SheetPlacedViewCandidate" in text
    assert "class SheetPlacedScheduleCandidate" in text
    assert "def _placed_view_candidates(" in text
    assert "def _placed_schedule_candidates(" in text
    assert "required_placeholder_names" not in text
    assert "PDV_MODELE_VUE" not in text
    assert "PDV_MODELE_REPERAGE" not in text


def test_stage07b_lists_all_sheets_and_validates_only_selected_sheet():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def list_sheet_templates(" in text
    assert "def inspect_sheet_template(" in text
    assert "def _template_layout_from_mapping(" in text
    assert "for sheet in (" in text
    assert ".OfClass(ViewSheet)" in text
    assert "self._template_layout(sheet)" not in text[
        text.index("    def list_sheet_templates("):
        text.index("    def inspect_sheet_template(")
    ]
    inspect_block = text[
        text.index("    def inspect_sheet_template("):
        text.index("    def create_sheet_from_template(")
    ]
    assert "self._placed_view_candidates(sheet)" in inspect_block
    assert "self._placed_schedule_candidates(sheet)" in inspect_block
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
    assert "def inspect_sheet_template(" in controller
    assert "def sheet_assembly_readiness(" in controller
    assert "def create_sheet_from_template(" in controller
    assert "def sheet_assembly_build_id(" in controller

    assert "import sheet_assembly_service as _sheet_assembly_service" in script
    assert "_reload_module(_sheet_assembly_service)" in script
    assert "SheetAssemblyService = _sheet_assembly_service.SheetAssemblyService" in script
    assert "sheet_assembly_service = SheetAssemblyService(document)" in script
    assert "sheet_assembly_service=sheet_assembly_service" in script


def test_stage07_ui_exposes_sheet_template_and_create_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    assert "Étape 07C — Composition automatique" in xaml
    assert "Feuille modèle — choix utilisateur" in xaml
    for name in (
        "SheetInfoText",
        "SheetTemplateCombo",
        "SheetMainViewCombo",
        "SheetLocationViewCombo",
        "SheetInteriorScheduleCombo",
        "SheetExteriorScheduleCombo",
        "SheetAutoFitCheckBox",
        "SheetAllowedScalesTextBox",
        "CreateSheetButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'SelectionChanged="SheetTemplateChanged"' in xaml
    assert 'Click="CreateSheet_Click"' in xaml
    assert "def CreateSheet_Click(" in window
    assert "def _load_sheet_templates(" in window
    assert "def _inspect_selected_sheet_template(" in window
    assert "def _load_sheet_readiness(" in window
    assert "def _selected_sheet_role_mapping(" in window
    assert "def SheetRoleChoiceChanged(" in window
    assert "def SheetFitChoiceChanged(" in window
    assert "def _sheet_fit_options(" in window
    assert "self.SheetTemplateCombo.SelectedIndex = -1" in window
    assert "template_main_viewport_unique_id" in window
    assert "template_location_viewport_unique_id" in window
    assert "template_interior_schedule_instance_unique_id" in window
    assert "template_exterior_schedule_instance_unique_id" in window
    assert "auto_fit_main_view=auto_fit_main_view" in window
    assert "allowed_scales=allowed_scales" in window
    assert "create_sheet_from_template(" in window


def test_stage07_documentation_is_opened():
    text = DOC.read_text(encoding="utf-8")
    assert "Étape 06 — Cotations V1 : VALIDÉE." in text
    assert "## Ouverture Étape 07 — Assemblage de la feuille" in text
    assert "Prototype 07A : VALIDÉ TECHNIQUEMENT" in text
    assert "### Prototype 07B — Feuille modèle" in text
    assert "Correctif 07B.2 — mapping explicite des éléments placés" in text
    assert "Vue modèle — logement" in text
    assert "Vue modèle — repérage" in text
    assert "Nomenclature modèle — intérieure" in text
    assert "Nomenclature modèle — extérieure" in text
    assert "feature/plans-de-vente-stage07-sheet-assembly" in text



def test_stage07b_result_reports_template_sheet():
    text = SERVICE.read_text(encoding="utf-8")

    assert "template_sheet_label" in text
    assert "result.template_sheet_label" in WINDOW.read_text(encoding="utf-8")
    assert "stage07c-auto-fit-main-view-v5" in text



def test_stage07b_controller_passes_four_mapping_ids():
    controller = CONTROLLER.read_text(encoding="utf-8")

    for name in (
        "template_main_viewport_unique_id",
        "template_location_viewport_unique_id",
        "template_interior_schedule_instance_unique_id",
        "template_exterior_schedule_instance_unique_id",
    ):
        assert name in controller


def test_stage07b_create_requires_distinct_template_roles():
    text = SERVICE.read_text(encoding="utf-8")

    assert "main_viewport_unique_id == location_viewport_unique_id" in text
    normalized = " ".join(text.split())
    assert (
        "interior_schedule_instance_unique_id "
        "== exterior_schedule_instance_unique_id"
    ) in normalized



def test_stage07c_service_fits_main_view_to_template_box():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _create_fitted_main_viewport(" in text
    assert "choose_fitting_scale(" in text
    assert "viewport_fits(" in text
    assert "ViewDuplicateOption.WithDetailing" in text
    assert "source_view.Duplicate(" in text
    assert "fitted_view.Scale = int(scale)" in text
    assert "layout.viewport_box_sizes.get(" in text
    assert '"main_view"' in text


def test_stage07c_never_changes_scale_of_original_production_view():
    text = SERVICE.read_text(encoding="utf-8")

    helper = text[
        text.index("    def _create_fitted_main_viewport("):
        text.index("    def _unique_view_name(", text.index("    def _create_fitted_main_viewport("))
    ]

    assert "source_view.Scale =" not in helper
    assert "source_view.Duplicate(" in helper
    assert "fitted_view.Scale =" in helper


def test_stage07c_controller_accepts_fit_options():
    controller = CONTROLLER.read_text(encoding="utf-8")

    assert "auto_fit_main_view=True" in controller
    assert "allowed_scales=None" in controller
    assert "auto_fit_main_view=auto_fit_main_view" in controller
    assert "allowed_scales=allowed_scales" in controller
