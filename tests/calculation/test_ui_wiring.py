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
    assert "#FA641F" in text
    assert "TAAPrimaryButton" in text
    assert "TAASecondaryButton" in text


def test_python_ui_files_are_syntax_valid():
    for filename in (
        "calculs_window.py",
        "calculation_report_window.py",
    ):
        ast.parse(_read(os.path.join(UI_DIR, filename)))

    ast.parse(_read(os.path.join(
        PANEL,
        "services",
        "room_calculation_workflow.py",
    )))


def test_unit_selector_is_contextual_and_warnings_are_shown_before_write():
    window_path = os.path.join(UI_DIR, "calculs_window.py")
    text = _read(window_path)

    assert "TargetParameterChanged" in text
    assert 'target.storage_type in ("Integer", "String")' in text
    assert "if prepared.warnings:" in text
    assert "Avertissements :" in text
