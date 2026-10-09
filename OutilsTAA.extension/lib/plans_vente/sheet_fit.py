# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Calculs purs du 07C — ajustement d'échelle sur la zone modèle."""

import re


DEFAULT_ALLOWED_SCALES = (25, 50, 75, 100)


def parse_allowed_scales(value, default=None):
    """Normalise une liste / chaîne d'échelles en dénominateurs positifs."""
    if default is None:
        default = DEFAULT_ALLOWED_SCALES

    if value is None:
        values = list(default)
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        text = str(value or "").strip()
        if not text:
            values = list(default)
        else:
            values = [
                token
                for token in re.split(r"[^0-9]+", text)
                if token
            ]

    result = []
    for value in values:
        try:
            scale = int(value)
        except Exception:
            continue
        if scale <= 0 or scale in result:
            continue
        result.append(scale)

    if not result:
        raise ValueError("Indiquez au moins une échelle positive.")

    return sorted(result)


def choose_fitting_scale(
    current_scale,
    current_width,
    current_height,
    target_width,
    target_height,
    allowed_scales=None,
):
    """Choisit l'échelle qui remplit le plus la zone sans la dépasser.

    Le calcul utilise l'emprise réellement mesurée du viewport à l'échelle
    courante puis applique la relation inverse entre taille papier et
    dénominateur d'échelle. La mesure Revit finale reste contrôlée ensuite.
    """
    scales = parse_allowed_scales(allowed_scales)

    current_scale = int(current_scale)
    current_width = float(current_width)
    current_height = float(current_height)
    target_width = float(target_width)
    target_height = float(target_height)

    if (
        current_scale <= 0
        or current_width <= 0.0
        or current_height <= 0.0
        or target_width <= 0.0
        or target_height <= 0.0
    ):
        raise ValueError("Dimensions ou échelle invalides pour l'ajustement.")

    for scale in scales:
        predicted_width = current_width * float(current_scale) / float(scale)
        predicted_height = current_height * float(current_scale) / float(scale)
        if (
            predicted_width <= target_width + 1e-9
            and predicted_height <= target_height + 1e-9
        ):
            return scale

    return scales[-1]


def viewport_fits(width, height, target_width, target_height, tolerance=1e-6):
    return (
        float(width) <= float(target_width) + float(tolerance)
        and float(height) <= float(target_height) + float(tolerance)
    )



def scale_candidates_from_reference(reference_scale, allowed_scales=None):
    """Référence d'abord, puis uniquement des échelles plus petites graphiquement."""
    reference_scale = int(reference_scale)
    if reference_scale <= 0:
        raise ValueError("Échelle de référence invalide.")

    allowed = parse_allowed_scales(allowed_scales)
    result = [reference_scale]
    for scale in allowed:
        if scale > reference_scale and scale not in result:
            result.append(scale)
    return result


def rectangles_overlap(left, right, clearance=0.0):
    """Teste deux rectangles (min_x, min_y, max_x, max_y)."""
    clearance = max(0.0, float(clearance))
    return not (
        float(left[2]) + clearance <= float(right[0])
        or float(right[2]) + clearance <= float(left[0])
        or float(left[3]) + clearance <= float(right[1])
        or float(right[3]) + clearance <= float(left[1])
    )


def segment_intersects_rectangle(start, end, rectangle, clearance=0.0):
    """Intersection 2D segment/rectangle, avec marge optionnelle."""
    min_x, min_y, max_x, max_y = [float(value) for value in rectangle]
    clearance = max(0.0, float(clearance))
    min_x -= clearance
    min_y -= clearance
    max_x += clearance
    max_y += clearance

    x1, y1 = float(start[0]), float(start[1])
    x2, y2 = float(end[0]), float(end[1])

    if (
        min_x <= x1 <= max_x
        and min_y <= y1 <= max_y
    ) or (
        min_x <= x2 <= max_x
        and min_y <= y2 <= max_y
    ):
        return True

    def orientation(ax, ay, bx, by, cx, cy):
        return ((bx - ax) * (cy - ay)) - ((by - ay) * (cx - ax))

    def on_segment(ax, ay, bx, by, cx, cy):
        return (
            min(ax, bx) - 1e-12 <= cx <= max(ax, bx) + 1e-12
            and min(ay, by) - 1e-12 <= cy <= max(ay, by) + 1e-12
        )

    def intersects(a, b, c, d):
        o1 = orientation(a[0], a[1], b[0], b[1], c[0], c[1])
        o2 = orientation(a[0], a[1], b[0], b[1], d[0], d[1])
        o3 = orientation(c[0], c[1], d[0], d[1], a[0], a[1])
        o4 = orientation(c[0], c[1], d[0], d[1], b[0], b[1])

        if (
            ((o1 > 0 and o2 < 0) or (o1 < 0 and o2 > 0))
            and ((o3 > 0 and o4 < 0) or (o3 < 0 and o4 > 0))
        ):
            return True

        if abs(o1) <= 1e-12 and on_segment(a[0], a[1], b[0], b[1], c[0], c[1]):
            return True
        if abs(o2) <= 1e-12 and on_segment(a[0], a[1], b[0], b[1], d[0], d[1]):
            return True
        if abs(o3) <= 1e-12 and on_segment(c[0], c[1], d[0], d[1], a[0], a[1]):
            return True
        if abs(o4) <= 1e-12 and on_segment(c[0], c[1], d[0], d[1], b[0], b[1]):
            return True
        return False

    segment_a = (x1, y1)
    segment_b = (x2, y2)
    edges = (
        ((min_x, min_y), (max_x, min_y)),
        ((max_x, min_y), (max_x, max_y)),
        ((max_x, max_y), (min_x, max_y)),
        ((min_x, max_y), (min_x, min_y)),
    )
    return any(
        intersects(segment_a, segment_b, edge_a, edge_b)
        for edge_a, edge_b in edges
    )
