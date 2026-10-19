# -*- coding: utf-8 -*-
"""Execute source adapters and V1 services with simulated Revit boundaries only."""
import importlib.util
import math
from pathlib import Path
import sys
from types import SimpleNamespace as NS

import pytest

from plans_vente.source_room import (SourceRoom, bounds_to_host, point_to_host,
                                    point_to_source, room_inputs, resolve_room,
                                    host_level_name)
from plans_vente.housing import RoomSnapshot, Housing
from plans_vente.housing_grouper import HousingGrouper
from plans_vente.multilevel import split_housing_by_level

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / 'OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel/services'


def service_module(name):
    spec = importlib.util.spec_from_file_location('linked_test_' + name, SERVICES / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Id:
    def __init__(self, value):
        self.Value = value.Value if isinstance(value, Id) else value
    def __eq__(self, other):
        return isinstance(other, Id) and self.Value == other.Value
    def __hash__(self):
        return hash(self.Value)


def xyz(x, y, z):
    return NS(X=x, Y=y, Z=z)


class Transform:
    def __init__(self, angle=0, shift=(0, 0, 0), mirror=False):
        c, s = math.cos(angle), math.sin(angle)
        sign = -1 if mirror else 1
        self.m = ((sign*c, -s), (sign*s, c))
        self.shift = shift
        self.BasisZ = xyz(0, 0, 1)
    def OfPoint(self, p):
        a, b = self.m
        return xyz(a[0]*p.X+a[1]*p.Y+self.shift[0], b[0]*p.X+b[1]*p.Y+self.shift[1], p.Z+self.shift[2])
    @property
    def Inverse(self):
        inverse = Transform()
        a, b = self.m
        inverse.m = ((a[0], b[0]), (a[1], b[1]))
        point = inverse.OfPoint(xyz(*[-v for v in self.shift]))
        inverse.shift = (point.X, point.Y, point.Z)
        return inverse


class Curve:
    def __init__(self, start, end):
        self.start, self.end = start, end
    def GetEndPoint(self, index):
        return (self.start, self.end)[index]
    def Tessellate(self):
        return [self.start, self.end]
    def CreateTransformed(self, transform):
        return Curve(transform.OfPoint(self.start), transform.OfPoint(self.end))


class Document:
    def __init__(self, title='SITE', elements=None):
        self.Title = title
        self.elements = elements or {}
    def GetElement(self, key):
        return self.elements.get(key)


def raw_room(uid='r1', level='RDC', z=0, value='101', area=20):
    points = [xyz(0, 0, z), xyz(6, 0, z), xyz(6, 4, z), xyz(0, 4, z)]
    segments = [NS(GetCurve=lambda a=a, b=b: Curve(a, b))
                for a, b in zip(points, points[1:]+points[:1])]
    return NS(UniqueId=uid, Name='Séjour', Number='1', Id=Id(42), Area=area,
              Level=NS(Name=level, Elevation=z, ProjectElevation=z, Id=Id(10)),
              LevelId=Id(10), Location=NS(Point=xyz(3, 2, z)), Parameters=[], value=value,
              GetBoundarySegments=lambda options: [segments],
              IsPointInRoom=lambda p: 0 <= p.X <= 6 and 0 <= p.Y <= 4 and z <= p.Z <= z+3,
              get_BoundingBox=lambda view: NS(Min=xyz(0, 0, z), Max=xyz(6, 4, z+3)),
              LookupParameter=lambda name: NS(AsString=lambda: {'Bâtiment': 'B', 'Typologie': 'T3'}.get(name, '')))


def linked(number=1, room=None, transform=None, document=None):
    link = NS(UniqueId='link-unique-{}'.format(number), Id=Id(number))
    return SourceRoom(document or Document('BATIMENT'), room or raw_room(), link,
                      transform or Transform(shift=(100, 200, 10)), 'Bâtiment [instance {}]'.format(number))


def snapshot(source, value='101'):
    return RoomSnapshot(source.UniqueId, housing_key=value, level_name=source.room_element.Level.Name,
                        source_room=source, include_links=True)


def housing(source):
    return HousingGrouper().group([snapshot(source)], 'Logement').housings[0]


@pytest.fixture
def db(monkeypatch):
    database = NS(XYZ=xyz, ElementId=Id, BoundingBoxXYZ=lambda: NS(),
                  SpatialElementBoundaryOptions=lambda: NS(),
                  SpatialElementBoundaryLocation=NS(Finish='finish'),
                  LinkElementId=lambda *ids: ids, UV=lambda u, v: NS(U=u, V=v))
    monkeypatch.setitem(sys.modules, 'Autodesk', NS())
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit', NS())
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', database)
    return database


@pytest.mark.parametrize('angle,mirror', [(0, False), (math.pi/2, False), (0.63, False), (0.63, True)])
def test_point_round_trip_and_bbox_all_corners(angle, mirror):
    transform = Transform(angle, (100, -30, 12), mirror)
    point = xyz(2, 7, 3)
    back = point_to_source(point_to_host(point, transform), transform)
    assert (back.X, back.Y, back.Z) == pytest.approx((2, 7, 3))
    box = NS(Min=xyz(0, 0, 0), Max=xyz(6, 4, 3))
    lo, hi = bounds_to_host(box, transform, xyz)
    for x in (0, 6):
        for y in (0, 4):
            for z in (0, 3):
                p = transform.OfPoint(xyz(x, y, z))
                assert lo.X-1e-9 <= p.X <= hi.X+1e-9
                assert lo.Y-1e-9 <= p.Y <= hi.Y+1e-9
                assert lo.Z <= p.Z <= hi.Z


def test_source_room_exposes_host_geometry_but_reads_source_parameters(db):
    source = linked(transform=Transform(math.pi/2, (100, 200, 10)))
    curve = source.GetBoundarySegments(None)[0][0].GetCurve()
    assert (curve.end.X, curve.end.Y, curve.end.Z) == pytest.approx((100, 206, 10))
    assert source.IsPointInRoom(xyz(98, 203, 11))
    assert not source.IsPointInRoom(xyz(3, 2, 1))
    assert source.Level.ProjectElevation == 10
    assert source.Location.Point.X == 98
    assert source.Area == 20
    assert source.LookupParameter('Bâtiment').AsString() == 'B'
    assert source.get_BoundingBox(None).Min.X == 96


def test_identity_includes_link_instance_even_for_same_document_and_room():
    doc = Document('BATIMENT')
    one, two = linked(1, document=doc), linked(2, document=doc)
    host = RoomSnapshot('r1', housing_key='101', level_name='RDC')
    result = HousingGrouper().group([host, snapshot(one), snapshot(two)], 'Logement')
    assert len(result.housings) == 3
    assert len({h.identity for h in result.housings}) == 3
    assert len({h.key for h in result.housings}) == 3
    assert {h.display_key for h in result.housings} == {'101'}
    assert len({r for h in result.housings for r in h.room_unique_ids}) == 3


def test_host_room_resolution_remains_exactly_v1():
    room = raw_room()
    document = Document(elements={'r1': room})
    h = Housing('101', [RoomSnapshot('r1', housing_key='101')])
    assert room_inputs(h) == ['r1']
    assert resolve_room(document, room_inputs(h)[0]) is room
    source = linked()
    assert resolve_room(document, source) is source


def test_multilevel_split_retains_instance_source_filter_and_total_areas(db):
    one = linked(room=raw_room('low', 'N0', area=20))
    two = linked(room=raw_room('high', 'N1', z=10, area=30))
    h = HousingGrouper().group([snapshot(one), snapshot(two)], 'Logement').housings[0]
    levels = split_housing_by_level(h)
    assert len(levels) == 2
    assert all(level.source_key == one.source_key and level.include_links for level in levels)
    assert all(level.filter_key == '101' for level in levels)
    assert sum(resolve_room(None, r).Area for level in levels for r in room_inputs(level)) == 50
    assert len({level.key for level in levels}) == 2


def test_collector_caches_source_document_and_skips_unloaded_and_bad_links():
    module = service_module('room_collector_service')
    host, source = Document(), Document('BATIMENT')
    calls = []
    class Collector:
        def __init__(self, document):
            calls.append(document)
            self.doc = document
        def OfCategory(self, category): return self
        def WhereElementIsNotElementType(self): return self
        def ToElements(self): return [raw_room()]
    gets = []
    def link(index, doc):
        def get():
            gets.append(index)
            if isinstance(doc, Exception): raise doc
            return doc
        return NS(UniqueId='link-{}'.format(index), Id=Id(index), Name='Lien {}'.format(index),
                  GetLinkDocument=get, GetTotalTransform=lambda: Transform(shift=(index*10, 0, 0)))
    service = module.RoomCollectorService(host, Collector, 'rooms')
    rooms = service.collect_source_rooms([link(1, source), link(2, None), link(3, RuntimeError('erreur')), link(4, source)])
    assert len(rooms) == 3
    assert calls == [host, source]
    assert gets == [1, 2, 3, 4]
    assert len(service.warnings) == 2
    assert 'déchargé' in service.warnings[0]
    assert rooms[1].transform_to_host.shift[0] == 10
    assert rooms[2].transform_to_host.shift[0] == 40


def test_analysis_filters_same_numbers_by_source_and_option_off_never_collects_links(db):
    module = service_module('housing_analysis_service')
    calls = []
    host = raw_room(uid='host', value='101')
    one, two = linked(1), linked(2)
    parameters = NS(get_text_parameter_descriptors=lambda rooms: [],
                    read_text_value=lambda room, descriptor, default='': room.value if descriptor.name == 'Logement' else room.source_name)
    collector = NS(collect_all_rooms=lambda: calls.append('host') or [host],
                   collect_source_rooms=lambda: calls.append('links') or [host, one, two], warnings=['déchargé'])
    service = module.HousingAnalysisService(collector, parameters, HousingGrouper())
    descriptor = NS(name='Logement')
    service.load_context(False)
    result = service.analyze(descriptor)
    assert calls == ['host'] and len(result.housings) == 1 and result.housings[0].key == '101'
    assert not result.housings[0].include_links
    context = service.load_context(True)
    result = service.analyze(descriptor)
    assert context.warnings == ['déchargé']
    assert len(result.housings) == 3
    selected = service.filter_housings(result.housings[1:], NS(name='Source'), 'contains', 'instance 2')
    assert [h.source_key for h in selected] == [two.source_key]
    service.load_context(False)
    assert not service._context.warnings and len(service.analyze(descriptor).housings) == 1


def test_parameter_discovery_samples_each_document_once():
    module = service_module('room_parameter_service')
    service = module.RoomParameterService()
    counts = []
    def descriptor(p):
        counts.append(p)
        return NS(identity_key=p, name=p, storage_type='String')
    service.create_descriptor = descriptor
    host = [NS(Parameters=['host']) for _ in range(20)]
    document = Document('LINK')
    sources = [NS(source_document=document, Parameters=['link']) for _ in range(30)]
    result = service.get_text_parameter_descriptors(host+sources)
    assert counts.count('host') == counts.count('link') == 8
    assert {d.name for d in result} == {'host', 'link'}


def test_project_parameter_name_fallback_is_only_unambiguous_linked_text():
    module = service_module('room_parameter_service')
    service = module.RoomParameterService()
    descriptor = NS(identity_kind='DEFINITION', identity_key='host-def', name='Logement')
    value = NS(StorageType='String')
    service.create_descriptor = lambda p: NS(identity_key='link-def')
    source = NS(source_kind='linked', GetParameters=lambda name: [value])
    assert service.get_parameter(source, descriptor) is value
    source.GetParameters = lambda name: [value, value]
    assert service.get_parameter(source, descriptor) is None
    source.GetParameters = lambda name: [value]
    source.source_kind = 'host'
    assert service.get_parameter(source, descriptor) is None


def test_host_levels_use_transformed_project_elevation_not_same_name(db):
    source = linked()
    h = housing(source)
    levels = [NS(Name='RDC', ProjectElevation=0), NS(Name='SITE +3', ProjectElevation=10)]
    db.Level = object()
    db.FilteredElementCollector = lambda doc: NS(OfClass=lambda cls: NS(ToElements=lambda: levels))
    assert host_level_name(h, Document()) == 'SITE +3'
    levels.append(NS(Name='Ambigu', ProjectElevation=10))
    with pytest.raises(ValueError, match='ambigu'):
        host_level_name(h, Document())
    levels[:] = [NS(Name='RDC', ProjectElevation=0)]
    with pytest.raises(ValueError, match='absent'):
        host_level_name(h, Document())


def test_real_crop_adapter_receives_link_transformed_boundary(db):
    service = service_module('crop_geometry_service').CropGeometryService(Document())
    source = linked(transform=Transform(math.pi/2, (100, 200, 10)))
    points = service._collect_boundary_points(room_inputs(housing(source)))
    assert len(points) == 8
    assert min(p[0] for p in points) == 96
    assert max(p[1] for p in points) == 206
    assert {p[2] for p in points} == {10}


def test_tag_creation_uses_instance_room_pair_and_host_position(db):
    module = service_module('room_tag_service')
    calls = []
    tag = NS(IsInRoom=True)
    document = NS(Create=NS(NewRoomTag=lambda *args: calls.append(args) or tag), Regenerate=lambda: None)
    service = module.RoomTagService(document)
    service._bounding_box_2d = lambda tag, view: (97, 202, 99, 204)
    service._tag_box_inside_room = lambda *args: True
    service._set_tag_head_position = lambda *args: None
    source = linked(transform=Transform(math.pi/2, (100, 200, 10)))
    service._place_one_tag(source, NS(Id=Id(99)), object(), [(98, 203)], 11, [], 0)
    assert calls[0][0] == (source.revit_link_instance.Id, source.Id)
    assert (calls[0][1].U, calls[0][1].V) == (98, 203)
    assert calls[0][2] == Id(99)


def test_tag_duplicate_identity_separates_host_and_link_instances():
    service = service_module('room_tag_service').RoomTagService(Document())
    tags = [NS(TaggedLocalRoomId=Id(42)),
            NS(TaggedRoomId=NS(LinkInstanceId=Id(2), LinkedElementId=Id(42)))]
    ids = service._already_tagged_room_ids(tags)
    assert service._room_tag_identity(linked(1)) not in ids
    assert service._room_tag_identity(linked(2)) in ids
    assert service._room_tag_identity(raw_room()) in ids


def test_dimension_candidates_lift_native_references_and_numeric_geometry(db):
    module = service_module('dimension_service')
    source = linked(transform=Transform(math.pi/2, (100, 200, 10)))
    calls = []
    class Ref:
        def CreateLinkReference(self, instance):
            calls.append(instance)
            return ('host-reference', instance.Id.Value)
    candidate = module._BoundaryReferenceCandidate((0, 0, 6, 0), Ref(), 77, (Ref(), Ref()), 'floor_edge')
    service = module.DimensionService(Document())
    service._linked_services[source.source_key] = NS(_room_boundary_candidates=lambda raw: [candidate])
    warnings = []
    result = service._linked_boundary_candidates(source, warnings)
    assert result[0].segment == pytest.approx((100, 200, 100, 206))
    assert result[0].reference == ('host-reference', 1)
    assert result[0].length_references == (('host-reference', 1), ('host-reference', 1))
    assert result[0].source_kind == 'floor_edge'
    assert len(calls) == 3 and not warnings


def test_link_dimension_reference_failure_is_reported_not_replaced_by_host_id(db):
    module = service_module('dimension_service')
    source = linked()
    class BadRef:
        def CreateLinkReference(self, instance): raise RuntimeError('API refus')
    candidate = module._BoundaryReferenceCandidate((0, 0, 6, 0), BadRef(), 77)
    service = module.DimensionService(Document())
    service._linked_services[source.source_key] = NS(_room_boundary_candidates=lambda raw: [candidate])
    warnings = []
    assert service._linked_boundary_candidates(source, warnings) == []
    assert source.source_name in warnings[0] and 'API refus' in warnings[0]


def test_cartouche_reads_source_metadata_and_multilevel_order(db):
    module = service_module('full_generation_service')
    service = module.FullGenerationService.__new__(module.FullGenerationService)
    service.document = Document()
    one, two = linked(room=raw_room('low', 'Niveau 0')), linked(room=raw_room('high', 'Niveau 1', 10))
    h = HousingGrouper().group([snapshot(one), snapshot(two)], 'Logement').housings[0]
    metadata, warnings = service._room_metadata(h, 'Bâtiment', 'Typologie', 'host-view')
    assert metadata['building'] == 'B' and metadata['typology'] == 'T3'
    assert metadata['floor'] == '0 / 1'
    assert not warnings
    levels = sorted(split_housing_by_level(h), key=service._level_sort_value)
    assert [level.level_names for level in levels] == [['Niveau 0'], ['Niveau 1']]


def test_linked_failure_contains_source_housing_and_last_real_stage():
    module = service_module('plans_vente_controller')
    controller = module.PlansVenteController.__new__(module.PlansVenteController)
    h = housing(linked())
    events = []
    def failing(housing, progress_callback):
        progress_callback(0.5, 'Cotations', 'Traitement', 'En cours')
        raise ValueError('référence refusée')
    with pytest.raises(RuntimeError, match='étape Cotations') as caught:
        controller._generate_with_source_context(failing, h, progress_callback=lambda *args: events.append(args))
    assert h.source_name in str(caught.value) and '101' in str(caught.value)
    assert events == [(0.5, 'Cotations', 'Traitement', 'En cours')]


class Definition:
    def __init__(self, include=True, category=1):
        self.IncludeLinkedFiles = include
        self.CategoryId = Id(category)
        self.fields = {1: NS(FieldId=1, FieldType='Instance', ParameterId=Id(99), IsHidden=False)}
        self.filters = [NS(FieldId=1, FilterType='Equal', value='Habitable')]
        self.IsItemized = False
        self.ShowGrandTotal = True
    def GetFieldOrder(self): return list(self.fields)
    def GetField(self, key): return self.fields[key]
    def GetFilterCount(self): return len(self.filters)
    def GetFilter(self, index): return self.filters[index]
    def RemoveFilter(self, index): self.filters.pop(index)
    def AddFilter(self, value): self.filters.append(value)
    def CanFilterByValue(self, key): return True
    def AddField(self, kind, parameter):
        key = max(self.fields)+1
        field = NS(FieldId=key, FieldType=kind, ParameterId=parameter, IsHidden=False)
        self.fields[key] = field
        return field


@pytest.fixture
def schedules(db):
    db.BuiltInCategory = NS(OST_Rooms=1)
    db.BuiltInParameter = NS(RVT_LINK_INSTANCE_NAME=11, RVT_LINK_FILE_NAME_WITHOUT_EXT=12)
    db.ScheduleFieldType = NS(RevitLinkInstance='LinkInstance', RevitLinkType='LinkType')
    db.ScheduleFilterType = NS(Equal='Equal')
    db.ScheduleFilter = lambda field, kind, value: NS(FieldId=field, FilterType=kind, value=value)
    module = service_module('schedule_service')
    service = module.ScheduleService(Document())
    service._link_schedule_identities = {'link-unique-1': ('BATIMENT_A', 'Instance A'),
                                         'link-unique-2': ('BATIMENT_B', 'Instance B')}
    return service


def test_schedule_native_filters_isolate_source_and_preserve_totals(schedules):
    definition = Definition()
    original_filter = definition.filters[0]
    schedule = NS(Definition=definition, Name='Surfaces')
    schedules._apply_source_filter(schedule, housing(linked(1)))
    assert definition.IncludeLinkedFiles
    assert definition.IsItemized is False and definition.ShowGrandTotal is True
    assert definition.filters[0] is original_filter
    assert [f.value for f in definition.filters[1:]] == ['BATIMENT_A', 'Instance A']
    assert all(field.IsHidden for key, field in definition.fields.items() if key != 1)
    # A model's inherited source filters are replaced, not intersected with B.
    schedules._apply_source_filter(schedule, housing(linked(2)))
    assert [f.value for f in definition.filters[1:]] == ['BATIMENT_B', 'Instance B']
    assert len(definition.fields) == 3


def test_schedule_missing_native_link_option_fails_with_instruction(schedules):
    schedule = NS(Definition=Definition(include=False), Name='Surfaces')
    with pytest.raises(ValueError, match='Inclure les éléments'):
        schedules._apply_source_filter(schedule, housing(linked()))
    assert not schedule.Definition.IncludeLinkedFiles


def test_schedule_duplicate_instance_names_fail_closed(schedules):
    schedules._link_schedule_identities['link-unique-2'] = ('BATIMENT_A', 'Instance A')
    with pytest.raises(ValueError, match='ambigu'):
        schedules._source_schedule_values(linked(1))
    schedules._link_schedule_identities['link-unique-1'] = ('BATIMENT_A', '')
    with pytest.raises(ValueError, match='vide'):
        schedules._source_schedule_values(linked(1))


def test_host_schedule_only_excludes_links_when_option_enabled(schedules):
    schedule = NS(Definition=Definition(), Name='Surfaces')
    h = Housing('101', [RoomSnapshot('host', housing_key='101')])
    schedules._apply_source_filter(schedule, h)
    assert schedule.Definition.IncludeLinkedFiles
    h.rooms[0].include_links = True
    schedules._apply_source_filter(schedule, h)
    assert not schedule.Definition.IncludeLinkedFiles


def test_non_room_model_schedule_is_preserved(schedules):
    schedule = NS(Definition=Definition(category=2), Name='Informations')
    schedules._apply_source_filter(schedule, housing(linked()))
    assert len(schedule.Definition.filters) == 1


def test_level_sort_handles_nonnumeric_linked_levels(db):
    module = service_module('full_generation_service')
    service = module.FullGenerationService.__new__(module.FullGenerationService)
    high = housing(linked(room=raw_room(level='Mezzanine', z=10)))
    low = housing(linked(room=raw_room(level='Rez-de-jardin', z=0)))
    assert sorted([high, low], key=service._level_sort_value) == [low, high]


def test_native_dimension_creation_receives_host_z_and_link_references(db):
    module = service_module('dimension_service')
    db.Line = NS(CreateBound=lambda a, b: (a, b))
    class References(list):
        def Append(self, ref): self.append(ref)
    db.ReferenceArray = References
    calls = []
    document = NS(Create=NS(NewDimension=lambda *args: calls.append(args) or 'dimension'))
    service = module.DimensionService(document)
    source = linked()
    assert service._create_dimension('view', 'type', 'link-ref-a', 'link-ref-b', (100, 200), (106, 200), source) == 'dimension'
    assert calls[0][1][0].Z == calls[0][1][1].Z == 10
    assert calls[0][2] == ['link-ref-a', 'link-ref-b']


def test_location_plan_uses_same_transformed_crop_input():
    # Executable extraction of the orchestration's call, no duplicated geometry engine.
    import ast
    text = (SERVICES/'location_plan_service.py').read_text()
    tree = ast.parse(text)
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'build_optimized_crop']
    assert len(calls) == 1
    expression = ast.Expression(calls[0].args[0])
    source = linked()
    actual = eval(compile(expression, '<location inputs>', 'eval'), {'room_inputs': room_inputs, 'housing': housing(source)})
    assert actual == [source]


