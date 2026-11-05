# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Positions de repli pour petites pieces, en reutilisant le contrat PDV 06F.

Aucune reference Revit n'est creee ou modifiee ici. La cote reste une
dimension native entre les memes faces finies que Plans de vente.
Ce repli ne se declenche qu'apres echec du placement strict des 2 axes.
"""

import math

from plans_vente.dimension_positioning import DimensionPlacement


def external_candidates(line, room_points, contains, settings,
                        tag_boxes=(), dimension_boxes=(),
                        equipment_boxes=(), witness_anchors=None,
                        text_axis=None, max_positions=4):
    """Decale lateralement une cote hors de l'interieur trop etroit.

    Le texte est calibre par les memes largeur/hauteur papier que PDV.
    Toutes les collisions sont recalculees sur l'ensemble des polygones
    (texte, ligne, temoins) ; les obstacles reels restent bloquants
    par select_collision_free_placements. Au maximum 4 essais/axe.
    """
    if not room_points or not line or len(line) != 2:
        return []
    start, end = line
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        return []
    axis = dx / length, dy / length
    normal = -axis[1], axis[0]
    values = [x * normal[0] + y * normal[1]
              for x, y in room_points]
    low, high = min(values), max(values)
    if high - low <= 1e-9:
        return []
    # Uniquement de petits depassements a l'echelle de la vue :
    # 1 puis 2 fois la hauteur estimee du texte, pas plusieurs metres.
    margin = max(float(settings["text_height"]),
                 float(settings["padding"]) * 2.)
    offsets = (low - margin, high + margin,
               low - 2. * margin, high + 2. * margin)
    original = start[0] * normal[0] + start[1] * normal[1]
    results = []
    for offset in offsets[:max(0, min(int(max_positions), 4))]:
        delta = offset - original
        moved_start = (start[0] + normal[0]*delta,
                       start[1] + normal[1]*delta)
        moved_end = (end[0] + normal[0]*delta,
                     end[1] + normal[1]*delta)
        candidate = DimensionPlacement(
            moved_start, moved_end,
            settings["text_width"], settings["text_height"],
            settings["padding"], settings["witness_length"],
            witness_anchors, text_axis)
        candidate.text_inside = all(
            bool(contains(point)) for polygon in candidate.text_polygons
            for point in polygon)
        candidate.outside_count = sum(
            1 for polygon in candidate.text_polygons
            for point in polygon if not contains(point))
        candidate.tag_hits = candidate.hits_boxes(tag_boxes)
        candidate.dimension_hits = candidate.hits_boxes(dimension_boxes)
        candidate.equipment_hits = candidate.hits_boxes(equipment_boxes)
        candidate.clearance_penalty = sum(
            1 for fraction in (.25, .5, .75)
            for sign in (-1., 1.)
            if not contains((
                moved_start[0] + dx*fraction + normal[0]*sign*
                settings["clearance"],
                moved_start[1] + dy*fraction + normal[1]*sign*
                settings["clearance"])))
        candidate.rank = 20 + len(results)
        candidate.external_compact = True
        results.append(candidate)
    return results
