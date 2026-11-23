# -*- coding: utf-8 -*-
"""Contrats statiques uniquement : pas une validation d'exécution WPF/Revit."""

import ast
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Parametres.panel"
STACK = PANEL / "Commandes.stack"


def test_both_buttons_open_same_window_with_distinct_mode():
    for folder, mode in (("Numeroter.pushbutton", "number"),
                         ("ModifierTexte.pushbutton", "text")):
        script = (STACK / folder / "script.py").read_text(encoding="utf-8")
        ast.parse(script)
        assert "from room_parameters_window import launch" in script
        assert 'launch("{}")'.format(mode) in script
        assert 'os.path.join(os.path.dirname(__file__), "..", "..")' in script


def test_compact_revit_ribbon_stack_structure():
    assert (PANEL / "bundle.yaml").read_text(encoding="utf-8").strip().endswith("- Commandes")
    stack = (STACK / "bundle.yaml").read_text(encoding="utf-8")
    assert "- Numeroter" in stack and "- ModifierTexte" in stack
    assert len(list(STACK.glob("*.pushbutton"))) == 2


def test_single_window_has_preview_and_confirmation_controls():
    tree = ET.parse(PANEL / "ui" / "room_parameters.xaml")
    names = set()
    for element in tree.iter():
        names.update(value for key, value in element.attrib.items()
                     if key == "Name" or key.endswith("}Name"))
    required = {"ModeCombo", "ParameterCombo", "OperationCombo", "InputText",
                "ExtraText", "PreviewGrid", "ApplyButton", "ConfirmCheck",
                "SelectButton", "MessageText"}
    assert required.issubset(names)
    assert len(list(PANEL.glob("ui/*.xaml"))) == 1


def test_revit_writer_blocks_stale_preview_and_rolls_back():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "room_parameter_edit_service.py").read_text(encoding="utf-8")
    ast.parse(source)
    ast.parse(service)
    assert "self.preview_signature != self._signature()" in source
    assert "self.ConfirmCheck.IsChecked" in source
    assert "transaction.RollBack()" in service
    assert "parameter.AsString() or \"\"" in service
    assert "room.GroupId != DB.ElementId.InvalidElementId" in service


def test_taa_theme_and_business_separation():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    xaml = (PANEL / "ui" / "room_parameters.xaml").read_text(encoding="utf-8")
    assert "load_resource_dictionary(self, theme)" in source
    assert "TAAPrimaryButton" in xaml
    assert "TAAOrangeBrush" in xaml
    assert "#D97128" not in xaml
    assert "DB.Transaction(" not in source
    assert "commit_changes(selected)" in source
    assert "check_collisions(" in source
    assert "self.settings.set(" in source


def test_system_data_assembly_loaded_before_import():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    assert 'clr.AddReference("System.Data")' in source
    assert source.index('clr.AddReference("System.Data")') < source.index("from System.Data import DataTable")