def test_checkbox_and_source_binding_have_canonical_handlers():
    import ast
    import xml.etree.ElementTree as ET
    ui = SERVICES.parent / 'ui'
    xaml = ET.fromstring((ui/'plans_vente_final.xaml').read_text())
    ns = '{http://schemas.microsoft.com/winfx/2006/xaml}'
    checkbox = next(element for element in xaml.iter() if element.attrib.get(ns+'Name') == 'IncludeLinksCheck')
    assert checkbox.attrib['IsChecked'] == 'False'
    tree = ast.parse((ui/'plans_vente_final_window.py').read_text())
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == checkbox.attrib['Click']]
    assert len(handlers) == 1
    row = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'HousingRow')
    space = {}
    exec(compile(ast.Module(body=[row], type_ignores=[]), '<housing row>', 'exec'), space)
    value = space['HousingRow'](housing(linked()))
    assert value.Key == '101' and value.Source == 'Bâtiment [instance 1]'


def test_output_name_collision_is_never_silently_skipped_as_an_existing_plan():
    host = RoomSnapshot('host', housing_key='101-L1', level_name='RDC')
    with pytest.raises(ValueError, match='Collision'):
        HousingGrouper().group([host, snapshot(linked(1))], 'Logement')


def test_stale_link_room_fails_before_host_document_lookup():
    source = linked()
    source.room_element.IsValidObject = False
    with pytest.raises(ValueError, match='relancer'):
        resolve_room(Document(), source)


