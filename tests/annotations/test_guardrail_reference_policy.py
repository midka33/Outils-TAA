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
    select_contiguous_guardrail_pair,
    select_native_edge_with_path_continuity,
    diagnose_guardrail_path_continuity,
    select_native_edge_with_path_axis_offset_recovery)


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
        "existing = self._existing_dimension_reference_pairs(room)")
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



def test_loggia_2238_une_limite_complete_et_deux_rails_suivants():
    """2 cotes : un rail continu + deux demi-rails sur l'autre bord."""
    full = object()
    first_half, second_half = object(), object()
    limit_a = (0., 0., 3.62, 0.)
    limit_b = (0., 3.12, 3.62, 3.12)
    paths = [
        (full, [(0., .01, 3.62, .01)]),
        (first_half, [(0., 3.13, 3.62*.52, 3.13)]),
        (second_half, [(3.62*.52, 3.13, 3.62, 3.13)]),
    ]
    chosen, info = select_guardrails_by_path(
        paths, [limit_a, limit_b], tolerance=.5,
        max_railings=3, max_segments=80,
        ambiguity_gap=.001, allow_contiguous_companion=True,
        companion_gap=.1, companion_lateral=.02,
        with_diagnostics=True)
    assert chosen == [full, first_half, second_half]
    assert info["selected"] == 3
    assert info["companions"] == 1
    assert info["reason"] == "selected"


def test_second_rail_peut_etre_examine_meme_sans_preuve_par_le_chemin():
    a, b = object(), object()
    target = [(0., 0., 3.62, 0.)]
    paths = [
        (a, [(0., .01, 3.62*.52, .01)]),
        (b, [(0., .015, 3.62*.50, .015)]),
    ]
    selected, info = select_guardrails_by_path(
        paths, target, tolerance=.5,
        max_railings=3, allow_contiguous_companion=True,
        companion_gap=.1, companion_lateral=.02,
        with_diagnostics=True)
    # Examen autorise mais la continuite doit rester a prouver avec
    # les aretes natives ; aucune cote ne peut etre creee ici.
    assert selected == [a, b]
    assert info["companions"] == 1


def test_complement_de_rail_refuse_si_decales_30mm():
    a, b = object(), object()
    target = [(0., 0., 3.62, 0.)]
    paths = [
        (a, [(0., .01, 3.62*.52, .01)]),
        (b, [(3.62*.52, .04, 3.62, .04)]),
    ]
    selected, info = select_guardrails_by_path(
        paths, target, tolerance=.5,
        max_railings=3, allow_contiguous_companion=True,
        companion_gap=.1, companion_lateral=.02,
        with_diagnostics=True)
    # Le chemin ne prouve pas l'ecart des aretes natives :
    # les deux objets peuvent etre examines et rejetes ensuite.
    assert selected == [a, b]
    assert info["companions"] == 1


def test_companion_ne_fait_pas_depassement_silencieux_du_budget():
    """Deux limites avec quatre rails : rejet total si budget a trois."""
    objs = [object() for _ in range(4)]
    p = 3.62
    targets = [(0., 0., p, 0.), (0., 3.12, p, 3.12)]
    items = [
        (objs[0], [(0., .01, p*.52, .01)]),
        (objs[1], [(p*.52, .01, p, .01)]),
        (objs[2], [(0., 3.13, p*.52, 3.13)]),
        (objs[3], [(p*.52, 3.13, p, 3.13)]),
    ]
    selected, info = select_guardrails_by_path(
        items, targets, .5, max_railings=3,
        allow_contiguous_companion=True,
        companion_gap=.1, companion_lateral=.02,
        with_diagnostics=True)
    assert selected == []
    assert info["reason"] == "rail_budget"



