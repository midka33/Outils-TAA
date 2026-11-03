# -*- coding: utf-8 -*-
"""
Tests unitaires pour le moteur cinématique Ackermann.

Ces tests vérifient les calculs de trajectoire pour différents scénarios.
"""

import pytest
import math
from lib.giration.models.vehicle import Vehicle
from lib.giration.services.kinematics import AckermannKinematics, TrajectoryPoint
from lib.giration.geometry.vector2d import Vector2D


# Créer un véhicule de test standard
TEST_VEHICLE = Vehicle(
    name="Test Vehicle",
    category="Test",
    length=5.0,
    width=2.0,
    wheelbase=3.0,
    front_overhang=1.0,
    rear_overhang=1.0,
    front_track=1.6,
    rear_track=1.5,
    max_steering_angle=math.radians(45),  # 45 degrés
    min_turning_radius=5.0
)


class TestTrajectoryPoint:
    """Tests pour TrajectoryPoint."""
    
    def test_creation_from_tuple(self):
        """Test de la création à partir d'un tuple."""
        point = TrajectoryPoint((1.0, 2.0), angle=0.5, steering_angle=0.1)
        assert point.position.x == 1.0
        assert point.position.y == 2.0
        assert point.angle == 0.5
        assert point.steering_angle == 0.1
    
    def test_creation_from_vector2d(self):
        """Test de la création à partir d'un Vector2D."""
        v = Vector2D(1.0, 2.0)
        point = TrajectoryPoint(v, angle=0.5)
        assert point.position == v
    
    def test_to_dict(self):
        """Test de la conversion en dictionnaire."""
        point = TrajectoryPoint((1.0, 2.0), angle=0.5, steering_angle=0.1, is_reverse=True, timestamp=1.0)
        d = point.to_dict()
        assert d['x'] == 1.0
        assert d['y'] == 2.0
        assert d['angle'] == 0.5
        assert d['steering_angle'] == 0.1
        assert d['is_reverse'] == True
        assert d['timestamp'] == 1.0
    
    def test_from_dict(self):
        """Test de la création à partir d'un dictionnaire."""
        d = {'x': 1.0, 'y': 2.0, 'angle': 0.5, 'steering_angle': 0.1, 'is_reverse': True, 'timestamp': 1.0}
        point = TrajectoryPoint.from_dict(d)
        assert point.position.x == 1.0
        assert point.position.y == 2.0
        assert point.angle == 0.5
        assert point.steering_angle == 0.1
        assert point.is_reverse == True
        assert point.timestamp == 1.0


class TestAckermannKinematicsStraight:
    """Tests pour les trajectoires en ligne droite."""
    
    def test_straight_forward(self):
        """Test d'une trajectoire en ligne droite vers l'avant."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=0.0,
            distance=10.0,
            is_reverse=False,
            num_points=5
        )
        
        # Vérifier que tous les points sont sur l'axe X
        for point in trajectory:
            assert abs(point.position.y) < 1e-10
        
        # Vérifier que la distance est correcte
        assert abs(trajectory[-1].position.x - 10.0) < 1e-10
    
    def test_straight_backward(self):
        """Test d'une trajectoire en ligne droite en marche arrière."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=0.0,
            distance=10.0,
            is_reverse=True,
            num_points=5
        )
        
        # Vérifier que tous les points sont sur l'axe X (négatif)
        for point in trajectory:
            assert abs(point.position.y) < 1e-10
        
        # Vérifier que la distance est correcte (négative)
        assert abs(trajectory[-1].position.x - (-10.0)) < 1e-10
    
    def test_straight_with_angle(self):
        """Test d'une trajectoire en ligne droite avec un angle initial."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=math.pi/2,  # 90 degrés
            steering_angle=0.0,
            distance=5.0,
            is_reverse=False,
            num_points=5
        )
        
        # Vérifier que tous les points sont sur l'axe Y
        for point in trajectory:
            assert abs(point.position.x) < 1e-10
        
        # Vérifier que la distance est correcte
        assert abs(trajectory[-1].position.y - 5.0) < 1e-10


class TestAckermannKinematicsCurved:
    """Tests pour les trajectoires courbes."""
    
    def test_curved_forward_left(self):
        """Test d'une trajectoire courbe vers la gauche (braquage positif)."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        steering_angle = math.radians(30)  # 30 degrés
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=steering_angle,
            distance=5.0,
            is_reverse=False,
            num_points=10
        )
        
        # Vérifier que la trajectoire courbe vers la gauche (Y positif)
        # Le point final doit avoir une coordonnée Y positive
        assert trajectory[-1].position.y > 0.0
        
        # Vérifier que l'orientation change
        assert trajectory[-1].angle > 0.0
    
    def test_curved_forward_right(self):
        """Test d'une trajectoire courbe vers la droite (braquage négatif)."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        steering_angle = math.radians(-30)  # -30 degrés
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=steering_angle,
            distance=5.0,
            is_reverse=False,
            num_points=10
        )
        
        # Vérifier que la trajectoire courbe vers la droite (Y négatif)
        assert trajectory[-1].position.y < 0.0
        
        # Vérifier que l'orientation change
        assert trajectory[-1].angle < 0.0
    
    def test_curved_backward_left(self):
        """Test d'une trajectoire courbe en marche arrière vers la gauche."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        steering_angle = math.radians(30)
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=steering_angle,
            distance=5.0,
            is_reverse=True,
            num_points=10
        )
        
        # En marche arrière, la courbure est inversée
        # Le point final doit avoir une coordonnée Y négative
        assert trajectory[-1].position.y < 0.0


