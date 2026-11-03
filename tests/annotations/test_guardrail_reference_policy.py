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
    guardrail_minimum_overlap, diagnose_guardrail_candidates,
    select_contiguous_guardrail_pair)


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


def test_trois_garde_corps_a_meme_distance_choisir_le_plus_long():
    """Une egalite ne provoque plus de repli 2D arbitraire."""
    short, long, medium = object(), object(), object()
    result, info = select_guardrails_by_path(
        [(short, [(0., 0., 0., 1.8)]),
         (long, [(0., 0., 0., 3.62)]),
         (medium, [(0., 0., 0., 2.8)])],
        [(0., 0., 0., 3.62)], tolerance=.50,
        with_diagnostics=True)
    assert result == [long]
    assert info["ties_by_length"] == 1


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


def test_egalite_distance_choisit_le_plus_grand_avec_diagnostic():
    """Tolérance d'égalité 1 mm : le plus grand rail prime."""
    boundary = [(0., 0., 0., 3.62)]
    short, long, other = object(), object(), object()
    result, info = select_guardrails_by_path(
        [(short, [(.0400, 0., .0400, 2.5)]),
         (long, [(.0406, 0., .0406, 3.62)]),
         (other, [(.3, 0., .3, 3.62)])],
        boundary, tolerance=.5, ambiguity_gap=.001,
        with_diagnostics=True)
    assert result == [long]
    assert info["ties_by_length"] == 1
    assert info["reason"] == "selected"


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


def test_plusieurs_garde_corps_deux_limites_retenus_par_proximite():
    left_a, left_b, right = object(), object(), object()
    targets = [(0., 0., 0., 3.62), (3.12, 0., 3.12, 3.62)]
    paths = [
        (left_a, [(.04, 0., .04, 3.62)]),
        (left_b, [(.045, 0., .045, 3.62)]),
        (right, [(3.08, 0., 3.08, 3.62)]),
    ]
    result, info = select_guardrails_by_path(
        paths, targets, tolerance=.5,
        max_railings=2, ambiguity_gap=.001,
        with_diagnostics=True)
    assert result == [left_a, right]
    assert info["ambiguous"] == 0
    assert info["reason"] == "selected"


def test_filtrage_ne_relit_pas_les_solides_pour_diagnostiquer():
    # Le filtre opere sur les seules courbes de chemin mises en cache.
    a = object()
    result, info = select_guardrails_by_path(
        [(a, [(0., .04, 3.12, .04)])],
        [(0., 0., 3.12, 0.)], .5,
        with_diagnostics=True)
    assert result == [a]
    assert info["inspected"] == 1



def test_annexe_rail_seul_52pct_ne_suffit_pas():
    """Une arête couvrant 52% de la pièce n'est PAS suffisante seule."""
    limit = (0., 0., 0., 3.62)
    first = ((.015, 0., .015, 3.62*.52), "native-1", 10, 3.2)
    assert guardrail_minimum_overlap(True) == .60
    assert select_guardrail_edge(
        limit, [first], tolerance=.050,
        minimum_overlap=guardrail_minimum_overlap(True)) is None
    assert select_contiguous_guardrail_pair(
        limit, [first], tolerance=.050,
        max_gap=.10, max_lateral_mismatch=.02) is None


def test_deux_garde_corps_de_52pct_et_48pct_forment_une_limite_continue():
    """2238 : coter sur une vraie Reference, companion = preuve de continuité."""
    limit = (0., 0., 0., 3.62)
    pieces = [
        ((.015, 0., .015, 3.62*.52), "native-1", 10, 3.2),
        ((.018, 3.62*.52, .018, 3.62), "native-2", 11, 3.2),
    ]
    chosen = select_contiguous_guardrail_pair(
        limit, pieces, tolerance=.050, max_gap=.10,
        max_lateral_mismatch=.02, max_elevation_difference=.15)
    assert chosen[0] == "native-1"
    assert chosen[1] == 10
    info = chosen[2]
    assert info["support_count"] == 2
    assert abs(info["combined_overlap_ratio"]-1.) < 1e-9
    assert info["overlap_ratio"] < .60
    assert abs(info["lateral_mismatch"]-.003) < 1e-9


def test_deux_rails_meme_element_ou_superposes_ne_sont_pas_contigus():
    lim = (0., 0., 0., 3.62)
    first = ((.015, 0., .015, 3.62*.52), "native-1", 10, 3.2)
    repeated = ((.018, 3.62*.52, .018, 3.62), "native-2", 10, 3.2)
    assert select_contiguous_guardrail_pair(
        lim, [first, repeated], .050, max_gap=.10,
        max_lateral_mismatch=.02) is None
    same_half = ((.018, 0., .018, 3.62*.52), "native-2", 11, 3.2)
    assert select_contiguous_guardrail_pair(
        lim, [first, same_half], .050, max_gap=.10,
        max_lateral_mismatch=.02) is None


def test_un_trou_de_150mm_ou_un_decalage_de_30mm_rejette_la_paire():
    lim = (0., 0., 0., 3.62)
    first = ((.015, 0., .015, 3.62*.52), "native-1", 10, 3.2)
    hole = ((.018, 3.62*.52+.15, .018, 3.62), "native-2", 11, 3.2)
    assert select_contiguous_guardrail_pair(
        lim, [first, hole], .050, max_gap=.10,
        max_lateral_mismatch=.02) is None
    off = ((.045, 3.62*.52, .045, 3.62), "native-2", 11, 3.2)
    assert select_contiguous_guardrail_pair(
        lim, [first, off], .050, max_gap=.10,
        max_lateral_mismatch=.02) is None


