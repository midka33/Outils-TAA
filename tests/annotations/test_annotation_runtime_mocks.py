# -*- coding: utf-8 -*-
"""Régression du raccordement : Room.Name lève AttributeError sous IronPython.

Tests exécutables hors Revit avec doubles minimaux des services Revit.
"""
import importlib.util
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
SERVICE = (HERE / "OutilsTAA.extension" / "OutilsTAA.tab" /
           "Annotations.panel" / "services" / "annotations_service.py")


class FakeParameter:
    def __init__(self, value):
        self.value = value

    def AsString(self):
        return self.value


class FakeRoom:
    UniqueId = "id-room-A"
    Number = "A101"

    @property
    def Name(self):
        raise AttributeError("Name")

    def __init__(self, level):
        self.Level = level

    def get_Parameter(self, key):
        return FakeParameter({"ROOM_NAME": "Séjour",
                              "ROOM_NUMBER": "A101"}.get(key))


class FakeLevel:
    def __init__(self):
        self.safe_name = "R+1"

    @property
    def Name(self):
        raise AttributeError("Name")


class FakeSnapshot:
    def __init__(self, unique_id, name="", number="", level_name=""):
        self.unique_id = unique_id
        self.name = name
        self.number = number
        self.level_name = level_name


class FakeHousing:
    def __init__(self, key, rooms):
        self.key = key
        self.rooms = rooms


def load_annotation_module(monkeypatch):
    db = types.ModuleType("Autodesk.Revit.DB")
    db.BuiltInParameter = types.SimpleNamespace(
        ROOM_NAME="ROOM_NAME", ROOM_NUMBER="ROOM_NUMBER")
    db.Element = types.SimpleNamespace(
        Name=types.SimpleNamespace(
            GetValue=lambda element: element.safe_name
        ))
    db.ViewType = types.SimpleNamespace(FloorPlan="FloorPlan")
    revit = types.ModuleType("Autodesk.Revit")
    revit.DB = db
    autodesk = types.ModuleType("Autodesk")
    autodesk.Revit = revit
    generic = types.ModuleType("System.Collections.Generic")
    generic.List = list
    collections = types.ModuleType("System.Collections")
    collections.Generic = generic
    system = types.ModuleType("System")
    system.Collections = collections

    package = types.ModuleType("plans_vente")
    package.__path__ = []
    housing = types.ModuleType("plans_vente.housing")
    housing.Housing = FakeHousing
    housing.RoomSnapshot = FakeSnapshot
    dims = types.ModuleType("dimension_service")
    dims.DimensionService = type("DimensionService", (object,), {
        "__init__": lambda self, document: None,
    })
    tags = types.ModuleType("room_tag_service")
    tags.RoomTagService = type("RoomTagService", (object,), {
        "__init__": lambda self, document: None,
    })
    for name, module in (
        ("Autodesk", autodesk),
        ("Autodesk.Revit", revit),
        ("Autodesk.Revit.DB", db),
        ("System", system),
        ("System.Collections", collections),
        ("System.Collections.Generic", generic),
        ("plans_vente", package),
        ("plans_vente.housing", housing),
        ("dimension_service", dims),
        ("room_tag_service", tags),
    ):
        monkeypatch.setitem(sys.modules, name, module)

    name = "_test_annotations_revit_adapter"
    spec = importlib.util.spec_from_file_location(name, SERVICE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_room_housing_does_not_read_room_name_property(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    snapshot = mod.room_housing([FakeRoom(FakeLevel())], "logement-test").rooms[0]
    assert snapshot.unique_id == "id-room-A"
    assert snapshot.name == "Séjour"
    assert snapshot.number == "A101"
    assert snapshot.level_name == "R+1"


def test_group_type_names_use_revit_element_get_value(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    assert mod.safe_name(FakeLevel()) == "R+1"


def test_annotation_adapter_uses_only_orthogonal_opposing_faces(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    # Le moteur original donne ses references au nouvel adaptateur.
    # Il ne doit plus produire deux cotes paralleles le long des murs.
    segments = [
        (0., 0., 7., 0.),
        (7., 0., 7., 3.),
        (7., 3., 0., 3.),
        (0., 3., 0., 0.),
        (0., 0., 1., 1.),
    ]
    class Boundary(object):
        def __init__(self, segment):
            self.segment = segment
            self.reference = object()
    raw = [Boundary(segment) for segment in segments]
    monkeypatch.setattr(
        mod.DimensionService, "_room_boundary_candidates",
        lambda self, room: raw, raising=False)

    service = mod.GenericDimensions(None)
    room = types.SimpleNamespace(UniqueId="room-test")
    selected = service._room_boundary_candidates(room)
    assert len(selected) == 4
    assert all(item in raw[:4] for item in selected)
    assert service._fallback_length_indexes(selected, []) == []
    assert service._fallback_length_indexes(selected, [object()]) == []
