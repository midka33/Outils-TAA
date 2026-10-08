# -*- coding: utf-8 -*-
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"
PARAMETERS = PANEL / "services" / "room_parameter_service.py"
SHEETS = PANEL / "services" / "sheet_assembly_service.py"


def test_window_does_not_eagerly_load_static_revit_lists():
    text = WINDOW.read_text(encoding="utf-8")
    init = text[text.index("class PlansVenteWindow"):text.index("    def _load_theme")]

    assert "self._load_location_static_choices()" not in init
    assert "self._load_room_tag_types()" not in init
    assert "self._load_dimension_types()" not in init
    assert "self._load_sheet_templates()" not in init
    assert "self._deferred_static_choices_loaded = False" in init
    assert "self._sheet_templates_loaded = False" in init


def test_sheet_templates_are_loaded_only_when_combo_is_opened():
    window = WINDOW.read_text(encoding="utf-8")
    xaml = XAML.read_text(encoding="utf-8")

    assert "def SheetTemplateDropDownOpened(" in window
    assert "if not self._sheet_templates_loaded:" in window
    assert "self._load_sheet_templates()" in window
    assert 'DropDownOpened="SheetTemplateDropDownOpened"' in xaml


def test_parameter_schema_discovery_is_sampled_at_startup():
    text = PARAMETERS.read_text(encoding="utf-8")

    assert "DISCOVERY_SAMPLE_LIMIT = 8" in text
    assert "[:self.DISCOVERY_SAMPLE_LIMIT]" in text


def test_sheet_template_discovery_uses_global_indexes_not_per_sheet_layout():
    text = SHEETS.read_text(encoding="utf-8")
    start = text.index("    def list_sheet_templates(")
    end = text.index("    def create_sheet_from_template(", start)
    block = text[start:end]

    assert "roles_by_sheet" in block
    assert "title_blocks_by_sheet" in block
    assert ".OfClass(Viewport)" in block
    assert ".OfClass(ScheduleSheetInstance)" in block
    assert "self._template_layout(sheet)" not in block
