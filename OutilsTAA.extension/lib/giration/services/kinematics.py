# -*- coding: utf-8 -*-
"""
Moteur cinématique pour la simulation de giration des véhicules.

Ce module implémente les calculs nécessaires pour simuler le mouvement
d'un véhicule rigide selon le modèle cinématique d'Ackermann.

Modèle utilisé:
- Véhicule rigide à 2 essieux (avant et arrière)
- Direction uniquement sur l'essieu avant (modèle Ackermann)
- Pas de glissement latéral (hypothèse de roulement sans dérapage)
- Vitesse constante ou variable
"""

from ..geometry.vector2d import Vector2D
from ..models.vehicle import Vehicle
import math


class TrajectoryPoint:
    """
    Représente un point sur une trajectoire.
    
    Attributs:
        position: Position du point de référence (généralement centre ou arrière)
        angle: Orientation du véhicule (radians)
        steering_angle: Angle de braquage des roues avant (radians)
        is_reverse: True si le véhicule est en marche arrière
        timestamp: Temps écoulé depuis le début (optionnel)
    """
    
    def __init__(
        self,
        position,
        angle=0.0,
        steering_angle=0.0,
        is_reverse=False,
        timestamp=0.0
    ):
        self.position = Vector2D(position[0], position[1]) if isinstance(position, (tuple, list)) else position
        self.angle = float(angle)
        self.steering_angle = float(steering_angle)
        self.is_reverse = bool(is_reverse)
        self.timestamp = float(timestamp)
    
    def __repr__(self):
        return "TrajectoryPoint(pos={0}, angle={1}, steer={2}, reverse={3})".format(self.position, self.angle, self.steering_angle, self.is_reverse)
    
    def to_dict(self):
        return {
            'x': self.position.x,
            'y': self.position.y,
            'angle': self.angle,
            'steering_angle': self.steering_angle,
            'is_reverse': self.is_reverse,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            position=(data.get('x', 0), data.get('y', 0)),
            angle=data.get('angle', 0.0),
            steering_angle=data.get('steering_angle', 0.0),
            is_reverse=data.get('is_reverse', False),
            timestamp=data.get('timestamp', 0.0)
        )


