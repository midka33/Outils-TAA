# -*- coding: utf-8 -*-
"""Régression : une cote en conflit ne doit pas interdire la cote valide."""

import sys
from pathlib import Path

# Export lance egalement tests/ ; ne pas dependre de son PYTHONPATH.
LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from annotations.strict_dimension_positioning import (
    SkippedPlacement,
    select_collision_free_placements,
)
from plans_vente.dimension_positioning import (
    DimensionPlacement,
    placement_candidates,
    placement_conflicts,
)

SETTINGS = dict(clearance=.3, text_width=.6, text_height=.15,
                padding=.015, witness_length=.075)


def inside(point):
    return 0 < point[0] < 6 and 0 < point[1] < 4


def fake_candidate(x, tag_hits=0, dim_hits=0, text_inside=True, outside=0):
    """Objet de test respectant la structure du calcul 06F."""
    class Candidate(object):
        pass
    item = Candidate()
    item.polygons = [[(x, 1.), (x+.1, 1.),
                      (x+.1, 1.1), (x, 1.1)]]
    item.text_polygons = list(item.polygons)
    item.tag_hits = tag_hits
    item.dimension_hits = dim_hits
    item.text_inside = text_inside
    item.outside_count = outside
    item.equipment_hits = 0
    item.clearance_penalty = 0
    item.rank = x
    item.warnings = []
    item.line_start = (x, 1.)
    item.line_end = (x+.1, 1.)
    return item


def test_collision_on_one_orientation_preserves_second_dimension():
    bad = fake_candidate(0., tag_hits=1)
    good = fake_candidate(2.)
    result = select_collision_free_placements([[bad], [good]])
    assert isinstance(result[0], SkippedPlacement)
    assert result[1] is good


def test_two_overlapping_dimensions_yield_only_one():
    a = fake_candidate(1.)
    b = fake_candidate(1.05)
    assert placement_conflicts(a, b) != (0, 0)
    result = select_collision_free_placements([[a], [b]])
    assert sum(not isinstance(x, SkippedPlacement) for x in result) == 1


def test_two_non_overlapping_dimensions_can_both_be_retained():
    a = fake_candidate(1.)
    b = fake_candidate(3.)
    result = select_collision_free_placements([[a], [b]])
    assert result == [a, b]


def test_existing_tag_and_dimension_obstacles_are_absolute():
    a = fake_candidate(1., tag_hits=1)
    b = fake_candidate(2., dim_hits=1)
    result = select_collision_free_placements([[a], [b]])
    assert all(isinstance(x, SkippedPlacement) for x in result)


def test_candidate_with_text_outside_room_is_skipped():
    a = fake_candidate(1., text_inside=False)
    b = fake_candidate(3.)
    result = select_collision_free_placements([[a], [b]])
    assert isinstance(result[0], SkippedPlacement)
    assert result[1] is b


def test_real_pdv_candidate_generation_can_reuse_strict_selection():
    points = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    lines = [((0., 2.), (6., 2.)), ((3., 0.), (3., 4.))]
    center_tag = (2.5, 1.6, 3.5, 2.4)
    groups = [placement_candidates(line, points, inside,
                                   tag_boxes=[center_tag], **SETTINGS)
              for line in lines]
    for group in groups:
        for c in group:
            c.text_inside = all(inside(point) for poly in c.text_polygons
                                for point in poly)
    chosen = select_collision_free_placements(groups)
    active = [x for x in chosen if not isinstance(x, SkippedPlacement)]
    assert len(active) >= 1
    assert all(c.tag_hits == 0 and c.dimension_hits == 0 for c in active)
    if len(active) == 2:
        assert placement_conflicts(active[0], active[1]) == (0, 0)



def test_two_complete_room_spans_can_cross_without_text_or_witness_overlap():
    """Deux mesures completes rectangulaires se croisent inevitablement."""
    horiz = DimensionPlacement((.2, 1.), (5.8, 1.),
                               .55, .07, .005, .02)
    vert = DimensionPlacement((1.4, .2), (1.4, 3.8),
                              .55, .07, .005, .02)
    assert placement_conflicts(horiz, vert) == (0, 1)
    chosen = select_collision_free_placements([[horiz], [vert]])
    assert chosen == [horiz, vert]


def test_intersection_au_niveau_du_texte_reste_interdite():
    horiz = DimensionPlacement((.2, 2.), (5.8, 2.),
                               .55, .07, .005, .02)
    vert = DimensionPlacement((3., .2), (3., 3.8),
                              .55, .07, .005, .02)
    assert placement_conflicts(horiz, vert)[0] == 1
    chosen = select_collision_free_placements([[horiz], [vert]])
    assert sum(not isinstance(c, SkippedPlacement) for c in chosen) == 1


def test_intersection_parallele_parfaite_et_chevauchement_restent_interdits():
    first = DimensionPlacement((.2, 2.), (5.8, 2.),
                               .55, .07, .005, .02)
    second = DimensionPlacement((1., 2.), (5., 2.),
                                .55, .07, .005, .02)
    chosen = select_collision_free_placements([[first], [second]])
    assert sum(not isinstance(c, SkippedPlacement) for c in chosen) == 1