def test_native_link_schedule_identity_is_read_once_per_analysis(db):
    module = service_module('schedule_service')
    db.BuiltInParameter = NS(RVT_LINK_INSTANCE_NAME=11, RVT_LINK_FILE_NAME_WITHOUT_EXT=12)
    db.RevitLinkInstance = object()
    calls = []
    link_type = NS(get_Parameter=lambda p: NS(AsString=lambda: 'BATIMENT'))
    document = Document(elements={Id(100): link_type})
    links = [NS(UniqueId='link-unique-{}'.format(i), GetTypeId=lambda: Id(100),
                get_Parameter=lambda p, i=i: NS(AsString=lambda: 'Instance {}'.format(i))) for i in (1, 2)]
    db.FilteredElementCollector = lambda doc: calls.append(doc) or NS(OfClass=lambda cls: NS(ToElements=lambda: links))
    service = module.ScheduleService(document)
    assert service._source_schedule_values(linked(1)) == ('BATIMENT', 'Instance 1')
    assert service._source_schedule_values(linked(2)) == ('BATIMENT', 'Instance 2')
    assert calls == [document]


def test_schedule_project_parameter_bridge_requires_unique_name_and_link_origin():
    service = service_module('schedule_service').ScheduleService(Document())
    service._field_matches_descriptor = lambda field, descriptor: False
    fields = {1: NS(GetName=lambda: 'Logement'), 2: NS(GetName=lambda: 'Autre')}
    definition = NS(GetFieldOrder=lambda: list(fields), GetField=fields.get)
    descriptor = NS(name='Logement', identity_kind='DEFINITION', source_kind='linked')
    assert service._find_housing_field_id(definition, descriptor) == 1
    descriptor.source_kind = 'host'
    assert service._find_housing_field_id(definition, descriptor) is None
    descriptor.source_kind = 'linked'
    fields[2].GetName = lambda: 'Logement'
    assert service._find_housing_field_id(definition, descriptor) is None


