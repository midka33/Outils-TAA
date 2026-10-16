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
    assert "Logements sur 2 niveaux" not in main
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
        "MultiLevelInfoText",
        "CreateBatchButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'Click="CreateBatch_Click"' in xaml
    assert 'Click="AdvancedOptions_Click"' in xaml
    assert 'DisplayMemberPath="label"' in xaml
    assert 'DisplayMemberPath="Label"' in xaml
    assert "Comportement automatique selon la feuille modèle" in xaml


def test_stage09_python_windows_parse_and_batch_reuses_validated_07d_engine():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    advanced = ADVANCED_WINDOW.read_text(encoding="utf-8")

    ast.parse(main)
    ast.parse(advanced)

    assert 'UI_BUILD = "stage09-rc16-progress"' in main
    assert "def CreateBatch_Click(" in main
    assert "def _run_batch(" in main
    assert "self.controller.generate_full_plan(" in main
    assert "self.controller.plan_exists(" in main
    assert "self.controller.filter_housings(" in main
    assert "PlansVenteAdvancedWindow(" in main

    full = FULL.read_text(encoding="utf-8")
    assert 'FULL_GENERATION_BUILD = "stage07d-template-driven-full-generation-v4"' in full


def test_stage09b_template_automatically_selects_multilevel_behavior():
    text = MAIN_WINDOW.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")

    assert "self.controller.detect_multilevel_template_mode(" in text
    assert 'self._multilevel_mode = str(' in text
    assert 'self._multilevel_mode == "sheet_per_level"' in text
    assert "self.controller.split_housing_by_level(housing)" in text
    assert "self.controller.generate_multilevel_one_sheet(" in text

    assert "def detect_multilevel_template_mode(" in controller
    assert "def detect_multilevel_template_mode(" in full
    assert '"mode": "sheet_per_level"' in full
    assert '"mode": "one_sheet"' in full
    assert '"main_view_count": 1' in full
    assert '"main_view_count": 2' in full


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


def test_stage09b_has_no_manual_multilevel_radio_choice():
    xaml = MAIN_XAML.read_text(encoding="utf-8")
    main = MAIN_WINDOW.read_text(encoding="utf-8")

    assert "MultiLevelOneSheetRadio" not in xaml
    assert "MultiLevelOneSheetPerLevelRadio" not in xaml
    assert "MultiLevelIgnoreRadio" not in xaml
    assert "def MultiLevelModeChanged(" not in main


def test_stage09_accepts_single_view_template_without_detected_location_view():
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert 'if len(infos) == 1:' in full
    assert 'return infos[0], None, warnings' in full
    assert '"mode": "sheet_per_level"' in full
    assert 'Repérage non créé' in full
    assert 'location_viewport_model = None' in sheet
    assert 'if template_location_viewport_unique_id:' in sheet


def test_stage09_all_runtime_python_files_parse():
    runtime_files = (
        MAIN_WINDOW,
        ADVANCED_WINDOW,
        CONTROLLER,
        ANALYSIS,
        SHEET,
        FULL,
        PANEL / "services" / "schedule_service.py",
        PANEL / "services" / "prototype_view_service.py",
        PANEL / "services" / "location_plan_service.py",
        PANEL / "services" / "room_tag_service.py",
        PANEL / "services" / "dimension_service.py",
        PANEL / "PlansDeVente.pushbutton" / "script.py",
    )

    for path in runtime_files:
        ast.parse(path.read_text(encoding="utf-8"))


def test_stage09_template_contract_is_unambiguous():
    full = FULL.read_text(encoding="utf-8")
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    xaml = MAIN_XAML.read_text(encoding="utf-8")

    assert '"mode": "sheet_per_level"' in full
    assert '"main_view_count": 1' in full
    assert '"mode": "one_sheet"' in full
    assert '"main_view_count": 2' in full
    assert "Le modèle contient {} vues logement" in full

    assert "detect_multilevel_template_mode(" in main
    assert "MultiLevelOneSheetRadio" not in xaml
    assert "MultiLevelOneSheetPerLevelRadio" not in xaml
    assert "MultiLevelIgnoreRadio" not in xaml


def test_stage09_optional_location_plan_never_blocks_template_selection():
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert "return infos[0], None, warnings" in full
    assert "Repérage non créé" in full
    assert "location_viewport_model = None" in sheet
    assert "if template_location_viewport_unique_id:" in sheet


