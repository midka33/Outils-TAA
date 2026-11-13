# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Choix prudent de longueurs de murs dans les groupes de modele.

Utilise seulement les references d'extremites natives deja autorisees
par l'adaptateur de cotation. Ne pretend pas remplacer une distance
entre deux faces opposees par une largeur inventee.
Aucune dependance Revit : compatible IronPython 2.7 et Python 3.
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