def test_loggia_2238_chemin_entier_arrete_native_demie_garde_second_gc():
    """GetPath() peut etre complet alors que TopRail ne couvre que 52%."""
    full = object()
    first_half, second_half = object(), object()
    limit_a = (0., 0., 3.62, 0.)
    limit_b = (0., 3.12, 3.62, 3.12)
    paths = [
        (full, [(0., .01, 3.62, .01)]),
        # chemin de 100% ; son arête native TopRail ne fait que 52%
        (first_half, [(0., 3.13, 3.62, 3.13)]),
        (second_half, [(3.62*.52, 3.13, 3.62, 3.13)]),
    ]
    chosen, info = select_guardrails_by_path(
        paths, [limit_a, limit_b], tolerance=.5, max_railings=3,
        allow_contiguous_companion=True, ambiguity_gap=.001,
        with_diagnostics=True)
    assert chosen == [full, first_half, second_half]
    assert info["companions"] == 1
    assert info["selected"] == 3

    # Le contrôle NATIF, et non GetPath(), valide la paire.
    edges = [
        ((0., 3.13, 3.62*.52, 3.13), "native-A", 101, 2.8),
        ((3.62*.52, 3.13, 3.62, 3.13), "native-B", 102, 2.8),
    ]
    native = select_contiguous_guardrail_pair(
        limit_b, edges, tolerance=.05, max_gap=.10,
        max_lateral_mismatch=.02, max_elevation_difference=.15)
    assert native is not None
    assert native[2]["support_count"] == 2
    assert abs(native[2]["combined_overlap_ratio"]-1.) < 1.e-9


def test_candidat_supplémentaire_seul_ne_suffit_pas_a_coter():
    """Ne pas fabriquer une cote si la continuite des aretes est fausse."""
    limit = (0., 0., 3.62, 0.)
    two_edges = [
        ((0., .01, 3.62*.52, .01), "first", 101, 2.8),
        ((0., .015, 3.62*.50, .015), "second", 102, 2.8)]
    result = select_contiguous_guardrail_pair(
        limit, two_edges, tolerance=.05, max_gap=.10,
        max_lateral_mismatch=.02, max_elevation_difference=.15)
    assert result is None


def test_rail_budget_ne_parcourt_pas_4_rails():
    target = [(0., 0., 3.62, 0.)]
    items = [(object(), [(0., .01+i*.005, 3.62*.5, .01+i*.005)])
             for i in range(4)]
    selected, info = select_guardrails_by_path(
        items, target, .5, max_railings=3,
        allow_contiguous_companion=True, with_diagnostics=True)
    # Un seul complément envisagé pour une limite, pas les quatre ouvrages.
    assert len(selected) <= 3



