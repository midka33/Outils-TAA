# -*- coding: utf-8 -*-
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"))
from baies_diagnostic.ui_table import build_type_table, display_text


class Columns(list):
    def Add(self, value):
        self.append(value)


class Rows(list):
    def Add(self, value):
        self.append(value)


class FakeDataTable:
    def __init__(self, name):
        self.name = name
        self.Columns = Columns()
        self.Rows = Rows()
        self.DefaultView = self.Rows

    def NewRow(self):
        return {}


def install_mocks(monkeypatch, fail_first=False):
    refs = []
    clr = types.ModuleType("clr")

    def add_reference(name):
        refs.append(name)
        if fail_first and name == "System.Data.Common":
            raise ImportError("assembly not found")

    clr.AddReference = add_reference
    system = types.ModuleType("System")
    data = types.ModuleType("System.Data")
    data.DataTable = FakeDataTable
    monkeypatch.setitem(sys.modules, "clr", clr)
    monkeypatch.setitem(sys.modules, "System", system)
    monkeypatch.setitem(sys.modules, "System.Data", data)
    return refs


def test_loading_explicit_common_assembly(monkeypatch):
    refs = install_mocks(monkeypatch)
    table = build_type_table([dict(source="Projet", family="Fenêtre à soufflet", type="120 × 135", count=2, methods="TABLEAU", status="À vérifier")])
    assert refs == ["System.Data.Common"]
    assert list(table.Columns) == ["source", "family", "type", "count", "methods", "status"]
    assert table.Rows[0]["family"] == "Fenêtre à soufflet"
    assert table.Rows[0]["count"] == "2"


def test_legacy_assembly_fallback(monkeypatch):
    refs = install_mocks(monkeypatch, True)
    table = build_type_table([dict(family="Porte-fenêtre")])
    assert refs == ["System.Data.Common", "System.Data"]
    assert table.Rows[0]["source"] == ""


def test_empty_result(monkeypatch):
    install_mocks(monkeypatch)
    assert len(build_type_table([]).Rows) == 0


def test_text_none_and_unicode():
    assert display_text(None) == ""
    assert display_text("Étage") == "Étage"
