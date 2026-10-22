# -*- coding: utf-8 -*-
"""Le filtre Revit conserve séparément toutes les exclusions pour l'audit."""
from __future__ import unicode_literals
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"))
PATH = (Path(__file__).resolve().parents[2] / "OutilsTAA.extension"
        / "OutilsTAA.tab" / "Calculs.panel" / "services" / "baies_diagnostic_service.py")


def load_service():
    spec = importlib.util.spec_from_file_location("baies_exclusions_service", PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Id:
    Value = 123


class Category:
    Name = "Murs"


class Host:
    Category = Category()


class Family:
    def __init__(self, name):
        self.Name = name


class Symbol:
    def __init__(self, name, family):
        self.Name = name
        self.Family = Family(family)


class Instance:
    Id = Id()
    UniqueId = "test-123"
    Host = Host()
    def __init__(self, family):
        self.Symbol = Symbol(family + "-type", family)


class Collector:
    def __init__(self, items):
        self.items = items

    def OfCategory(self, category):
        self.category = category
        return self

    def WhereElementIsNotElementType(self):
        return self

    def __iter__(self):
        if self.category == "windows":
            return iter(self.items)
        return iter([])


class FakeDB:
    class BuiltInCategory:
        OST_Windows = "windows"
        OST_Doors = "doors"
    FamilyInstance = Instance

    class Element:
        class Name:
            @staticmethod
            def GetValue(x):
                return x.Name


def run(monkeypatch, exclude_lanterns=True, exclude_mrx=True):
    m = load_service()
    items = [Instance("FEN-EXT-GEN-1V_ITI"),
             Instance("FEN-EXT-GEN-1V_Lanterneau"),
             Instance("FEN-EXT-GEN-1V_MRX")]
    FakeDB.FilteredElementCollector = lambda document: Collector(items)
    monkeypatch.setattr(m.BaiesDiagnosticService, "_db", staticmethod(lambda: FakeDB))
    monkeypatch.setattr(m.BaiesDiagnosticService, "_snapshot", lambda self, doc, el, source, source_id, category: {
        "family": el.Symbol.Family.Name, "source_id": source_id, "category": category
    })
    rows, warnings, excluded = [], [], []
    m.BaiesDiagnosticService(object())._collect(object(), "Projet hôte", "HOST",
        rows, warnings, excluded, facade_only=True,
        exclude_lanterns=exclude_lanterns, exclude_mrx=exclude_mrx)
    return rows, warnings, excluded


def test_default_exclusion(monkeypatch):
    rows, warnings, excluded = run(monkeypatch)
    assert len(rows) == 1
    assert len(excluded) == 2
    assert not warnings
    assert sorted(x["reason"] for x in excluded) == ["LANTERNEAU", "MRX"]


def test_include_lantern_only_for_diagnostic(monkeypatch):
    rows, _, excluded = run(monkeypatch, exclude_lanterns=False)
    assert len(rows) == 2
    assert [x["reason"] for x in excluded] == ["MRX"]


def test_include_mrx_only_for_diagnostic(monkeypatch):
    rows, _, excluded = run(monkeypatch, exclude_mrx=False)
    assert len(rows) == 2
    assert [x["reason"] for x in excluded] == ["LANTERNEAU"]


def test_include_all_for_diagnostic(monkeypatch):
    rows, warnings, excluded = run(monkeypatch, exclude_lanterns=False, exclude_mrx=False)
    assert len(rows) == 3
    assert len(excluded) == 0
    assert len(warnings) == 0
