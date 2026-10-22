# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Raccordement des cotes paralleles sur une ligne graphique commune.

Une ligne de cote peut etre translatee dans la direction perpendiculaire
sans changer les References Revit. Les alignements ne sont retenus que
pour des cotes voisines, de meme orientation, et si le placement passe
ensuite tous les controles de collision et de contenance.
"""

import math

from plans_vente.dimension_positioning import DimensionPlacement


def _dot(left, right):
    return left[0] * right[0] + left[1] * right[1]


def _axis(line):
    start, end = line
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    return dx / length, dy / length


def _projection_interval(line, axis):
    a = _dot(line[0], axis)
    b = _dot(line[1], axis)
    return min(a, b), max(a, b)


def _interval_gap(a, b):
    return max(0.0, max(a[0] - b[1], b[0] - a[1]))


def matching_rails(line, rails, max_neighbor_gap,
                   max_angle_degrees=0.05):
    """Rails de cotation voisins et paralleles ; aucune direction imposee."""
    axis = _axis(line)
    if axis is None:
        return []
    normal = -axis[1], axis[0]
    t_minmax = _projection_interval(line, axis)
    cos_limit = math.cos(math.radians(max_angle_degrees))
    result = []
    for rail in rails or ():
        other = _axis(rail)
        if other is None or abs(_dot(axis, other)) < cos_limit:
            continue
        gap = _interval_gap(t_minmax, _projection_interval(rail, axis))
        if gap > max_neighbor_gap:
            continue
        result.append((_dot(rail[0], normal), gap))
    return sorted(result, key=lambda item: item[1])


def alignment_penalty(candidate, rails, max_neighbor_gap, snap_tolerance,
                      angle_degrees=0.05):
    """0 si candidat aligne sur un rail voisin ; 1 dans les autres cas."""
    line = candidate.line_start, candidate.line_end
    axis = _axis(line)
    if axis is None:
        return 1
    normal = -axis[1], axis[0]
    value = _dot(line[0], normal)
    return 0 if any(
        abs(value - offset) <= snap_tolerance
        for offset, gap in matching_rails(
            line, rails, max_neighbor_gap, angle_degrees)) else 1


def aligned_candidates(line, room_points, rails, contains, settings,
                       tag_boxes=(), dimension_boxes=(), equipment_boxes=(),
                       witness_anchors=None, text_axis=None,
                       max_neighbor_gap=8., max_angle_degrees=5.0):
    """Ajoute des positions exactement colineaires aux cotes voisines.

    Ces positions sont evaluees via le meme contrat graphique que
    les candidats du moteur 06F, sans assouplir collision ni texte interieur.
    """
    axis = _axis(line)
    if axis is None or not room_points:
        return []
    normal = -axis[1], axis[0]
    limits = [_dot(point, normal) for point in room_points]
    low, high = min(limits), max(limits)
    margin = max(settings["padding"] * 2.,
                 settings["text_height"])
    existing_offset = _dot(line[0], normal)
    result = []
    for offset, gap in matching_rails(
            line, rails, max_neighbor_gap, max_angle_degrees):
        if not low + margin < offset < high - margin:
            continue
        if abs(offset - existing_offset) < 1e-8:
            continue
        if any(abs(offset - candidate.alignment_offset) < 1e-7
               for candidate in result):
            continue

        dx = normal[0] * (offset - existing_offset)
        dy = normal[1] * (offset - existing_offset)
        start = line[0][0] + dx, line[0][1] + dy
        end = line[1][0] + dx, line[1][1] + dy
        candidate = DimensionPlacement(
            start, end, settings["text_width"], settings["text_height"],
            settings["padding"], settings["witness_length"],
            witness_anchors, text_axis)
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        inset = min(settings["padding"] * 2., length * .02)
        probes = [
            (start[0] + axis[0] * (inset + (length - 2 * inset) * i / 8.),
             start[1] + axis[1] * (inset + (length - 2 * inset) * i / 8.))
            for i in range(9)
        ]
        for fraction in (.25, .5, .75):
            for sign in (-1, 1):
                probes.append((
                    start[0] + axis[0] * length * fraction
                    + normal[0] * sign * settings["padding"],
                    start[1] + axis[1] * length * fraction
                    + normal[1] * sign * settings["padding"]))
        for polygon in candidate.text_polygons:
            probes.extend(polygon)
        candidate.outside_count = sum(
            1 for probe in probes if not contains(probe))
        candidate.tag_hits = candidate.hits_boxes(tag_boxes)
        candidate.dimension_hits = candidate.hits_boxes(dimension_boxes)
        candidate.equipment_hits = candidate.hits_boxes(equipment_boxes)
        candidate.clearance_penalty = sum(
            1 for fraction in (.25, .5, .75) for sign in (-1, 1)
            if not contains((
                start[0] + axis[0] * length * fraction
                + normal[0] * sign * settings["clearance"] * .95,
                start[1] + axis[1] * length * fraction
                + normal[1] * sign * settings["clearance"] * .95)))
        candidate.text_inside = all(
            contains(point)
            for polygon in candidate.text_polygons for point in polygon)
        candidate.alignment_offset = offset
        candidate.rank = 10 + len(result)
        result.append(candidate)
    return result
