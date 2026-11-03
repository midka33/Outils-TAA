# -*- coding: utf-8 -*-
"""
Tests unitaires pour le modèle Vehicle.

Ces tests vérifient les propriétés géométriques et les calculs des véhicules.
"""

import pytest
import math
from lib.giration.models.vehicle import Vehicle
from lib.giration.geometry.vector2d import Vector2D


class TestVehicleInitialization:
    """Tests d'initialisation de Vehicle."""
    
    def test_basic_initialization(self):
        """Test de l'initialisation de base."""
        v = Vehicle(
            name="Test Vehicle",
            category="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0
        )
        assert v.name == "Test Vehicle"
        assert v.category == "Test"
        assert v.length == 5.0
        assert v.width == 2.0
        assert v.wheelbase == 3.0
    
    def test_initialization_with_all_parameters(self):
        """Test de l'initialisation avec tous les paramètres."""
        v = Vehicle(
            name="Full Vehicle",
            category="Complete",
            length=6.0,
            width=2.2,
            wheelbase=3.5,
            front_overhang=1.0,
            rear_overhang=1.5,
            front_track=1.8,
            rear_track=1.7,
            max_steering_angle=math.radians(45),
            min_turning_radius=7.0,
            source="Test Source",
            reference="REF-001"
        )
        assert v.name == "Full Vehicle"
        assert v.front_overhang == 1.0
        assert v.rear_overhang == 1.5
        assert v.max_steering_angle == math.radians(45)
        assert v.min_turning_radius == 7.0
        assert v.source == "Test Source"
        assert v.reference == "REF-001"
    
    def test_min_turning_radius_calculation(self):
        """Test du calcul automatique du rayon minimal de giration."""
        v = Vehicle(
            name="Auto Radius Vehicle",
            category="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0,
            max_steering_angle=math.radians(45)
        )
        # R = wheelbase / tan(steering_angle)
        expected_radius = 3.0 / math.tan(math.radians(45))
        assert abs(v.min_turning_radius - expected_radius) < 1e-10


class TestVehicleProperties:
    """Tests des propriétés calculées de Vehicle."""
    
    def test_rear_axle_position(self):
        """Test de la position de l'essieu arrière."""
        v = Vehicle(
            name="Test",
            length=5.0,
            rear_overhang=1.0
        )
        assert v.rear_axle_position == 1.0
    
    def test_front_axle_position(self):
        """Test de la position de l'essieu avant."""
        v = Vehicle(
            name="Test",
            length=5.0,
            wheelbase=3.0,
            rear_overhang=1.0
        )
        # front_axle = rear_overhang + wheelbase
        assert v.front_axle_position == 4.0
    
    def test_center_position(self):
        """Test de la position du centre."""
        v = Vehicle(
            name="Test",
            length=5.0
        )
        assert v.center_position == 2.5
    
    def test_get_axle_positions(self):
        """Test de la récupération des positions des essieux."""
        v = Vehicle(
            name="Test",
            length=5.0,
            wheelbase=3.0,
            rear_overhang=1.0
        )
        rear, front = v.get_axle_positions()
        assert rear == 1.0
        assert front == 4.0


class TestVehicleWheelPositions:
    """Tests des calculs de position des roues."""
    
    def test_wheel_positions_zero_angle(self):
        """Test des positions des roues avec un angle de 0."""
        v = Vehicle(
            name="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0,
            front_overhang=1.0,
            rear_overhang=1.0,
            front_track=1.6,
            rear_track=1.5
        )
        
        wheels = v.get_wheel_positions(x=0, y=0, angle=0)
        
        # Essieu arrière à 1.0m de l'arrière
        assert abs(wheels['rear_left'].x - 1.0) < 1e-10
        assert abs(wheels['rear_right'].x - 1.0) < 1e-10
        
        # Essieu avant à 4.0m de l'arrière
        assert abs(wheels['front_left'].x - 4.0) < 1e-10
        assert abs(wheels['front_right'].x - 4.0) < 1e-10
        
        # Voie arrière = 1.5m
        assert abs(wheels['rear_left'].y - (-0.75)) < 1e-10
        assert abs(wheels['rear_right'].y - 0.75) < 1e-10
        
        # Voie avant = 1.6m
        assert abs(wheels['front_left'].y - (-0.8)) < 1e-10
        assert abs(wheels['front_right'].y - 0.8) < 1e-10
    
    def test_wheel_positions_90_degrees(self):
        """Test des positions des roues avec un angle de 90 degrés."""
        v = Vehicle(
            name="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0,
            front_overhang=1.0,
            rear_overhang=1.0,
            front_track=1.6,
            rear_track=1.5
        )
        
        wheels = v.get_wheel_positions(x=0, y=0, angle=math.pi/2)
        
        # Avec un angle de 90°, le véhicule est orienté vers le haut
        # Essieu arrière à (0, 1.0)
        assert abs(wheels['rear_left'].x - 0.0) < 1e-10
        assert abs(wheels['rear_right'].x - 0.0) < 1e-10
        assert abs(wheels['rear_left'].y - 1.0) < 1e-10
        assert abs(wheels['rear_right'].y - 1.0) < 1e-10
        
        # Essieu avant à (0, 4.0)
        assert abs(wheels['front_left'].x - 0.0) < 1e-10
        assert abs(wheels['front_right'].x - 0.0) < 1e-10
        assert abs(wheels['front_left'].y - 4.0) < 1e-10
        assert abs(wheels['front_right'].y - 4.0) < 1e-10


