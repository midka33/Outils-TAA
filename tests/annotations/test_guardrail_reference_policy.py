# -*- coding: utf-8 -*-
"""Avant repere 2D, chercher une reference native de garde-corps pertinente."""

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from common.guardrail_reference_policy import (
    matches_guardrail_edge, select_guardrail_edge,
    select_guardrails_by_path)


def test_arrete_native_superposee_a_la_separation_est_admissible():
    separation = (0., 0., 3.12, 0.)
    reference = object()
    result = select_guardrail_edge(
        separation, [
            ((0., .004, 3.12, .004), reference, "gc", 3.7)
        ], tolerance=.020)
    assert result == (reference, "gc")


def test_arrete_de_garde_corps_lointaine_ne_deplace_pas_cote():
    separation = (0., 0., 3.12, 0.)
    assert select_guardrail_edge(
        separation, [
            ((0., .25, 3.12, .25), "reference", "gc", 3.7)
        ], tolerance=.02) is None


def test_axe_oblique_court_rejete_meme_si_proche():
    separation = (0., 0., 3.12, 0.)
    assert select_guardrail_edge(
        separation, [
            ((0., 0., .1, .1), "reference", "gc", 3.7)
        ], tolerance=.02) is None


def test_prefere_l_arete_la_plus_proche_et_non_l_axe_du_gc():
    separation = (0., 0., 3.12, 0.)
    edges = [
        ((0., .010, 3.12, .010), "edge1", "gc", 3.7),
        ((0., .003, 3.12, .003), "edge2", "gc", 3.7),
    ]
    assert select_guardrail_edge(
        separation, edges, tolerance=.02) == ("edge2", "gc")


def test_repli_si_aucune_reference_native_verifiable():
    separation = (0., 0., 3.12, 0.)
    assert select_guardrail_edge(
        separation, [((0., 0., 3.12, 0.), None, 3, 0)],
        tolerance=.02) is None


def test_budget_surplus_interdit_toute_extraction_approximative():
    edges = [((0., 0., 3.12, 0.), object(), i, 0)
             for i in range(121)]
    assert select_guardrail_edge(
        (0., 0., 3.12, 0.), edges,
        tolerance=.02, max_edges=120) is None


def test_test_non_regression_ordre_references():
    """Contrat de l'adaptateur : la recherche dalle reste prioritaire."""
    adapter = (LIB.parent / "OutilsTAA.tab" / "Annotations.panel" /
               "services" / "annotations_service.py")
    source = adapter.read_text(encoding="utf-8")
    assert "super(GenericDimensions, self)._room_boundary_candidates(room)" in source
    assert "self._upgrade_separator_guardrail(" in source
    assert source.index(
        "candidates = super(GenericDimensions, self)._room_boundary_candidates(room)"
    ) < source.index("self._upgrade_separator_guardrail(")
    assert source.index("self._upgrade_separator_guardrail(") < source.index(
        "existing = self._existing_dimension_reference_pairs()")
    assert 'candidate.source_kind = "guardrail_edge"' in source
    assert 'if getattr(candidate, "source_kind", None) != "separator":' in source


def test_trois_garde_corps_dans_piece_un_seul_proche_de_separation():
    """Le faux positif bbox de la loggia 2238 ne doit plus bloquer le GC."""
    selected_boundary = [(0., 0., 0., 3.62)]
    target = object()
    others = [object(), object(), object()]
    paths = [
        (others[0], [(1., 0., 1., 3.62)]),
        (target, [(-.06, 0., -.06, 3.62)]),
        (others[1], [(3.12, 0., 3.12, 3.62)]),
        (others[2], [(0., 6., 3.12, 6.)]),
    ]
    assert select_guardrails_by_path(
        paths, selected_boundary, tolerance=.50) == [target]


def test_deux_garde_corps_pertinents_sont_acceptes():
    a, b = object(), object()
    paths = [
        (a, [(-.04, 0., -.04, 3.62)]),
        (b, [(3.1, 0., 3.1, 3.62)]),
        (object(), [(1.2, 0., 1.2, 3.62)]),
    ]
    result = select_guardrails_by_path(
        paths, [(0., 0., 0., 3.62), (3.12, 0., 3.12, 3.62)],
        tolerance=.50)
    assert result == [a, b]


def test_trois_garde_corps_reellement_sur_la_limite_restent_refuses():
    result = select_guardrails_by_path(
        [(i, [(0., 0., 0., 3.62)]) for i in range(3)],
        [(0., 0., 0., 3.62)], tolerance=.50)
    assert result == []


def test_ni_chemin_lointain_ni_angle_incompatible():
    result = select_guardrails_by_path(
        [(1, [(1.5, 0., 1.5, 3.62)]),
         (2, [(0., 0., 3.12, 0.)])],
        [(0., 0., 0., 3.62)], tolerance=.50)
    assert result == []


def test_budget_de_chemins_interrompt_avant_les_solides():
    paths = [(i, [(0., 0., 1., 0.)]) for i in range(81)]
    assert select_guardrails_by_path(
        paths, [(0., 0., 3.12, 0.)],
        tolerance=.50, max_segments=80) == []


def test_preselection_ne_peut_pas_remplacer_reference_native():
    """Un chemin de garde-corps ne porte jamais de Reference de cote."""
    candidate = object()
    chosen = select_guardrails_by_path(
        [(candidate, [(0., .05, 3.12, .05)])],
        [(0., 0., 3.12, 0.)], tolerance=.50)
    assert chosen == [candidate]
    assert select_guardrail_edge(
        (0., 0., 3.12, 0.),
        [((0., .05, 3.12, .05), object(), candidate, 3.7)],
        tolerance=.02) is None
