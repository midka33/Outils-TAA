# -*- coding: utf-8 -*-
import math

import pytest

from plans_vente.dimension_geometry import (
    circulation_width_pairs, dominant_dimension_pairs, is_circulation_name,
)
from plans_vente.dimension_positioning import placement_candidates, select_placements


L_ROOM = [(0., 0.), (5.2, 0.), (5.2, 3.4), (4., 3.4), (4., 1.2), (0., 1.2)]


def segments(points):
    return [a + b for a, b in zip(points, points[1:] + points[:1])]


def inside_l(p):
    return (0 < p[0] < 5.2 and 0 < p[1] < 1.2) or (4 < p[0] < 5.2 and 0 < p[1] < 3.4)


def widths(points, contains):
    return circulation_width_pairs(segments(points), contains, .6, .3)


@pytest.mark.parametrize('name', ['Entrée/Dgt', 'ENTREE 1171', 'Dégagement', 'Dgt.',
                                  'Couloir', 'Circulation', 'Entrées', 'DÉGAGEMENT 2'])
def test_circulation_names_include_accented_and_combined_labels(name):
    assert is_circulation_name(name)


@pytest.mark.parametrize('name', ['Chambre 1', 'Séjour', 'Loggia', 'Cellier', 'Sdb',
                                  'Cuisine', 'Local entretien', '', None])
def test_other_rooms_keep_the_validated_selection_rule(name):
    assert not is_circulation_name(name)


def test_l_entrance_uses_two_branch_widths_instead_of_general_lengths():
    old = dominant_dimension_pairs(segments(L_ROOM))
    assert max(p.distance for p in old) == pytest.approx(5.2)
    result = widths(L_ROOM, inside_l)
    assert len(result) == 2
    assert [p.distance for p in result] == pytest.approx([1.2, 1.2])
    for pair in result:
        midpoint = tuple((a + b) / 2. for a, b in zip(pair.line_start, pair.line_end))
        assert inside_l(midpoint)


def test_straight_corridor_gets_one_transverse_width_and_no_length():
    points = [(0., 0.), (12., 0.), (12., 1.1), (0., 1.1)]
    result = widths(points, lambda p: 0 < p[0] < 12 and 0 < p[1] < 1.1)
    assert len(result) == 1
    assert result[0].distance == pytest.approx(1.1)
    assert result[0].line_start[0] == result[0].line_end[0]


def test_oblique_corridor_preserves_transverse_measure():
    angle = .42
    def rotate(p):
        return (p[0] * math.cos(angle) - p[1] * math.sin(angle),
                p[0] * math.sin(angle) + p[1] * math.cos(angle))
    def contains(p):
        x = p[0] * math.cos(angle) + p[1] * math.sin(angle)
        y = -p[0] * math.sin(angle) + p[1] * math.cos(angle)
        return 0 < x < 8 and 0 < y < 1.2
    result = widths([rotate(p) for p in [(0., 0.), (8., 0.), (8., 1.2), (0., 1.2)]], contains)
    assert len(result) == 1
    assert result[0].distance == pytest.approx(1.2)


def test_parallel_limits_across_exterior_are_not_accepted_as_widths():
    points = [(0., 0.), (6., 0.), (6., 1.2), (0., 1.2)]
    assert widths(points, lambda p: False) == []


def test_small_recess_is_not_mistaken_for_a_passage_width():
    points = [(0., 0.), (6., 0.), (6., 1.2), (0., 1.2)]
    boundaries = segments(points) + [(0., .2, .2, .2), (0., .4, .2, .4)]
    result = circulation_width_pairs(boundaries, lambda p: 0 < p[0] < 6 and 0 < p[1] < 1.2, .6, .3)
    assert len(result) == 1
    assert result[0].distance == pytest.approx(1.2)


def test_graphic_optimizer_keeps_each_width_in_its_own_l_branch():
    pairs = widths(L_ROOM, inside_l)
    groups = [placement_candidates(
        (p.line_start, p.line_end), p.placement_points, inside_l,
        clearance=.3, text_width=.6, text_height=.15, padding=.015,
        witness_length=.075, tag_boxes=[(1.5, .3, 2.5, .8)]) for p in pairs]
    result = select_placements(groups)
    assert len(result) == 2
    for pair, placed in zip(pairs, result):
        assert placed.outside_count == 0
        axis = pair.tangent
        projections = [p[0] * axis[0] + p[1] * axis[1] for p in pair.placement_points]
        position = placed.line_start[0] * axis[0] + placed.line_start[1] * axis[1]
        assert min(projections) <= position <= max(projections)
        assert math.dist(placed.line_start, placed.line_end) == pytest.approx(1.2)


def test_square_entrance_can_keep_two_equal_widths():
    points = [(0., 0.), (2., 0.), (2., 2.), (0., 2.)]
    assert len(widths(points, lambda p: 0 < p[0] < 2 and 0 < p[1] < 2)) == 2


def test_sampling_budget_is_bounded_even_for_many_parallel_segments():
    calls = []
    boundaries = [(0., y * .7, 100., y * .7) for y in range(100)]
    def blocked(p):
        calls.append(p)
        return False
    assert circulation_width_pairs(boundaries, blocked, .6, .3) == []
    assert len(calls) <= 1400



def test_local_width_is_preferred_over_larger_valid_span():
    # Régression A003 : deux paires parallèles peuvent être géométriquement
    # valides dans une entrée/dégagement, mais la grande portée ne doit pas
    # gagner simplement parce que son support longitudinal est un peu meilleur.
    boundaries = [
        (0.0, 0.0, 3.3, 0.0),
        (0.0, 2.7, 3.3, 2.7),   # grande portée 2,70 m
        (10.0, 10.0, 11.3, 10.0),
        (10.0, 11.2, 11.3, 11.2),  # largeur locale 1,20 m
    ]

    result = circulation_width_pairs(
        boundaries,
        lambda p: True,
        minimum_width=0.6,
        minimum_overlap=0.3,
    )

    assert len(result) == 1
    assert result[0].distance == pytest.approx(1.2)
