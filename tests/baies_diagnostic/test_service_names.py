# -*- coding: utf-8 -*-
"""Régression IronPython BUG-CALCULS-008 : Name inaccessible sur FamilySymbol."""
from __future__ import unicode_literals

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"))

SERVICE_PATH = (Path(__file__).resolve().parents[2]
    / "OutilsTAA.extension" / "OutilsTAA.tab" / "Calculs.panel"
    / "services" / "baies_diagnostic_service.py")


def _load():
    spec = importlib.util.spec_from_file_location("baies_diagnostic_service_test", SERVICE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeId(object):
    def __init__(self, value):
        self.Value = value


class BrokenName(object):
    def __init__(self, name, value):
        self.expected_name = name
        self.Id = FakeId(value)

    @property
    def Name(self):
        raise AttributeError("Name")

    def get_Parameter(self, parameter):
        return None


class NormalName(BrokenName):
    @property
    def Name(self):
        return self.expected_name


class BrokenDescriptor(object):
    def GetValue(self, item):
        if isinstance(item, BrokenName):
            return item.expected_name
        raise AttributeError("Name")


class FailedDescriptor(object):
    def GetValue(self, item):
        raise AttributeError("Name")


def db(descriptor):
    class Element(object):
        Name = descriptor

    class BuiltInParameter(object):
        SYMBOL_NAME_PARAM = "symbol-name"

    class DB(object):
        pass

    DB.Element = Element
    DB.BuiltInParameter = BuiltInParameter
    return DB


def test_family_symbol_in_ironpython_name_error():
    m = _load()
    symbol = BrokenName("FEN_2V_120x135", 201)
    family = BrokenName("Menuiseries Extérieures", 202)
    d = db(BrokenDescriptor())
    assert m._element_name(symbol, d) == "FEN_2V_120x135"
    assert m._element_name(family, d) == "Menuiseries Extérieures"


def test_direct_name_used_as_fallback_if_descriptor_fails():
    m = _load()
    symbol = NormalName("Porte-fenêtre 2V", 33)
    assert m._element_name(symbol, db(FailedDescriptor())) == "Porte-fenêtre 2V"


def test_missing_type_name_is_nonfatal():
    m = _load()
    assert m._element_name(BrokenName("", 99), db(FailedDescriptor()), "Type inconnu #99") == "Type inconnu #99"
    assert m._element_name(None, db(FailedDescriptor()), "Sans famille") == "Sans famille"


def test_snapshot_processes_broken_family_and_type_names(monkeypatch):
    m = _load()

    class Family(BrokenName):
        pass

    class Symbol(BrokenName):
        Family = Family("FEN_TAA", 55)

    class Instance(object):
        Symbol = Symbol("120x135", 56)
        Host = None
        FromRoom = None
        ToRoom = None
        Id = FakeId(57)
        UniqueId = "57-uid"

        def get_BoundingBox(self, view):
            return None

    class Document(object):
        Title = "Test Revit"

    monkeypatch.setattr(m.BaiesDiagnosticService, "_db", staticmethod(lambda: db(BrokenDescriptor())))
    monkeypatch.setattr(m.BaiesDiagnosticService, "_parameters",
                        lambda self, item, origin: (
                            [dict(name="Largeur", value_m=1.2, origin="type"),
                             dict(name="Hauteur", value_m=1.35, origin="type")]
                            if origin == "type" else []
                        ))
    service = m.BaiesDiagnosticService(Document())
    row = service._snapshot(Document(), Instance(), "Projet hôte", "HOST", "Fenêtre")
    assert row["family"] == "FEN_TAA"
    assert row["type"] == "120x135"
    assert row["status"] == "NOMINAL_A_CONFIRMER"
    assert row["area_m2"] == 1.62
