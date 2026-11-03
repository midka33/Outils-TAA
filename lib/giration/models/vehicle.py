# -*- coding: utf-8 -*-
"""
Modèle de véhicule pour la simulation de giration.

Ce module définit les caractéristiques géométriques et cinématiques
d'un véhicule, nécessaires pour calculer ses trajectoires.
"""

from ..geometry.vector2d import Vector2D
import math


class Vehicle:
    """
    Représente un véhicule avec ses caractéristiques géométriques et cinématiques.
    
    Un véhicule est défini par:
    - Ses dimensions (longueur, largeur, empattement, etc.)
    - Ses caractéristiques de braquage (angle maximal, rayon minimal)
    - La position de ses essieux et roues
    
    Le modèle cinématique utilisé est celui d'Ackermann pour les véhicules rigides,
    qui permet de calculer les trajectoires en fonction de l'angle de braquage.
    
    Attributs:
        name: Nom du véhicule
        category: Catégorie (ex: "Camion", "Véhicule de secours")
        length: Longueur totale (m)
        width: Largeur totale (m)
        wheelbase: Empattement - distance entre essieux avant et arrière (m)
        front_overhang: Porte-à-faux avant (m)
        rear_overhang: Porte-à-faux arrière (m)
        front_track: Voie avant - distance entre roues avant (m)
        rear_track: Voie arrière - distance entre roues arrière (m)
        max_steering_angle: Angle maximal de braquage des roues avant (radians)
        min_turning_radius: Rayon minimal de giration (m) - calculé ou mesuré
        
    Note:
        Le rayon minimal de giration est la distance minimale entre le centre de
        rotation et le point le plus extérieur du véhicule lors d'un virage serré.
        Pour un véhicule à 2 essieux, il peut être calculé à partir de l'empattement
        et de l'angle maximal de braquage, mais peut aussi être mesuré directement.
    """
    
    def __init__(
        self,
        name,
        category="Inconnu",
        length=0.0,
        width=0.0,
        wheelbase=0.0,
        front_overhang=0.0,
        rear_overhang=0.0,
        front_track=0.0,
        rear_track=0.0,
        max_steering_angle=0.0,
        min_turning_radius=None,
        source=None,
        reference=None
    ):
        """
        Initialise un véhicule.
        
        Args:
            name: Nom du véhicule
            category: Catégorie du véhicule
            length: Longueur totale (m)
            width: Largeur totale (m)
            wheelbase: Empattement (m)
            front_overhang: Porte-à-faux avant (m)
            rear_overhang: Porte-à-faux arrière (m)
            front_track: Voie avant (m)
            rear_track: Voie arrière (m)
            max_steering_angle: Angle maximal de braquage (radians)
            min_turning_radius: Rayon minimal de giration (m) - optionnel
            source: Source des données
            reference: Référence du document
        """
        self.name = name
        self.category = category
        self.length = float(length)
        self.width = float(width)
        self.wheelbase = float(wheelbase)
        self.front_overhang = float(front_overhang)
        self.rear_overhang = float(rear_overhang)
        self.front_track = float(front_track)
        self.rear_track = float(rear_track)
        self.max_steering_angle = float(max_steering_angle)
        self.min_turning_radius = min_turning_radius
        self.source = source
        self.reference = reference
        
        # Calcul du rayon minimal si non fourni
        if min_turning_radius is None and wheelbase > 0 and max_steering_angle > 0:
            self.min_turning_radius = self._calculate_min_turning_radius()
    
    def __repr__(self):
        return f"Vehicle(name='{self.name}', category='{self.category}')"
    
    def __str__(self):
        return self.name
    
    def _calculate_min_turning_radius(self):
        """
        Calcule le rayon minimal de giration basé sur l'empattement et l'angle de braquage.
        
        Pour un véhicule à 2 essieux avec direction avant (modèle Ackermann simplifié),
        le rayon de giration minimal R est donné par:
        R = wheelbase / tan(max_steering_angle)
        
        Cependant, le rayon "extérieur" (distance du centre à la roue avant extérieure)
        est plus grand et dépend aussi de la voie.
        
        Returns:
            float: Rayon minimal de giration en mètres
        """
        if self.wheelbase <= 0 or self.max_steering_angle <= 0:
            return float('inf')
        
        # Rayon de courbure de la trajectoire de l'essieu arrière
        # R = L / tan(δ) où L = empattement, δ = angle de braquage
        radius = self.wheelbase / math.tan(self.max_steering_angle)
        
        # Le rayon minimal "extérieur" tient compte de la voie avant
        # Le point le plus éloigné est la roue avant extérieure
        # Distance = sqrt(radius^2 + (wheelbase)^2) + front_track/2
        # Mais pour simplifier, on retourne le rayon de base
        return radius
    
    @property
    def rear_axle_position(self):
        """
        Position de l'essieu arrière par rapport à l'origine (arrière du véhicule).
        
        Returns:
            float: Distance de l'essieu arrière à l'arrière du véhicule
        """
        return self.rear_overhang
    
    @property
    def front_axle_position(self):
        """
        Position de l'essieu avant par rapport à l'origine.
        
        Returns:
            float: Distance de l'essieu avant à l'arrière du véhicule
        """
        return self.rear_overhang + self.wheelbase
    
    @property
    def center_position(self):
        """
        Position du centre du véhicule par rapport à l'origine.
        
        Returns:
            float: Distance du centre à l'arrière du véhicule
        """
        return self.length / 2.0
    
    def get_axle_positions(self):
        """
        Retourne les positions des essieux par rapport à l'arrière du véhicule.
        
        Returns:
            tuple: (position_essieu_arrière, position_essieu_avant)
        """
        return (self.rear_axle_position, self.front_axle_position)
    
    def get_wheel_positions(self, x=0, y=0, angle=0):
        """
        Calcule les positions des 4 roues du véhicule.
        
        Le véhicule est positionné avec son arrière à (x, y) et orienté selon angle.
        
        Args:
            x: Coordonnée X de l'arrière du véhicule
            y: Coordonnée Y de l'arrière du véhicule
            angle: Angle d'orientation du véhicule (radians) - 0 = vers la droite
            
        Returns:
            dict: Dictionnaire avec les positions des roues
                {
                    'rear_left': Vector2D,
                    'rear_right': Vector2D,
                    'front_left': Vector2D,
                    'front_right': Vector2D
                }
        """
        # Position de l'essieu arrière (centre)
        rear_axle_x = x + self.rear_axle_position * math.cos(angle)
        rear_axle_y = y + self.rear_axle_position * math.sin(angle)
        
        # Position de l'essieu avant (centre)
        front_axle_x = x + self.front_axle_position * math.cos(angle)
        front_axle_y = y + self.front_axle_position * math.sin(angle)
        
        # Déplacement latéral pour les roues (voie / 2)
        half_front_track = self.front_track / 2.0
        half_rear_track = self.rear_track / 2.0
        
        # Vecteur latéral (perpendiculaire à l'orientation)
        lateral_x = -math.sin(angle) * half_front_track
        lateral_y = math.cos(angle) * half_front_track
        
        rear_lateral_x = -math.sin(angle) * half_rear_track
        rear_lateral_y = math.cos(angle) * half_rear_track
        
        return {
            'rear_left': Vector2D(rear_axle_x + rear_lateral_x, rear_axle_y + rear_lateral_y),
            'rear_right': Vector2D(rear_axle_x - rear_lateral_x, rear_axle_y - rear_lateral_y),
            'front_left': Vector2D(front_axle_x + lateral_x, front_axle_y + lateral_y),
            'front_right': Vector2D(front_axle_x - lateral_x, front_axle_y - lateral_y),
        }
    
    def get_corners(self, x=0, y=0, angle=0):
        """
        Calcule les coins de la carrosserie du véhicule.
        
        Le véhicule est modélisé comme un rectangle avec:
        - Longueur = length
        - Largeur = width
        - Centre à (x + center_position, y) orienté selon angle
        
        Args:
            x: Coordonnée X de l'arrière du véhicule
            y: Coordonnée Y de l'arrière du véhicule
            angle: Angle d'orientation (radians)
            
        Returns:
            list: Liste des 4 coins dans l'ordre [arrière-gauche, arrière-droite, 
                  avant-droite, avant-gauche]
        """
        # Position du centre
        center_x = x + self.center_position * math.cos(angle)
        center_y = y + self.center_position * math.sin(angle)
        
        # Demi-dimensions
        half_length = self.length / 2.0
        half_width = self.width / 2.0
        
        # Vecteurs de base
        forward_x = math.cos(angle) * half_length
        forward_y = math.sin(angle) * half_length
        right_x = -math.sin(angle) * half_width
        right_y = math.cos(angle) * half_width
        
        # Calcul des 4 coins
        rear_left = Vector2D(center_x - forward_x - right_x, center_y - forward_y - right_y)
        rear_right = Vector2D(center_x - forward_x + right_x, center_y - forward_y + right_y)
        front_right = Vector2D(center_x + forward_x + right_x, center_y + forward_y + right_y)
        front_left = Vector2D(center_x + forward_x - right_x, center_y + forward_y - right_y)
        
        return [rear_left, rear_right, front_right, front_left]
    
    def can_turn(self, steering_angle):
        """
        Vérifie si un angle de braquage est valide pour ce véhicule.
        
        Args:
            steering_angle: Angle de braquage souhaité (radians)
            
        Returns:
            bool: True si l'angle est valide, False sinon
        """
        return abs(steering_angle) <= self.max_steering_angle
    
    def to_dict(self):
        """
        Convertit le véhicule en dictionnaire pour sérialisation.
        
        Returns:
            dict: Représentation dictionnaire du véhicule
        """
        return {
            'name': self.name,
            'category': self.category,
            'length': self.length,
            'width': self.width,
            'wheelbase': self.wheelbase,
            'front_overhang': self.front_overhang,
            'rear_overhang': self.rear_overhang,
            'front_track': self.front_track,
            'rear_track': self.rear_track,
            'max_steering_angle': self.max_steering_angle,
            'min_turning_radius': self.min_turning_radius,
            'source': self.source,
            'reference': self.reference
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Crée un véhicule à partir d'un dictionnaire.
        
        Args:
            data: Dictionnaire contenant les données du véhicule
            
        Returns:
            Vehicle: Nouveau véhicule
        """
        return cls(
            name=data.get('name', 'Inconnu'),
            category=data.get('category', 'Inconnu'),
            length=data.get('length', 0.0),
            width=data.get('width', 0.0),
            wheelbase=data.get('wheelbase', 0.0),
            front_overhang=data.get('front_overhang', 0.0),
            rear_overhang=data.get('rear_overhang', 0.0),
            front_track=data.get('front_track', 0.0),
            rear_track=data.get('rear_track', 0.0),
            max_steering_angle=data.get('max_steering_angle', 0.0),
            min_turning_radius=data.get('min_turning_radius', None),
            source=data.get('source', None),
            reference=data.get('reference', None)
        )
