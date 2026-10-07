# -*- coding: utf-8 -*-
"""Contrats statiques de l'interface Calculs des pièces."""

import ast
import os
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PANEL = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Calculs.panel",
)
UI_DIR = os.path.join(PANEL, "ui")
EXTENSION = os.path.join(ROOT, "OutilsTAA.extension")


def _read(path):
    with open(path, "r") as handle:
        return handle.read()


def _method_names(path):
    tree = ast.parse(_read(path))
    return set(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )


def test_main_xaml_is_well_formed_and_has_no_scope_choice_controls():
    path = os.path.join(UI_DIR, "calculs_ui.xaml")
    root = ET.parse(path).getroot()
    text = _read(path)

    assert root is not None
    assert "Vue active" not in text
    assert "Pièces sélectionnées" not in text
    assert "RadioButton" not in text
    assert "Toutes les pièces du projet" in text
    assert 'HorizontalScrollBarVisibility="Disabled"' in text


def test_xaml_event_handlers_exist_on_window_class():
    xaml_path = os.path.join(UI_DIR, "calculs_ui.xaml")
    python_path = os.path.join(UI_DIR, "calculs_window.py")
    methods = _method_names(python_path)

    handlers = set()
    for element in ET.parse(xaml_path).iter():
        for attribute in ("Click", "SelectionChanged"):
            value = element.attrib.get(attribute)
            if value:
                handlers.add(value)

    assert handlers
    assert handlers.issubset(methods)


def test_group_value_selection_xaml_handlers_exist():
    xaml_path = os.path.join(UI_DIR, "group_value_selection.xaml")
    python_path = os.path.join(
        UI_DIR,
        "group_value_selection_window.py",
    )
    methods = _method_names(python_path)

    root = ET.parse(xaml_path).getroot()
    handlers = set()
    for element in root.iter():
        value = element.attrib.get("Click")
        if value:
            handlers.add(value)

    assert root is not None
    assert handlers == {"Apply_Click", "Cancel_Click"}
    assert handlers.issubset(methods)


def test_report_xaml_event_handler_exists():
    xaml_path = os.path.join(UI_DIR, "calculation_report.xaml")
    python_path = os.path.join(UI_DIR, "calculation_report_window.py")
    methods = _method_names(python_path)

    handlers = set()
    for element in ET.parse(xaml_path).iter():
        value = element.attrib.get("Click")
        if value:
            handlers.add(value)

    assert handlers == {"Close_Click"}
    assert handlers.issubset(methods)


def test_script_does_not_use_active_view_scope():
    script = _read(
        os.path.join(PANEL, "CalculsPieces.pushbutton", "script.py")
    )
    collector = _read(
        os.path.join(PANEL, "services", "room_collector_service.py")
    )

    assert "ActiveView" not in script
    assert "ActiveView" not in collector


def test_shared_theme_exists_and_uses_taa_orange():
    theme_path = os.path.join(
        EXTENSION,
        "resources",
        "ui",
        "taa_theme.xaml",
    )
    text = _read(theme_path)

    ET.parse(theme_path)
    assert "#FD8B5A" in text
    assert "#FA641F" in text
    assert "TAAPrimaryButton" in text
    assert "TAASecondaryButton" in text


def test_python_ui_files_are_syntax_valid():
    for filename in (
        "calculs_window.py",
        "calculation_report_window.py",
        "group_value_selection_window.py",
    ):
        ast.parse(_read(os.path.join(UI_DIR, filename)))

    ast.parse(_read(os.path.join(
        PANEL,
        "services",
        "room_calculation_workflow.py",
    )))


def test_group_conflict_choice_is_wired_before_write():
    window_path = os.path.join(UI_DIR, "calculs_window.py")
    text = _read(window_path)

    assert "analyze_group_alignment" in text
    assert "GroupAlignmentResolution.keep_variable" in text
    assert "GroupAlignmentResolution.align_selected" in text
    assert "GroupValueSelectionWindow" in text
    assert "Conserver les résultats exacts" in text
    assert "Conserver l'alignement" in text


def test_unit_selector_is_contextual_and_warnings_are_shown_before_write():
    window_path = os.path.join(UI_DIR, "calculs_window.py")
    text = _read(window_path)

    assert "TargetParameterChanged" in text
    assert 'target.storage_type in ("Integer", "String")' in text
    assert "if prepared.warnings:" in text
    assert "Avertissements :" in text


def test_main_window_is_compact_at_standard_resolution():
    path = os.path.join(UI_DIR, "calculs_ui.xaml")
    root = ET.parse(path).getroot()
    text = _read(path)

    assert int(root.attrib["Height"]) <= 600
    assert int(root.attrib["MinHeight"]) <= 500
    assert int(root.attrib["Width"]) <= 900
    assert 'VerticalScrollBarVisibility="Auto"' in text
    assert "Les résultats sont validés avant l'ouverture" not in text
    assert "ToolTip=" in text


def test_compact_layout_keeps_common_controls_on_shared_rows():
    root = ET.parse(os.path.join(UI_DIR, "calculs_ui.xaml")).getroot()

    by_name = {}
    for element in root.iter():
        for key, value in element.attrib.items():
            if key.endswith("}Name"):
                by_name[value] = element

    assert by_name["FilterParameterCombo"].attrib.get("{http://schemas.microsoft.com/winfx/2006/xaml/presentation}Grid.Column") is None
    assert by_name["GroupParameterCombo"] is not None
    assert by_name["SourceParameterCombo"] is not None
    assert by_name["TargetParameterCombo"] is not None


def test_ribbon_icons_exist_and_are_32px_png():
    import struct

    button_dir = os.path.join(PANEL, "CalculsPieces.pushbutton")
    for filename in ("icon.png", "icon.dark.png"):
        path = os.path.join(button_dir, filename)
        assert os.path.exists(path)
        with open(path, "rb") as handle:
            data = handle.read(24)

        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        width, height = struct.unpack(">II", data[16:24])
        assert (width, height) == (32, 32)