def test_limite_incomplete_ou_garde_corps_vertical_rejete():
    lim = (0., 0., 0., 3.62)
    pieces = [
        ((.015, 0., .015, 3.62*.35), "native-1", 10, 3.2),
        ((.015, 3.62*.35, .015, 3.62*.70), "native-2", 11, 3.2),
    ]
    assert select_contiguous_guardrail_pair(
        lim, pieces, .050, max_gap=.10, max_lateral_mismatch=.02) is None
    pieces[1] = ((.015, 3.62*.35, .015, 3.62*.95),
                 "native-2", 11, 4.0)
    assert select_contiguous_guardrail_pair(
        lim, pieces, .050, max_gap=.10,
        max_lateral_mismatch=.02, max_elevation_difference=.15) is None


def test_annexe_52pct_rejette_au_dela_50mm_et_angle_sup_3deg():
    limit = (0., 0., 0., 3.62)
    assert select_guardrail_edge(
        limit, [((.065, 0., .065, 3.62*.52), "rail", 50, 0.)],
        tolerance=.050, minimum_overlap=.50) is None
    assert select_guardrail_edge(
        limit, [((.015, 0., .4, 3.62*.52), "rail", 50, 0.)],
        tolerance=.050, angle_degrees=3.,
        minimum_overlap=.50) is None



def test_reference_native_plus_proche_devant_une_arete_plus_longue():
    # La proximite prime sur la longueur, a condition que les deux
    # references respectent les limites d'angle et de recouvrement.
    boundary = (0., 0., 3.62, 0.)
    edges = [
        ((0., .04, 3.62, .04), "long-plus-loin", 12, 3.),
        ((0., .02, 3.0, .02), "court-proche", 11, 3.),
    ]
    assert select_guardrail_edge(boundary, edges, .05) == ("court-proche", 11)


def test_reference_native_meme_distance_choisit_plus_longue():
    boundary = (0., 0., 3.62, 0.)
    short = ((0., .015, 2.8, .015), "court", 11, 3.)
    long = ((0., .015, 3.62, .015), "long", 12, 3.)
    assert select_guardrail_edge(
        boundary, [short, long], .05) == ("long", 12)
    assert select_guardrail_edge(
        boundary, [long, short], .05) == ("long", 12)


def test_reference_native_egalite_un_millimetre_choisit_plus_longue():
    boundary = (0., 0., 3.62, 0.)
    edges = [
        ((0., .015, 2.8, .015), "plus-pres-court", 11, 3.),
        ((0., .0156, 3.62, .0156), "plus-loin-long", 12, 3.),
    ]
    assert select_guardrail_edge(
        boundary, edges, .05, distance_equality=.001) == (
        "plus-loin-long", 12)
    assert select_guardrail_edge(
        boundary, edges, .05, distance_equality=0.) == (
        "plus-pres-court", 11)


def test_reference_egale_distance_en_chaine_ne_change_pas_distance_de_base():
    boundary = (0., 0., 3.62, 0.)
    edges = [
        ((0., .015, 2.8, .015), "court-pres", 1, 3.),
        ((0., .0158, 3.0, .0158), "moyen", 2, 3.),
        ((0., .0167, 3.62, .0167), "long-trop-loin", 3, 3.),
    ]
    assert select_guardrail_edge(
        boundary, edges, .05, distance_equality=.001) == (
        "moyen", 2)


def test_deux_gc_contigus_reference_le_plus_proche_meme_si_plus_court():
    # La reference de cote est le plus proche des deux troncons.
    boundary = (0., 0., 0., 3.62)
    e1 = ((.03, 0., .03, 3.62*.52), "long", 101, 3.0)
    e2 = ((.01, 3.62*.52, .01, 3.62), "court-pres", 102, 3.0)
    match = select_contiguous_guardrail_pair(
        boundary, [e1,e2], tolerance=.05,
        max_gap=.10, max_lateral_mismatch=.02,
        distance_equality=.001)
    assert match[0:2] == ("court-pres", 102)


def test_deux_gc_contigus_meme_distance_reference_le_plus_long():
    boundary = (0., 0., 0., 3.62)
    e1 = ((.015, 0., .015, 3.62*.52), "long", 101, 3.0)
    e2 = ((.015, 3.62*.52, .015, 3.62), "court", 102, 3.0)
    match = select_contiguous_guardrail_pair(
        boundary, [e1,e2], tolerance=.05,
        max_gap=.10, max_lateral_mismatch=.02,
        distance_equality=.001)
    assert match[0:2] == ("long", 101)


def test_champs_diagnostic_selection_par_longueur():
    """Rapport de preselection : égalités departagees, sans ambiguïté."""
    boundary = [(0., 0., 0., 3.62)]
    objects = [object(),object()]
    matches, stats = select_guardrails_by_path(
        [(objects[0],[(.015,0.,.015,2.4)]),
         (objects[1],[(.015,0.,.015,3.62)])],
        boundary, tolerance=.5, ambiguity_gap=.001,
        with_diagnostics=True)
    assert matches == [objects[1]]
    assert stats["ties_by_length"] == 1
