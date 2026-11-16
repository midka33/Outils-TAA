# -*- coding: utf-8 -*-
"""Tests métier hors Revit pour les règles de publication dynamiques."""
import importlib.util
import sys
from pathlib import Path

PANEL = (Path(__file__).resolve().parents[1] /
         "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel")
for d in ("models", "services"):
    sys.path.insert(0, str(PANEL / d))

from publication_set import PublicationSet
from publication_source import PublicationSource
from dynamic_sheet_groups import resolve_dynamic


class Param(object):
    def __init__(self, value):
        self.value = value
    def AsString(self):
        return self.value
    def AsValueString(self):
        return self.value


class Sheet(object):
    def __init__(self, uid, carnet, section, number=None):
        self.UniqueId = uid
        self.Name = uid
        self.SheetNumber = number or uid
        self.Id = type("ID", (), {"IntegerValue": len(uid)})()
        self.parameters = {"Carnet": carnet, "Section": section}
    def LookupParameter(self, name):
        return Param(self.parameters[name]) if name in self.parameters else None


def folder(group=None):
    return PublicationSet(
        "Carnet DEP", source=PublicationSource(
            PublicationSource.DYNAMIC, "Carnet", "DEP", group),
        set_id="root-dyn", persistent=True, folder_id="default")


def test_dynamic_add_and_remove_on_recalculation():
    obj = folder()
    a = Sheet("A", "DEP", "A")
    direct, groups = resolve_dynamic(obj, [a])
    assert [x.unique_id for x in direct] == ["A"] and not groups
    b = Sheet("B", "DEP", "B")
    assert len(resolve_dynamic(obj, [a, b])[0]) == 2
    b.parameters["Carnet"] = "Autre"
    assert [x.unique_id for x in resolve_dynamic(obj, [a, b])[0]] == ["A"]


def test_dynamic_grouping_ids_and_blank_values():
    obj = folder("Section")
    values = [Sheet("A", "DEP", "G1"), Sheet("B", "DEP", "G2"),
              Sheet("C", "DEP", "")]
    direct, groups = resolve_dynamic(obj, values)
    assert not direct
    assert [x.name for x in groups] == ["G1", "G2", "Sans valeur"]
    ids = [x.id for x in groups]
    assert len(ids) == len(set(ids))
    assert ids == [x.id for x in resolve_dynamic(obj, values)[1]]
    assert all(x.dynamic_virtual and not x.persistent for x in groups)


def test_dynamic_missing_parameter_refuses_silent_empty_result():
    obj = folder("Missing")
    try:
        resolve_dynamic(obj, [Sheet("A", "DEP", "S")])
    except ValueError as exc:
        assert "Missing" in str(exc)
    else:
        raise AssertionError("Expected missing parameter error")


def test_dynamic_is_pure_and_source_does_not_change():
    obj = folder("Section")
    obj.items = []
    resolve_dynamic(obj, [Sheet("A", "DEP", "S")])
    assert not obj.items
    assert obj.source.mode == PublicationSource.DYNAMIC
