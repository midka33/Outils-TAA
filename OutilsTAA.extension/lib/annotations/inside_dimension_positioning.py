# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Selection de deux lignes de cote INTERIEURES pour les petites pieces.

Le moteur de Plans de vente produit toujours les candidats et references.
Ce module choisit des positions SANS decaler les references Revit.
Les superpositions ne sont admises qu'en dernier recours et signalees.
"""

from itertools import product
from plans_vente.dimension_positioning import placement_conflicts


def line_inside_room(candidate, contains, samples=9):
    """La ligne de cote traverse l'interieur (hors ses attaches aux faces).

    Sonder son interieur et non ses extremites qui touchent normalement
    le mur / la limite Revit. Refuser un trajet qui quitte une piece en L.
    """
    try:
        x0, y0 = candidate.line_start
        x1, y1 = candidate.line_end
        if (x1-x0)**2 + (y1-y0)**2 < 1.e-12:
            return False
        count = max(3, int(samples))
        return all(contains((x0+(x1-x0)*(i+.5)/count,
                             y0+(y1-y0)*(i+.5)/count))
                   for i in range(count))
    except Exception:
        return False


def text_anchor_inside_room(candidate, contains):
    """La position d'ancrage du texte est au milieu de la ligne.

    Dans un WC, l'enveloppe du texte natif peut etre plus large que la
    piece ; elle est signalee, sans DEPLACER la cote hors de la piece.
    """
    try:
        return bool(contains((
            (candidate.line_start[0]+candidate.line_end[0])*.5,
            (candidate.line_start[1]+candidate.line_end[1])*.5)))
    except Exception:
        return False


def select_inside_placements(groups, contains):
    """Choisir une ligne INTERIEURE par direction avec vraies references.

    Toujours privilegier deux axes lorsqu'ils possedent chacun au moins
    un candidat interieur, meme si cela fait se croiser des textes,
    temoins ou une etiquette. Conserver les risques dans les warnings.
    Ne jamais inventer une seconde paire de Reference Revit.
    """
    groups = [list(g) for g in groups]
    if not groups:
        return []
    if len(groups) > 2:
        raise ValueError("Deux orientations principales au maximum.")
    eligible = [[c for c in group
                 if line_inside_room(c, contains)
                 and text_anchor_inside_room(c, contains)]
                for group in groups]
    # En l'absence d'un axe geometriquement fiable, laisser une sentinelle
    # plutot que de coter a l'exterieur ou sur une direction inventee.
    from annotations.strict_dimension_positioning import SkippedPlacement
    options = [candidates or [None] for candidates in eligible]
    best = None
    for selection in product(*options):
        chosen = [c for c in selection if c is not None]
        collisions_text = 0
        collisions_graphics = 0
        if len(chosen) == 2:
            collisions_text, collisions_graphics = placement_conflicts(
                chosen[0], chosen[1])
        score = (
            -len(chosen),
            sum(bool(c.tag_hits) for c in chosen),
            sum(bool(c.dimension_hits) for c in chosen),
            collisions_text,
            sum(int(not getattr(c, "text_inside", False))
                for c in chosen),
            sum(c.outside_count for c in chosen),
            collisions_graphics,
            sum(c.equipment_hits for c in chosen),
            sum(c.clearance_penalty for c in chosen),
            sum(c.rank for c in chosen),
        )
        if best is None or score < best[0]:
            best = score, selection
    if best is None:
        return [SkippedPlacement("aucun candidat interieur") for g in groups]
    result = []
    for candidate in best[1]:
        if candidate is None:
            result.append(SkippedPlacement(
                "aucune ligne de cote utilisable a l'interieur de la piece"))
            continue
        candidate.warnings = []
        if not getattr(candidate, "text_inside", False):
            candidate.warnings.append(
                "PETITE PIECE : texte centre dans la piece, "
                "mais enveloppe du texte trop grande ; "
                "superposition autorisee, controle visuel")
        if candidate.tag_hits:
            candidate.warnings.append(
                "SUPERPOSITION INTERIEURE AUTORISEE avec une etiquette "
                "(petite piece) ; controle visuel")
        if candidate.dimension_hits:
            candidate.warnings.append(
                "SUPERPOSITION INTERIEURE AUTORISEE avec une cote "
                "deja presente ; controle des references et doublons")
        if candidate.equipment_hits:
            candidate.warnings.append(
                "proximite avec un equipement (controle recommande)")
        result.append(candidate)
    if len(result) == 2 and not any(
            isinstance(c, SkippedPlacement) for c in result):
        conflict_text, conflict_graphics = placement_conflicts(
            result[0], result[1])
        if conflict_text or conflict_graphics:
            result[1].warnings.append(
                "SUPERPOSITION INTERIEURE AUTORISEE entre les deux cotes "
                "(texte : {}, traits/temoins : {}) ; controle visuel"
                .format(conflict_text, conflict_graphics))
    return result
