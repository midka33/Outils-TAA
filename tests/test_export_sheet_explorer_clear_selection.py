# -*- coding: utf-8 -*-
"""Contrat UI et sélection cumulative de l'explorateur Export."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"


def test_clear_button_is_above_add_and_wired():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")
    assert 'x:Name="SheetExplorerClearSelectionButton"' in xaml
    assert 'Click="SheetExplorerClearSelection_Click"' in xaml
    assert xaml.index('x:Name="SheetExplorerClearSelectionButton"') < xaml.index('x:Name="SheetExplorerAddButton"')
    handlers = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert "def SheetExplorerClearSelection_Click(self, sender, args):" in handlers
    assert "explorer.clear_selection()" in handlers


def test_clear_selection_clears_hidden_ids_without_changing_filters():
    source = (PANEL / "sheet_explorer.py").read_text(encoding="utf-8")
    start = source.index("    def clear_selection(self):")
    end = source.index("    def _update_count(self):", start)
    method = source[start:end]
    assert "self.selected_ids.clear()" in method
    assert "self.window.SheetExplorerList.UnselectAll()" in method
    assert "self._rendering = True" in method
    assert "self._rendering = False" in method
    assert "self._update_count()" in method
    assert "SheetExplorerParameter" not in method
    assert "SheetExplorerValue" not in method


def test_count_controls_both_button_states():
    source = (PANEL / "sheet_explorer.py").read_text(encoding="utf-8")
    start = source.index("    def _update_count(self):")
    end = source.index("    def _build_context_menu(self):", start)
    method = source[start:end]
    assert "self.window.SheetExplorerAddButton.IsEnabled = count > 0" in method
    assert "self.window.SheetExplorerClearSelectionButton.IsEnabled = count > 0" in method
    assert "def selection_changed(self, args):" in source
    assert "self.selected_ids.add(str(tag))" in source
