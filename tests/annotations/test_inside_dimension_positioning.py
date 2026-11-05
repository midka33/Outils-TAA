# -*- coding: utf-8 -*-
"""Regle agence : 2 cotes interieur si 2 directions natives ; collisions tolerees."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from plans_vente.dimension_positioning import placement_candidates
from annotations.inside_dimension_positioning import (
    line_inside_room, text_anchor_inside_room, select_inside_placements)
from annotations.strict_dimension_positioning import (
    SkippedPlacement, select_collision_free_placements)


def test_deux_cotes_restent_interieures_meme_si_tags_et_textes_superposes():
    points = [(0., 0.), (.90, 0.), (.90, .60), (0., .60)]
    contains = lambda p: 0. < p[0] < .90 and 0. < p[1] < .60
    settings = dict(clearance=.15, text_width=1.0, text_height=.11,
                    padding=.007, witness_length=.04)
    tags = [(0.0, 0.0, .90, .60)]
    groups = [
        placement_candidates(((0., .30), (.90, .30)),
                             points, contains, tag_boxes=tags, **settings),
        placement_candidates(((.45, 0.), (.45, .60)),
                             points, contains, tag_boxes=tags, **settings),
    ]
    strict = select_collision_free_placements(groups)
    assert all(isinstance(c, SkippedPlacement) for c in strict)
    selected = select_inside_placements(groups, contains)
    assert len(selected) == 2
    assert all(not isinstance(c, SkippedPlacement) for c in selected)
    assert all(line_inside_room(c, contains) and
               text_anchor_inside_room(c, contains) for c in selected)
    assert all(c.tag_hits > 0 for c in selected)
    assert any("SUPERPOSITION INTERIEURE AUTORISEE" in warning
               for c in selected for warning in c.warnings)


def test_piece_en_l_refuse_ligne_qui_traverse_un_vide():
    # Local en L : manque le quart superieur droit.
    def contains(point):
        x, y = point
        return (0. < x < 3. and 0. < y < 1.) or (
            0. < x < 1. and 0. < y < 3.)
    class Candidate(object):
        line_start = (.30, 2.2)
        line_end = (2.7, 2.2)
    assert not line_inside_room(Candidate(), contains, samples=21)


def test_ne_cree_pas_deuxieme_orientation_absente():
    points = [(0., 0.), (.9, 0.), (.9, .6), (0., .6)]
    contains = lambda p: 0. < p[0] < .9 and 0. < p[1] < .6
    group = placement_candidates(
        ((0., .30), (.9, .30)), points, contains,
        clearance=.1, text_width=.5, text_height=.08,
        padding=.005, witness_length=.03)
    selected = select_inside_placements([group], contains)
    assert len(selected) == 1
    assert line_inside_room(selected[0], contains)


def test_ironpython_ne_depend_pas_de_code_python3():
    import ast
    source = (LIB / "annotations" / "inside_dimension_positioning.py").read_text(
        encoding="utf-8")
    ast.parse(source)
    assert "from itertools import product" in source