def test_stage09_rc2_duplex_slots_share_one_scale():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _place_multilevel_views_in_template_slots(" in sheet
    assert "scale_candidates_from_reference(" in sheet
    assert "slot_sizes" in sheet
    assert "fits_slots" in sheet
    assert "no_overlap" in sheet
    assert "les vues ont été réduites ensemble" in sheet


def test_stage09_rc2_location_highlight_failure_is_non_blocking():
    location = (PANEL / "services" / "location_plan_service.py").read_text(
        encoding="utf-8"
    )
    full = FULL.read_text(encoding="utf-8")

    assert "highlight_available" in location
    assert "Repérage créé sans surbrillance" in location
    assert "warnings=warnings" in location
    assert 'getattr(location_result, "warnings", [])' in full


def test_stage09_rc2_batch_reports_duration():
    main = MAIN_WINDOW.read_text(encoding="utf-8")

    assert "batch_started_at = time.time()" in main
    assert "elapsed_seconds" in main
    assert "Durée totale" in main
    assert "Temps moyen / plan créé" in main


def test_stage09_rc3_annotation_crop_is_enabled():
    crop = (PANEL / "services" / "crop_geometry_service.py").read_text(
        encoding="utf-8"
    )

    assert "VIEWER_ANNOTATION_CROP_ACTIVE" in crop
    assert "VIEWER_ANNOTATION_CROP_OFFSET" in crop
    assert "minimum_offset = 1.0 / 96.0" in crop
    assert "des annotations extérieures peuvent élargir le viewport" in crop


def test_stage09_rc3_obsolete_multiview_warning_is_removed():
    full = FULL.read_text(encoding="utf-8")

    assert "les autres viewports seront traités dans l'extension multi-vues" not in full


def test_stage09_rc4_crop_boundary_is_hidden():
    crop = (PANEL / "services" / "crop_geometry_service.py").read_text(
        encoding="utf-8"
    )

    assert "view.CropBoxVisible = False" in crop
    assert "LeftAnnotationCropOffset = minimum_offset" in crop
    assert "RightAnnotationCropOffset = minimum_offset" in crop
    assert "TopAnnotationCropOffset = minimum_offset" in crop
    assert "BottomAnnotationCropOffset = minimum_offset" in crop


def test_stage09_rc5_duplex_scale_ignores_annotation_extents():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _view_crop_paper_size(" in sheet
    assert "self._view_crop_paper_size(" in sheet
    assert "geometry_rectangles" in sheet
    assert "GetBoxOutline()" not in sheet[
        sheet.index("    def _place_multilevel_views_in_template_slots("):
        sheet.index("    def list_title_block_types(")
    ]


def test_stage09_rc6_duplex_alignment_uses_geometric_view_center():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _view_outline_center_on_sheet(" in sheet
    assert "GetProjectionToSheetTransform()" in sheet
    assert "viewport.SetBoxCenter(" in sheet
    assert "actual_center = self._view_outline_center_on_sheet(" in sheet
    assert "target_x, target_y = slot_centers[index]" in sheet


def test_stage09_rc7_duplex_alignment_uses_real_crop_shape():
    sheet = SHEET.read_text(encoding="utf-8")

    assert "def _view_crop_rectangle_on_sheet(" in sheet
    assert "GetCropRegionShapeManager()" in sheet
    assert "GetCropShape()" in sheet
    assert "curve.Tessellate()" in sheet
    assert "transform.OfPoint(point)" in sheet
    assert "_view_outline_center_on_sheet" not in sheet


def test_stage09_rc15_explicit_zones_apply_to_single_and_multilevel():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    full = FULL.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    assert 'UI_BUILD = "stage09-rc15-explicit-main-zones"' in main

    # L'interface transmet le même style aux deux chemins de génération.
    multilevel_start = main.index("self.controller.generate_multilevel_one_sheet(")
    multilevel_block = main[multilevel_start:multilevel_start + 3500]
    assert "main_view_zone_line_style" in multilevel_block

    standard_start = main.index("self.controller.generate_full_plan(")
    standard_block = main[standard_start:standard_start + 3500]
    assert "main_view_zone_line_style" in standard_block

    # Contrôleur + service complet relaient le contrat.
    assert "def generate_full_plan(" in controller
    assert "def generate_multilevel_one_sheet(" in controller
    assert "main_view_zone_line_style=" in controller
    assert "def generate(" in full
    assert "def generate_multilevel_one_sheet(" in full
    assert "main_view_zone_line_style=" in full

    # Mono-vue et multi-vues utilisent le même moteur explicite.
    create_single = sheet[
        sheet.index("    def create_sheet_from_blueprint("):
        sheet.index("    def create_multilevel_sheet_from_blueprint(")
    ]
    assert "_place_multilevel_views_in_template_slots(" in create_single
    assert "main_view_zone_line_style=main_view_zone_line_style" in create_single

    placement = sheet[
        sheet.index("    def _place_multilevel_views_in_template_slots("):
        sheet.index("    def list_title_block_types(")
    ]
    assert "_sheet_curve_segments_by_line_style(" in placement
    assert "_zone_around_point_from_segments(" in placement
    assert "target_zones.append(zone)" in placement
    assert "Le placement explicite nécessite au moins une vue principale." in placement


def test_stage09_rc15_validates_zone_rectangles_before_batch_generation():
    main = MAIN_WINDOW.read_text(encoding="utf-8")

    create = main[
        main.index("    def CreateBatch_Click("):
        main.index("    def _run_batch(")
    ]

    assert "self.controller.diagnose_template_zones(" in create
    assert "invalid_zone_views" in create
    assert "Vue(s) sans rectangle fermé" in create
    assert "Zones principales : {} — {} rectangle(s) validé(s)" in create


def test_stage09_final_ui_has_no_manual_zone_diagnostic_button():
    xaml = MAIN_XAML.read_text(encoding="utf-8")
    main = MAIN_WINDOW.read_text(encoding="utf-8")

    assert 'x:Name="DiagnoseZonesButton"' not in xaml
    assert 'Click="DiagnoseZones_Click"' not in xaml
    assert "Diagnostiquer les zones des vues principales" not in xaml
    assert "def DiagnoseZones_Click(" not in main

    # Le choix du style reste visible car il pilote les zones explicites.
    assert 'x:Name="MainViewZoneLineStyleCombo"' in xaml
    assert "Lignes des zones des vues principales" in xaml


def test_stage09_zone_validation_remains_internal_before_generation():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    sheet = SHEET.read_text(encoding="utf-8")

    create = main[
        main.index("    def CreateBatch_Click("):
        main.index("    def _run_batch(")
    ]

    assert "self.controller.diagnose_template_zones(" in create
    assert "invalid_zone_views" in create
    assert "Vue(s) sans rectangle fermé" in create
    assert "def diagnose_template_zones(" in controller
    assert "def diagnose_titleblock_zones(" in sheet

    diagnostic = sheet[
        sheet.index("    def _sheet_curve_segments_by_line_style("):
        sheet.index("    def _title_block_segments(")
    ]
    assert "FilteredElementCollector(self.document, sheet.Id)" in diagnostic
    assert ".OfClass(CurveElement)" in diagnostic
    assert "curve_element.LineStyle" in diagnostic
    assert "curve_element.GeometryCurve" in diagnostic


def test_stage09_rc16_progress_window_contract():
    main = MAIN_WINDOW.read_text(encoding="utf-8")
    progress_py = (
        ROOT
        / "OutilsTAA.extension"
        / "OutilsTAA.tab"
        / "PlansDeVente.panel"
        / "ui"
        / "plans_vente_progress_window.py"
    ).read_text(encoding="utf-8")
    progress_xaml = (
        ROOT
        / "OutilsTAA.extension"
        / "OutilsTAA.tab"
        / "PlansDeVente.panel"
        / "ui"
        / "plans_vente_progress.xaml"
    ).read_text(encoding="utf-8")

    assert 'UI_BUILD = "stage09-rc16-progress"' in main
    assert "from plans_vente_progress_window import PlansVenteProgressSession" in main
    assert "with PlansVenteProgressSession(self, total) as progress:" in main
    assert "progress.update(" in main
    assert "progress.finish(" in main

    assert "class PlansVenteProgressWindow" in progress_py
    assert "class PlansVenteProgressSession" in progress_py
    assert "owner.IsEnabled = False" in progress_py
    assert "self.owner.IsEnabled = self.was_enabled" in progress_py
    assert "DispatcherPriority.Loaded" in progress_py

    assert 'x:Name="ProgressBar"' in progress_xaml
    assert 'x:Name="PercentText"' in progress_xaml
    assert 'x:Name="HousingText"' in progress_xaml
    assert 'x:Name="UnitsText"' in progress_xaml
    assert 'x:Name="PhaseText"' in progress_xaml
    assert '#FD8B5A' in progress_xaml
    assert '#FA641F' in progress_xaml
