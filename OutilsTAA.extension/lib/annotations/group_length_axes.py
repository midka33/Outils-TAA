# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Choix de directions et limites de piece pour les groupes de modele.

Les segments numeriques proviennent de Room.GetBoundarySegments(Finish)
dans l'adaptateur : les extrémités du mur physique NE sont pas des
références valables pour une limite tronquée par une autre pièce.
Deux repères de détail 2D non associatifs placés aux bornes de la limite
de la pièce permettent le secours ; la valeur Revit est vérifiée ensuite.
Ne prétend jamais mesurer des faces opposées non parallèles.
Aucune dépendance Revit : compatible IronPython 2.7 et Python 3.
"""

import math


def _axis(segment):
    x0, y0, x1, y1 = [float(v) for v in segment]
    dx, dy = x1 - x0, y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length <= 1e-9:
        return None
    return (dx / length, dy / length, length)


def _sine_difference(a, b):
    # Deux segments orientes en sens inverse sont la meme direction.
    return abs(a[0] * b[1] - a[1] * b[0])


def select_group_length_fallbacks(segments, eligible_indexes,
                                  existing_dimension_lines=None,
                                  max_results=2,
                                  min_axis_angle_degrees=30.0):
    """Retient jusqu'a deux longueurs sur des directions distinctes.

    Si une cote entre deux faces est deja disponible, choisir seulement
    une longueur non parallele a sa ligne de cote. Sinon choisir la
    meilleure paire de murs en maximisant longueurs * ouverture angulaire,
    sans jamais retourner deux axes presque paralleles.

    Retourne des INDEX des segments (et non des references Revit).
    """
    values = list(segments or [])
    eligible = []
    seen = set()
    for index in eligible_indexes or []:
        if index in seen or index < 0 or index >= len(values):
            continue
        seen.add(index)
        axis = _axis(values[index])
        if axis is not None:
            eligible.append((index, axis))
    if not eligible or max_results <= 0:
        return []

    min_sine = math.sin(math.radians(
        max(0.0, min(89.0, float(min_axis_angle_degrees)))))

    fixed = []
    for segment in existing_dimension_lines or []:
        axis = _axis(segment)
        if axis is not None:
            fixed.append(axis)
    remaining = max(0, int(max_results) - len(fixed))
    if not remaining:
        return []

    if fixed:
        ranked = []
        for index, axis in eligible:
            angles = [_sine_difference(axis, prior) for prior in fixed]
            if any(value < min_sine - 1e-10 for value in angles):
                continue
            ranked.append((axis[2] * min(angles), axis[2], -index, index))
        if not ranked:
            return []
        ranked.sort(reverse=True)
        return [ranked[0][3]]

    # En l'absence de faces opposees, prioriser deux orientations
    # et leur portee utile plutot que deux longs murs quasi paralleles.
    best = None
    for left in range(len(eligible)):
        index_a, axis_a = eligible[left]
        for right in range(left + 1, len(eligible)):
            index_b, axis_b = eligible[right]
            sine = _sine_difference(axis_a, axis_b)
            if sine < min_sine - 1e-10:
                continue
            value = (axis_a[2] * axis_b[2] * sine,
                     axis_a[2] + axis_b[2],
                     -min(index_a, index_b))
            if best is None or value > best[0]:
                best = (value, (index_a, index_b))
    if best is not None and remaining >= 2:
        pair = list(best[1])
        pair.sort(key=lambda item: (-_axis(values[item])[2], item))
        return pair

    # Une seule direction utilisable : une cote, jamais deux paralleles.
    eligible.sort(key=lambda item: (-item[1][2], item[0]))
    return [eligible[0][0]]


def room_boundary_end_markers(segment, half_length):
    """Deux traits perpendiculaires aux extremites de la limite de piece.

    Le trait de cote correspondant mesure EXACTEMENT la longueur de
    BoundarySegment propre a la piece, jamais le mur porteur complet.
    Les marques 2D sont non associatives aux ouvrages.
    """
    axis = _axis(segment)
    if axis is None:
        raise ValueError("Limite de piece de longueur nulle.")
    dx, dy, expected_length = axis
    nx, ny = -dy, dx
    half = min(float(half_length), expected_length * 0.25)
    if half <= 1e-8:
        raise ValueError("Repere de limite trop court.")
    x0, y0, x1, y1 = [float(x) for x in segment]
    first = (x0 - nx * half, y0 - ny * half,
             x0 + nx * half, y0 + ny * half)
    second = (x1 - nx * half, y1 - ny * half,
              x1 + nx * half, y1 + ny * half)
    return first, second, expected_length


def local_boundary_value_matches(actual, expected, tolerance):
    """Refuser une cote qui mesure au-dela de la limite de cette piece."""
    if actual is None or expected is None:
        return False
    value = float(actual)
    target = float(expected)
    return (math.isfinite(value) if hasattr(math, "isfinite")
            else not (math.isnan(value) or math.isinf(value))) and (
                target > 0 and abs(value - target) <= float(tolerance))
