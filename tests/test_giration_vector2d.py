# -*- coding: utf-8 -*-
"""
Tests unitaires pour Vector2D.

Ces tests vérifient les opérations géométriques de base sur les vecteurs 2D.
"""

import pytest
import math
from lib.giration.geometry.vector2d import Vector2D


class TestVector2DInitialization:
    """Tests d'initialisation de Vector2D."""
    
    def test_default_initialization(self):
        """Test de l'initialisation par défaut."""
        v = Vector2D()
        assert v.x == 0.0
        assert v.y == 0.0
    
    def test_initialization_with_values(self):
        """Test de l'initialisation avec des valeurs."""
        v = Vector2D(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0
    
    def test_initialization_converts_to_float(self):
        """Test que les valeurs sont converties en float."""
        v = Vector2D(3, 4)
        assert isinstance(v.x, float)
        assert isinstance(v.y, float)


class TestVector2DEquality:
    """Tests d'égalité de Vector2D."""
    
    def test_equality_with_tolerance(self):
        """Test de l'égalité avec tolérance numérique."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(1.0 + 1e-11, 2.0 + 1e-11)
        assert v1 == v2
    
    def test_inequality(self):
        """Test de l'inégalité."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1 != v2
    
    def test_equality_with_non_vector(self):
        """Test de l'égalité avec un non-Vector2D."""
        v = Vector2D(1.0, 2.0)
        assert v != (1.0, 2.0)
        assert v != [1.0, 2.0]


class TestVector2DArithmetic:
    """Tests des opérations arithmétiques sur Vector2D."""
    
    def test_addition(self):
        """Test de l'addition de vecteurs."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        result = v1 + v2
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_subtraction(self):
        """Test de la soustraction de vecteurs."""
        v1 = Vector2D(5.0, 6.0)
        v2 = Vector2D(2.0, 3.0)
        result = v1 - v2
        assert result.x == 3.0
        assert result.y == 3.0
    
    def test_scalar_multiplication(self):
        """Test de la multiplication par un scalaire."""
        v = Vector2D(2.0, 3.0)
        result = v * 2.0
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_reverse_scalar_multiplication(self):
        """Test de la multiplication par un scalaire (commutative)."""
        v = Vector2D(2.0, 3.0)
        result = 2.0 * v
        assert result.x == 4.0
        assert result.y == 6.0
    
    def test_scalar_division(self):
        """Test de la division par un scalaire."""
        v = Vector2D(4.0, 6.0)
        result = v / 2.0
        assert result.x == 2.0
        assert result.y == 3.0
    
    def test_negation(self):
        """Test de la négation."""
        v = Vector2D(1.0, 2.0)
        result = -v
        assert result.x == -1.0
        assert result.y == -2.0


class TestVector2DMagnitude:
    """Tests de magnitude de Vector2D."""
    
    def test_magnitude_zero_vector(self):
        """Test de la magnitude du vecteur nul."""
        v = Vector2D(0.0, 0.0)
        assert v.magnitude == 0.0
    
    def test_magnitude_unit_vector_x(self):
        """Test de la magnitude du vecteur unitaire X."""
        v = Vector2D(1.0, 0.0)
        assert abs(v.magnitude - 1.0) < 1e-10
    
    def test_magnitude_unit_vector_y(self):
        """Test de la magnitude du vecteur unitaire Y."""
        v = Vector2D(0.0, 1.0)
        assert abs(v.magnitude - 1.0) < 1e-10
    
    def test_magnitude_pythagorean(self):
        """Test de la magnitude avec le théorème de Pythagore."""
        v = Vector2D(3.0, 4.0)
        assert abs(v.magnitude - 5.0) < 1e-10
    
    def test_magnitude_squared(self):
        """Test du carré de la magnitude."""
        v = Vector2D(3.0, 4.0)
        assert v.magnitude_squared == 25.0


class TestVector2DNormalization:
    """Tests de normalisation de Vector2D."""
    
    def test_normalize_zero_vector(self):
        """Test de la normalisation du vecteur nul."""
        v = Vector2D(0.0, 0.0)
        result = v.normalize()
        assert result.x == 0.0
        assert result.y == 0.0
    
    def test_normalize_unit_vector(self):
        """Test de la normalisation d'un vecteur unitaire."""
        v = Vector2D(1.0, 0.0)
        result = v.normalize()
        assert abs(result.x - 1.0) < 1e-10
        assert abs(result.y - 0.0) < 1e-10
    
    def test_normalize_arbitrary_vector(self):
        """Test de la normalisation d'un vecteur arbitraire."""
        v = Vector2D(3.0, 4.0)
        result = v.normalize()
        assert abs(result.magnitude - 1.0) < 1e-10
        assert abs(result.x - 0.6) < 1e-10
        assert abs(result.y - 0.8) < 1e-10
    
    def test_normalized_returns_copy(self):
        """Test que normalized() retourne une copie."""
        v = Vector2D(3.0, 4.0)
        result = v.normalized()
        assert result is not v


class TestVector2DDotProduct:
    """Tests du produit scalaire de Vector2D."""
    
    def test_dot_product_zero(self):
        """Test du produit scalaire avec un vecteur nul."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(0.0, 0.0)
        assert v1.dot(v2) == 0.0
    
    def test_dot_product_orthogonal(self):
        """Test du produit scalaire de vecteurs orthogonaux."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert abs(v1.dot(v2)) < 1e-10
    
    def test_dot_product_parallel(self):
        """Test du produit scalaire de vecteurs parallèles."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(2.0, 4.0)
        assert abs(v1.dot(v2) - 10.0) < 1e-10
    
    def test_dot_product_arbitrary(self):
        """Test du produit scalaire de vecteurs arbitraires."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.dot(v2) == 11.0


class TestVector2DCrossProduct:
    """Tests du produit vectoriel 2D de Vector2D."""
    
    def test_cross_product_zero(self):
        """Test du produit vectoriel avec un vecteur nul."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(0.0, 0.0)
        assert v1.cross(v2) == 0.0
    
    def test_cross_product_parallel(self):
        """Test du produit vectoriel de vecteurs parallèles."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(2.0, 4.0)
        assert abs(v1.cross(v2)) < 1e-10
    
    def test_cross_product_orthogonal(self):
        """Test du produit vectoriel de vecteurs orthogonaux."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert abs(v1.cross(v2) - 1.0) < 1e-10
    
    def test_cross_product_arbitrary(self):
        """Test du produit vectoriel de vecteurs arbitraires."""
        v1 = Vector2D(1.0, 2.0)
        v2 = Vector2D(3.0, 4.0)
        assert abs(v1.cross(v2) - (-2.0)) < 1e-10


class TestVector2DAngle:
    """Tests des calculs d'angle de Vector2D."""
    
    def test_angle_to_parallel_same_direction(self):
        """Test de l'angle entre vecteurs parallèles dans le même sens."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(2.0, 0.0)
        assert abs(v1.angle_to(v2)) < 1e-10
    
    def test_angle_to_parallel_opposite_direction(self):
        """Test de l'angle entre vecteurs parallèles dans des sens opposés."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(-1.0, 0.0)
        assert abs(v1.angle_to(v2) - math.pi) < 1e-10
    
    def test_angle_to_orthogonal(self):
        """Test de l'angle entre vecteurs orthogonaux."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert abs(v1.angle_to(v2) - math.pi/2) < 1e-10
    
    def test_angle_between(self):
        """Test de la méthode statique angle_between."""
        v1 = Vector2D(1.0, 0.0)
        v2 = Vector2D(0.0, 1.0)
        assert abs(Vector2D.angle_between(v1, v2) - math.pi/2) < 1e-10


class TestVector2DRotation:
    """Tests de rotation de Vector2D."""
    
    def test_rotate_zero_angle(self):
        """Test de la rotation avec un angle nul."""
        v = Vector2D(1.0, 2.0)
        result = v.rotate(0.0)
        assert result == v
    
    def test_rotate_90_degrees(self):
        """Test de la rotation de 90 degrés."""
        v = Vector2D(1.0, 0.0)
        result = v.rotate(math.pi/2)
        assert abs(result.x - 0.0) < 1e-10
        assert abs(result.y - 1.0) < 1e-10
    
    def test_rotate_180_degrees(self):
        """Test de la rotation de 180 degrés."""
        v = Vector2D(1.0, 0.0)
        result = v.rotate(math.pi)
        assert abs(result.x - (-1.0)) < 1e-10
        assert abs(result.y - 0.0) < 1e-10
    
    def test_rotate_270_degrees(self):
        """Test de la rotation de 270 degrés."""
        v = Vector2D(1.0, 0.0)
        result = v.rotate(3 * math.pi/2)
        assert abs(result.x - 0.0) < 1e-10
        assert abs(result.y - (-1.0)) < 1e-10
    
    def test_rotated_returns_copy(self):
        """Test que rotated() retourne une copie."""
        v = Vector2D(1.0, 0.0)
        result = v.rotated(math.pi/2)
        assert result is not v


class TestVector2DDistance:
    """Tests de distance de Vector2D."""
    
    def test_distance_to_self(self):
        """Test de la distance à soi-même."""
        v = Vector2D(1.0, 2.0)
        assert v.distance_to(v) == 0.0
    
    def test_distance_to_another(self):
        """Test de la distance à un autre vecteur."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert abs(v1.distance_to(v2) - 5.0) < 1e-10
    
    def test_distance_squared(self):
        """Test du carré de la distance."""
        v1 = Vector2D(0.0, 0.0)
        v2 = Vector2D(3.0, 4.0)
        assert v1.distance_squared_to(v2) == 25.0


class TestVector2DConversion:
    """Tests de conversion de Vector2D."""
    
    def test_to_tuple(self):
        """Test de la conversion en tuple."""
        v = Vector2D(1.0, 2.0)
        assert v.to_tuple() == (1.0, 2.0)
    
    def test_to_list(self):
        """Test de la conversion en liste."""
        v = Vector2D(1.0, 2.0)
        assert v.to_list() == [1.0, 2.0]


class TestVector2DFromAngle:
    """Tests de création à partir d'un angle."""
    
    def test_from_angle_zero(self):
        """Test de la création avec un angle de 0."""
        v = Vector2D.from_angle(0.0, 1.0)
        assert abs(v.x - 1.0) < 1e-10
        assert abs(v.y - 0.0) < 1e-10
    
    def test_from_angle_90_degrees(self):
        """Test de la création avec un angle de 90 degrés."""
        v = Vector2D.from_angle(math.pi/2, 1.0)
        assert abs(v.x - 0.0) < 1e-10
        assert abs(v.y - 1.0) < 1e-10
    
    def test_from_angle_180_degrees(self):
        """Test de la création avec un angle de 180 degrés."""
        v = Vector2D.from_angle(math.pi, 1.0)
        assert abs(v.x - (-1.0)) < 1e-10
        assert abs(v.y - 0.0) < 1e-10


class TestVector2DRepr:
    """Tests de représentation de Vector2D."""
    
    def test_repr(self):
        """Test de la représentation."""
        v = Vector2D(1.0, 2.0)
        assert repr(v) == "Vector2D(1.0, 2.0)"
