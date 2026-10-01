# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Calcul pur d'une emprise rectangulaire pour le prototype de crop."""


class CropBounds(object):
    def __init__(self, min_x, min_y, max_x, max_y, z=0.0):
        self.min_x = float(min_x)
        self.min_y = float(min_y)
        self.max_x = float(max_x)
        self.max_y = float(max_y)
        self.z = float(z)
        if self.max_x <= self.min_x or self.max_y <= self.min_y:
            raise ValueError("L'emprise de crop doit avoir une largeur et une hauteur positives.")

    @property
    def width(self):
        return self.max_x - self.min_x

    @property
    def height(self):
        return self.max_y - self.min_y

    def expanded(self, margin):
        margin = float(margin or 0.0)
        if margin < 0:
            raise ValueError("La marge de crop ne peut pas être négative.")
        return CropBounds(
            self.min_x - margin,
            self.min_y - margin,
            self.max_x + margin,
            self.max_y + margin,
            self.z,
        )

    @classmethod
    def from_points(cls, points):
        values = list(points or [])
        if not values:
            raise ValueError("Aucun point disponible pour calculer le crop.")

        xs = [float(point[0]) for point in values]
        ys = [float(point[1]) for point in values]
        zs = [float(point[2]) for point in values]

        return cls(
            min(xs),
            min(ys),
            max(xs),
            max(ys),
            sum(zs) / float(len(zs)),
        )
