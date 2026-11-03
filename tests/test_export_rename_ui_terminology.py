# -*- coding: utf-8 -*-
"""Contrats UI : renommage exploitable et terminologie dossiers (hors Revit)."""

import ast
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace as NS

PANEL = Path(__file__).resolve().parents[1] / (
    "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
)


def _window_method(name, namespace=None):
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    cls = next(
        x for x in ast.parse(source).body
        if isinstance(x, ast.ClassDef) and x.name == "ExportWindow"
    )
    node = next(
        x for x in cls.body
        if isinstance(x, ast.FunctionDef) and x.name == name
    )
    globals_dict = namespace or {}
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 "export_window.py", "exec"), globals_dict)
    return globals_dict[name]


def test_rename_button_and_per_node_menu_are_present():
    xaml = ET.parse(str(PANEL / "ui.xaml")).getroot()
    xmlns = "{http://schemas.microsoft.com/winfx/2006/xaml/presentation}"
    buttons = [
        node.attrib for node in xaml.iter(xmlns + "Button")
        if node.get("Content") == "Renommer"
    ]
    assert len(buttons) == 1
    assert buttons[0]["Click"] == "RenameFolder_Click"
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert source.count("node.ContextMenu = self._context_menu_for_folder(node.Tag)") == 2
    assert 'rename.Tag = tag' in source
    assert "self.PublicationTree.ContextMenu = menu" not in source


def test_right_click_renames_the_target_under_mouse_not_previous_selection():
    renamed = []
    selections = []
    requested = []
    target = NS(id="published", name="Façades B")
    previous = NS(id="other", name="Façades A")
    tag = ("CARNET", target)
    menu = NS(Tag=tag)
    forms = NS(
        alert=lambda *args, **kwargs: requested.append(("alert", args)),
        ask_for_string=lambda **kwargs: "Façades B — corrigé",
    )
    manager = NS(
        _expanded=lambda: (["general"], ["published"]),
        _scroll_offset=lambda: 3,
        _key=lambda tag: "{0}:{1}".format(tag[0], tag[1].id),
        _restore_expanded=lambda state: None,
        _restore_scroll=lambda value: None,
        _select=lambda keys: selections.append(keys),
    )
    window = NS(
        repository=NS(rename_publication_folder=lambda i, n: renamed.append((i, n))),
        _publication_selection_tags=lambda: [("CARNET", previous)],
        _drag_drop_manager=manager,
        _refresh_tree=lambda: None,
    )
    _window_method("RenameFolder_Click", {"forms": forms})(window, menu, None)
    assert renamed == [("published", "Façades B — corrigé")]
    assert selections == [["CARNET:published"]]
    assert requested == []


def test_preview_progress_report_and_summary_avoid_word_carnet():
    for filename in ("publication_preview.xaml", "publication_report.xaml"):
        root = ET.parse(str(PANEL / filename)).getroot()
        headers = [
            elem.attrib.get("Header", "")
            for elem in root.iter()
            if elem.tag.endswith("DataGridTextColumn")
        ]
        assert "Dossier" in headers
        assert "Carnet" not in headers

    progress = (PANEL / "publication_progress.xaml").read_text(encoding="utf-8")
    overview = (PANEL / "services/publication_overview.py").read_text(encoding="utf-8")
    preview_service = (PANEL / "services/publication_preview_service.py").read_text(encoding="utf-8")
    assert 'Text="Dossier de publication :"' in progress
    assert "dossier(s) |" in overview
    assert "PDF combiné du dossier" in preview_service
