# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Géométrie pure pour les deux cotations principales d'une pièce."""

import math


class DimensionAxisCandidate(object):
    def __init__(
        self,
        first_index,
        second_index,
        tangent,
        normal,
        distance,
        line_start,
        line_end,
        score,
    ):
        self.first_index = int(first_index)
        self.second_index = int(second_index)
        self.tangent = tangent
        self.normal = normal
        self.distance = float(distance)
        self.line_start = line_start
        self.line_end = line_end
        self.score = float(score)


def _length(segment):
    dx = float(segment[2]) - float(segment[0])
    dy = float(segment[3]) - float(segment[1])
    return math.sqrt((dx * dx) + (dy * dy))


def _canonical_direction(segment):
    length = _length(segment)
    if length <= 1e-12:
        return None

    dx = (float(segment[2]) - float(segment[0])) / length
    dy = (float(segment[3]) - float(segment[1])) / length

    # Une direction de mur n'a pas de sens orienté pour nos besoins.
    # On normalise donc le signe pour regrouper (1, 0) et (-1, 0).
    if dx < -1e-12 or (abs(dx) <= 1e-12 and dy < 0.0):
        dx = -dx
        dy = -dy

    return (dx, dy)


def _dot(left, right):
    return (left[0] * right[0]) + (left[1] * right[1])


def _midpoint(segment):
    return (
        (float(segment[0]) + float(segment[2])) * 0.5,
        (float(segment[1]) + float(segment[3])) * 0.5,
    )


def _projection_interval(segment, axis):
    a = (float(segment[0]) * axis[0]) + (float(segment[1]) * axis[1])
    b = (float(segment[2]) * axis[0]) + (float(segment[3]) * axis[1])
    return (min(a, b), max(a, b))


def _point_from_axes(tangent, normal, tangent_value, normal_value):
    return (
        (tangent[0] * tangent_value) + (normal[0] * normal_value),
        (tangent[1] * tangent_value) + (normal[1] * normal_value),
    )


def dominant_dimension_pairs(
    segments,
    angle_tolerance_degrees=5.0,
    minimum_relative_length=0.25,
    placement_fraction=0.25,
    max_results=2,
):
    """Retourne les paires de limites les plus représentatives.

    segments contient des tuples (x1, y1, x2, y2). La fonction ne dépend pas
    de Revit afin de pouvoir être testée hors Revit.

    Le filtrage des petits décrochements est effectué dans chaque famille de
    directions. Cela évite qu'un couloir long fasse disparaître ses deux
    petits côtés, tout en écartant les micro-segments d'une niche.
    """
    values = list(segments or [])
    prepared = []
    for index, segment in enumerate(values):
        length = _length(segment)
        direction = _canonical_direction(segment)
        if direction is None:
            continue
        prepared.append(
            {
                "index": index,
                "segment": segment,
                "length": length,
                "direction": direction,
                "midpoint": _midpoint(segment),
            }
        )

    # Deux limites suffisent pour former une cote entre faces opposées.
    # L'ancien seuil à 4 excluait à tort les pièces dont une limite est courbe
    # ou non exploitable mais qui possèdent tout de même une paire parallèle.
    if len(prepared) < 2:
        return []

    tolerance = math.cos(math.radians(float(angle_tolerance_degrees)))
    clusters = []

    for item in prepared:
        target = None
        for cluster in clusters:
            if abs(_dot(item["direction"], cluster["direction"])) >= tolerance:
                target = cluster
                break
        if target is None:
            target = {
                "direction": item["direction"],
                "items": [],
            }
            clusters.append(target)
        target["items"].append(item)

    candidates = []
    relative = max(0.0, min(1.0, float(minimum_relative_length)))
    fraction = max(0.0, min(1.0, float(placement_fraction)))

    for cluster in clusters:
        items = cluster["items"]
        if len(items) < 2:
            continue

        max_length = max(item["length"] for item in items)
        usable = [
            item for item in items
            if item["length"] + 1e-12 >= (max_length * relative)
        ]
        if len(usable) < 2:
            continue

        tangent = cluster["direction"]
        normal = (-tangent[1], tangent[0])

        best = None
        for left_index in range(len(usable) - 1):
            left = usable[left_index]
            left_normal = _dot(left["midpoint"], normal)

            for right_index in range(left_index + 1, len(usable)):
                right = usable[right_index]
                right_normal = _dot(right["midpoint"], normal)
                separation = abs(right_normal - left_normal)
                if separation <= 1e-9:
                    continue

                pair_score = separation * min(left["length"], right["length"])
                if best is None or pair_score > best[0]:
                    best = (
                        pair_score,
                        separation,
                        left,
                        right,
                        left_normal,
                        right_normal,
                    )

        if best is None:
            continue

        pair_score, separation, left, right, left_normal, right_normal = best
        left_interval = _projection_interval(left["segment"], tangent)
        right_interval = _projection_interval(right["segment"], tangent)

        overlap_min = max(left_interval[0], right_interval[0])
        overlap_max = min(left_interval[1], right_interval[1])

        if overlap_max > overlap_min + 1e-9:
            tangent_value = overlap_min + (
                (overlap_max - overlap_min) * fraction
            )
        else:
            tangent_value = (
                _dot(left["midpoint"], tangent)
                + _dot(right["midpoint"], tangent)
            ) * 0.5

        line_start = _point_from_axes(
            tangent,
            normal,
            tangent_value,
            left_normal,
        )
        line_end = _point_from_axes(
            tangent,
            normal,
            tangent_value,
            right_normal,
        )

        candidates.append(
            DimensionAxisCandidate(
                first_index=left["index"],
                second_index=right["index"],
                tangent=tangent,
                normal=normal,
                distance=separation,
                line_start=line_start,
                line_end=line_end,
                score=pair_score,
            )
        )

    candidates.sort(key=lambda item: item.score, reverse=True)
    limit = max(0, int(max_results or 0))
    return candidates[:limit] if limit else []



def representative_length_indexes(
    segments,
    angle_tolerance_degrees=12.0,
    max_results=2,
):
    """Retourne les segments longs les plus représentatifs par direction.

    Une seule limite est conservée par famille de directions afin d'éviter de
    proposer deux longueurs parallèles comme les deux dimensions principales.
    """
    values = list(segments or [])
    prepared = []
    for index, segment in enumerate(values):
        length = _length(segment)
        direction = _canonical_direction(segment)
        if direction is None:
            continue
        prepared.append(
            {
                "index": index,
                "length": length,
                "direction": direction,
            }
        )

    prepared.sort(key=lambda item: item["length"], reverse=True)
    tolerance = math.cos(math.radians(float(angle_tolerance_degrees)))
    selected = []

    for item in prepared:
        if any(
            abs(_dot(item["direction"], existing["direction"])) >= tolerance
            for existing in selected
        ):
            continue
        selected.append(item)
        if len(selected) >= int(max_results or 0):
            break

    return [item["index"] for item in selected]
