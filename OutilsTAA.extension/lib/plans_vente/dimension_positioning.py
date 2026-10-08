# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Placement 06F sans Revit : translations parallèles, références inchangées.

Les emprises sont des estimations graphiques, pas des objets Revit temporaires.
Le callback de contenance doit utiliser le Z intérieur validé de la pièce.
"""

import math
from itertools import product

from plans_vente.tag_positioning import boxes_overlap


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _move(p, direction, distance):
    return (p[0] + direction[0] * distance, p[1] + direction[1] * distance)


def _box(points):
    return (min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points))


def _rectangle(center, axis, half_width, half_height):
    normal = (-axis[1], axis[0])
    return [_move(_move(center, axis, x * half_width), normal, y * half_height)
            for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _band(start, end, half_width):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return _rectangle(start, (1, 0), half_width, half_width)
    center = ((start[0] + end[0]) * .5, (start[1] + end[1]) * .5)
    return _rectangle(center, (dx / length, dy / length), length * .5, half_width)


def _box_polygon(box):
    return [(box[0], box[1]), (box[2], box[1]),
            (box[2], box[3]), (box[0], box[3])]


def _overlap(left, right):
    """SAT : ne pas confondre deux grandes AABB de cotes obliques et un contact."""
    if not boxes_overlap(_box(left), _box(right)):
        return False
    for polygon in (left, right):
        for index, point in enumerate(polygon):
            other = polygon[(index + 1) % len(polygon)]
            axis = (point[1] - other[1], other[0] - point[0])
            a = [_dot(p, axis) for p in left]
            b = [_dot(p, axis) for p in right]
            if max(a) <= min(b) or max(b) <= min(a):
                return False
    return True


class DimensionPlacement(object):
    def __init__(self, start, end, text_width, text_height, padding,
                 witness_length, witness_anchors=None, text_axis=None):
        self.line_start, self.line_end = start, end
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        axis = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
        normal = (-axis[1], axis[0])
        center = ((start[0] + end[0]) * .5, (start[1] + end[1]) * .5)
        self.line_polygon = _band(start, end, padding)
        # Le type peut garder le texte horizontal dans la vue ou aligné à la
        # cote : réserver les deux orientations sans changer le texte natif.
        self.text_polygons = [_rectangle(center, axis, text_width * .5, text_height)]
        if text_axis is not None:
            self.text_polygons.append(
                _rectangle(center, text_axis, text_width * .5, text_height))
        self.polygons = [self.line_polygon] + self.text_polygons
        for index, point in enumerate((start, end)):
            anchor = (witness_anchors[index] if witness_anchors else
                      _move(point, normal, -witness_length))
            self.polygons.append(_band(anchor, _move(point, normal, witness_length), padding))
        # Même contrat XY que RoomTagService.exclusion_boxes. Découper la
        # ligne limite les fausses grandes réservations sur les axes obliques.
        self.exclusion_boxes = [_box(p) for p in self.polygons[1:]]
        for index in range(8):
            self.exclusion_boxes.append(_box(_band(
                _move(start, axis, length * index / 8.),
                _move(start, axis, length * (index + 1) / 8.), padding)))
        self.outside_count = 0
        self.tag_hits = 0
        self.dimension_hits = 0
        self.equipment_hits = 0
        self.clearance_penalty = 0.0
        self.rank = 0
        self.warnings = []

    def hits_boxes(self, boxes):
        return sum(1 for box in boxes if any(
            _overlap(polygon, _box_polygon(box)) for polygon in self.polygons))


def _candidate_positions(line, room_points, clearance):
    start, end = line
    length = math.hypot(end[0] - start[0], end[1] - start[1])
    if length < 1e-9:
        raise ValueError("Ligne de cote de longueur nulle.")
    axis = ((end[0] - start[0]) / length, (end[1] - start[1]) / length)
    normal = (-axis[1], axis[0])
    projections = [_dot(p, normal) for p in room_points]
    low, high = min(projections), max(projections)
    original = _dot(start, normal)
    # Dix positions au maximum, dont les deux côtés et des marges réduites.
    raw = []
    for factor in (1., .5, .25):
        gap = min(clearance * factor, (high - low) * .5)
        raw.extend((low + gap, high - gap))
    raw.extend(low + (high - low) * f for f in (.25, .75, .5))
    raw.append(original)
    seen = []
    for value in raw:
        if any(abs(value - old) < 1e-8 for old in seen):
            continue
        seen.append(value)
        yield (_move(start, normal, value - original),
               _move(end, normal, value - original), axis, normal)


def placement_candidates(line, room_points, contains, clearance, text_width,
                         text_height, padding, witness_length, tag_boxes=(),
                         dimension_boxes=(), equipment_boxes=(),
                         witness_anchors=None, text_axis=None):
    """Au plus 10 candidats et 23 sondes intérieures par candidat (sans témoins).

    L'échantillonnage n'est pas une preuve topologique de contenance. Les points
    proches des références sont légèrement rentrés : une limite finie est un
    contact voulu, pas une cote extérieure. Les témoins peuvent toucher le mur.
    """
    if not room_points:
        raise ValueError("Contour de pièce indisponible pour le placement.")
    result = []
    for rank, (start, end, axis, normal) in enumerate(
            _candidate_positions(line, room_points, clearance)):
        candidate = DimensionPlacement(start, end, text_width, text_height,
                                       padding, witness_length, witness_anchors, text_axis)
        length = math.hypot(end[0] - start[0], end[1] - start[1])
        inset = min(padding * 2., length * .02)
        probes = [_move(start, axis, inset + (length - 2 * inset) * i / 8.)
                  for i in range(9)]
        probes.extend(_move(_move(start, axis, length * fraction), normal, sign * padding)
                      for fraction in (.25, .5, .75) for sign in (-1, 1))
        for polygon in candidate.text_polygons:
            probes.extend(polygon)
        candidate.outside_count = sum(1 for p in probes if not contains(p))
        candidate.tag_hits = candidate.hits_boxes(tag_boxes)
        candidate.dimension_hits = candidate.hits_boxes(dimension_boxes)
        candidate.equipment_hits = candidate.hits_boxes(equipment_boxes)
        # Sondes transversales locales : plus fiables qu'une bbox sur une pièce
        # en L, tout en restant bornées (six sondes supplémentaires par candidat).
        candidate.clearance_penalty = sum(
            1 for fraction in (.25, .5, .75) for sign in (-1, 1)
            if not contains(_move(_move(start, axis, length * fraction),
                                  normal, sign * clearance * .95)))
        candidate.rank = rank
        result.append(candidate)
    return result


def placement_conflicts(left, right):
    """Texte prioritaire sur croisement nu de lignes, témoins compris."""
    text_hits = int(any(_overlap(a, b) for a in left.text_polygons for b in right.polygons)
                    or any(_overlap(a, b) for a in right.text_polygons for b in left.polygons))
    graphic_hit = int(any(_overlap(a, b) for a in left.polygons for b in right.polygons))
    return text_hits, graphic_hit


def select_placements(candidate_groups):
    """Choix conjoint des deux cotes : <=100 combinaisons purement géométriques."""
    groups = list(candidate_groups)
    if not groups:
        return []
    if len(groups) > 2 or any(not group for group in groups):
        raise ValueError("Une ou deux familles non vides sont requises.")
    best = None
    for combination in product(*groups):
        text_hits, graphic_hits = (placement_conflicts(*combination)
                                   if len(combination) == 2 else (0, 0))
        outside = [c.outside_count for c in combination]
        score = (sum(bool(n) for n in outside), sum(outside),
                 sum(c.tag_hits for c in combination),
                 sum(c.dimension_hits for c in combination) + text_hits,
                 graphic_hits, sum(c.equipment_hits for c in combination),
                 sum(c.clearance_penalty for c in combination),
                 sum(c.rank for c in combination), tuple(c.rank for c in combination))
        if best is None or score < best[0]:
            best = (score, combination)
    chosen = list(best[1])
    for candidate in chosen:
        candidate.warnings = []
        if candidate.outside_count:
            candidate.warnings.append("emprise intérieure complète introuvable")
        if candidate.tag_hits:
            candidate.warnings.append("collision possible avec une étiquette")
        if candidate.dimension_hits:
            candidate.warnings.append("collision possible avec une cote existante")
        if candidate.equipment_hits:
            candidate.warnings.append("collision possible avec un équipement")
    if len(chosen) == 2:
        text_hits, graphic_hits = placement_conflicts(*chosen)
        if text_hits:
            chosen[1].warnings.append("collision possible avec le texte de l'autre cote")
        elif graphic_hits:
            chosen[1].warnings.append("croisement résiduel des cotes ou témoins")
    return chosen
