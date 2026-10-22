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
        "FLOOR_LEVEL_TOLERANCE_MM": 500.,
        "FLOOR_EDGE_MIN_LENGTH_MM": 100.,
        "_millimeters_to_internal": staticmethod(lambda mm: mm / 1000.),
    })
    tags = types.ModuleType("room_tag_service")
    tags.RoomTagService = type("RoomTagService", (object,), {
        "__init__": lambda self, document: None,
    })
    crash_trace = types.ModuleType("crash_trace")
    crash_trace.trace = lambda *args, **kwargs: None
    crash_trace.TRACE_PATH = "temporary-test-log"
    for name, module in (
        ("crash_trace", crash_trace),
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


def test_balcon_utilise_uniquement_moteur_pdv_apres_crash(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    service = mod.GenericDimensions(object())
    expected = ("reference_pdv", "floor-id")
    monkeypatch.setattr(
        mod.DimensionService, "_matching_floor_edge_reference",
        lambda self, room, curve: expected, raising=False)
    assert service._matching_floor_edge_reference(object(), object()) == expected

    # Aucun second parcours des solides Revit n'est autorise ici.
    assert "_nearby_floor_edges" not in mod.GenericDimensions.__dict__
    assert "_matching_floor_edge_reference" not in mod.GenericDimensions.__dict__


def test_wc_small_room_plan_graphics_selects_fallback_without_texte_inside(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    service = mod.GenericDimensions(object())
    service.PAPER_CLEARANCE_MM = 6.
    service.PAPER_TEXT_WIDTH_MM = 12.
    service.PAPER_TEXT_HEIGHT_MM = 3.
    service.PAPER_PADDING_MM = .3
    service.PAPER_WITNESS_MM = 1.5
    service._millimeters_to_internal = lambda value: value / 1000.
    service._placement_room_points = lambda room: [
        (0., 0.), (1.2, 0.), (1.2, .8), (0., .8)]
    service._probe_z = lambda room: 1.
    service._xyz = lambda x, y, z: types.SimpleNamespace(X=x, Y=y, Z=z)
    service._room_label = lambda room: "WC"
    service._alignment_rails = lambda view: []
    room = types.SimpleNamespace(IsPointInRoom=lambda p: (
        0. < p.X < 1.2 and 0. < p.Y < .8))
    view = types.SimpleNamespace(
        Scale=100, RightDirection=types.SimpleNamespace(X=1., Y=0.))
    warnings = []
    placements = service._plan_graphics(
        room, view, [((.6, 0.), (.6, .8))], [None],
        [], [], [], warnings)
    from annotations.strict_dimension_positioning import SkippedPlacement
    assert len(placements) == 1
    assert not isinstance(placements[0], SkippedPlacement)
    assert any("hors piece" in message for message in placements[0].warnings)



def test_crash_safety_refuse_dimension_batch_et_groupe_sans_selection(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    service = mod.AnnotationService(object())
    try:
        service.run("dims", [], "type")
    except ValueError as error:
        assert "une vue et une piece" in str(error)
    else:
        raise AssertionError("Le diagnostic doit interdire cotations en masse.")


def test_mode_diagnostic_seule_la_piece_cible_est_examinee(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    class FakeRoomId(object):
        def __init__(self, uid):
            self.UniqueId = uid
            self.GroupId = "invalid-group"
            self.Number = uid
    view = types.SimpleNamespace(
        ViewType="FloorPlan", IsTemplate=False, Name="Vue test",
        Id="view-id")
    mod.DB.ElementId = types.SimpleNamespace(InvalidElementId="invalid-group")
    service = mod.AnnotationService(object())
    service._rooms = lambda v: [FakeRoomId("A"), FakeRoomId("B")]
    processed = []
    service._run_unit = lambda view, rooms, kind, atype, group, style: (
        processed.append(rooms[0].UniqueId) or 0, [])
    count, report = service.run(
        "dims", [view], "type", diagnostic_room_uid="B")
    assert processed == ["B"]
    assert count == 0


def test_balcon_proxies_2d_reference_native_sans_solides_et_cleanup(monkeypatch):
    """Revit simulé : une limite separator devient une DetailCurve cotable."""
    mod = load_annotation_module(monkeypatch)
    db = mod.DB
    timeline = []

    class EId(object):
        def __init__(self, n):
            self.Value = n

    class Ref(object):
        def __init__(self, element_id):
            self.ElementId = element_id

    class Detail(object):
        def __init__(self, i):
            self.Id = EId(i)
            self.GeometryCurve = types.SimpleNamespace(Reference=Ref(self.Id))
            self.LineStyle = None

    class Transaction(object):
        def __init__(self, document, label):
            self.label = label

        def Start(self):
            timeline.append("tx-start")

        def Commit(self):
            timeline.append("tx-commit")

        def RollBack(self):
            timeline.append("tx-rollback")

    class Line(object):
        @staticmethod
        def CreateBound(a, b):
            return a, b

    db.Transaction = Transaction
    db.Line = Line
    db.XYZ = lambda x, y, z: (x, y, z)
    db.UnitTypeId = types.SimpleNamespace(Millimeters="mm")
    db.UnitUtils = types.SimpleNamespace(
        ConvertToInternalUnits=lambda x, unit: x / 304.8)

    class Maker(object):
        def __init__(self):
            self.details = []

        def NewDetailCurve(self, view, curve):
            detail = Detail(100 + len(self.details))
            self.details.append((detail, curve))
            return detail

    maker = Maker()
    doc = types.SimpleNamespace(
        Create=maker,
        Regenerate=lambda: timeline.append("regenerate"),
        Delete=lambda element_id: timeline.append(
            "delete-" + str(element_id.Value)),
    )
    service = mod.AnnotationService(doc)
    class Boundary(object):
        def __init__(self, source, segment):
            self.source_kind = source
            self.segment = segment
            self.reference = Ref(EId(999))
            self.element_id_value = 999
            self.length_references = None

    separator = Boundary("separator", (0., 0., 0., 3.6))
    wall = Boundary("wall", (3.12, 0., 3.12, 3.6))
    room = types.SimpleNamespace(
        UniqueId="2238", Level=types.SimpleNamespace(Elevation=10.))
    service.dims._room_boundary_candidates = lambda r: [separator, wall]
    view, style = object(), object()
    created = service._create_separator_proxies(view, [room], style)
    assert len(created) == 1
    assert len(maker.details) == 1
    assert separator.source_kind == "proxy"
    assert separator.reference.ElementId.Value == created[0].Value
    assert separator.length_references is None
    assert wall.source_kind == "wall"
    assert service.dims.proxy_candidates["2238"] == [separator, wall]
    assert maker.details[0][0].LineStyle is style
    assert "regenerate" in timeline
    assert timeline[-1] == "tx-commit"

    # La cote native utilise la référence du détail : rien à supprimer.
    dim = types.SimpleNamespace(
        Id=EId(1), References=[separator.reference, wall.reference])
    service._elements = lambda v, kind: [dim]
    service._cleanup_unused_separator_proxies(view, created, {1})
    assert not any(event.startswith("delete-") for event in timeline)


def test_balcon_deux_proxies_et_seulement_une_cote_nettoie_reste(monkeypatch):
    """Des lignes 2D orphelines ne restent pas si une cote est refusée."""
    mod = load_annotation_module(monkeypatch)
    class EId(object):
        def __init__(self, value):
            self.Value = value
    class Tx(object):
        def __init__(self, doc, name):
            pass
        def Start(self):
            pass
        def Commit(self):
            pass
        def RollBack(self):
            pass
    mod.DB.Transaction = Tx
    deleted = []
    doc = types.SimpleNamespace(Delete=lambda element_id: deleted.append(
        element_id.Value))
    service = mod.AnnotationService(doc)
    dim = types.SimpleNamespace(
        Id=EId(500),
        References=[types.SimpleNamespace(ElementId=EId(12)),
                    types.SimpleNamespace(ElementId=EId(111))])
    service._elements = lambda v, kind: [dim]
    service._cleanup_unused_separator_proxies(
        object(), [EId(12), EId(13)], {500})
    assert deleted == [13]


def test_balcon_aucune_dimension_references_proxies_provoque_rollback(monkeypatch):
    """Pas d'accumulation de traits 2D après un échec de cotation."""
    mod = load_annotation_module(monkeypatch)
    class EId(object):
        def __init__(self, value):
            self.Value = value
    service = mod.AnnotationService(object())
    service._elements = lambda view, kind: []
    try:
        service._cleanup_unused_separator_proxies(object(), [EId(99)], set())
    except RuntimeError as error:
        assert "Aucune cote creee" in str(error)
    else:
        raise AssertionError("Une ligne orpheline doit provoquer une annulation.")


def test_balcon_second_lancement_reconnait_cote_existante_avec_proxy(monkeypatch):
    """Les deux références du proxy diffèrent des séparations initiales."""
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    class EId(object):
        def __init__(self, number):
            self.Value = number

    class DetailLine(object):
        def __init__(self):
            self.GeometryCurve = NativeLine()

    class NativeLine(object):
        Length = .005
        def GetEndPoint(self, i):
            return types.SimpleNamespace(X=0., Y=1.81)  # loggia 3,62 m

    class Collector(object):
        def __init__(self, doc, view_id):
            self.doc = doc
        def OfCategory(self, category):
            return self
        def WhereElementIsNotElementType(self):
            return self
        def ToElements(self):
            return self.doc.dimensions

    class Ref(object):
        def __init__(self, ident):
            self.ElementId = EId(ident)

    mod.DB.DetailCurve = DetailLine
    mod.DB.Line = NativeLine
    mod.DB.FilteredElementCollector = Collector
    mod.DB.BuiltInCategory = types.SimpleNamespace(OST_Dimensions=5)
    dim = types.SimpleNamespace(
        References=[Ref(17), Ref(71)], Value=3.12,
        IsHidden=lambda view: False)
    doc = types.SimpleNamespace(
        dimensions=[dim],
        GetElement=lambda i: DetailLine() if i.Value == 17 else None)
    service = mod.GenericDimensions(doc)
    service._millimeters_to_internal = lambda mm: mm / 1000.
    service.target_view = types.SimpleNamespace(Id="test-view")
    class Candidate(object):
        def __init__(self, segment, kind):
            self.segment, self.source_kind = segment, kind
            self.reference = object()
    raw = [
        Candidate((0., 0., 3.12, 0.), "wall"),
        Candidate((3.12, 0., 3.12, 3.62), "wall"),
        Candidate((3.12, 3.62, 0., 3.62), "wall"),
        Candidate((0., 3.62, 0., 0.), "separator"),
    ]
    monkeypatch.setattr(
        mod.DimensionService, "_room_boundary_candidates",
        lambda self, room: list(raw), raising=False)
    service._existing_dimension_reference_pairs = lambda: set()
    assert service._existing_proxy_dimensions() == [(3.12, [(0., 1.81)])]
    # Les faces gauche/droite mesurent deja 3,12 m. Ne proposer que
    # les faces haut/bas pour la cote de 3,62 m restante.
    remaining = service._room_boundary_candidates(
        types.SimpleNamespace(UniqueId="room-2238"))
    assert remaining == [raw[0], raw[2]]


def test_revit_adapter_local_floor_candidates_filters_other_level_by_xy(monkeypatch):
    """Vrai raccordement du hook du service a la politique commune."""
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    class Point(object):
        def __init__(self, x, y):
            self.X, self.Y = x, y

    class Box(object):
        def __init__(self, x0, y0, x1, y1):
            self.Min = Point(x0, y0)
            self.Max = Point(x1, y1)

    class Floor(object):
        def __init__(self, box, key):
            self.box, self.key = box, key

        def get_BoundingBox(self, view):
            return self.box

    remote = Floor(Box(100, 100, 110, 110), "meme-niveau")
    neighbor = Floor(Box(-.1, -.1, 3.2, 3.7), "proche-autre-niveau")
    room = types.SimpleNamespace(
        UniqueId="2238",
        get_BoundingBox=lambda v: Box(0, 0, 3.12, 3.62),
        get_Parameter=lambda param: FakeParameter("2238"))
    service = mod.GenericDimensions(object())
    service._millimeters_to_internal = lambda mm: mm / 1000.
    chosen = service._floor_candidates(room, [remote], [neighbor])
    assert chosen == [neighbor]
    assert service._floor_cache_key(room, 10) == (10, "2238")
    assert service._floor_cache_key(types.SimpleNamespace(UniqueId="1170"), 10) != (
        10, "2238")


def test_revit_adapter_ninsiste_pas_si_trop_de_planchers_a_extraire(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    v = lambda x, y: types.SimpleNamespace(X=x, Y=y)
    bounds = types.SimpleNamespace(Min=v(0, 0), Max=v(4, 4))
    floors = [types.SimpleNamespace(
        get_BoundingBox=lambda view: bounds) for _ in range(7)]
    service = mod.GenericDimensions(object())
    service._millimeters_to_internal = lambda mm: mm / 1000.
    room = types.SimpleNamespace(
        UniqueId="2238",
        get_BoundingBox=lambda view: bounds,
        get_Parameter=lambda param: FakeParameter("2238"))
    assert service._floor_candidates(room, floors, []) == []



def test_guardrail_reference_prioritaire_sur_reperes_2d(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    service = mod.GenericDimensions(object())
    edge_reference = object()
    edge_id = types.SimpleNamespace(Value=2450)
    service._nearby_guardrail_edges = lambda room, boundaries: [
        ((0., .005, 3.12, .005), edge_reference, edge_id, 3.7)
    ]
    service.FLOOR_EDGE_TOLERANCE_MM = 20.
    service.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES = 3.
    service.FLOOR_EDGE_MIN_OVERLAP_RATIO = .6
    class Candidate(object):
        def __init__(self, source_kind, segment, reference):
            self.source_kind = source_kind
            self.segment = segment
            self.reference = reference
            self.element_id_value = 1000
            self.length_references = None

    separator = Candidate("separator", (0., 0., 3.12, 0.), object())
    floor = Candidate("floor_edge", (0., 3.62, 3.12, 3.62), object())
    original_floor = floor.reference
    room = types.SimpleNamespace(
        UniqueId="2238",
        get_Parameter=lambda p: FakeParameter("2238"))
    chosen = service._upgrade_separator_guardrail(room, [separator, floor])
    assert chosen == [separator, floor]
    assert separator.source_kind == "guardrail_edge"
    assert separator.reference is edge_reference
    assert separator.element_id_value == 2450
    assert floor.reference is original_floor
    assert floor.source_kind == "floor_edge"
    assert any("garde-corps" in t for t in service._guardrail_warnings)


def test_guardrail_non_superpose_ne_remplace_pas_separation(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))
    service = mod.GenericDimensions(object())
    service._nearby_guardrail_edges = lambda room, boundaries: [
        ((0., .35, 3.12, .35), object(),
         types.SimpleNamespace(Value=2450), 3.7)
    ]
    service.FLOOR_EDGE_TOLERANCE_MM = 20.
    service.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES = 3.
    service.FLOOR_EDGE_MIN_OVERLAP_RATIO = .6
    marker = object()
    candidate = types.SimpleNamespace(
        source_kind="separator", segment=(0., 0., 3.12, 0.),
        reference=marker)
    room = types.SimpleNamespace(UniqueId="2238")
    service._upgrade_separator_guardrail(room, [candidate])
    assert candidate.source_kind == "separator"
    assert candidate.reference is marker


def test_guardrail_reference_non_native_no_scan_when_view_absent(monkeypatch):
    mod = load_annotation_module(monkeypatch)
    service = mod.GenericDimensions(object())
    assert service._nearby_guardrail_edges(
        types.SimpleNamespace(UniqueId="2238")) == []



def test_guardrail_native_reference_reconnue_au_second_lancement(monkeypatch):
    """Substitution AVANT la comparaison : pas de cote double sur 2238."""
    mod = load_annotation_module(monkeypatch)
    library = HERE / "OutilsTAA.extension" / "lib"
    monkeypatch.syspath_prepend(str(library))

    class Ref(object):
        def __init__(self, value):
            self.value = value
        def ConvertToStableRepresentation(self, document):
            return self.value

    class Bound(object):
        def __init__(self, segment, kind, name):
            self.segment = segment
            self.source_kind = kind
            self.reference = Ref(name)
            self.element_id_value = 25
            self.length_references = None

    segments = [(0., 0., 3.12, 0.),
                (3.12, 0., 3.12, 3.62),
                (3.12, 3.62, 0., 3.62),
                (0., 3.62, 0., 0.)]
    original = [
        Bound(segment, kind, name)
        for segment, kind, name in zip(
            segments, ["wall", "wall", "wall", "separator"],
            ["bas", "droite", "haut", "sep"])
    ]
    monkeypatch.setattr(
        mod.DimensionService, "_room_boundary_candidates",
        lambda self, room: list(original), raising=False)

    service = mod.GenericDimensions(object())
    service.FLOOR_EDGE_TOLERANCE_MM = 20.
    service.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES = 3.
    service.FLOOR_EDGE_MIN_OVERLAP_RATIO = .6
    railing_id = types.SimpleNamespace(Value=2002)
    service._nearby_guardrail_edges = lambda room, boundaries: [
        ((0., 3.62, 0., 0.), Ref("garde-corps"), railing_id, 3.)]
    service._existing_proxy_dimensions = lambda: []
    service._existing_dimension_reference_pairs = lambda: {
        frozenset(("droite", "garde-corps"))}
    room = types.SimpleNamespace(
        UniqueId="2238",
        get_Parameter=lambda p: FakeParameter("2238"))
    pending = service._room_boundary_candidates(room)
    # Le sens horizontal est déjà coté ; la paire haut/bas reste éligible.
    assert pending == [original[0], original[2]]
    assert original[3].source_kind == "guardrail_edge"
