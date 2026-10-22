# -*- coding: utf-8 -*-
"""Avant repere 2D, chercher une reference native de garde-corps pertinente."""

import sys
from pathlib import Path

LIB = Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from common.guardrail_reference_policy import (
    matches_guardrail_edge, select_guardrail_edge,
    select_guardrails_by_path,
    is_exterior_annex, guardrail_tolerance_mm,
    guardrail_minimum_overlap, diagnose_guardrail_candidates)


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
    assert len(result) == 2
    assert set(result) == {a, b}


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



def test_exterior_annex_types_and_int_ext_parameter():
    for label in ("Loggia", "Balcon B102", "Terrasse accessible", "Jardin privatif"):
        assert is_exterior_annex(label)
    assert is_exterior_annex("Cour A004", "Ext")
    assert is_exterior_annex("Extérieur", "extérieur")
    assert not is_exterior_annex("Chambre")
    assert not is_exterior_annex("Salle de bains", "Int")


def test_tolérance_extérieure_rattrape_35mm_sans_relacher_les_angles():
    limite = (0., 0., 3.12, 0.)
    guardrail = (0., .035, 3.12, .035)
    edges = [(guardrail, "reference-native", "rail", 3.7)]
    assert select_guardrail_edge(limite, edges, tolerance=.020) is None
    reference = select_guardrail_edge(
        limite, edges, tolerance=.050, include_metrics=True)
    assert reference[0:2] == ("reference-native", "rail")
    assert abs(reference[2]["distance"]-.035) < 1e-9
    assert guardrail_tolerance_mm(True) == 50.
    assert guardrail_tolerance_mm(False) == 20.


def test_decalage_de_65mm_reste_interdit_sur_annexe():
    limit = (0., 0., 3.12, 0.)
    edges = [((0., .065, 3.12, .065), "R", 5, 0.)]
    assert select_guardrail_edge(limit, edges, tolerance=.050) is None
    diagnosis = diagnose_guardrail_candidates(limit, edges, tolerance=.050)
    assert len(diagnosis) == 1
    assert "ecart" in diagnosis[0]["reasons"]
    assert abs(diagnosis[0]["distance"]-.065) < 1e-9


def test_annexe_rejette_guardrail_35mm_si_orienté_incorrectement():
    limit = (0., 0., 3.12, 0.)
    diagonal = [(0., .035, 3.12, .60), "R", 5, 0.]
    assert select_guardrail_edge(limit, [diagonal], tolerance=.050) is None



def test_trois_garde_corps_proches_mais_un_seul_nu_clairement_meilleur():
    """Régression 2238 : ne pas écarter 3 candidats par simple comptage."""
    boundary = [(0., 0., 0., 3.62)]
    inner, neighbor, outer = object(), object(), object()
    paths = [
        (inner, [(.040, 0., .040, 3.62)]),
        (neighbor, [(.210, 0., .210, 3.62)]),
        (outer, [(.380, 0., .380, 3.62)]),
    ]
    result, info = select_guardrails_by_path(
        paths, boundary, tolerance=.5, max_railings=2,
        ambiguity_gap=.025, with_diagnostics=True)
    assert result == [inner]
    assert info["path_matches"] == 3
    assert info["ambiguous"] == 0
    assert info["selected"] == 1
    assert info["reason"] == "selected"
    assert abs(info["closest_distance"] - .04) < 1e-9


def test_ex_aquo_sur_la_meme_limite_est_refuse_avec_diagnostic():
    """Deux nus très proches ne doivent jamais etre départagés au hasard."""
    boundary = [(0., 0., 0., 3.62)]
    a, b, c = object(), object(), object()
    result, info = select_guardrails_by_path(
        [(a, [(.040, 0., .040, 3.62)]),
         (b, [(.046, 0., .046, 3.62)]),
         (c, [(.3, 0., .3, 3.62)])],
        boundary, tolerance=.5, ambiguity_gap=.025,
        with_diagnostics=True)
    assert result == []
    assert info["ambiguous"] == 1
    assert info["reason"] == "ambiguous"


