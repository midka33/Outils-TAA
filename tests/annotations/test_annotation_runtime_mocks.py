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
        # Le vrai service conserve self.document ; le double aussi.
        "__init__": lambda self, document: setattr(self, "document", document),
        "ANGLE_TOLERANCE_DEGREES": 5.0,
        "MINIMUM_RELATIVE_LENGTH": 0.25,
        "PLACEMENT_FRACTION": 0.25,
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


def test_adaptateur_positionne_sur_rail_voisin_sans_changer_references(monkeypatch):
    """Appelle le vrai _plan_graphics de l'adaptateur, pas le helper seul."""
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    service = mod.GenericDimensions(None)
    service.PAPER_CLEARANCE_MM = 3.
    service.PAPER_TEXT_WIDTH_MM = 6.
    service.PAPER_TEXT_HEIGHT_MM = 1.5
    service.PAPER_PADDING_MM = .15
    service.PAPER_WITNESS_MM = .75
    service._millimeters_to_internal = lambda value: value / 1000.
    service._placement_room_points = lambda room: [
        (0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    service._probe_z = lambda room: 1.
    service._xyz = lambda x, y, z: types.SimpleNamespace(X=x, Y=y, Z=z)
    service._room_label = lambda room: "piece-test"
    service._alignment_rails = lambda view: [
        ((6.2, 1.4), (9.8, 1.4))]
    room = types.SimpleNamespace(
        IsPointInRoom=lambda p: 0. < p.X < 6. and 0. < p.Y < 4.)
    view = types.SimpleNamespace(
        Scale=100, RightDirection=types.SimpleNamespace(X=1., Y=0.))
    warnings = []
    chosen = service._plan_graphics(
        room, view, [((0., 1.7), (6., 1.7))], [None],
        [], [], [], warnings)
    assert len(chosen) == 1
    assert abs(chosen[0].line_start[1] - 1.4) < 1e-8
    assert not warnings



def test_room_partiellement_cotee_reste_eligible(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    service = mod.AnnotationService(None)
    room = types.SimpleNamespace(get_BoundingBox=lambda view: object())
    view = object()
    # Un groupe de cotes existant ne suffit pas a disqualifier une piece.
    # La comparaison des references decide de l'axe encore manquant.
    assert service._not_yet_dimensioned(view, [room]) == [room]


def test_reference_identique_evite_doublon_mais_garde_l_autre_axe(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))

    class Ref(object):
        def __init__(self, label):
            self.label = label

        def ConvertToStableRepresentation(self, doc):
            return self.label

    class Dim(object):
        def __init__(self):
            self.References = [Ref("face-bas"), Ref("face-haut")]

        def IsHidden(self, view):
            return False

    class Collector(object):
        def __init__(self, doc, view_id):
            self.doc = doc

        def OfCategory(self, category):
            return self

        def WhereElementIsNotElementType(self):
            return self

        def ToElements(self):
            return self.doc.dimensions

    mod.DB.FilteredElementCollector = Collector
    mod.DB.BuiltInCategory = types.SimpleNamespace(OST_Dimensions=123)

    segments = [(0., 0., 7., 0.),
                (7., 0., 7., 3.),
                (7., 3., 0., 3.),
                (0., 3., 0., 0.)]
    class Bound(object):
        def __init__(self, segment, key):
            self.segment = segment
            self.reference = Ref(key)

    raw = [Bound(segment, key) for segment, key in
           zip(segments, ("face-bas", "face-droite",
                          "face-haut", "face-gauche"))]
    monkeypatch.setattr(mod.DimensionService, "_room_boundary_candidates",
                        lambda self, room: list(raw), raising=False)

    doc = types.SimpleNamespace(dimensions=[Dim()])
    service = mod.GenericDimensions(doc)
    service.target_view = types.SimpleNamespace(Id="vue-0")
    service.ANGLE_TOLERANCE_DEGREES = 5.
    service.MINIMUM_RELATIVE_LENGTH = .25
    service.PLACEMENT_FRACTION = .25
    room = types.SimpleNamespace(UniqueId="piece-A101")
    assert service._existing_dimension_reference_pairs() == {
        frozenset(("face-bas", "face-haut"))}
    pending = service._room_boundary_candidates(room)
    assert [b.segment for b in pending] == [segments[1], segments[3]]

    # Une fois l'axe restant cote, il ne faut rien ajouter au relancement.
    doc.dimensions.append(types.SimpleNamespace(
        References=[Ref("face-droite"), Ref("face-gauche")],
        IsHidden=lambda view: False))
    assert service._room_boundary_candidates(room) == []