class TestAckermannKinematicsPath:
    """Tests pour les chemins composés de plusieurs segments."""
    
    def test_simple_path(self):
        """Test d'un chemin avec deux segments."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        segments = [
            {'distance': 5.0, 'steering_angle': 0.0, 'is_reverse': False},
            {'distance': 3.0, 'steering_angle': math.radians(30), 'is_reverse': False}
        ]
        
        trajectory = kinematics.calculate_path(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            segments=segments
        )
        
        # Vérifier que la trajectoire a le bon nombre de points
        assert len(trajectory) > len(segments)
        
        # Vérifier que le premier segment est en ligne droite
        for i in range(5):  # Premier segment a 10 points par défaut
            if i < len(trajectory):
                assert abs(trajectory[i].position.y) < 1e-10


class TestAckermannKinematicsWheelTrajectories:
    """Tests pour les trajectoires des roues."""
    
    def test_wheel_trajectories_straight(self):
        """Test des trajectoires des roues en ligne droite."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=0.0,
            distance=10.0,
            is_reverse=False,
            num_points=5
        )
        
        wheel_trajectories = kinematics.calculate_wheel_trajectories(
            trajectory,
            reference_point='rear'
        )
        
        # Vérifier que toutes les roues ont des trajectoires
        assert len(wheel_trajectories['front_left']) == len(trajectory)
        assert len(wheel_trajectories['front_right']) == len(trajectory)
        assert len(wheel_trajectories['rear_left']) == len(trajectory)
        assert len(wheel_trajectories['rear_right']) == len(trajectory)
        
        # Vérifier que les roues avant et arrière sont à la bonne distance
        # Distance entre roues avant et arrière = empattement
        for i in range(len(trajectory)):
            front_left = wheel_trajectories['front_left'][i]
            rear_left = wheel_trajectories['rear_left'][i]
            distance = front_left.distance_to(rear_left)
            assert abs(distance - TEST_VEHICLE.wheelbase) < 0.1


class TestAckermannKinematicsSweptArea:
    """Tests pour l'enveloppe balayée."""
    
    def test_swept_area_straight(self):
        """Test de l'enveloppe balayée en ligne droite."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=0.0,
            distance=10.0,
            is_reverse=False,
            num_points=5
        )
        
        swept_polygons = kinematics.calculate_swept_area(
            trajectory,
            reference_point='rear'
        )
        
        # Vérifier que chaque point a un polygone de coins
        assert len(swept_polygons) == len(trajectory)
        
        # Vérifier que chaque polygone a 4 coins
        for polygon in swept_polygons:
            assert len(polygon) == 4


class TestAckermannKinematicsValidation:
    """Tests pour la validation des trajectoires."""
    
    def test_valid_trajectory(self):
        """Test d'une trajectoire valide."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=math.radians(30),  # Dans la limite
            distance=5.0,
            is_reverse=False,
            num_points=5
        )
        
        is_valid, errors = kinematics.validate_trajectory(trajectory)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_steering_angle(self):
        """Test d'une trajectoire avec un angle de braquage invalide."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        # Créer une trajectoire avec un angle de braquage trop grand
        trajectory = [
            TrajectoryPoint((0.0, 0.0), angle=0.0, steering_angle=math.radians(50)),
            TrajectoryPoint((1.0, 0.0), angle=0.0, steering_angle=math.radians(50))
        ]
        
        is_valid, errors = kinematics.validate_trajectory(trajectory)
        assert not is_valid
        assert len(errors) > 0


class TestAckermannKinematicsEdgeCases:
    """Tests des cas limites."""
    
    def test_zero_distance(self):
        """Test avec une distance nulle."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        trajectory = kinematics.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            steering_angle=0.0,
            distance=0.0,
            is_reverse=False,
            num_points=5
        )
        
        # Doit retourner au moins un point
        assert len(trajectory) >= 1
        assert trajectory[0].position.x == 0.0
        assert trajectory[0].position.y == 0.0
    
    def test_empty_segments(self):
        """Test avec une liste de segments vide."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        trajectory = kinematics.calculate_path(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            segments=[]
        )
        
        # Doit retourner au moins le point de départ
        assert len(trajectory) >= 1
    
    def test_single_point_path(self):
        """Test avec un seul segment de distance nulle."""
        kinematics = AckermannKinematics(TEST_VEHICLE)
        
        segments = [{'distance': 0.0, 'steering_angle': 0.0, 'is_reverse': False}]
        
        trajectory = kinematics.calculate_path(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            segments=segments
        )
        
        assert len(trajectory) >= 1
