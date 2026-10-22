# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Deux plus grandes dimensions entre faces finies opposees.

Aucun angle de perpendicularite impose : les pieces biaises peuvent avoir
leurs deux plus grandes dimensions dans des directions obliques.
Le moteur geometrique de Plans de vente reste la source des paires.
"""

from plans_vente.dimension_geometry import dominant_dimension_pairs


def principal_pairs(segments, angle_tolerance_degrees=5.0,
                    minimum_relative_length=0.25,
                    placement_fraction=0.25):
    """Choisit les deux plus grandes distances mesurables sur deux axes utiles.

    Le moteur PDV fournit une paire dominante *par famille de directions*.
    Tri prioritaire par distance entre faces (pas la longueur de leurs murs).
    A distance egale, la longueur des faces et le score PDV departagent.
    Aucune direction n'est exigee perpendiculaire a une autre.
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
    available.sort(key=lambda pair: (pair.distance, pair.score), reverse=True)
    return available[:2]


def principal_reference_indexes(segments, **settings):
    """Indices des references exactes des deux paires retenues.

    Le service Revit conserve les References et leur ordre sans modification.
    """
    indexes = set()
    for pair in principal_pairs(segments, **settings):
        indexes.add(pair.first_index)
        indexes.add(pair.second_index)
    return indexes
