# -*- coding: utf-8 -*-
"""Vecteurs 2D indépendants de Revit et d'une dépendance externe."""
import math


class Vector2D(object):
    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return 'Vector2D({0}, {1})'.format(self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, Vector2D) and abs(self.x - other.x) < 1e-10 and abs(self.y - other.y) < 1e-10

    def __ne__(self, other):
        return not self == other

    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, value):
        return Vector2D(self.x * value, self.y * value)

    __rmul__ = __mul__

    def __truediv__(self, value):
        return Vector2D(self.x / value, self.y / value)

    __div__ = __truediv__

    def __neg__(self):
        return Vector2D(-self.x, -self.y)

    @property
    def magnitude_squared(self):
        return self.x * self.x + self.y * self.y

    @property
    def magnitude(self):
        return math.sqrt(self.magnitude_squared)

    def normalize(self):
        return self / self.magnitude if self.magnitude else Vector2D()

    def normalized(self):
        return self.normalize()

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def cross(self, other):
        return self.x * other.y - self.y * other.x

    def angle_to(self, other):
        d = self.magnitude * other.magnitude
        if not d:
            return 0.0
        return math.acos(max(-1.0, min(1.0, self.dot(other) / d)))

    def angle_between(self, other):
        return self.angle_to(other)

    def rotate(self, angle):
        c, s = math.cos(angle), math.sin(angle)
        return Vector2D(self.x * c - self.y * s, self.x * s + self.y * c)

    def rotated(self, angle):
        return self.rotate(angle)

    def distance_to(self, other):
        return (self - other).magnitude

    def distance_squared(self, other):
        return (self - other).magnitude_squared

    def to_tuple(self):
        return self.x, self.y

    def to_list(self):
        return [self.x, self.y]

    @classmethod
    def from_angle(cls, angle, magnitude=1.0):
        return cls(math.cos(angle) * magnitude, math.sin(angle) * magnitude)
