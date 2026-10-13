# -*- coding: utf-8 -*-
"""Empty publication folders must remain in the Export tree."""
import ast
from pathlib import Path
from types import SimpleNamespace

PANEL = Path(__file__).resolve().parents[1] / "OutilsTAA.extension/OutilsTAA.tab/Export.panel"


def _filter_method():
    path = PANEL / "export_window.py"
    syntax = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(node for node in syntax.body if getattr(node, "name", None) == "ExportWindow")
    func = next(node for node in cls.body if getattr(node, "name", None) == "_belongs_to_current_project")
    namespace = {}
    exec(compile(ast.Module(body=[func], type_ignores=[]), str(path), "exec"), namespace)
    return namespace["_belongs_to_current_project"]


def test_empty_persistent_folder_remains_visible():
    check = _filter_method()
    window = SimpleNamespace(current_project_unique_ids={"current"})
    empty = SimpleNamespace(persistent=True, items=[], name="PDF")
    assert check(window, empty)


def test_foreign_sheet_set_remains_hidden():
    check = _filter_method()
    window = SimpleNamespace(current_project_unique_ids={"current"})
    foreign = SimpleNamespace(persistent=True, items=[SimpleNamespace(unique_id="foreign")])
    assert not check(window, foreign)


def test_nonpersistent_empty_session_set_is_not_preserved():
    check = _filter_method()
    window = SimpleNamespace(current_project_unique_ids={"current"})
    temporary = SimpleNamespace(persistent=False, items=[])
    assert not check(window, temporary)


def test_sheet_from_current_project_stays_visible():
    check = _filter_method()
    window = SimpleNamespace(current_project_unique_ids={"current"})
    target = SimpleNamespace(persistent=True, items=[SimpleNamespace(unique_id="current")])
    assert check(window, target)