def test_default_revit_link_collection_reports_nested_and_tilted_links(db):
    module = service_module('room_collector_service')
    host, source = Document(), Document('BATIMENT')
    link_class = object()
    db.RevitLinkInstance = link_class
    tilted = Transform()
    tilted.BasisZ = xyz(0.2, 0, 0.98)
    def link(i, transform):
        return NS(UniqueId='link-{}'.format(i), Id=Id(i), Name='Lien {}'.format(i),
                  GetLinkDocument=lambda: source, GetTotalTransform=lambda: transform)
    links = [link(1, Transform()), link(2, tilted)]
    class Collector:
        def __init__(self, doc): self.doc, self.cls = doc, None
        def OfClass(self, cls): self.cls = cls; return self
        def OfCategory(self, cat): return self
        def WhereElementIsNotElementType(self): return self
        def ToElements(self): return links if self.doc is host and self.cls is link_class else [raw_room()]
        def GetElementCount(self): return 1
    db.FilteredElementCollector = Collector
    service = module.RoomCollectorService(host, Collector, 'rooms')
    result = service.collect_source_rooms()
    assert len(result) == 2
    assert any('imbriqué' in w for w in service.warnings)
    assert any('incliné' in w for w in service.warnings)


def test_linked_crop_read_failure_is_not_silently_replaced_by_other_rooms(db):
    module = service_module('crop_geometry_service')
    source = linked()
    def broken(options): raise RuntimeError('géométrie source inaccessible')
    source.room_element.GetBoundarySegments = broken
    service = module.CropGeometryService(Document())
    with pytest.raises(RuntimeError, match='source inaccessible'):
        service._collect_boundary_points([linked(2), source])
