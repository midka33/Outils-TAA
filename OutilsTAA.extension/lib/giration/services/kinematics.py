# -*- coding: utf-8 -*-
"""Cinématique du vélo équivalent d'un véhicule rigide à deux essieux.

Coordonnées en mètres ; angle en radians ; point de trajectoire = centre du
pare-chocs arrière (origine longitudinale de la carrosserie).
Le modèle suppose un roulement sans glissement et un braquage avant moyen.
"""
import math

from ..geometry.vector2d import Vector2D

_EPS = 1e-9


class TrajectoryPoint(object):
    """Position de l'arrière de la carrosserie et cap du véhicule."""

    def __init__(self, position, angle=0.0, steering_angle=0.0,
                 is_reverse=False, timestamp=0.0):
        self.position = _vector(position)
        self.angle = float(angle)
        self.steering_angle = float(steering_angle)
        self.is_reverse = bool(is_reverse)
        self.timestamp = float(timestamp)

    def __repr__(self):
        return "TrajectoryPoint(pos={0}, angle={1}, steer={2}, reverse={3})".format(
            self.position, self.angle, self.steering_angle, self.is_reverse)

    def to_dict(self):
        return dict(x=self.position.x, y=self.position.y, angle=self.angle,
                    steering_angle=self.steering_angle, is_reverse=self.is_reverse,
                    timestamp=self.timestamp)

    @classmethod
    def from_dict(cls, data):
        return cls((data['x'], data['y']), data.get('angle', 0.0),
                   data.get('steering_angle', 0.0), data.get('is_reverse', False),
                   data.get('timestamp', 0.0))


def _vector(value):
    if isinstance(value, Vector2D):
        return value
    return Vector2D(value[0], value[1])


def _unit(theta):
    return Vector2D(math.cos(theta), math.sin(theta))


def _finite(value):
    return not (math.isnan(value) or math.isinf(value))


class AckermannKinematics(object):
    """Intégration analytique par courbure constante sur chaque segment.

    La courbure k = tan(delta) / empattement est celle de l'essieu arrière.
    Pour la marche arrière, l'abscisse curviligne est signée. Les limites de
    vitesse de rotation du volant ne sont *pas* modélisées.
    """

    def __init__(self, vehicle):
        self.vehicle = vehicle

    def calculate_trajectory(self, start_point, start_angle=0.0,
                             steering_angle=0.0, distance=0.0,
                             is_reverse=False, num_points=10):
        distance = float(distance)
        steering_angle = float(steering_angle)
        start_angle = float(start_angle)
        count = int(num_points)
        if count < 1 or distance < 0.0 or not all(_finite(v) for v in
                (distance, steering_angle, start_angle)):
            raise ValueError("Distance, cap ou echantillonnage invalides")
        if self.vehicle.wheelbase <= 0:
            raise ValueError("Empattement nul")
        if not self.vehicle.can_turn(steering_angle):
            raise ValueError("Angle de braquage hors capacite")
        rear_body = _vector(start_point)
        rear_axle = rear_body + _unit(start_angle) * self.vehicle.rear_overhang
        curvature = math.tan(steering_angle) / self.vehicle.wheelbase
        signed_length = -distance if is_reverse else distance
        points = []
        for index in range(count + 1):
            s = signed_length * index / float(count)
            heading = start_angle + curvature * s
            if abs(curvature) < _EPS:
                axle = rear_axle + _unit(start_angle) * s
            else:
                axle = Vector2D(
                    rear_axle.x + (math.sin(heading) - math.sin(start_angle)) / curvature,
                    rear_axle.y - (math.cos(heading) - math.cos(start_angle)) / curvature)
            body = axle - _unit(heading) * self.vehicle.rear_overhang
            points.append(TrajectoryPoint(body, heading, steering_angle, is_reverse))
        return points

    def calculate_path(self, start_point, start_angle=0.0, segments=None):
        if not segments:
            return [TrajectoryPoint(start_point, start_angle)]
        result = []
        position = _vector(start_point)
        angle = float(start_angle)
        for segment in segments:
            section = self.calculate_trajectory(
                position, angle, segment.get('steering_angle', 0.0),
                segment.get('distance', 0.0), segment.get('is_reverse', False),
                segment.get('num_points', 10))
            result.extend(section if not result else section[1:])
            position, angle = section[-1].position, section[-1].angle
        return result

    def _body_origin(self, point, reference_point):
        if reference_point == 'rear':
            return point.position
        if reference_point == 'center':
            return point.position - _unit(point.angle) * self.vehicle.center_position
        raise ValueError("Point de reference inconnu: {0}".format(reference_point))

    def calculate_wheel_trajectories(self, trajectory, reference_point='rear'):
        wheels = dict(front_left=[], front_right=[], rear_left=[], rear_right=[])
        for point in trajectory:
            p = self._body_origin(point, reference_point)
            positions = self.vehicle.get_wheel_positions(p.x, p.y, point.angle)
            for name in wheels:
                wheels[name].append(positions[name])
        return wheels

    def calculate_swept_area(self, trajectory, reference_point='rear'):
        """Empreintes successives, PAS union de l'enveloppe balayée.

        Fonction historique conservée pour les appels/tests antérieurs. Son nom
        est ambigu : ne PAS présenter cette sortie comme un contour continu.
        """
        result = []
        for point in trajectory:
            p = self._body_origin(point, reference_point)
            result.append(self.vehicle.get_corners(p.x, p.y, point.angle))
        return result

    def calculate_swept_mesh(self, trajectory, reference_point='rear'):
        """Maillage approché entre les empreintes pour contrôle visuel.

        Une union polygonale robuste et les vrais contours externes/internes
        restent à développer et comparer à des résultats de référence.
        """
        footprints = self.calculate_swept_area(trajectory, reference_point)
        polygons = [list(p) for p in footprints]
        for before, after in zip(footprints[:-1], footprints[1:]):
            for i in range(len(before)):
                j = (i + 1) % len(before)
                polygons.append([before[i], before[j], after[j], after[i]])
        return polygons

    def validate_trajectory(self, trajectory):
        errors = []
        for index, point in enumerate(trajectory):
            if not self.vehicle.can_turn(point.steering_angle):
                errors.append("Point {0}: braquage impossible".format(index))
            if not all(_finite(value) for value in (point.position.x,
                    point.position.y, point.angle)):
                errors.append("Point {0}: coordonnees non finies".format(index))
        return not errors, errors
