# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
UPDATE = PANEL / "services" / "plan_update_service.py"
SHEET = PANEL / "services" / "sheet_assembly_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
SCRIPT = PANEL / "PlansDeVente.pushbutton" / "script.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"
DOC = ROOT / "docs" / "20_Plans_de_Vente.md"


def test_stage08_service_parses_and_has_atomic_update_contract():
    text = UPDATE.read_text(encoding="utf-8")
    ast.parse(text)

    assert 'PLAN_UPDATE_BUILD = "stage08-regenerate-existing-plan-v2"' in text
    assert "class ExistingPlanInspection(object):" in text
    assert "class PlanUpdateResult(object):" in text
    assert "def inspect(" in text
    assert "def update(" in text
    assert "TransactionGroup(" in text
    assert "group.Assimilate()" in text
    assert "group.RollBack()" in text


def test_stage08_preserves_sheet_and_regenerates_managed_artifacts():
    update = UPDATE.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _find_target_sheet(" in update
    assert '"PDV-{}".format(housing_key)' in update
    assert "def _layout_override(" in update
    assert '"main_point"' in update
    assert '"location_point"' in update
    assert '"schedule_points"' in update
    assert "def _delete_managed_artifacts(" in update

    assert "def update_sheet_from_blueprint(" in sheet
    block = sheet[
        sheet.index("    def update_sheet_from_blueprint("):
        sheet.index("    def list_title_block_types(")
    ]
    assert "ViewSheet.Create(" not in block
    assert "target_sheet.Id" in block
    assert "location_viewport_type_id" in block
    assert "main_viewport_type_id" in block


def test_stage08_blocks_shared_generated_views_or_schedules():
    text = UPDATE.read_text(encoding="utf-8")

    assert "def _external_usage_blocking_reason(" in text
    assert "Une vue PDV du logement est aussi placée" in text
    assert "Une nomenclature PDV du logement est aussi placée" in text


def test_stage08_does_not_delete_master_views_or_unrelated_schedules():
    text = UPDATE.read_text(encoding="utf-8")

    generated = text[
        text.index("    def _generated_views("):
        text.index("    @staticmethod\n    def _is_main_generated_name", text.index("    def _generated_views("))
    ]
    assert "PDV MASTER" not in generated

    matcher = text[
        text.index("    def _is_managed_schedule_name("):
        text.index("    def _find_target_sheet(", text.index("    def _is_managed_schedule_name("))
    ]
    assert 'text.startswith("PDV_")' not in matcher
    assert '"PDV_{}_".format(key)' in matcher


def test_stage08_controller_and_entrypoint_are_wired_without_self_reference():
    controller = CONTROLLER.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "plan_update_service=None" in controller
    assert "def inspect_plan_update(" in controller
    assert "def update_full_plan(" in controller
    assert "def plan_update_build_id(" in controller

    assert "import plan_update_service as _plan_update_service" in script
    assert "PlanUpdateService = _plan_update_service.PlanUpdateService" in script
    assert "plan_update_service = PlanUpdateService(" in script

    start = script.index("    plan_update_service = PlanUpdateService(")
    end = script.index("\n\n    controller = PlansVenteController(", start)
    construction = script[start:end]
    assert "plan_update_service=plan_update_service" not in construction

    controller_block = script[
        script.index("    controller = PlansVenteController("):
        script.index("\n\n    window = PlansVenteWindow")
    ]
    assert "plan_update_service=plan_update_service" in controller_block


def test_stage08_ui_has_update_action_and_explicit_manual_edit_warning():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")
    ast.parse(window)

    assert "Étape 08 — Mise à jour" in xaml
    assert 'x:Name="UpdateFullPlanButton"' in xaml
    assert 'Click="UpdateFullPlan_Click"' in xaml
    assert "Mettre à jour le plan de vente" in xaml

    assert "def UpdateFullPlan_Click(" in window
    assert "inspect_plan_update(" in window
    assert "update_full_plan(" in window
    assert "modifications manuelles réalisées directement" in window
    assert "def _update_plan_update_button_state(" in window


def test_stage08_documentation_is_present():
    text = DOC.read_text(encoding="utf-8")

    assert "## Étape 08 — Mise à jour d’un plan de vente existant" in text
    assert "stage08-regenerate-existing-plan-v2" in text
    assert "conserve la feuille" in text.lower()



def test_stage08_excludes_old_generated_views_from_new_source_selection():
    update = UPDATE.read_text(encoding="utf-8")
    full = (
        PANEL / "services" / "full_generation_service.py"
    ).read_text(encoding="utf-8")

    assert "old_generated_view_ids = [" in update
    assert "excluded_unique_ids=old_generated_view_ids" in update
    assert "excluded_unique_ids=None" in full
    assert "if excluded:" in full



def test_stage08_purges_shared_dependent_annotations_before_regeneration():
    text = UPDATE.read_text(encoding="utf-8")

    assert "def _managed_annotation_ids(" in text
    assert "BuiltInCategory.OST_RoomTags" in text
    assert "BuiltInCategory.OST_Dimensions" in text
    assert "TaggedLocalRoomId" in text
    assert "self._delete_managed_artifacts(" in text
    assert "for annotation_id in annotation_ids:" in text
    assert "self.document.Delete(annotation_id)" in text