def test_2238_deux_chemins_de_moitie_et_une_seule_reference_native():
    """Deux GetPath successifs 52% + 48% mais un seul TopRail cotable."""
    lim = (0., 0., 3.62, 0.)
    p1 = (0., .015, 3.62*.52, .015)
    p2 = (3.62*.52, .018, 3.62, .018)
    rail_paths = [(101, [p1]), (102, [p2])]
    native = [((0., .010, 3.62*.52, .010), "NATIVE", 901, 3.2)]
    match = select_native_edge_with_path_continuity(
        lim, native, rail_paths, {901:101},
        native_tolerance=.05, path_tolerance=.50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert match is not None
    assert match[0:2] == ("NATIVE", 901)
    assert match[2]["path_support_count"] == 2
    assert match[2]["path_combined_overlap_ratio"] > .99
    assert match[2]["overlap_ratio"] < .60
    assert match[2]["associative_to_both"] is False


def test_chemins_superposes_52plus48_ne_sont_pas_une_limite_continue():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.52, .015)]),
             (102, [(0., .018, 3.62*.48, .018)])]
    edges = [((0., .01, 3.62*.52, .01), "NATIVE", 901, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_somme_65pourcent_insuffisante_sans_90pourcent_utile():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.35, .015)]),
             (102, [(3.62*.35, .018, 3.62*.65, .018)])]
    edges = [((0., .01, 3.62*.35, .01), "NATIVE", 901, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_reference_native_dun_troisieme_gc_ne_valide_pas_les_deux_chemins():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.52, .015)]),
             (102, [(3.62*.52, .018, 3.62, .018)]),
             (103, [(0., .30, 3.62, .30)])]
    edges = [((0., .01, 3.62*.52, .01), "OTHER_NATIVE", 903, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {903:103}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_reference_native_excedant_50mm_est_refusee_meme_avec_chemins():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.52, .015)]),
             (102, [(3.62*.52, .018, 3.62, .018)])]
    edges = [((0., .065, 3.62*.52, .065), "TOO_FAR", 901, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_chemin_complet_plus_demi_chemin_superpose_ne_prouve_pas_continuite():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62, .015)]),
             (102, [(3.62*.52, .018, 3.62, .018)])]
    edges = [((0., .010, 3.62*.52, .010), "NATIVE", 901, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_deux_chemins_separes_150mm_refuses():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.52, .015)]),
             (102, [(3.62*.52+.15, .018, 3.62, .018)])]
    edges = [((0., .010, 3.62*.52, .010), "NATIVE", 901, 3.2)]
    assert select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_entre_deux_references_natives_choisir_la_plus_proche():
    lim = (0., 0., 3.62, 0.)
    paths = [(101, [(0., .015, 3.62*.52, .015)]),
             (102, [(3.62*.52, .018, 3.62, .018)])]
    edges = [
        ((0., .04, 3.62*.52, .04), "LONG_FAR", 901, 3.2),
        ((3.62*.52, .010, 3.62, .010), "NEAR", 902, 3.2)]
    match = select_native_edge_with_path_continuity(
        lim, edges, paths, {901:101, 902:102}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert match[0] == "NEAR"


def test_diagnostic_2238_chemins_successifs_couvrent_100pct():
    """52 % + 48 % successifs : message de diagnostic compatible."""
    length = 3.62
    paths = [
        (16141887, [(0., .015, length*.52, .015)]),
        (8951804, [(length*.52, .018, length, .018)]),
    ]
    status = diagnose_guardrail_path_continuity(
        (0., 0., length, 0.), paths, path_tolerance=.50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert status["supported"]
    assert status["reason"] == "chemins_compatibles"
    assert status["pair_count"] == 1
    assert abs(status["best"]["coverage"] - 1.) < 1.e-9
    assert status["best"]["parent_ids"] == (16141887, 8951804)
    assert abs(status["best"]["start_end"][0][1] - .52) < 1.e-9


def test_diagnostic_2238_chemin_100pct_plus_demi_chemin_superpose():
    """Une union 100 % ne valide PAS deux ouvrages qui se superposent."""
    length = 3.62
    paths = [
        (16141887, [(0., .015, length, .015)]),
        (8951804, [(length*.52, .018, length, .018)]),
    ]
    status = diagnose_guardrail_path_continuity(
        (0., 0., length, 0.), paths, path_tolerance=.50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert not status["supported"]
    assert status["best"]["coverage"] > .99
    assert abs(status["best"]["overlap"] - .48) < 1.e-9
    assert "chemins_superposes" in status["best"]["reasons"]
    assert select_native_edge_with_path_continuity(
        (0., 0., length, 0.),
        [((0., .01, length*.52, .01), "NATIVE", 901, 3.2)],
        paths, {901:16141887}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02) is None


def test_diagnostic_2238_deux_chemins_sur_la_meme_moitie():
    length = 3.62
    paths = [
        (16141887, [(0., .015, length*.52, .015)]),
        (8951804, [(0., .018, length*.48, .018)]),
    ]
    status = diagnose_guardrail_path_continuity(
        (0., 0., length, 0.), paths, path_tolerance=.50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert not status["supported"]
    assert "chemins_superposes" in status["best"]["reasons"]
    assert "couverture_insuffisante" in status["best"]["reasons"]
    assert 0.51 < status["best"]["coverage"] < 0.53


def test_diagnostic_2238_chemins_separes_par_150mm():
    length = 3.62
    paths = [
        (16141887, [(0., .015, length*.52, .015)]),
        (8951804, [(length*.52+.15, .018, length, .018)]),
    ]
    status = diagnose_guardrail_path_continuity(
        (0., 0., length, 0.), paths, path_tolerance=.50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert not status["supported"]
    assert "raccord_trop_grand" in status["best"]["reasons"]
    assert abs(status["best"]["gap"]-.15) < 1.e-9


def test_diagnostic_2238_absence_deuxieme_chemin_et_budget():
    target = (0., 0., 3.62, 0.)
    one = diagnose_guardrail_path_continuity(
        target, [(16141887, [(0., 0., 3.62, 0.)])], .50)
    assert one["reason"] == "pas_de_paire"
    assert one["pair_count"] == 0
    many = diagnose_guardrail_path_continuity(
        target, [(i, [(0., 0., 3.62, 0.)]) for i in range(4)],
        .50, max_railings=3)
    assert many["reason"] == "budget"
    assert not many["supported"]


def test_diagnostic_2238_ne_change_jamais_la_selection_de_reference():
    target = (0., 0., 3.62, 0.)
    paths = [(16141887, [(0., .015, 1.88, .015)]),
             (8951804, [(1.88, .018, 3.62, .018)])]
    native = [((0., .01, 1.88, .01), "NATIVE", 901, 3.2)]
    before = select_native_edge_with_path_continuity(
        target, native, paths, {901:16141887}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    _ = diagnose_guardrail_path_continuity(
        target, paths, .50, maximum_gap=.10,
        maximum_lateral_mismatch=.02)
    after = select_native_edge_with_path_continuity(
        target, native, paths, {901:16141887}, .05, .50,
        maximum_gap=.10, maximum_lateral_mismatch=.02)
    assert before == after
    assert after is not None


def test_revit_diagnostic_est_raccorde_apres_echec_de_continuite():
    """Le rapport montre les motifs seulement apres echec du fallback."""
    panel = (Path(__file__).resolve().parents[2] /
             "OutilsTAA.extension/OutilsTAA.tab/Annotations.panel"
             "/services/annotations_service.py")
    source = panel.read_text(encoding="utf-8")
    assert "diagnose_guardrail_path_continuity(" in source
    assert "diagnostic continuité GC" in source
    assert "chemins compatibles mais aucune arete" in source
    assert "max_railings=3, max_paths=80" in source


def test_2238_recuperation_beta_axes_de_33mm_et_arete_native_zero_mm():
    """Couverture 100%, chemins sur le meme cote a 25/58 mm du nu."""
    millimetre = 1. / 304.8
    length = 3.62
    path_a = (0., 25*millimetre, length*.52, 25*millimetre)
    path_b = (length*.52, 58*millimetre,
              length, 58*millimetre)
    paths = [(16141871, [path_a]), (8951804, [path_b])]
    edges = [((0., 0., length*.52, 0.), "NATIVE", 16141873, 3.2)]
    result = select_native_edge_with_path_axis_offset_recovery(
        (0., 0., length, 0.), edges, paths,
        {16141873: 16141871},
        native_tolerance=50*millimetre, path_tolerance=.5,
        max_relaxed_lateral=40*millimetre,
        max_boundary_axis_offset=60*millimetre,
        max_native_offset=5*millimetre,
        maximum_gap=10*millimetre)
    assert result is not None
    assert result[:2] == ("NATIVE", 16141873)
    assert result[2]["axis_offset_recovery"] is True
    assert result[2]["associative_to_both"] is False
    assert abs(result[2]["axis_offset_gap"]/millimetre - 33.) < .01
    assert abs(result[2]["axis_offset_max"]/millimetre - 58.) < .01
    assert result[2]["path_combined_overlap_ratio"] > .999
    # Avec le seuil historique de 20 mm, cette paire reste refusee.
    assert select_native_edge_with_path_continuity(
        (0., 0., length, 0.), edges, paths, {16141873: 16141871},
        50*millimetre, .5, maximum_gap=10*millimetre,
        maximum_lateral_mismatch=20*millimetre) is None


def test_recuperation_2238_refuse_axe_de_41mm_ou_max_61mm():
    mm = 1. / 304.8
    length = 3.62
    boundary = (0., 0., length, 0.)
    edge = [((0., 0., length*.52, 0.), "NATIVE", 201, 3.2)]
    for upper in (61, 67):
        paths = [(11, [(0., 20*mm, length*.52, 20*mm)]),
                 (12, [(length*.52, upper*mm, length, upper*mm)])]
        assert select_native_edge_with_path_axis_offset_recovery(
            boundary, edge, paths, {201:11},
            50*mm, .5, max_relaxed_lateral=40*mm,
            max_boundary_axis_offset=60*mm,
            max_native_offset=5*mm,
            maximum_gap=10*mm) is None


def test_recuperation_2238_refuse_arete_native_6mm():
    mm = 1. / 304.8
    length = 3.62
    paths = [(11, [(0., 25*mm, length*.52, 25*mm)]),
             (12, [(length*.52, 58*mm, length, 58*mm)])]
    edge = [((0., 6*mm, length*.52, 6*mm), "NATIVE", 201, 3.2)]
    assert select_native_edge_with_path_axis_offset_recovery(
        (0., 0., length, 0.), edge, paths, {201:11},
        50*mm, .5, max_relaxed_lateral=40*mm,
        max_boundary_axis_offset=60*mm,
        max_native_offset=5*mm,
        maximum_gap=10*mm) is None


def test_recuperation_2238_refuse_trou_superposition_ou_axe_oppose():
    mm = 1. / 304.8
    length = 3.62
    edge = [((0., 0., length*.52, 0.), "NATIVE", 201, 3.2)]
    first = (0., 25*mm, length*.52, 25*mm)
    remaining = [
        # 20 mm de trou
        (length*.52+20*mm, 58*mm, length, 58*mm),
        # plus de 2% de superposition
        (length*.48, 58*mm, length, 58*mm),
        # axe de l'autre cote de la limite
        (length*.52, -8*mm, length, -8*mm),
    ]
    for second in remaining:
        paths = [(11, [first]), (12, [second])]
        assert select_native_edge_with_path_axis_offset_recovery(
            (0., 0., length, 0.), edge, paths, {201:11},
            50*mm, .5, max_relaxed_lateral=40*mm,
            max_boundary_axis_offset=60*mm,
            max_native_offset=5*mm,
            maximum_gap=10*mm) is None


def test_recuperation_2238_refuse_reference_autre_garde_corps():
    mm = 1. / 304.8
    length = 3.62
    paths = [(11, [(0., 25*mm, length*.52, 25*mm)]),
             (12, [(length*.52, 58*mm, length, 58*mm)]),
             (13, [(0., 80*mm, length, 80*mm)])]
    edge = [((0., 0., length*.52, 0.), "OTHER", 201, 3.2)]
    assert select_native_edge_with_path_axis_offset_recovery(
        (0., 0., length, 0.), edge, paths, {201:13},
        50*mm, .5, max_relaxed_lateral=40*mm,
        max_boundary_axis_offset=60*mm,
        max_native_offset=5*mm,
        maximum_gap=10*mm) is None


def test_recuperation_beta_raccordee_uniquement_sur_l_echec_natif():
    path = (Path(__file__).resolve().parents[2] /
            "OutilsTAA.extension/OutilsTAA.tab/Annotations.panel"
            "/services/annotations_service.py")
    source = path.read_text(encoding="utf-8")
    assert "select_native_edge_with_path_axis_offset_recovery(" in source
    assert "RECUPERATION BETA du GC" in source
    assert "max_relaxed_lateral=self._millimeters_to_internal(40.)" in source
    assert "max_boundary_axis_offset=self._millimeters_to_internal(60.)" in source
    assert "max_native_offset=self._millimeters_to_internal(5.)" in source
    assert "maximum_gap=self._millimeters_to_internal(10.)" in source
