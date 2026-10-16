# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Géométrie pure pour le placement des étiquettes de pièces."""


def polygon_area(points):
    values = list(points or [])
    if len(values) < 3:
        return 0.0

    total = 0.0
    for index, point in enumerate(values):
        following = values[(index + 1) % len(values)]
        total += (point[0] * following[1]) - (following[0] * point[1])
    return 0.5 * total


def polygon_centroid(points):
    values = list(points or [])
    if not values:
        raise ValueError("Aucun point disponible pour calculer le centre.")

    area = polygon_area(values)
    if abs(area) <= 1e-12:
        return (
            sum(point[0] for point in values) / float(len(values)),
            sum(point[1] for point in values) / float(len(values)),
        )

    factor_sum_x = 0.0
    factor_sum_y = 0.0
    for index, point in enumerate(values):
        following = values[(index + 1) % len(values)]
        cross = (point[0] * following[1]) - (following[0] * point[1])
        factor_sum_x += (point[0] + following[0]) * cross
        factor_sum_y += (point[1] + following[1]) * cross

    denominator = 6.0 * area
    return (factor_sum_x / denominator, factor_sum_y / denominator)


def ordered_candidate_points(points, location_point=None):
    """Produit des points centraux puis une grille de secours, sans Revit."""
    values = list(points or [])
    if not values:
        return []

    xs = [point[0] for point in values]
    ys = [point[1] for point in values]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    centroid = polygon_centroid(values)
    bbox_center = ((min_x + max_x) * 0.5, (min_y + max_y) * 0.5)

    raw = [centroid, bbox_center]
    if location_point is not None:
        raw.append((float(location_point[0]), float(location_point[1])))

    fractions = (0.5, 0.35, 0.65, 0.2, 0.8)
    grid = []
    for fx in fractions:
        for fy in fractions:
            point = (
                min_x + ((max_x - min_x) * fx),
                min_y + ((max_y - min_y) * fy),
            )
            distance = (
                ((point[0] - centroid[0]) ** 2)
                + ((point[1] - centroid[1]) ** 2)
            )
            grid.append((distance, point))
    grid.sort(key=lambda item: item[0])
    raw.extend(point for _, point in grid)

    result = []
    for point in raw:
        if not any(
            abs(point[0] - existing[0]) <= 1e-9
            and abs(point[1] - existing[1]) <= 1e-9
            for existing in result
        ):
            result.append(point)
    return result


def boxes_overlap(left, right, padding=0.0):
    if left is None or right is None:
        return False

    pad = max(0.0, float(padding or 0.0))
    return not (
        left[2] + pad <= right[0]
        or right[2] + pad <= left[0]
        or left[3] + pad <= right[1]
        or right[3] + pad <= left[1]
    )
