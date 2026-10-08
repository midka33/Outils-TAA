# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Géométrie pure pour les deux cotations principales d'une pièce."""

import math
import re
import unicodedata


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



def segment_match_metrics(
    reference_segment,
    candidate_segment,
    angle_tolerance_degrees=3.0,
    distance_tolerance=0.1,
    minimum_overlap_ratio=0.6,
):
    """Mesure si deux segments sont assez parallèles et superposés.

    Retourne un dictionnaire avec distance, recouvrement et score, ou None si
    le candidat n'est pas suffisamment proche. Les unités sont celles des
    coordonnées fournies (pieds internes Revit côté service).
    """
    reference_direction = _canonical_direction(reference_segment)
    candidate_direction = _canonical_direction(candidate_segment)
    if reference_direction is None or candidate_direction is None:
        return None

    tolerance = math.cos(math.radians(float(angle_tolerance_degrees)))
    if abs(_dot(reference_direction, candidate_direction)) < tolerance:
        return None

    reference_length = _length(reference_segment)
    if reference_length <= 1e-12:
        return None

    normal = (-reference_direction[1], reference_direction[0])
    reference_midpoint = _midpoint(reference_segment)
    candidate_midpoint = _midpoint(candidate_segment)
    delta = (
        candidate_midpoint[0] - reference_midpoint[0],
        candidate_midpoint[1] - reference_midpoint[1],
    )
    distance = abs(_dot(delta, normal))
    if distance > float(distance_tolerance):
        return None

    reference_interval = _projection_interval(
        reference_segment,
        reference_direction,
    )
    candidate_interval = _projection_interval(
        candidate_segment,
        reference_direction,
    )
    overlap = max(
        0.0,
        min(reference_interval[1], candidate_interval[1])
        - max(reference_interval[0], candidate_interval[0]),
    )
    overlap_ratio = overlap / reference_length
    if overlap_ratio + 1e-12 < float(minimum_overlap_ratio):
        return None

    # Score faible = meilleur. La distance géométrique reste prioritaire,
    # puis le manque de recouvrement départage les candidats quasi confondus.
    score = distance + (
        max(0.0, 1.0 - overlap_ratio) * float(distance_tolerance)
    )
    return {
        "distance": distance,
        "overlap_ratio": overlap_ratio,
        "score": score,
    }


def is_circulation_name(name):
    """Noms métier explicites ; ne pas reclasser une chambre étroite."""
    try:
        text_type = unicode
    except NameError:
        text_type = str
    value = unicodedata.normalize("NFKD", text_type(name or "").lower())
    value = "".join(c for c in value if not unicodedata.combining(c))
    words = set(re.findall(r"[a-z]+", value))
    return bool(words.intersection((
        "entree", "entrees", "couloir", "couloirs", "degagement",
        "degagements", "dgt", "dgtmt", "degt", "circulation", "circulations")))


def circulation_width_pairs(segments, contains, minimum_width,
                            minimum_overlap, angle_tolerance_degrees=5.0):
    """Largeurs locales entre faces en vis-à-vis, une par direction (max. 2).

    Le recouvrement longitudinal doit être au moins égal à la largeur : une
    longueur générale entre deux bouts courts de couloir n'est pas une largeur.
    Les cinq sections intérieures sondées déterminent une plage locale où 06F
    peut déplacer la cote. Le budget est limité à 40 paires / 1 400 sondes.
    """
    values = list(segments or [])
    tolerance = math.cos(math.radians(float(angle_tolerance_degrees)))
    ranked = []
    for first_index, first in enumerate(values):
        tangent = _canonical_direction(first)
        if tangent is None:
            continue
        normal = (-tangent[1], tangent[0])
        for second_index in range(first_index + 1, len(values)):
            second = values[second_index]
            direction = _canonical_direction(second)
            if direction is None or abs(_dot(tangent, direction)) < tolerance:
                continue
            first_interval = _projection_interval(first, tangent)
            second_interval = _projection_interval(second, tangent)
            low = max(first_interval[0], second_interval[0])
            high = min(first_interval[1], second_interval[1])
            overlap = high - low
            first_n = _dot(_midpoint(first), normal)
            second_n = _dot(_midpoint(second), normal)
            width = abs(second_n - first_n)
            if width < minimum_width or overlap < max(minimum_overlap, width):
                continue
            # La continuité des faces est plus représentative qu'un minuscule
            # pincement. À support égal, préférer la largeur la plus faible.
            score = overlap / width
            ranked.append((score, overlap, first_index, second_index,
                           tangent, normal, first_n, second_n, low, high))
    ranked.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
    result = []
    checked = 0
    for score, overlap, first_index, second_index, tangent, normal, first_n, second_n, low, high in ranked:
        if any(abs(_dot(tangent, pair.tangent)) >= tolerance for pair in result):
            continue
        if checked >= 40:
            break
        checked += 1
        # Écarter les sections traversant l'extérieur (L, gaines, murs). Ne pas
        # supposer que deux segments parallèles encadrent le même bras.
        samples = []
        for fraction in (.1, .3, .5, .7, .9):
            along = low + overlap * fraction
            valid = all(contains(_point_from_axes(
                tangent, normal, along, first_n + (second_n - first_n) * across))
                for across in (.02, .18, .34, .5, .66, .82, .98))
            samples.append((along, valid))
        runs, current = [], []
        for along, valid in samples:
            if valid:
                current.append(along)
            else:
                if current:
                    runs.append(current)
                current = []
        if current:
            runs.append(current)
        # Au moins deux sections voisines : pas une ouverture ponctuelle.
        runs = [run for run in runs if len(run) >= 2]
        if not runs:
            continue
        run = max(runs, key=lambda item: (len(item), -item[0]))
        along = (run[0] + run[-1]) * .5
        pair = DimensionAxisCandidate(
            first_index, second_index, tangent, normal, abs(second_n - first_n),
            _point_from_axes(tangent, normal, along, first_n),
            _point_from_axes(tangent, normal, along, second_n), score)
        pair.placement_points = [_point_from_axes(tangent, normal, t, n)
                                 for t in (run[0], run[-1])
                                 for n in (first_n, second_n)]
        result.append(pair)
        if len(result) == 2:
            break
    return result
