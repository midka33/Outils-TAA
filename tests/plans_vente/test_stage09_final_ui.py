# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

from plans_vente.housing_filter import (
    FILTER_OPERATORS,
    matches_any,
    matches_value,
)


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
MAIN_XAML = PANEL / "ui" / "plans_vente_final.xaml"
MAIN_WINDOW = PANEL / "ui" / "plans_vente_final_window.py"
ADVANCED_XAML = PANEL / "ui" / "plans_vente_advanced.xaml"
ADVANCED_WINDOW = PANEL / "ui" / "plans_vente_advanced_window.py"
SCRIPT = PANEL / "PlansDeVente.pushbutton" / "script.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
ANALYSIS = PANEL / "services" / "housing_analysis_service.py"
SHEET = PANEL / "services" / "sheet_assembly_service.py"
FULL = PANEL / "services" / "full_generation_service.py"
REFERENCES = ROOT / "docs" / "references" / "plans-vente"


def test_stage09_filter_contract_supports_requested_operators():
    labels = dict(FILTER_OPERATORS)

    assert labels["starts_with"] == "commence par"
    assert labels["equals"] == "est égal à"
    assert labels["contains"] == "contient"
    assert labels["ends_with"] == "se termine par"
    assert labels["not_equals"] == "est différent de"

    assert matches_value("A502", "starts_with", "A5")
    assert matches_value("A502", "equals", "a502")
    assert matches_value("A502", "contains", "50")
    assert matches_value("A502", "ends_with", "02")
    assert matches_value("A502", "not_equals", "A501")
    assert matches_value("", "is_empty", "")
    assert matches_value("A502", "is_not_empty", "")


def test_stage09_filter_matches_housing_when_any_room_value_matches():
    assert matches_any(["T4", "T4", "T4"], "equals", "T4")
    assert matches_any(["A502", "A502"], "starts_with", "A5")
    assert not matches_any(["A401", "A402"], "starts_with", "A5")
    assert matches_any(["A401", "A402"], "not_equals", "A500")


def test_stage09_main_and_advanced_xaml_are_valid_and_use_taa_brand_orange():
    ET.parse(str(MAIN_XAML))
    ET.parse(str(ADVANCED_XAML))

    main = MAIN_XAML.read_text(encoding="utf-8")
    advanced = ADVANCED_XAML.read_text(encoding="utf-8")

    for text in (main, advanced):
        assert 'FontFamily="Segoe UI"' in text
        assert 'FontSize="13"' in text
        assert "TAABrandOrangeBrush" in text

    assert "Portée de génération" in main
    assert "Choix de la feuille modèle" in main
    assert "Logements sur 2 niveaux" in main
    assert "Création des plans de vente" in main


