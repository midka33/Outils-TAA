# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Repère 2D pur décrivant l'orientation d'une vue Revit dans le modèle."""

import math


class ViewFrame(object):
    """Repère plan défini par une origine, un axe écran X et un axe écran Y."""

    def __init__(self, origin, right, up):
        self.origin = self._point3(origin)
        self.right = self._normalize(right, "axe horizontal")
        self.up = self._normalize(up, "axe vertical")

        dot = self._dot(self.right, self.up)
        if abs(dot) > 1e-6:
            raise ValueError(
                "Les axes du repère de vue doivent être orthogonaux."
            )

    def project(self, point):
        """Projette un point monde dans les coordonnées écran (u, v)."""
        point = self._point3(point)
        delta = (
            point[0] - self.origin[0],
            point[1] - self.origin[1],
            point[2] - self.origin[2],
        )
        return (
            self._dot(delta, self.right),
            self._dot(delta, self.up),
        )

    def to_world(self, u, v):
        """Reconstruit un point monde situé dans le plan de la vue."""
        u = float(u)
        v = float(v)
        return (
            self.origin[0] + self.right[0] * u + self.up[0] * v,
            self.origin[1] + self.right[1] * u + self.up[1] * v,
            self.origin[2] + self.right[2] * u + self.up[2] * v,
        )

    @staticmethod
    def _point3(value):
        if value is None or len(value) != 3:
            raise ValueError("Un point 3D est requis.")
        return (float(value[0]), float(value[1]), float(value[2]))

    @classmethod
    def _normalize(cls, value, label):
        vector = cls._point3(value)
        length = math.sqrt(cls._dot(vector, vector))
        if length <= 1e-9:
            raise ValueError("{} invalide.".format(label))
        return (
            vector[0] / length,
            vector[1] / length,
            vector[2] / length,
        )

    @staticmethod
    def _dot(left, right):
        return (
            left[0] * right[0]
            + left[1] * right[1]
            + left[2] * right[2]
        )
