# -*- coding: utf-8 -*-
"""Vrai service 06F ; seules les frontières API Revit sont simulées."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import sys

import pytest


PANEL = Path(__file__).resolve().parents[2] / 'OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel'
spec = importlib.util.spec_from_file_location('pdv_dimension_adapter_06f',
                                               str(PANEL / 'services/dimension_service.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def xyz(x, y, z):
    return NS(X=x, Y=y, Z=z)


POINTS = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]


class Transaction(object):
    def __init__(self, *args):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


@pytest.fixture
def setup(monkeypatch):
    probes = []
    def inside(point):
        probes.append(point)
        return (12 < point.Z < 15 and 0 < point.X < 6 and 0 < point.Y < 4)
    room = NS(Name='Séjour', Number='1', Level=NS(Elevation=12.),
              IsPointInRoom=inside,
              get_BoundingBox=lambda view: NS(Min=xyz(0, 0, 12), Max=xyz(6, 4, 15)))
    view = NS(Name='PDV PROTO - A - Test', Scale=50, RightDirection=xyz(1, 0, 0))
    dtype = NS(Name='TAA')
    objects = dict(room=room, view=view, dtype=dtype)
    service = module.DimensionService(NS(GetElement=objects.get))
    service._single_level_name = lambda housing: 'R+3'
    validation = []
    service._validate_target_view = lambda *args: validation.append(args)
    service._is_linear_dimension_type = lambda dtype: True
    service._element_type_name = lambda dtype: dtype.Name
    service._view_obstacles = lambda *args: ([(2.5, 1.6, 3.5, 2.4)], [], [])
    service._placement_room_points = lambda room: POINTS
    service._millimeters_to_internal = lambda mm: mm / 1000.
    service._xyz = xyz
    service._graphic_box = lambda element, view: None
    boundaries = [module._BoundaryReferenceCandidate(
        a + b, object(), i, length_references=(object(), object()))
        for i, (a, b) in enumerate(zip(POINTS, POINTS[1:] + POINTS[:1]))]
    service._room_boundary_candidates = lambda room: boundaries
    created = []
    def create(*args):
        created.append(args)
        return object()
    service._create_dimension = create
    monkeypatch.setattr(module, 'RevitTransaction', Transaction)
    housing = NS(key='A', room_unique_ids=['room'])
    return NS(service=service, room=room, view=view, dtype=dtype, objects=objects,
              boundaries=boundaries, created=created, probes=probes,
              housing=housing, validation=validation)


def run(env):
    return env.service.create_dimensions(env.housing, 'view', 'dtype')


def test_real_create_path_preserves_floor_edge_identity_and_returns_reservations(setup):
    floor_reference = object()
    setup.boundaries[0].reference = floor_reference
    setup.boundaries[0].source_kind = 'floor_edge'
    setup.boundaries[0].length_references = None
    result = run(setup)
    assert result.created_count == 2
    assert result.full_room_count == 1
    assert any(floor_reference is ref for args in setup.created for ref in args[2:4])
    assert all(args[0] is setup.view and args[1] is setup.dtype for args in setup.created)
    assert result.exclusion_boxes and all(len(box) == 4 for box in result.exclusion_boxes)
    assert setup.validation == [(setup.view, 'A', 'R+3')]
    assert setup.probes and all(p.Z == 13.5 for p in setup.probes)
    assert not any('séparation' in warning for warning in result.warnings)


def test_separator_fallback_warning_survives_06f(setup):
    setup.boundaries[0].source_kind = 'separator'
    result = run(setup)
    assert result.created_count == 2
    assert any('La cote peut disparaître' in warning for warning in result.warnings)


def test_graphic_probe_failure_preserves_06e_count_and_reports_cause(setup):
    def fail(point):
        raise RuntimeError('probe unavailable')
    setup.room.IsPointInRoom = fail
    result = run(setup)
    assert result.created_count == 2
    assert any('probe unavailable' in warning and 'position 06E' in warning
               for warning in result.warnings)


def test_one_failed_reference_uses_length_fallback_without_losing_success(setup):
    original = setup.service._create_dimension
    calls = []
    def fail_once(*args):
        calls.append(args)
        if len(calls) == 1:
            raise RuntimeError('invalid reference')
        return original(*args)
    setup.service._create_dimension = fail_once
    result = run(setup)
    assert len(calls) == 3
    assert result.created_count == 2
    assert result.exclusion_boxes
    assert any('invalid reference' in warning for warning in result.warnings)


def test_rollback_does_not_publish_phantom_exclusion_boxes(setup, monkeypatch):
    class FailingTransaction(Transaction):
        def __exit__(self, *args):
            raise RuntimeError('rollback')
    monkeypatch.setattr(module, 'RevitTransaction', FailingTransaction)
    result = run(setup)
    assert result.created_count == 0
    assert result.exclusion_boxes == []
    assert result.skipped_room_count == 1


def test_failure_in_one_room_does_not_block_next_room(setup, monkeypatch):
    class FirstTransactionFails(Transaction):
        count = 0
        def __exit__(self, *args):
            FirstTransactionFails.count += 1
            if FirstTransactionFails.count == 1:
                raise RuntimeError('first room rollback')
            return False
    monkeypatch.setattr(module, 'RevitTransaction', FirstTransactionFails)
    setup.objects['room2'] = setup.room
    setup.housing.room_unique_ids.append('room2')
    result = run(setup)
    assert result.created_count == 2
    assert result.skipped_room_count == result.full_room_count == 1


def test_scale_conversion_doubles_paper_offsets(setup):
    def place():
        return setup.service._plan_graphics(setup.room, setup.view,
            [((0, 1), (6, 1))], [None], [], [], [], [])[0]
    at_50 = place()
    setup.view.Scale = 100
    at_100 = place()
    assert abs(at_100.line_start[1] - 2.) > 0  # Position intérieure, hors axe central.
    assert min(at_100.line_start[1], 4 - at_100.line_start[1]) == pytest.approx(
        2 * min(at_50.line_start[1], 4 - at_50.line_start[1]))


def test_actual_dimension_bbox_is_exposed_after_creation(setup):
    box = (1., 1., 5., 3.)
    setup.service._graphic_box = lambda *args: box
    result = run(setup)
    assert box in result.exclusion_boxes
    assert any('contrôler le texte et les témoins' in w for w in result.warnings)


def test_bbox_transform_uses_all_corners_in_world_xy(setup):
    element = NS(get_BoundingBox=lambda view: NS(
        Min=xyz(0, 0, 0), Max=xyz(2, 1, 3),
        Transform=NS(OfPoint=lambda p: xyz(-p.Y + 10, p.X + 20, p.Z))))
    assert module.DimensionService._graphic_box(setup.service, element, setup.view) == (9, 20, 10, 22)


def test_floor_edge_match_uses_exact_06e_tolerances_before_graphic_placement(setup):
    edge_ref = object()
    setup.service._floor_edges_for_room = lambda room: [
        ((0, .1, 6, .1), object(), 2, 12.),  # trop loin
        ((0, .01, 2, .01), object(), 3, 12.),  # trop court
        ((0, .01, 6, .01), edge_ref, 4, 12.)]
    curve = NS(GetEndPoint=lambda i: xyz(6 * i, 0, 12))
    assert setup.service._matching_floor_edge_reference(setup.room, curve) == (edge_ref, 4)


def test_visible_obstacle_collector_reads_target_view_categories_without_roomtag_class(setup, monkeypatch):
    collected = []
    element = NS(Category=NS(Id=2), IsHidden=lambda view: False)
    hidden = NS(Category=NS(Id=2), IsHidden=lambda view: True)
    class Collector(object):
        def __init__(self, document, view_id):
            assert view_id == 123
        def OfCategory(self, category):
            collected.append(category)
            self.category = category
            return self
        def WhereElementIsNotElementType(self):
            return self
        def ToElements(self):
            return [element, hidden]
    names = ('OST_RoomTags', 'OST_Dimensions', 'OST_PlumbingFixtures', 'OST_Furniture',
             'OST_Casework', 'OST_MechanicalEquipment', 'OST_SpecialityEquipment', 'OST_ElectricalEquipment')
    db = NS(BuiltInCategory=NS(**{name: name for name in names}), FilteredElementCollector=Collector)
    monkeypatch.setitem(sys.modules, 'Autodesk', NS())
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit', NS())
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', db)
    setup.view.Id = 123
    setup.view.GetCategoryHidden = lambda category: False
    setup.service._graphic_box = lambda *args: (0, 0, 1, 1)
    warnings = []
    tags, dimensions, equipment = module.DimensionService._view_obstacles(setup.service, setup.view, warnings)
    assert collected == list(names)
    assert len(tags) == len(dimensions) == 1
    assert len(equipment) == 6
    assert not warnings


def test_native_text_and_stage05_tags_are_not_mutated_and_new_module_reloads_first():
    service = (PANEL / 'services/dimension_service.py').read_text()
    script = (PANEL / 'PlansDeVente.pushbutton/script.py').read_text()
    assert 'TextPosition =' not in service
    assert 'ValueOverride' not in service
    assert 'TagHeadPosition' not in service
    assert 'SetCategoryHidden' not in service
    assert script.index('_reload_module(_dimension_positioning)') < script.index('_reload_module(_dimension_service)')
