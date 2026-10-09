# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "full_generation_service.py"
SCHEDULE = PANEL / "services" / "schedule_service.py"
SHEET = PANEL / "services" / "sheet_assembly_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"
SCRIPT = PANEL / "PlansDeVente.pushbutton" / "script.py"
DOC = ROOT / "docs" / "20_Plans_de_Vente.md"


def test_stage07d_service_is_template_driven_and_atomic():
    text = SERVICE.read_text(encoding="utf-8")
    ast.parse(text)

    assert 'FULL_GENERATION_BUILD = "stage07d-template-driven-full-generation-v3"' in text
    assert "def inspect_template(" in text
    assert "def generate(" in text
    assert "TransactionGroup(" in text
    assert "group.Assimilate()" in text
    assert "group.RollBack()" in text


def test_stage07d_detects_roles_from_model_instead_of_manual_mapping():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _classify_viewports(" in text
    assert "filled_regions" in text
    assert "room_tags" in text
    assert "dimensions" in text
    assert "location = min(infos, key=lambda item: item.area)" in text
    assert "main_candidates.sort(" in text


def test_stage07d_reuses_model_graphic_types_and_scale():
    text = SERVICE.read_text(encoding="utf-8")

    assert '"OST_RoomTags"' in text
    assert '"OST_Dimensions"' in text
    assert "def _filled_region_type(" in text
    assert "reference_scale=int(" in text
    assert "target_scale=inspection.reference_scale" in text


def test_stage07d_supports_any_number_of_schedules():
    schedule = SCHEDULE.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    service = SERVICE.read_text(encoding="utf-8")

    assert "def duplicate_templates_for_housing(" in schedule
    assert "for index, template in enumerate(templates, 1):" in schedule
    assert "allow_unfiltered=False" in schedule
    assert "allow_unfiltered=True" in service

    assert "def create_sheet_from_blueprint(" in sheet
    assert "for binding in bindings:" in sheet
    assert "for template_instance, schedule in resolved_schedules:" in sheet
    assert "placed_schedule_instances" in sheet
    assert "schedule_names=[" in sheet


def test_stage07d_controller_and_entrypoint_wire_service():
    controller = CONTROLLER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "full_generation_service=None" in controller
    assert "def inspect_full_generation_template(" in controller
    assert "def generate_full_plan(" in controller
    assert "def full_generation_build_id(" in controller

    assert "import full_generation_service as _full_generation_service" in script
    assert "FullGenerationService = _full_generation_service.FullGenerationService" in script
    assert "full_generation_service = FullGenerationService(" in script
    assert "full_generation_service=full_generation_service" in script


def test_stage07d_ui_has_one_click_full_plan_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    assert "Étape 07D — Génération complète" in xaml
    assert 'x:Name="CreateFullPlanButton"' in xaml
    assert 'Click="CreateFullPlan_Click"' in xaml
    assert "Créer le plan de vente complet" in xaml

    assert "def CreateFullPlan_Click(" in window
    assert "inspect_full_generation_template(" in window
    assert "generate_full_plan(" in window
    assert "def _update_full_generation_button_state(" in window


def test_stage07d_documentation_is_present():
    text = DOC.read_text(encoding="utf-8")

    assert "## Étape 07D — Génération complète depuis la feuille modèle" in text
    assert "stage07d-template-driven-full-generation-v3" in text
    assert "nombre libre de nomenclatures" in text
    assert "Correctif 07D.1 — repérage multi-niveau et crop de secours" in text
    assert "Correctif 07D.2 — crop du repérage repris depuis le modèle" in text



def test_stage07d_full_action_does_not_depend_on_manual_07c_role_mapping():
    window = WINDOW.read_text(encoding="utf-8")
    block = window[
        window.index("    def CreateFullPlan_Click("):
        window.index("    def CreateSheet_Click(")
    ]

    assert "_selected_sheet_role_mapping" not in block
    assert "DimensionViewCombo" not in block
    assert "inspect_full_generation_template(" in block



def test_stage07d_entrypoint_does_not_self_reference_service_during_construction():
    script = SCRIPT.read_text(encoding="utf-8")
    start = script.index("    full_generation_service = FullGenerationService(")
    end = script.index("\n\n    controller = PlansVenteController(", start)
    construction = script[start:end]

    assert "full_generation_service=full_generation_service" not in construction

    controller_start = script.index("    controller = PlansVenteController(")
    controller_end = script.index("\n\n    window = PlansVenteWindow", controller_start)
    controller_block = script[controller_start:controller_end]

    assert "full_generation_service=full_generation_service" in controller_block



def test_stage07d_repere_is_detected_by_filled_region_class():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _filled_region_count(" in text
    assert ".OfClass(FilledRegion)" in text
    classifier = text[
        text.index("    def _classify_viewports("):
        text.index("    def _resolve_source_view(")
    ]
    assert "filled_regions=self._filled_region_count(view)" in classifier
    assert '"OST_FilledRegion"' not in classifier


def test_stage07d_uses_distinct_source_for_location_plan_and_model_scale():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _resolve_location_source_view(" in text
    assert "self.location_plan_service.source_views_for_housing(housing)" in text
    assert "source_view_unique_id=location_source_candidate.unique_id" in text
    assert "target_scale=int(" in text
    assert 'getattr(location_info.view, "Scale", 0)' in text
    assert "def _view_crop_area(" in text


def test_stage07d_reads_annotation_types_from_dependent_primary_view_too():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _annotation_view_ids(" in text
    assert "view.GetPrimaryViewId()" in text
    dominant = text[
        text.index("    def _dominant_element_type("):
        text.index("    def _filled_region_type(")
    ]
    assert "for view_id in self._annotation_view_ids(view):" in dominant



def test_stage07d_location_plan_copies_crop_from_model_view():
    service = SERVICE.read_text(encoding="utf-8")
    location = (
        PANEL / "services" / "location_plan_service.py"
    ).read_text(encoding="utf-8")

    assert "crop_reference_view_unique_id=str(" in service
    assert 'getattr(location_info.view, "UniqueId", "")' in service

    assert "crop_reference_view_unique_id=None" in location
    assert "def _copy_crop_from_reference(" in location
    assert "reference_manager.GetCropShape()" in location
    assert "curve.CreateTransformed(translation)" in location
    assert "target_manager.SetCropShape(transformed[0])" in location
    assert "def _copy_rectangular_crop_box(" in location
    assert "def _copy_annotation_crop(" in location
