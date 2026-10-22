# -*- coding: utf-8 -*-
"""Avant repere 2D, chercher une reference native de garde-corps pertinente."""

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from common.guardrail_reference_policy import (
    matches_guardrail_edge, select_guardrail_edge)


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
