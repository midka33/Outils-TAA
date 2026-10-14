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


def test_stage09_python_windows_parse_and_batch_reuses_validated_07d_engine():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    advanced = ADVANCED_WINDOW.read_text(encoding="utf-8")

    ast.parse(main)
    ast.parse(advanced)

    assert 'UI_BUILD = "stage09a-final-ui-v1"' in main
    assert "def CreateBatch_Click(" in main
    assert "def _run_batch(" in main
    assert "self.controller.generate_full_plan(" in main
    assert "self.controller.plan_exists(" in main
    assert "self.controller.filter_housings(" in main
    assert "PlansVenteAdvancedWindow(" in main

    full = FULL.read_text(encoding="utf-8")
    assert 'FULL_GENERATION_BUILD = "stage07d-template-driven-full-generation-v4"' in full


def test_stage09_batch_never_generates_multilevel_housing_in_09a():
    text = MAIN_WINDOW.read_text(encoding="utf-8")
    block = text[
        text.index("    def CreateBatch_Click("):
        text.index("    def _run_batch(", text.index("    def CreateBatch_Click("))
    ]

    assert "single_level" in block
    assert "multilevel" in block
    assert "processable = single_level" in block
    assert "09B" in block


def test_stage09_advanced_options_expose_only_safe_overrides():
    xaml = ADVANCED_XAML.read_text(encoding="utf-8")
    window = ADVANCED_WINDOW.read_text(encoding="utf-8")

    for name in (
        "SkipExistingCheckBox",
        "HousingParameterCombo",
        "CropMarginTextBox",
        "AutoScaleCheckBox",
        "AllowedScalesTextBox",
        "DetailedReportCheckBox",
        "LogWarningsCheckBox",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert "Automatique — feuille modèle" in xaml
    assert "IsReadOnly="True"" in xaml
    assert "parse_allowed_scales(" in window
    assert '"crop_margin_mm"' in window
    assert '"skip_existing"' in window


def test_stage09_controller_services_support_filter_existing_check_and_options():
    controller = CONTROLLER.read_text(encoding="utf-8")
    analysis = ANALYSIS.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert "def filter_housings(" in controller
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
