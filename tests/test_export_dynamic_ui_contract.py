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
    assert 'dynamic_only=(' in bridge
    assert 'getattr(sender, "Name", None) == "CreateDynamicFolderButton"' in bridge
    assert 'self.CreationModePanel.Visibility = Visibility.Collapsed' in code
    assert 'self._dynamic_only or self.ModeDynamic.IsChecked' in code
    assert 'DynamicPreviewGroups' in dialog
    assert 'DynamicPreviewSummary' in dialog
    assert 'SelectionChanged="DynamicValue_Changed"' in dialog
    assert 'SelectionChanged="DynamicGroup_Changed"' in dialog
    assert "def _refresh_dynamic_preview(self):" in code
    assert "self.controller.preview_dynamic(" in code


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


def test_automatic_folders_use_distinct_icon():
    theme = (BASE.parents[1] / "resources" / "ui" / "Theme.xaml").read_text(
        encoding="utf-8")
    ui = read("export_window.py")
    assert 'x:Key="TaaAutoFolderIcon"' in theme
    assert 'x:Key="TaaAutoFolderBrush"' in theme
    assert 'icon.Stroke = self.FindResource(brush_key)' in ui
    assert '"TaaAutoFolderIcon" if (is_dynamic or is_virtual)' in ui
    assert '"TaaFolderIcon"' in ui


def test_freeze_single_child_command_is_separate_from_full_parent_freeze():
    ui = read("export_window.py")
    controller = read("services/carnet_controller.py")
    repository = read("services/carnet_repository.py")
    assert 'freeze_one.Header = "Figer uniquement ce sous-dossier"' in ui
    assert "freeze_one.Click += self.FreezeDynamicGroup_Click" in ui
    assert "def FreezeDynamicGroup_Click(self, sender, args):" in ui
    assert "self.controller.freeze_dynamic_group(group)" in ui
    assert "def freeze_dynamic_group(self, selected_group):" in controller
    assert "def freeze_dynamic_group(self, parent_id, group):" in repository
    assert 'freeze.Header = "Rendre ce dossier manuel (figer les feuilles)"' in ui
    assert "def FreezeDynamic_Click(self, sender, args):" in ui