def test_stage09_main_ui_exposes_generic_filter_batch_and_multilevel_choices():
    xaml = MAIN_XAML.read_text(encoding="utf-8")

    for name in (
        "AllHousingRadio",
        "FilteredHousingRadio",
        "FilterParameterCombo",
        "FilterOperatorCombo",
        "FilterValueTextBox",
        "HousingGrid",
        "SheetTemplateCombo",
        "MultiLevelOneSheetRadio",
        "MultiLevelOneSheetPerLevelRadio",
        "MultiLevelIgnoreRadio",
        "CreateBatchButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'Click="CreateBatch_Click"' in xaml
    assert 'Click="AdvancedOptions_Click"' in xaml
    assert 'DisplayMemberPath="label"' in xaml
    assert 'DisplayMemberPath="Label"' in xaml
    assert 'Content="1 feuille par logement, 1 vue par niveau"' in xaml
    assert 'x:Name="MultiLevelOneSheetRadio"' in xaml
    assert 'x:Name="MultiLevelOneSheetPerLevelRadio"' in xaml
    assert 'IsChecked="True"' in xaml


def test_stage09_python_windows_parse_and_batch_reuses_validated_07d_engine():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    advanced = ADVANCED_WINDOW.read_text(encoding="utf-8")

    ast.parse(main)
    ast.parse(advanced)

    assert 'UI_BUILD = "stage09b2-template-multilevel-v1"' in main
    assert "def CreateBatch_Click(" in main
    assert "def _run_batch(" in main
    assert "self.controller.generate_full_plan(" in main
    assert "self.controller.plan_exists(" in main
    assert "self.controller.filter_housings(" in main
    assert "PlansVenteAdvancedWindow(" in main

    full = FULL.read_text(encoding="utf-8")
    assert 'FULL_GENERATION_BUILD = "stage07d-template-driven-full-generation-v4"' in full


def test_stage09b_supports_both_sheet_per_level_and_one_sheet_modes():
    text = MAIN_WINDOW.read_text(encoding="utf-8")
    block = text[
        text.index("    def CreateBatch_Click("):
        text.index("    def _run_batch(", text.index("    def CreateBatch_Click("))
    ]
    run_block = text[
        text.index("    def _run_batch("):
        text.index("    def _show_batch_report(", text.index("    def _run_batch("))
    ]

    assert 'self._multilevel_mode == "sheet_per_level"' in block
    assert "self.controller.split_housing_by_level(housing)" in block
    assert "processable = list(single_level) + list(multilevel)" in block
    assert 'self._multilevel_mode == "one_sheet"' in run_block
    assert "self.controller.generate_multilevel_one_sheet(" in run_block


def test_stage09_advanced_options_expose_only_safe_overrides():
    xaml = ADVANCED_XAML.read_text(encoding="utf-8")
    window = ADVANCED_WINDOW.read_text(encoding="utf-8")

    for name in (
        "SkipExistingCheckBox",
        "HousingParameterCombo",
        "BuildingParameterCombo",
        "TypologyParameterCombo",
        "CropMarginTextBox",
        "AutoScaleCheckBox",
        "AllowedScalesTextBox",
        "DetailedReportCheckBox",
        "LogWarningsCheckBox",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert "Automatique — feuille modèle" in xaml
    assert 'IsReadOnly="True"' in xaml
    assert "parse_allowed_scales(" in window
    assert '"crop_margin_mm"' in window
    assert '"skip_existing"' in window


def test_stage09_controller_services_support_filter_existing_check_and_options():
    controller = CONTROLLER.read_text(encoding="utf-8")
    analysis = ANALYSIS.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert "def filter_housings(" in controller
    assert "def split_housing_by_level(" in controller
    assert "def filter_housings(" in analysis
    assert "def plan_exists(" in controller
    assert "def plan_exists(" in sheet

    assert "crop_margin_mm=None" in controller
    assert "auto_fit_main_view=True" in controller
    assert "crop_margin_mm=None" in full
    assert "auto_fit_main_view=True" in full


def test_stage09_entrypoint_uses_final_ui_and_keeps_legacy_alias():
    script = SCRIPT.read_text(encoding="utf-8")

    assert "from plans_vente_final_window import PlansVenteFinalWindow" in script
    assert "PlansVenteWindow = PlansVenteFinalWindow" in script
    assert "window = PlansVenteWindow(controller)" in script
    assert "plan_update_service" not in script


def test_stage09_reference_mockups_are_committed():
    readme = REFERENCES / "README.md"
    main_image = REFERENCES / "09_interface_principale.webp"
    advanced_image = REFERENCES / "09_options_avancees.webp"

    assert readme.exists()
    assert main_image.exists()
    assert advanced_image.exists()

    text = readme.read_text(encoding="utf-8")
    assert "TAABrandOrangeBrush" in text
    assert "09_interface_principale.webp" in text
    assert "09_options_avancees.webp" in text
    assert "Étape 09B" in text


def test_stage09b_generated_view_reuses_template_main_view_graphics():
    full = FULL.read_text(encoding="utf-8")
    prototype = (PANEL / "services" / "prototype_view_service.py").read_text(
        encoding="utf-8"
    )

    assert "main_template = self._view_template(main_info.view)" in full
    assert "view_template_unique_id=(" in full
    assert "view_template_unique_id=None" in prototype
    assert "master_view.ViewTemplateId = view_template.Id" in prototype
    assert "view_template_unique_id=view_template_unique_id" in prototype


def test_stage09b_sheet_cartouche_uses_business_housing_value():
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert 'housing_display_value=(' in full
    assert 'getattr(housing, "filter_key", None)' in full
    assert 'housing_parameter_name=str(' in full
    assert "def _write_housing_display_value(" in sheet
    assert "target.LookupParameter(name)" in sheet
    assert "parameter.Set(value)" in sheet
    assert "Numéro de feuille" in sheet


def test_stage09b_cartouche_receives_room_metadata():
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert "room_metadata, metadata_warnings = self._room_metadata(" in full
    assert "building_parameter_name=building_parameter_name" in full
    assert "typology_parameter_name=typology_parameter_name" in full
    assert "room_metadata=room_metadata" in full

    assert "def _write_room_metadata(" in sheet
    assert '("building", ("Bâtiment", "Batiment"), "Bâtiment")' in sheet
    assert '("floor", ("Niveau", "Étage", "Etage"), "Étage/Niveau")' in sheet
    assert '("typology", ("Zone",), "Typologie (paramètre cartouche Zone)")' in sheet


def test_stage09b_cartouche_parameter_sources_are_user_configurable():
    advanced_xaml = ADVANCED_XAML.read_text(encoding="utf-8")
    advanced = ADVANCED_WINDOW.read_text(encoding="utf-8")
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert 'x:Name="BuildingParameterCombo"' in advanced_xaml
    assert 'x:Name="TypologyParameterCombo"' in advanced_xaml
    assert '"building_parameter_name"' in advanced
    assert '"typology_parameter_name"' in advanced
    assert '"building_parameter_name"' in main
    assert '"typology_parameter_name"' in main
    assert "building_parameter_name=" in controller
    assert "typology_parameter_name=" in controller
    assert "building_parameter_name=" in full
    assert "typology_parameter_name=" in full
    assert "def _floor_number(" in full
    assert 'return "0"' in full


def test_stage09b_floor_comes_from_generated_main_view():
    full = FULL.read_text(encoding="utf-8")

    assert "main_view_unique_id=main_result.view_unique_id" in full
    assert "def _main_view_level_name(" in full
    assert 'getattr(view, "GenLevel", None)' in full
    assert "def _floor_numbers(" in full


def test_stage09b_multiple_levels_are_all_written_to_floor_field():
    full = FULL.read_text(encoding="utf-8")

    assert "def _floor_numbers(" in full
    assert 'result["floor"] = " / ".join(floors)' in full


def test_stage09_template_preview_uses_real_revit_sheet_image():
    xaml = MAIN_XAML.read_text(encoding="utf-8")
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert 'x:Name="TemplatePreviewImage"' in xaml
    assert 'x:Name="TemplatePreviewOverlay"' in xaml
    assert "Résultat attendu" not in xaml
    assert "def _export_and_show_sheet_preview(" in main
    assert "self.controller.export_sheet_preview(" in main
    assert "def _load_bitmap(" in main
    assert "def _render_preview_overlays(" in main
    assert "def export_sheet_preview(" in controller
    assert "ImageExportOptions()" in controller
    assert "ExportRange.SetOfViews" in controller
    assert "document.ExportImage(options)" in controller
    assert "def _sheet_preview_bounds(" in full
    assert "def _sheet_preview_items(" in full


def test_stage09b2_multilevel_engine_contract():
    controller = CONTROLLER.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    schedules = (PANEL / "services" / "schedule_service.py").read_text(
        encoding="utf-8"
    )

    assert "def generate_multilevel_one_sheet(" in controller
    assert "def generate_multilevel_one_sheet(" in full
    assert "split_housing_by_level(housing)" in full
    assert "all_levels=True" in full
    assert "def create_multilevel_sheet_from_blueprint(" in sheet
    assert "main_view_unique_ids" in sheet
    assert "placed_main_viewports" in sheet
    assert "all_levels=False" in schedules


def test_stage09b2_uses_explicit_multilevel_template_positions():
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _classify_multilevel_viewports(" in full
    assert "expected_levels=len(level_housings)" in full
    assert "template_main_viewport_unique_ids=[" in full
    assert "Les vues logement du modèle multi-niveaux doivent utiliser" in full

    assert "def create_multilevel_sheet_from_blueprint(" in sheet
    assert "template_main_viewport_unique_ids" in sheet
    assert "main_centers" in sheet
    assert "Les vues logement du modèle multi-niveaux doivent être" in sheet
    assert "positions exactes du" in sheet
    assert "se chevauchent malgré le modèle" in sheet
    assert "_create_common_scale_multilevel_viewports" not in sheet


def test_stage09_duplex_preview_highlights_both_model_views():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert '"main_view_extra"' in full
    assert '"main_view_extra": "Vue logement 2"' in main
