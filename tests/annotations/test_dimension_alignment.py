# -*- coding: utf-8 -*-
"""Alignement optionnel des cotes sur les rails voisins, sans collision."""

import math
import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from annotations.dimension_alignment import (
    matching_rails, aligned_candidates, alignment_penalty)
from annotations.strict_dimension_positioning import (
    select_collision_free_placements, SkippedPlacement)
from plans_vente.dimension_positioning import placement_candidates

SETTINGS = dict(
    clearance=.3, text_width=.6, text_height=.15, padding=.015,
    witness_length=.075)


def contains(point):
    return 0. < point[0] < 6. and 0. < point[1] < 4.


def setup_positions(rail, tag_boxes=()):
    line = ((0., 1.7), (6., 1.7))
    room = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    standard = placement_candidates(
        line, room, contains, tag_boxes=tag_boxes, **SETTINGS)
    for candidate in standard:
        candidate.text_inside = all(
            contains(p) for polygon in candidate.text_polygons
            for p in polygon)
    extra = aligned_candidates(
        line, room, [rail], contains, SETTINGS, tag_boxes=tag_boxes,
        max_neighbor_gap=1.)
    return standard, extra


def test_rail_voisin_donne_position_exactement_colineaire():
    rail = ((6.2, 1.4), (9.8, 1.4))
    standard, extra = setup_positions(rail)
    assert len(extra) == 1
    assert abs(extra[0].line_start[1] - 1.4) < 1e-8
    assert alignment_penalty(extra[0], [rail], 1., .001) == 0
    chosen = select_collision_free_placements(
        [standard + extra], rails=[rail], max_neighbor_gap=1.,
        snap_tolerance=.001)
    assert abs(chosen[0].line_start[1] - 1.4) < 1e-8


def test_l_alignement_ne_force_pas_une_collision_avec_etiquette():
    rail = ((6.2, 1.4), (9.8, 1.4))
    tag = (2.5, 1.28, 3.5, 1.55)
    standard, extra = setup_positions(rail, tag_boxes=[tag])
    assert extra and extra[0].tag_hits > 0
    chosen = select_collision_free_placements(
        [standard + extra], rails=[rail], max_neighbor_gap=1.,
        snap_tolerance=.001)
    assert chosen[0] is not extra[0]
    if not isinstance(chosen[0], SkippedPlacement):
        assert chosen[0].tag_hits == 0


def test_ne_pas_align_er_avec_cote_d_autre_zone():
    line = ((0., 1.7), (6., 1.7))
    distant_rail = ((30., 1.4), (34., 1.4))
    assert not matching_rails(line, [distant_rail], max_neighbor_gap=1.)
    room = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    assert aligned_candidates(line, room, [distant_rail], contains,
                              SETTINGS, max_neighbor_gap=1.) == []


def test_paires_obliques_reconnues_par_angle_sans_orthogonalite():
    line = ((0., 0.), (4., 4.))
    rail = ((4.2, 4.6), (6.2, 6.6))
    near = matching_rails(line, [rail], max_neighbor_gap=1.)
    assert len(near) == 1
    assert abs(near[0][0]) > .1


def test_pas_de_forcage_de_position_hors_de_la_piece():
    line = ((0., 1.7), (6., 1.7))
    rail = ((6.2, 7.), (10., 7.))
    room = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    assert aligned_candidates(line, room, [rail], contains,
                              SETTINGS, max_neighbor_gap=1.) == []
