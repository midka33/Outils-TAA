# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Choix strict des cotations, sans imposer que les deux cotes soient possibles.

Le moteur Plans de vente conserve son algorithme d'origine.
Cet adaptateur n'autorise que des candidats sans recouvrement avec
les etiquettes ou les cotations deja posees, et sans conflit entre
les nouvelles cotations. Il peut retenir une seule cote si necessaire.
"""

from itertools import product

from plans_vente.dimension_positioning import placement_conflicts, _overlap
from annotations.dimension_alignment import alignment_penalty


class SkippedPlacement(object):
    """Sentinelle explicite pour une cote non placable sans collision."""

    line_start = None
    line_end = None
    warnings = []

    def __init__(self, reason):
        self.reason = reason


def _is_eligible(candidate):
    return (not candidate.tag_hits
            and not candidate.dimension_hits
            and bool(getattr(candidate, "text_inside", True)))


def _same_line_direction(left, right, tolerance_degrees=15.0):
    """Deux lignes quasiment paralleles ne doivent pas se superposer."""
    import math
    a = (left.line_end[0] - left.line_start[0],
         left.line_end[1] - left.line_start[1])
    b = (right.line_end[0] - right.line_start[0],
         right.line_end[1] - right.line_start[1])
    na = math.hypot(*a)
    nb = math.hypot(*b)
    if na < 1e-9 or nb < 1e-9:
        return True
    dot = abs((a[0] * b[0] + a[1] * b[1]) / (na * nb))
    return dot >= math.cos(math.radians(tolerance_degrees))


def _compatible(left, right):
    """Autorise uniquement le croisement simple de deux traits de cote.

    Deux cotes completes traversant une piece rectangulaire se croisent
    necessairement. Ce croisement ponctuel des traits est acceptable en
    dessin architectural ; les chiffres, textes et temoins doivent rester
    sans superposition. Les segments colineaires restent interdits.
    """
    text_hits, graphic_hits = placement_conflicts(left, right)
    if text_hits:
        return False
    if not graphic_hits:
        return True
    if not left.polygons or not right.polygons:
        return False
    for i, poly_a in enumerate(left.polygons):
        for j, poly_b in enumerate(right.polygons):
            if not _overlap(poly_a, poly_b):
                continue
            if i == 0 and j == 0 and not _same_line_direction(left, right):
                continue
            return False
    return True


def select_collision_free_placements(candidate_groups, rails=(),
                                    max_neighbor_gap=8., snap_tolerance=.05):
    """Retourne un placement ou une sentinelle par orientation initiale.

    Contrairement au choix conjoint historique, une orientation impossible
    n'empeche pas de produire les autres. Les indices restent identiques
    a ceux attendus par DimensionService.create_dimensions.
    """
    groups = [list(group) for group in candidate_groups]
    if not groups:
        return []
    if len(groups) > 2:
        raise ValueError("Deux orientations maximum pour les cotations principales.")

    options = [[None] + [candidate for candidate in group
                         if _is_eligible(candidate)] for group in groups]
    best = None
    for combination in product(*options):
        chosen = [candidate for candidate in combination if candidate is not None]
        if len(chosen) == 2 and not _compatible(chosen[0], chosen[1]):
            continue
        score = (
            -len(chosen),
            sum(int(candidate.outside_count > 0) for candidate in chosen),
            sum(candidate.outside_count for candidate in chosen),
            sum(alignment_penalty(candidate, rails, max_neighbor_gap,
                                  snap_tolerance) for candidate in chosen)
            if rails else 0,
            sum(candidate.equipment_hits for candidate in chosen),
            sum(candidate.clearance_penalty for candidate in chosen),
            sum(candidate.rank for candidate in chosen),
            tuple(candidate.rank if candidate is not None else 999
                  for candidate in combination),
        )
        if best is None or score < best[0]:
            best = (score, combination)

    chosen = best[1]
    result = []
    for index, candidate in enumerate(chosen):
        if candidate is None:
            group = groups[index]
            reason = ("aucune position sans chevauchement avec etiquettes/cotes"
                      " et avec texte de cote entierement dans la piece")
            if not group:
                reason = "aucune position candidate disponible"
            result.append(SkippedPlacement(reason))
        else:
            candidate.warnings = []
            if candidate.outside_count:
                candidate.warnings.append(
                    "ligne de cote possiblement proche ou au-dela de la limite de piece"
                )
            if candidate.equipment_hits:
                candidate.warnings.append(
                    "proximite avec un equipement (controle recommande)"
                )
            result.append(candidate)
    return result
