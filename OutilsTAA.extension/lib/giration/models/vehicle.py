# -*- coding: utf-8 -*-
"""Géométrie paramétrée d'un véhicule RIGIDE à deux essieux."""
import math
from ..geometry.vector2d import Vector2D


class Vehicle(object):
    """Origine (x, y) : milieu du pare-chocs arrière, cap le long de la caisse.

    Les valeurs de rayon mesuré doivent indiquer leur convention (essieu,
    braquage bord à bord, mur à mur). L'angle est un braquage moyen équivalent.
    """

    def __init__(self, name, category="Inconnu", length=0.0, width=0.0,
                 wheelbase=0.0, front_overhang=0.0, rear_overhang=0.0,
                 front_track=0.0, rear_track=0.0, max_steering_angle=0.0,
                 min_turning_radius=None, source=None, reference=None,
                 verified=False, radius_convention=None):
        self.name, self.category = name, category
        self.length, self.width = float(length), float(width)
        self.wheelbase = float(wheelbase)
        self.front_overhang = float(front_overhang)
        self.rear_overhang = float(rear_overhang)
        self.front_track, self.rear_track = float(front_track), float(rear_track)
        self.max_steering_angle = float(max_steering_angle)
        self.source, self.reference = source, reference
        self.verified = bool(verified)
        self.radius_convention = radius_convention
        self._validate_geometry()
        if min_turning_radius is None and self.wheelbase and self.max_steering_angle:
            self.min_turning_radius = self.wheelbase / math.tan(self.max_steering_angle)
            self.radius_convention = 'rear_axle'
        else:
            self.min_turning_radius = min_turning_radius
            if min_turning_radius is not None and not radius_convention:
                self.radius_convention = 'non_documentee'

    def _validate_geometry(self):
        numbers = [self.length, self.width, self.wheelbase, self.front_overhang,
                   self.rear_overhang, self.front_track, self.rear_track,
                   self.max_steering_angle]
        if any(math.isnan(v) or math.isinf(v) or v < 0.0 for v in numbers):
            raise ValueError('Caracteristique negative ou non finie')
        if self.max_steering_angle >= math.pi / 2.0:
            raise ValueError('Braquage superieur ou egal a 90 degres')
        if self.length and self.wheelbase and self.front_overhang and self.rear_overhang and (
                abs(self.front_overhang + self.wheelbase + self.rear_overhang
                    - self.length) > 0.01):
            raise ValueError('Longueur differente de la somme des empattements/porte-a-faux')
        if self.width and max(self.front_track, self.rear_track) > self.width:
            raise ValueError('Voie superieure a la largeur du vehicule')

    @property
    def rear_axle_position(self):
        return self.rear_overhang

    @property
    def front_axle_position(self):
        return self.rear_overhang + self.wheelbase

    @property
    def center_position(self):
        return self.length / 2.0

    def get_axle_positions(self):
        return (self.rear_axle_position, self.front_axle_position)

    def _point(self, x, y, angle, longitudinal, lateral):
        return Vector2D(x + longitudinal * math.cos(angle) - lateral * math.sin(angle),
                        y + longitudinal * math.sin(angle) + lateral * math.cos(angle))

    def get_wheel_positions(self, x=0, y=0, angle=0):
        return {
            'rear_left': self._point(x, y, angle, self.rear_axle_position, self.rear_track / 2.0),
            'rear_right': self._point(x, y, angle, self.rear_axle_position, -self.rear_track / 2.0),
            'front_left': self._point(x, y, angle, self.front_axle_position, self.front_track / 2.0),
            'front_right': self._point(x, y, angle, self.front_axle_position, -self.front_track / 2.0)}

    def get_corners(self, x=0, y=0, angle=0):
        return [self._point(x, y, angle, 0.0, self.width / 2.0),
                self._point(x, y, angle, 0.0, -self.width / 2.0),
                self._point(x, y, angle, self.length, -self.width / 2.0),
                self._point(x, y, angle, self.length, self.width / 2.0)]

    def can_turn(self, steering_angle):
        return abs(steering_angle) <= self.max_steering_angle + 1e-10

    def to_dict(self):
        return dict(name=self.name, category=self.category, length=self.length,
                    width=self.width, wheelbase=self.wheelbase,
                    front_overhang=self.front_overhang, rear_overhang=self.rear_overhang,
                    front_track=self.front_track, rear_track=self.rear_track,
                    max_steering_angle=self.max_steering_angle,
                    min_turning_radius=self.min_turning_radius,
                    source=self.source, reference=self.reference,
                    verified=self.verified, radius_convention=self.radius_convention)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return "Vehicle(name={0!r}, category={1!r})".format(self.name, self.category)

    def __str__(self):
        return self.name