def test_deux_limites_et_plus_de_deux_gc_seuls_les_meilleurs_sont_examines():
    """Un GC par limite de cote, sans lever le budget natif à deux objets."""
    left, right, other = object(), object(), object()
    targets = [(0., 0., 0., 3.62), (3.12, 0., 3.12, 3.62)]
    paths = [
        (left, [(.04, 0., .04, 3.62)]),
        (right, [(3.08, 0., 3.08, 3.62)]),
        (other, [(1.5, 0., 1.5, 3.62)]),
    ]
    result, info = select_guardrails_by_path(
        paths, targets, tolerance=.5,
        max_railings=2, ambiguity_gap=.025,
        with_diagnostics=True)
    assert result == [left, right]
    assert info["selected"] == 2


def test_garde_corps_une_limite_ambigue_autre_claire_autorisee():
    left_a, left_b, right = object(), object(), object()
    targets = [(0., 0., 0., 3.62), (3.12, 0., 3.12, 3.62)]
    paths = [
        (left_a, [(.04, 0., .04, 3.62)]),
        (left_b, [(.045, 0., .045, 3.62)]),
        (right, [(3.08, 0., 3.08, 3.62)]),
    ]
    result, info = select_guardrails_by_path(
        paths, targets, tolerance=.5,
        max_railings=2, ambiguity_gap=.025,
        with_diagnostics=True)
    assert result == [right]
    assert info["ambiguous"] == 1
    assert info["reason"] == "partial_ambiguity"


def test_filtrage_ne_relit_pas_les_solides_pour_diagnostiquer():
    # Le filtre opere sur les seules courbes de chemin mises en cache.
    a = object()
    result, info = select_guardrails_by_path(
        [(a, [(0., .04, 3.12, .04)])],
        [(0., 0., 3.12, 0.)], .5,
        with_diagnostics=True)
    assert result == [a]
    assert info["inspected"] == 1



def test_annexe_2238_arrete_52pct_15mm_est_valide():
    """Cas réel : écart 15 mm / angle 0 / couverture 52 pour cent."""
    limite = (0., 0., 0., 3.62)
    portion = (.015, 0., .015, 3.62*.52)
    edges = [(portion, "rail-native", "garde-corps", 3.2)]
    assert guardrail_minimum_overlap(True) == .50
    assert guardrail_minimum_overlap(False) == .60
    assert select_guardrail_edge(
        limite, edges, tolerance=.050,
        minimum_overlap=.60) is None
    match = select_guardrail_edge(
        limite, edges, tolerance=.050,
        minimum_overlap=guardrail_minimum_overlap(True),
        include_metrics=True)
    assert match[0] == "rail-native"
    assert abs(match[2]["distance"] - .015) < 1e-9
    assert abs(match[2]["overlap_ratio"] - .52) < 1e-9


def test_annexe_rejette_un_garde_corps_ne_couvrant_que_49pct():
    limite = (0., 0., 0., 3.62)
    edges = [((.015, 0., .015, 3.62*.49), "rail", 50, 0.)]
    assert select_guardrail_edge(
        limite, edges, tolerance=.050,
        minimum_overlap=guardrail_minimum_overlap(True)) is None


def test_annexe_52pct_rejette_au_dela_50mm_et_angle_sup_3deg():
    limit = (0., 0., 0., 3.62)
    assert select_guardrail_edge(
        limit, [((.065, 0., .065, 3.62*.52), "rail", 50, 0.)],
        tolerance=.050, minimum_overlap=.50) is None
    assert select_guardrail_edge(
        limit, [((.015, 0., .4, 3.62*.52), "rail", 50, 0.)],
        tolerance=.050, angle_degrees=3.,
        minimum_overlap=.50) is None
