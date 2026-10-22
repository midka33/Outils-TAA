# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Selection des deux dimensions principales entre faces opposees.

Utilise le moteur pur de Plans de vente pour trouver les paires de faces
finies, puis exige deux directions perpendiculaires, si elles existent.
La mesure de la longueur d'un mur ne remplace jamais une cote principale.
"""

import math

from plans_vente.dimension_geometry import dominant_dimension_pairs


def principal_pairs(segments, perpendicular_tolerance_degrees=15.0,
                    angle_tolerance_degrees=5.0,
                    minimum_relative_length=0.25,
                    placement_fraction=0.25):
    """Maximum deux paires, de directions voisines de 90 degres.

    Retourne les objets natifs DimensionAxisCandidate de Plans de vente.
    Les dimensions restent les distances entre les faces opposees, pas
    des longueurs de murs. Une seule paire est acceptee si la seconde
    direction principale n'existe pas.
    """
    segments = list(segments or [])
    if len(segments) < 2:
        return []

    available = dominant_dimension_pairs(
        segments,
        angle_tolerance_degrees=angle_tolerance_degrees,
        minimum_relative_length=minimum_relative_length,
        placement_fraction=placement_fraction,
        max_results=len(segments),
    )
    if not available:
        return []

    result = [available[0]]
    first = available[0].tangent
    perpendicular_max_dot = math.sin(
        math.radians(float(perpendicular_tolerance_degrees)))
    for pair in available[1:]:
        second = pair.tangent
        if abs(first[0] * second[0] + first[1] * second[1]) <= perpendicular_max_dot:
            result.append(pair)
            break
    return result


def principal_reference_indexes(segments, **settings):
    """Indices des seules faces appartenant aux paires principales retenues.

    Le service Revit doit conserver les references et leur ordre d'origine.
    """
    indexes = set()
    for pair in principal_pairs(segments, **settings):
        indexes.add(pair.first_index)
        indexes.add(pair.second_index)
    return indexes
