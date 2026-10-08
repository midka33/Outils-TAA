# -*- coding: utf-8 -*-
"""06F : géométrie réelle du placement, sans import de Revit."""
import math

import pytest

from plans_vente.dimension_geometry import dominant_dimension_pairs, segment_match_metrics
from plans_vente.dimension_positioning import (
    placement_candidates, placement_conflicts, select_placements,
)


SETTINGS = dict(clearance=.3, text_width=.6, text_height=.15,
                padding=.015, witness_length=.075)


def rectangle(width=6., height=4.):
    return [(0., 0.), (width, 0.), (width, height), (0., height)]


def contains_polygon(points):
    def contains(p):
        inside = False
        for a, b in zip(points, points[1:] + points[:1]):
            if (a[1] > p[1]) != (b[1] > p[1]):
                x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
                if p[0] < x:
                    inside = not inside
        return inside
    return contains


def pairs_for(points):
    segments = [a + b for a, b in zip(points, points[1:] + points[:1])]
    return dominant_dimension_pairs(segments)


def plan(points, lines=None, **kwargs):
    if lines is None:
        lines = [(p.line_start, p.line_end) for p in pairs_for(points)]
    return select_placements([placement_candidates(
        line, points, contains_polygon(points), **dict(SETTINGS, **kwargs)) for line in lines])


def test_rectangle_preserves_two_full_associative_spans_and_interior_placement():
    points = rectangle()
    result = plan(points)
    assert len(result) == 2
    assert all(c.outside_count == 0 for c in result)
    assert sorted(round(math.dist(c.line_start, c.line_end), 6) for c in result) == [4., 6.]
    assert [(c.line_start, c.line_end) for c in result] == [
        (c.line_start, c.line_end) for c in plan(points)]


def test_two_full_internal_rectangle_spans_report_unavoidable_crossing_away_from_text():
    result = plan(rectangle())
    assert placement_conflicts(*result) == (0, 1)
    assert any("croisement résiduel" in w for c in result for w in c.warnings)


def test_two_partial_spans_in_separate_l_arms_do_not_cross():
    points = [(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6)]
    result = plan(points, [((2, 1), (6, 1)), ((1, 2), (1, 6))])
    assert all(c.outside_count == 0 for c in result)
    assert placement_conflicts(*result) == (0, 0)


def test_central_tag_avoided_by_both_lines_texts_and_witnesses():
    tag = (2.5, 1.6, 3.5, 2.4)
    result = plan(rectangle(), tag_boxes=[tag])
    assert all(c.hits_boxes([tag]) == 0 for c in result)
    assert all(c.outside_count == 0 for c in result)


def test_small_room_reduces_wall_clearance_without_losing_spans():
    result = plan(rectangle(.8, .7), clearance=.5)
    assert len(result) == 2
    assert all(c.outside_count == 0 for c in result)
    assert any(c.rank > 1 for c in result)


def test_impossible_tiny_room_warns_without_silently_dropping_dimension():
    result = plan(rectangle(.3, .35))
    assert len(result) == 2
    assert any("emprise intérieure" in w for c in result for w in c.warnings)


def test_long_corridor_preserves_both_directions():
    result = plan(rectangle(15., 1.2))
    assert len(result) == 2
    assert all(c.outside_count == 0 for c in result)
    assert sorted(round(math.dist(c.line_start, c.line_end), 6) for c in result) == [1.2, 15.]


def test_l_room_uses_room_containment_not_just_its_bounding_box():
    points = [(0, 0), (6, 0), (6, 2), (2, 2), (2, 6), (0, 6)]
    result = plan(points, [((0, 3), (6, 3)), ((3, 0), (3, 6))])
    assert all(c.outside_count == 0 for c in result)
    assert result[0].line_start[1] < 2
    assert result[1].line_start[0] < 2


