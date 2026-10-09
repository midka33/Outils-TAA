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