class TestVehicleCorners:
    """Tests des calculs des coins de la carrosserie."""
    
    def test_corners_zero_angle(self):
        """Test des coins avec un angle de 0."""
        v = Vehicle(
            name="Test",
            length=5.0,
            width=2.0,
            rear_overhang=1.0
        )
        
        corners = v.get_corners(x=0, y=0, angle=0)
        
        # 4 coins attendus
        assert len(corners) == 4
        
        # Coin arrière-gauche : (0, -1)
        assert abs(corners[0].x - 0.0) < 1e-10
        assert abs(corners[0].y - (-1.0)) < 1e-10
        
        # Coin arrière-droite : (0, 1)
        assert abs(corners[1].x - 0.0) < 1e-10
        assert abs(corners[1].y - 1.0) < 1e-10
        
        # Coin avant-droite : (5, 1)
        assert abs(corners[2].x - 5.0) < 1e-10
        assert abs(corners[2].y - 1.0) < 1e-10
        
        # Coin avant-gauche : (5, -1)
        assert abs(corners[3].x - 5.0) < 1e-10
        assert abs(corners[3].y - (-1.0)) < 1e-10
    
    def test_corners_90_degrees(self):
        """Test des coins avec un angle de 90 degrés."""
        v = Vehicle(
            name="Test",
            length=5.0,
            width=2.0,
            rear_overhang=1.0
        )
        
        corners = v.get_corners(x=0, y=0, angle=math.pi/2)
        
        # Avec un angle de 90°, le véhicule est orienté vers le haut
        # Coin arrière-gauche : (-1, 0)
        assert abs(corners[0].x - (-1.0)) < 1e-10
        assert abs(corners[0].y - 0.0) < 1e-10
        
        # Coin arrière-droite : (1, 0)
        assert abs(corners[1].x - 1.0) < 1e-10
        assert abs(corners[1].y - 0.0) < 1e-10
        
        # Coin avant-droite : (1, 5)
        assert abs(corners[2].x - 1.0) < 1e-10
        assert abs(corners[2].y - 5.0) < 1e-10
        
        # Coin avant-gauche : (-1, 5)
        assert abs(corners[3].x - (-1.0)) < 1e-10
        assert abs(corners[3].y - 5.0) < 1e-10


class TestVehicleSteering:
    """Tests des vérifications de braquage."""
    
    def test_can_turn_valid(self):
        """Test d'un angle de braquage valide."""
        v = Vehicle(
            name="Test",
            max_steering_angle=math.radians(45)
        )
        assert v.can_turn(math.radians(30))
        assert v.can_turn(math.radians(45))
        assert v.can_turn(math.radians(-30))
    
    def test_can_turn_invalid(self):
        """Test d'un angle de braquage invalide."""
        v = Vehicle(
            name="Test",
            max_steering_angle=math.radians(45)
        )
        assert not v.can_turn(math.radians(50))
        assert not v.can_turn(math.radians(-50))


class TestVehicleSerialization:
    """Tests de sérialisation de Vehicle."""
    
    def test_to_dict(self):
        """Test de la conversion en dictionnaire."""
        v = Vehicle(
            name="Test Vehicle",
            category="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0,
            front_overhang=1.0,
            rear_overhang=1.0,
            front_track=1.6,
            rear_track=1.5,
            max_steering_angle=math.radians(45),
            min_turning_radius=7.0,
            source="Test Source",
            reference="REF-001"
        )
        
        d = v.to_dict()
        assert d['name'] == "Test Vehicle"
        assert d['category'] == "Test"
        assert d['length'] == 5.0
        assert d['width'] == 2.0
        assert d['wheelbase'] == 3.0
        assert d['max_steering_angle'] == math.radians(45)
        assert d['min_turning_radius'] == 7.0
        assert d['source'] == "Test Source"
        assert d['reference'] == "REF-001"
    
    def test_from_dict(self):
        """Test de la création à partir d'un dictionnaire."""
        d = {
            'name': "From Dict Vehicle",
            'category': "Test",
            'length': 6.0,
            'width': 2.2,
            'wheelbase': 3.5,
            'front_overhang': 1.2,
            'rear_overhang': 1.3,
            'front_track': 1.7,
            'rear_track': 1.6,
            'max_steering_angle': math.radians(40),
            'min_turning_radius': 8.0,
            'source': "Dict Source",
            'reference': "REF-002"
        }
        
        v = Vehicle.from_dict(d)
        assert v.name == "From Dict Vehicle"
        assert v.length == 6.0
        assert v.width == 2.2
        assert v.wheelbase == 3.5
        assert v.max_steering_angle == math.radians(40)
        assert v.min_turning_radius == 8.0
    
    def test_roundtrip_serialization(self):
        """Test de la sérialisation/désérialisation."""
        v1 = Vehicle(
            name="Roundtrip Vehicle",
            category="Test",
            length=5.0,
            width=2.0,
            wheelbase=3.0,
            max_steering_angle=math.radians(45)
        )
        
        d = v1.to_dict()
        v2 = Vehicle.from_dict(d)
        
        assert v2.name == v1.name
        assert v2.category == v1.category
        assert v2.length == v1.length
        assert v2.width == v1.width
        assert v2.wheelbase == v1.wheelbase


class TestVehicleRepr:
    """Tests de représentation de Vehicle."""
    
    def test_repr(self):
        """Test de la représentation."""
        v = Vehicle(name="Test Vehicle", category="Test")
        assert repr(v) == "Vehicle(name='Test Vehicle', category='Test')"
    
    def test_str(self):
        """Test de la conversion en chaîne."""
        v = Vehicle(name="Test Vehicle", category="Test")
        assert str(v) == "Test Vehicle"
