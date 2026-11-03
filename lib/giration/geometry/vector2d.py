# -*- coding: utf-8 -*-
"""
Vecteur 2D pour les calculs géométriques.

Ce module fournit une implémentation de vecteur 2D avec les opérations
nécessaires pour la simulation de giration des véhicules.
"""

import math


class Vector2D:
    """
    Représente un vecteur 2D avec des opérations géométriques.
    
    Attributs:
        x: Coordonnée X
        y: Coordonnée Y
    """
    
    def __init__(self, x=0.0, y=0.0):
        """
        Initialise un vecteur 2D.
        
        Args:
            x: Coordonnée X (par défaut 0.0)
            y: Coordonnée Y (par défaut 0.0)
        """
        self.x = float(x)
        self.y = float(y)
    
    def __repr__(self):
        return f"Vector2D({self.x}, {self.y})"
    
    def __eq__(self, other, tolerance=1e-10):
        """Test d'égalité avec tolérance numérique."""
        if not isinstance(other, Vector2D):
            return False
        return abs(self.x - other.x) < tolerance and abs(self.y - other.y) < tolerance
    
    def __add__(self, other):
        """Addition de deux vecteurs."""
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        return NotImplemented
    
    def __sub__(self, other):
        """Soustraction de deux vecteurs."""
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        return NotImplemented
    
    def __mul__(self, scalar):
        """Multiplication par un scalaire."""
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar):
        """Multiplication par un scalaire (commutative)."""
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar):
        """Division par un scalaire."""
        return Vector2D(self.x / scalar, self.y / scalar)
    
    def __neg__(self):
        """Négation du vecteur."""
        return Vector2D(-self.x, -self.y)
    
    @property
    def magnitude(self):
        """Calcule la magnitude (longueur) du vecteur."""
        return math.sqrt(self.x**2 + self.y**2)
    
    @property
    def magnitude_squared(self):
        """Calcule le carré de la magnitude (plus rapide, évite la racine)."""
        return self.x**2 + self.y**2
    
    def normalize(self):
        """
        Normalise le vecteur (le transforme en vecteur unitaire).
        
        Returns:
            Vector2D: Vecteur normalisé
        """
        mag = self.magnitude
        if mag < 1e-10:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)
    
    def normalized(self):
        """Retourne une copie normalisée du vecteur."""
        return self.normalize()
    
    def dot(self, other):
        """
        Produit scalaire avec un autre vecteur.
        
        Args:
            other: Autre Vector2D
            
        Returns:
            float: Produit scalaire
        """
        return self.x * other.x + self.y * other.y
    
    def cross(self, other):
        """
        Produit vectoriel 2D (retourne un scalaire = z-component).
        
        Args:
            other: Autre Vector2D
            
        Returns:
            float: Composante Z du produit vectoriel
        """
        return self.x * other.y - self.y * other.x
    
    def angle_to(self, other):
        """
        Calcule l'angle entre ce vecteur et un autre (en radians).
        
        Args:
            other: Autre Vector2D
            
        Returns:
            float: Angle en radians
        """
        dot = self.dot(other)
        det = self.cross(other)
        return math.atan2(det, dot)
    
    def rotate(self, angle):
        """
        Rotate le vecteur d'un angle (en radians).
        
        Args:
            angle: Angle de rotation en radians
            
        Returns:
            Vector2D: Nouveau vecteur roté
        """
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2D(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    def rotated(self, angle):
        """Retourne une copie rotée du vecteur."""
        return self.rotate(angle)
    
    def distance_to(self, other):
        """
        Calcule la distance entre ce vecteur et un autre.
        
        Args:
            other: Autre Vector2D
            
        Returns:
            float: Distance
        """
        return (self - other).magnitude
    
    def distance_squared_to(self, other):
        """Calcule le carré de la distance (plus rapide)."""
        return (self - other).magnitude_squared
    
    def to_tuple(self):
        """Convertit en tuple (x, y)."""
        return (self.x, self.y)
    
    def to_list(self):
        """Convertit en liste [x, y]."""
        return [self.x, self.y]
    
    @classmethod
    def from_angle(cls, angle, magnitude=1.0):
        """
        Crée un vecteur à partir d'un angle et d'une magnitude.
        
        Args:
            angle: Angle en radians
            magnitude: Longueur du vecteur
            
        Returns:
            Vector2D: Nouveau vecteur
        """
        return Vector2D(magnitude * math.cos(angle), magnitude * math.sin(angle))
    
    @staticmethod
    def angle_between(v1, v2):
        """
        Calcule l'angle entre deux vecteurs (en radians).
        
        Args:
            v1: Premier Vector2D
            v2: Deuxième Vector2D
            
        Returns:
            float: Angle en radians
        """
        return v1.angle_to(v2)
