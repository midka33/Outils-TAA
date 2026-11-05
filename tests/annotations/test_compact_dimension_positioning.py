# -*- coding: utf-8 -*-
"""Recette pure hors Revit : placement d'une 2e cote dans petite piece.

Le module Plan de vente reste la source des types et moteurs d'implantation.
Ni reference de cote ni mutation Revit ne sont impliquees ici.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from plans_vente.dimension_positioning import (
    DimensionPlacement, placement_candidates, placement_conflicts, _overlap)
from annotations.compact_dimension_positioning import external_candidates
from annotations.strict_dimension_positioning import (
    _compatible, select_collision_free_placements, SkippedPlacement)

SETTINGS = dict(clearance=.30, text_width=.60, text_height=.15,
                padding=.015, witness_length=.075)


def room_polygon(width=1.0, height=1.2):
    return [(0., 0.), (width, 0.), (width, height), (0., height)]


def contains(point):
    return 0. < point[0] < 1. and 0. < point[1] < 1.2


def test_positions_exterieures_bornees_et_dimensions_inchangees():
    line = ((0., .60), (1., .60))
    original = tuple(line)
    candidates = external_candidates(
        line, room_polygon(), contains, SETTINGS, text_axis=(1., 0.))
    assert len(candidates) == 4
    assert line == original
    assert all(c.external_compact for c in candidates)
    assert all(not c.text_inside for c in candidates)
    assert all(c.outside_count > 0 for c in candidates)
    assert all(abs(c.line_start[1] - c.line_end[1]) < 1.e-8
               for c in candidates)
    assert all(abs(c.line_end[0] - c.line_start[0] - 1.) < 1.e-8
               for c in candidates)
    assert all(-.31 < c.line_start[1] < 1.51 for c in candidates)


def test_une_etiquette_existante_interdit_le_repli_exterieur():
    line = ((0., .60), (1., .60))
    candidates = external_candidates(
        line, room_polygon(), contains, SETTINGS,
        tag_boxes=[(-1., -1., 2., 2.)])
    assert len(candidates) == 4
    assert all(c.tag_hits > 0 for c in candidates)
    selected = select_collision_free_placements([candidates])
    assert isinstance(selected[0], SkippedPlacement)


def test_une_cote_existante_interdit_le_repli_exterieur():
    line = ((0., .60), (1., .60))
    candidates = external_candidates(
        line, room_polygon(), contains, SETTINGS,
        dimension_boxes=[(-1., -1., 2., 2.)])
    assert all(c.dimension_hits > 0 for c in candidates)
    assert isinstance(
        select_collision_free_placements([candidates])[0],
        SkippedPlacement)


def _rect(x0, y0, x1, y1):
    return [(x0,y0), (x1,y0), (x1,y1), (x0,y1)]


def _vertical_band(x0, y0, x1, y1):
    return [(x0,y0), (x0,y1), (x1,y1), (x1,y0)]


class Candidate:
    def __init__(self, line, label, witness, key):
        self.line_start, self.line_end = key
        self.text_polygons = [label]
        self.polygons = [line, label, witness]
        self.tag_hits = self.dimension_hits = self.equipment_hits = 0
        self.outside_count = 0
        self.text_inside = True
        self.clearance_penalty = 0
        self.rank = 0
        self.warnings = []


def test_croisement_ponctuel_de_deux_temoins_est_acceptable():
    # Dans PDV, le croisement entre traits des deux axes n'interdit
    # pas une cote. Les deux textes restent volontairement eloignes.
    a = Candidate(_rect(0, 3, 4, 3.02),
                  _rect(3, 3.5, 4, 3.7),
                  _vertical_band(.99, 0, 1.01, 2),
                  ((0, 3), (4, 3)))
    b = Candidate(_rect(5, 0, 5.02, 3),
                  _rect(5.5, 2, 6.5, 2.2),
                  _rect(0, .99, 2, 1.01),
                  ((5, 0), (5, 3)))
    assert placement_conflicts(a, b) == (0, 1)
    assert _compatible(a, b)
    assert select_collision_free_placements([[a], [b]]) == [a, b]


def test_temoins_et_lignes_paralleles_superposes_restes_interdits():
    a = Candidate(_rect(0, 3, 4, 3.02),
                  _rect(3, 3.5, 4, 3.7),
                  _vertical_band(.99, 0, 1.01, 2),
                  ((0, 3), (4, 3)))
    b = Candidate(_rect(5, 0, 5.02, 3),
                  _rect(5.5, 2, 6.5, 2.2),
                  _vertical_band(.99, 0, 1.01, 2),
                  ((5, 0), (5, 3)))
    assert not _compatible(a, b)
    result = select_collision_free_placements([[a], [b]])
    assert sum(not isinstance(c, SkippedPlacement) for c in result) == 1


def test_toute_intersection_avec_un_texte_reste_interdite():
    a = Candidate(_rect(0, 3, 4, 3.02),
                  _rect(0.9, 0.9, 1.1, 1.1),
                  _vertical_band(.99, 0, 1.01, 2),
                  ((0, 3), (4, 3)))
    b = Candidate(_rect(5, 0, 5.02, 3),
                  _rect(5.5, 2, 6.5, 2.2),
                  _rect(0, .99, 2, 1.01),
                  ((5, 0), (5, 3)))
    assert placement_conflicts(a, b)[0] > 0
    assert not _compatible(a, b)


def test_le_repli_utilise_le_moteur_pdv_sans_modifier_son_code():
    import ast
    service = (ROOT / "OutilsTAA.extension/OutilsTAA.tab" /
               "Annotations.panel/services/annotations_service.py")
    src = service.read_text(encoding="utf-8")
    assert "from plans_vente.dimension_positioning import placement_candidates" in src
    assert "from annotations.compact_dimension_positioning import" in src
    assert "external_candidates(" in src
    assert "apres" not in src or "deux" in src
    ast.parse(src)
