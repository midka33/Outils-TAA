# -*- coding: utf-8 -*-
"""Contrats de branchement WPF des dossiers calculés."""
from pathlib import Path

BASE = (Path(__file__).resolve().parents[1] /
        "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel")


def read(name):
    return (BASE / name).read_text(encoding="utf-8")


def test_automatic_folder_creation_is_accessible_and_has_options():
    xaml = read("ui.xaml")
    dialog = read("carnet_manager.xaml")
    code = read("carnet_manager_window.py")
    bridge = read("services/publication_preview_integration.py")
    assert 'x:Name="CreateDynamicFolderButton"' in xaml
    assert 'Click="OpenCarnetManager_Click"' in xaml
    assert 'x:Name="ModeDynamic"' in dialog
    assert 'x:Name="DynamicParameterCombo"' in dialog
    assert 'x:Name="DynamicGroupCombo"' in dialog
    assert "def DynamicParameter_Changed(self, sender, args):" in code
    assert "def DynamicGroup_Changed(self, sender, args):" in code
    assert "create_dynamic_persistent(" in code
    assert "manager.ModeDynamic.IsChecked = True" in bridge


def test_dynamic_conversion_is_explicit_and_readonly_refresh():
    ui = read("export_window.py")
    repo = read("services/carnet_repository.py")
    service = read("services/dynamic_sheet_groups.py")
    assert 'freeze.Header = "Rendre ce dossier manuel (figer les feuilles)"' in ui
    assert "def FreezeDynamic_Click(self, sender, args):" in ui
    assert "self.controller.freeze_dynamic(obj)" in ui
    assert "generated.extend(children)" in ui
    assert "self._carnets.extend(generated)" in ui
    assert "def freeze_dynamic(self, publication_set, direct_items, group_sets):" in repo
    assert "return self._mutate(mutation)" in repo
    assert "def resolve_dynamic(publication_set, sheets):" in service
    assert "def update_available_sheets(self, sheets):" in read("sheet_explorer.py")


def test_publication_rechecks_dynamic_rules():
    bridge = read("services/publication_preview_integration.py")
    ui = read("export_window.py")
    assert "def publish_click_with_preview(self, sender, args):" in bridge
    assert 'getattr(self, "_dynamic_errors", None)' in bridge
    assert 'getattr(self, "_dynamic_errors", None)' in ui


def test_dynamic_xaml_has_only_ui_elements_and_button_in_explorer():
    """Régression du crash IronPython WPF : '\\n' était un texte enfant."""
    from xml.etree import ElementTree as ET
    dialogue = read("carnet_manager.xaml")
    main = read("ui.xaml")
    ns = {"w": "http://schemas.microsoft.com/winfx/2006/xaml/presentation",
          "x": "http://schemas.microsoft.com/winfx/2006/xaml"}
    for document in (dialogue, main):
        root = ET.fromstring(document)
        for parent in root.iter():
            if parent.tag.endswith("}StackPanel") or parent.tag.endswith("}Grid"):
                if parent.text and parent.text.strip():
                    raise AssertionError("Texte non UIElement dans un conteneur WPF")
                for child in parent:
                    if child.tail and child.tail.strip():
                        raise AssertionError("Texte non UIElement dans un conteneur WPF")
    root = ET.fromstring(main)
    explorer = next(e for e in root.iter()
                    if e.get("{%s}Name" % ns["x"]) == "SheetExplorerPanel")
    buttons = {e.get("{%s}Name" % ns["x"]): e
               for e in explorer.iter() if e.tag.endswith("}Button")}
    assert "SheetExplorerAddButton" in buttons
    assert "CreateDynamicFolderButton" in buttons
    assert buttons["CreateDynamicFolderButton"].get("Grid.Column") == "1"
    assert all(e.get("{%s}Name" % ns["x"]) != "CreateDynamicFolderButton"
               for e in root.iter() if e not in list(explorer.iter()))