def test_nonorthogonal_parallel_walls_keep_orientation_and_span():
    angle = math.radians(28)
    def rotate(p):
        return (p[0] * math.cos(angle) - p[1] * math.sin(angle),
                p[0] * math.sin(angle) + p[1] * math.cos(angle))
    points = [rotate(p) for p in rectangle()]
    result = plan(points, text_axis=(math.cos(angle), math.sin(angle)))
    assert all(c.outside_count == 0 for c in result)
    for pair, placed in zip(pairs_for(points), result):
        assert math.dist(placed.line_start, placed.line_end) == pytest.approx(pair.distance)
        assert (placed.line_end[0] - placed.line_start[0], placed.line_end[1] - placed.line_start[1]) == pytest.approx(
            (pair.line_end[0] - pair.line_start[0], pair.line_end[1] - pair.line_start[1]))


def test_terrace_separator_floor_match_remains_independent_of_line_translation():
    separator = (0., 0., 6., 0.)
    edge = (0., .01, 6., .01)
    assert segment_match_metrics(separator, edge, distance_tolerance=.02) is not None
    result = plan(rectangle(), tag_boxes=[(2., 1.5, 4., 2.5)])
    assert len(result) == 2
    assert all(c.outside_count == 0 for c in result)
    assert separator == (0., 0., 6., 0.)  # Placement ne reçoit/modifie aucune référence.


def test_small_step_is_avoided_without_selecting_a_new_reference():
    points = [(0, 0), (6, 0), (6, 4), (3.1, 4), (3.1, 3.8),
              (2.9, 3.8), (2.9, 4), (0, 4)]
    result = plan(points, [((0, 3.9), (6, 3.9))])
    assert result[0].outside_count == 0
    assert result[0].line_start[1] < 3.8
    assert math.dist(result[0].line_start, result[0].line_end) == 6.


def test_best_side_avoids_equipment_and_existing_dimensions():
    result = plan(rectangle(), [((0, 1), (6, 1))],
                  equipment_boxes=[(.2, 0, 5.8, 2.5)],
                  dimension_boxes=[(0, 2.5, 6, 3.2)])
    assert result[0].line_start[1] > 3.2
    assert result[0].equipment_hits == result[0].dimension_hits == 0


def test_room_hole_changes_choice_even_without_an_obstacle_box():
    contains = contains_polygon(rectangle())
    def with_hole(p):
        return contains(p) and not (2 < p[0] < 4 and .1 < p[1] < 2.5)
    result = select_placements([placement_candidates(
        ((0, 1), (6, 1)), rectangle(), with_hole, **SETTINGS)])
    assert result[0].outside_count == 0
    assert result[0].line_start[1] > 2.5


def test_partial_curved_boundary_is_checked_by_real_contains_callback():
    points = [(0, 0), (6, 0), (6, 4), (0, 4)]
    def curved_room(p):
        return 0 < p[0] < 6 and 0 < p[1] < 3.5 + .5 * math.sin(math.pi * p[0] / 6)
    result = select_placements([placement_candidates(
        ((0, 3.8), (6, 3.8)), points, curved_room, **SETTINGS)])
    assert result[0].outside_count == 0


def test_tag_collision_includes_length_fallback_witness_lines():
    result = plan(rectangle(), [((0, .2), (6, .2))],
                  witness_anchors=((0, 0), (6, 0)),
                  tag_boxes=[(-.1, 1., .1, 2.)],
                  equipment_boxes=[(2., 0, 4., .4)])
    assert result[0].tag_hits == 0
    assert result[0].line_start[1] < 1.


def test_candidate_and_room_probe_budget_is_bounded():
    calls = []
    def contains(p):
        calls.append(p)
        return True
    candidates = placement_candidates(((0, 2), (6, 2)), rectangle(), contains,
                                      text_axis=(1, 0), **SETTINGS)
    assert len(candidates) <= 10
    assert len(calls) <= 290
    assert all(len(c.exclusion_boxes) <= 13 for c in candidates)


def test_inside_precedes_tag_avoidance_and_tags_precede_equipment():
    result = plan(rectangle(), [((0, 1), (6, 1))],
                  tag_boxes=[(0., 0., 6., 2.)], equipment_boxes=[(0., 2., 6., 4.)])
    assert result[0].outside_count == 0
    assert result[0].tag_hits == 0
    assert result[0].equipment_hits == 1
