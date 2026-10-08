# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Géométrie pure du prototype 07A — placement sur feuille."""


class SheetAnchor(object):
    def __init__(self, key, x, y):
        self.key = key or ""
        self.x = float(x)
        self.y = float(y)


def default_sheet_anchors(min_x, min_y, max_x, max_y):
    """Retourne les quatre ancrages V1 à partir de l'emprise de la feuille.

    Les coordonnées Revit de feuille sont en unités internes ; cette fonction
    reste volontairement indépendante de l'API Revit.
    """
    min_x = float(min_x)
    min_y = float(min_y)
    max_x = float(max_x)
    max_y = float(max_y)

    width = max_x - min_x
    height = max_y - min_y
    if width <= 0.0 or height <= 0.0:
        raise ValueError("Emprise de feuille invalide.")

    def point(key, fx, fy):
        return SheetAnchor(
            key,
            min_x + (width * float(fx)),
            min_y + (height * float(fy)),
        )

    return {
        "main_view": point("main_view", 0.38, 0.58),
        "location_view": point("location_view", 0.79, 0.73),
        "interior_schedule": point("interior_schedule", 0.67, 0.38),
        "exterior_schedule": point("exterior_schedule", 0.67, 0.22),
    }
