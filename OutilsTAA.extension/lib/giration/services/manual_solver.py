# -*- coding: utf-8 -*-
"""Résolution d'un arc à courbure constante vers un point choisi par clic.

Cette méthode discrète n'est PAS le pilotage continu d'Autodesk Vehicle Tracking.
"""
import math
from ..geometry.vector2d import Vector2D
from .kinematics import AckermannKinematics


def segment_to_rear_axle(vehicle, current_pose, target_rear_axle,
                         reverse=False, max_spacing=0.20):
    """Retourne les poses d'un arc tangent joignant le point de départ au clic.

    Le point cible est le CENTRE de l'essieu arrière, pas l'arrière de la caisse.
    Refuse les segments impossibles pour ce modèle et les demi-tours (>= 180°).
    """
    target = target_rear_axle
    if not isinstance(target, Vector2D):
        target = Vector2D(target[0], target[1])
    theta = current_pose.angle
    start = current_pose.position + Vector2D.from_angle(theta, vehicle.rear_overhang)
    dx, dy = (target - start).rotate(-theta).to_tuple()
    chord2 = dx * dx + dy * dy
    if chord2 < 1e-6:
        raise ValueError('Choisir un point distinct du depart')
    if reverse and dx >= -1e-5:
        raise ValueError('Le prochain point en marche arriere doit etre derriere le vehicule')
    if not reverse and dx <= 1e-5:
        raise ValueError('Le prochain point doit etre devant le vehicule')
    curvature = 2.0 * dy / chord2
    if abs(curvature) < 1e-8:
        steering = 0.0
        distance = abs(dx)
    else:
        steering = math.atan(curvature * vehicle.wheelbase)
        if not vehicle.can_turn(steering):
            raise ValueError('Point inaccessible au rayon de giration minimal')
        angle = 2.0 * math.atan2(dy, dx)
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        arc_length = angle / curvature
        if (reverse and arc_length >= 0) or (not reverse and arc_length <= 0):
            raise ValueError('Arc incompatible avec le sens de marche')
        distance = abs(arc_length)
    samples = int(math.ceil(max(distance / max_spacing,
                    abs(distance * curvature) / math.radians(2.0))))
    samples = max(1, min(5000, samples))
    result = AckermannKinematics(vehicle).calculate_trajectory(
        current_pose.position, theta, steering, distance, reverse, samples)
    end_rear_axle = result[-1].position + Vector2D.from_angle(
        result[-1].angle, vehicle.rear_overhang)
    if end_rear_axle.distance_to(target) > .001:
        raise ValueError('Resolution geometrique non convergente')
    return result