class AckermannKinematics:
    """
    Implémentation du modèle cinématique d'Ackermann pour véhicules rigides.
    
    Ce modèle permet de calculer la trajectoire d'un véhicule en fonction de:
    - Sa position initiale
    - Son orientation initiale
    - Son angle de braquage
    - Sa vitesse (ou déplacement)
    
    Le modèle Ackermann est une approximation du comportement réel qui suppose:
    1. Les roues arrière suivent la même trajectoire (pas de dérapage)
    2. Les roues avant sont orientées selon un angle moyen
    3. Le véhicule tourne autour d'un centre de rotation instantané
    
    Pour un véhicule avec:
    - Empattement L (wheelbase)
    - Angle de braquage δ (steering angle)
    
    Le rayon de courbure R est donné par:
    R = L / tan(δ)
    
    Le centre de rotation est situé à une distance R derrière l'essieu arrière,
    sur la perpendicular à l'axe du véhicule.
    """
    
    def __init__(self, vehicle):
        """
        Initialise le moteur cinématique avec un véhicule.
        
        Args:
            vehicle: Instance de Vehicle
        """
        self.vehicle = vehicle
    
    def calculate_trajectory(
        self,
        start_point,
        start_angle=0.0,
        steering_angle=0.0,
        distance=0.0,
        is_reverse=False,
        num_points=10
    ):
        """
        Calcule une trajectoire pour un déplacement donné.
        
        Args:
            start_point: Point de départ (tuple ou Vector2D)
            start_angle: Orientation initiale (radians)
            steering_angle: Angle de braquage (radians) - positif = braquage à gauche
            distance: Distance à parcourir (m)
            is_reverse: True pour marche arrière
            num_points: Nombre de points intermédiaires à calculer
            
        Returns:
            list: Liste de TrajectoryPoint représentant la trajectoire
        """
        points = []
        
        if distance < 1e-10:
            # Pas de déplacement
            points.append(TrajectoryPoint(
                position=Vector2D(start_point[0], start_point[1]) if isinstance(start_point, (tuple, list)) else start_point,
                angle=start_angle,
                steering_angle=steering_angle,
                is_reverse=is_reverse
            ))
            return points
        
        # Direction du déplacement
        direction = -1 if is_reverse else 1
        
        # Calcul du rayon de courbure
        if abs(steering_angle) < 1e-10:
            # Ligne droite
            return self._calculate_straight_trajectory(
                start_point, start_angle, distance * direction, num_points, steering_angle, is_reverse
            )
        else:
            # Courbe
            return self._calculate_curved_trajectory(
                start_point, start_angle, steering_angle, distance * direction, num_points, is_reverse
            )
    
    def _calculate_straight_trajectory(
        self,
        start_point,
        start_angle,
        distance,
        num_points,
        steering_angle,
        is_reverse
    ):
        """Calcule une trajectoire en ligne droite."""
        points = []
        
        if isinstance(start_point, (tuple, list)):
            start = Vector2D(start_point[0], start_point[1])
        else:
            start = start_point
        
        # Direction du déplacement
        direction_x = math.cos(start_angle)
        direction_y = math.sin(start_angle)
        
        for i in range(num_points + 1):
            ratio = i / num_points
            x = start.x + distance * ratio * direction_x
            y = start.y + distance * ratio * direction_y
            
            points.append(TrajectoryPoint(
                position=Vector2D(x, y),
                angle=start_angle,
                steering_angle=steering_angle,
                is_reverse=is_reverse
            ))
        
        return points
    
    def _calculate_curved_trajectory(
        self,
        start_point,
        start_angle,
        steering_angle,
        distance,
        num_points,
        is_reverse
    ):
        """
        Calcule une trajectoire courbe selon le modèle Ackermann.
        
        Pour un angle de braquage δ, le rayon de courbure R est:
        R = L / tan(δ)
        
        Le centre de rotation est situé à:
        - Une distance R derrière l'essieu arrière
        - Sur la perpendiculaire à l'axe du véhicule
        """
        points = []
        
        if isinstance(start_point, (tuple, list)):
            start = Vector2D(start_point[0], start_point[1])
        else:
            start = start_point
        
        # Rayon de courbure
        L = self.vehicle.wheelbase
        R = L / math.tan(abs(steering_angle))
        
        # Sens de la courbure (positif = virage à gauche)
        turn_direction = 1 if steering_angle > 0 else -1
        
        # Position du centre de rotation
        # Pour un virage à gauche (steering_angle > 0), le centre est à droite de l'essieu arrière
        # Distance de l'essieu arrière au centre = R
        rotation_center_x = start.x - turn_direction * R * math.sin(start_angle)
        rotation_center_y = start.y + turn_direction * R * math.cos(start_angle)
        rotation_center = Vector2D(rotation_center_x, rotation_center_y)
        
        # Position initiale de l'essieu arrière (point de référence)
        rear_axle_start = start + Vector2D(
            self.vehicle.rear_axle_position * math.cos(start_angle),
            self.vehicle.rear_axle_position * math.sin(start_angle)
        )
        
        # Angle initial par rapport au centre de rotation
        initial_vector = rear_axle_start - rotation_center
        initial_angle = math.atan2(initial_vector.y, initial_vector.x)
        
        # Angle à parcourir
        # arc_length = R * θ => θ = arc_length / R
        arc_length = abs(distance)
        angle_change = arc_length / R * turn_direction
        
        # Calcul des points
        for i in range(num_points + 1):
            ratio = i / num_points
            current_angle = initial_angle + angle_change * ratio * (1 if not is_reverse else -1)
            
            # Position de l'essieu arrière
            rear_axle_x = rotation_center.x + R * math.cos(current_angle)
            rear_axle_y = rotation_center.y + R * math.sin(current_angle)
            
            # Orientation du véhicule
            # L'orientation est tangente au cercle
            vehicle_angle = current_angle - (math.pi / 2) * turn_direction + start_angle
            # Correction pour maintenir la cohérence
            vehicle_angle = math.atan2(
                math.sin(current_angle) * turn_direction,
                math.cos(current_angle) * turn_direction
            ) + start_angle
            
            # Position du point de référence (arrière du véhicule)
            # Le point de référence est à une distance rear_axle_position derrière l'essieu arrière
            ref_x = rear_axle_x - self.vehicle.rear_axle_position * math.cos(vehicle_angle)
            ref_y = rear_axle_y - self.vehicle.rear_axle_position * math.sin(vehicle_angle)
            
            points.append(TrajectoryPoint(
                position=Vector2D(ref_x, ref_y),
                angle=vehicle_angle,
                steering_angle=steering_angle,
                is_reverse=is_reverse
            ))
        
        return points
    
    def calculate_path(
        self,
        start_point,
        start_angle=0.0,
        segments=None
    ):
        """
        Calcule un chemin complet à partir d'une série de segments.
        
        Chaque segment définit:
        - distance: distance à parcourir
        - steering_angle: angle de braquage
        - is_reverse: marche avant/arrière
        
        Args:
            start_point: Point de départ
            start_angle: Orientation initiale
            segments: Liste de dictionnaires {"distance": ..., "steering_angle": ..., "is_reverse": ...}
            
        Returns:
            list: Liste complète des points de la trajectoire
        """
        if segments is None or len(segments) == 0:
            return [TrajectoryPoint(start_point, start_angle)]
        
        all_points = []
        current_point = Vector2D(start_point[0], start_point[1]) if isinstance(start_point, (tuple, list)) else start_point
        current_angle = start_angle
        
        for segment in segments:
            distance = segment.get('distance', 0)
            steering = segment.get('steering_angle', 0)
            reverse = segment.get('is_reverse', False)
            num_points = segment.get('num_points', 10)
            
            segment_points = self.calculate_trajectory(
                current_point,
                current_angle,
                steering,
                distance,
                reverse,
                num_points
            )
            
            # Ajouter tous les points sauf le premier (déjà ajouté)
            if len(all_points) == 0:
                all_points.extend(segment_points)
            else:
                all_points.extend(segment_points[1:])
            
            # Mettre à jour la position et l'orientation
            current_point = segment_points[-1].position
            current_angle = segment_points[-1].angle
        
        return all_points
    
    def calculate_wheel_trajectories(
        self,
        trajectory,
        reference_point='rear'
    ):
        """
        Calcule les trajectoires des roues à partir de la trajectoire du véhicule.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            reference_point: Point de référence ('rear' ou 'center')
            
        Returns:
            dict: Dictionnaire avec les trajectoires des 4 roues
                {
                    'front_left': [Vector2D, ...],
                    'front_right': [Vector2D, ...],
                    'rear_left': [Vector2D, ...],
                    'rear_right': [Vector2D, ...]
                }
        """
        wheel_trajectories = {
            'front_left': [],
            'front_right': [],
            'rear_left': [],
            'rear_right': []
        }
        
        for point in trajectory:
            # Calculer les positions des roues pour cette position et orientation
            if reference_point == 'rear':
                # Le point de référence est l'arrière du véhicule
                wheels = self.vehicle.get_wheel_positions(
                    x=point.position.x,
                    y=point.position.y,
                    angle=point.angle
                )
            else:
                # Le point de référence est le centre
                # Il faut recalculer la position de l'arrière
                rear_x = point.position.x - self.vehicle.center_position * math.cos(point.angle)
                rear_y = point.position.y - self.vehicle.center_position * math.sin(point.angle)
                wheels = self.vehicle.get_wheel_positions(
                    x=rear_x,
                    y=rear_y,
                    angle=point.angle
                )
            
            wheel_trajectories['front_left'].append(wheels['front_left'])
            wheel_trajectories['front_right'].append(wheels['front_right'])
            wheel_trajectories['rear_left'].append(wheels['rear_left'])
            wheel_trajectories['rear_right'].append(wheels['rear_right'])
        
        return wheel_trajectories
    
    def calculate_swept_area(
        self,
        trajectory,
        reference_point='rear'
    ):
        """
        Calcule l'enveloppe balayée par le véhicule le long de la trajectoire.
        
        L'enveloppe balayée est la surface couverte par la carrosserie du véhicule
        au cours de son déplacement. Elle n'est PAS simplement un décalage parallèle
        de la trajectoire, car le véhicule tourne.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            reference_point: Point de référence
            
        Returns:
            list: Liste de polygones représentant l'enveloppe balayée
        """
        # Pour simplifier, on calcule l'enveloppe comme l'union des positions
        # du véhicule à chaque point de la trajectoire
        # 
        # Une méthode plus précise serait d'utiliser des opérations booléennes
        # sur les polygones, mais cela nécessiterait une bibliothèque comme Shapely
        
        # Pour l'instant, on retourne les coins du véhicule à chaque position
        swept_polygons = []
        
        for point in trajectory:
            if reference_point == 'rear':
                corners = self.vehicle.get_corners(
                    x=point.position.x,
                    y=point.position.y,
                    angle=point.angle
                )
            else:
                rear_x = point.position.x - self.vehicle.center_position * math.cos(point.angle)
                rear_y = point.position.y - self.vehicle.center_position * math.sin(point.angle)
                corners = self.vehicle.get_corners(
                    x=rear_x,
                    y=rear_y,
                    angle=point.angle
                )
            swept_polygons.append(corners)
        
        return swept_polygons
    
    def validate_trajectory(
        self,
        trajectory
    ):
        """
        Valide une trajectoire par rapport aux contraintes du véhicule.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            
        Returns:
            tuple: (is_valid, errors) où errors est une liste de messages d'erreur
        """
        errors = []
        
        for i, point in enumerate(trajectory):
            # Vérifier l'angle de braquage
            if abs(point.steering_angle) > self.vehicle.max_steering_angle:
                errors.append(
                    "Point {0}: Angle de braquage {1} dépasse le maximum {2}".format(
                        i, point.steering_angle, self.vehicle.max_steering_angle
                    )
                )
        
        return len(errors) == 0, errors
