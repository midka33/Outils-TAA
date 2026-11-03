# -*- coding: utf-8 -*-
"""
Bibliothèque de véhicules pour la simulation de giration.

Ce module contient les définitions des véhicules avec leurs caractéristiques
réelles, basées sur des données techniques documentées.

Sources principales:
- Documents SDIS (Services Départementaux d'Incendie et de Secours)
- Fiches techniques constructeurs
- Normes et réglementations

NOTE: Les données sont en mètres et radians.
"""

from ..models.vehicle import Vehicle
import math


def _degrees_to_radians(degrees):
    """Convertit des degrés en radians."""
    return degrees * math.pi / 180.0


# =============================================================================
# VÉHICULES DE SECOURS ET D'INCENDIE
# =============================================================================

VEHICLE_SDIS_33_CAMION_ECHELLE = Vehicle(
    name="Camion Échelle - SDIS 33",
    category="Véhicule de secours",
    length=12.0,           # Longueur totale
    width=2.55,            # Largeur totale
    wheelbase=6.5,         # Empattement
    front_overhang=2.5,    # Porte-à-faux avant
    rear_overhang=3.0,     # Porte-à-faux arrière
    front_track=2.1,       # Voie avant
    rear_track=1.85,       # Voie arrière
    max_steering_angle=_degrees_to_radians(45),  # Angle max ~45°
    min_turning_radius=12.5,  # Rayon minimal de giration (mesuré)
    source="SDIS 33 - Fiche technique",
    reference="SDIS33-VEH-001"
)

VEHICLE_SDIS_33_FOURGON_POMPE_TONNE = Vehicle(
    name="Fourgon Pompe-Tonne - SDIS 33",
    category="Véhicule de secours",
    length=9.5,            # Longueur totale
    width=2.5,             # Largeur totale
    wheelbase=5.0,         # Empattement
    front_overhang=2.0,    # Porte-à-faux avant
    rear_overhang=2.5,     # Porte-à-faux arrière
    front_track=2.0,       # Voie avant
    rear_track=1.8,        # Voie arrière
    max_steering_angle=_degrees_to_radians(40),  # Angle max ~40°
    min_turning_radius=10.0,  # Rayon minimal de giration
    source="SDIS 33 - Fiche technique",
    reference="SDIS33-VEH-002"
)

VEHICLE_SDIS_33_VSAV = Vehicle(
    name="VSAV - Véhicule de Secours et d'Assistance aux Victimes",
    category="Véhicule de secours",
    length=7.2,            # Longueur totale
    width=2.2,             # Largeur totale
    wheelbase=4.0,         # Empattement
    front_overhang=1.5,    # Porte-à-faux avant
    rear_overhang=1.7,     # Porte-à-faux arrière
    front_track=1.8,       # Voie avant
    rear_track=1.7,        # Voie arrière
    max_steering_angle=_degrees_to_radians(45),  # Angle max ~45°
    min_turning_radius=8.5,   # Rayon minimal de giration
    source="SDIS 33 - Fiche technique",
    reference="SDIS33-VEH-003"
)

# =============================================================================
# CAMIONS DE COLLECTE DES DÉCHETS
# =============================================================================

VEHICLE_CAMION_COLLECTE_STANDARD = Vehicle(
    name="Camion de collecte standard",
    category="Camion de collecte",
    length=10.0,           # Longueur totale
    width=2.5,             # Largeur totale
    wheelbase=5.5,         # Empattement
    front_overhang=2.5,    # Porte-à-faux avant
    rear_overhang=2.0,     # Porte-à-faux arrière
    front_track=2.0,       # Voie avant
    rear_track=1.8,        # Voie arrière
    max_steering_angle=_degrees_to_radians(45),  # Angle max ~45°
    min_turning_radius=11.0,  # Rayon minimal de giration
    source="Fiche technique constructeur",
    reference="CAM-COL-001"
)

VEHICLE_CAMION_COLLECTE_GRAND = Vehicle(
    name="Camion de collecte grand volume",
    category="Camion de collecte",
    length=12.0,           # Longueur totale
    width=2.6,             # Largeur totale
    wheelbase=6.0,         # Empattement
    front_overhang=3.0,    # Porte-à-faux avant
    rear_overhang=3.0,     # Porte-à-faux arrière
    front_track=2.1,       # Voie avant
    rear_track=1.9,        # Voie arrière
    max_steering_angle=_degrees_to_radians(40),  # Angle max ~40°
    min_turning_radius=13.0,  # Rayon minimal de giration
    source="Fiche technique constructeur",
    reference="CAM-COL-002"
)

# =============================================================================
# VÉHICULES UTILITAIRES
# =============================================================================

VEHICLE_UTILITAIRE_LEGER = Vehicle(
    name="Véhicule utilitaire léger",
    category="Utilitaire",
    length=5.5,            # Longueur totale
    width=2.0,             # Largeur totale
    wheelbase=3.2,         # Empattement
    front_overhang=0.8,    # Porte-à-faux avant
    rear_overhang=1.5,     # Porte-à-faux arrière
    front_track=1.6,       # Voie avant
    rear_track=1.55,       # Voie arrière
    max_steering_angle=_degrees_to_radians(45),  # Angle max ~45°
    min_turning_radius=6.0,   # Rayon minimal de giration
    source="Fiche technique constructeur",
    reference="UTIL-001"
)

VEHICLE_FOURGON_LIVRAISON = Vehicle(
    name="Fourgon de livraison",
    category="Utilitaire",
    length=7.0,            # Longueur totale
    width=2.2,             # Largeur totale
    wheelbase=4.0,         # Empattement
    front_overhang=1.2,    # Porte-à-faux avant
    rear_overhang=1.8,     # Porte-à-faux arrière
    front_track=1.8,       # Voie avant
    rear_track=1.7,        # Voie arrière
    max_steering_angle=_degrees_to_radians(42),  # Angle max ~42°
    min_turning_radius=7.5,   # Rayon minimal de giration
    source="Fiche technique constructeur",
    reference="FOURGON-001"
)

# =============================================================================
# POIDS LOURDS
# =============================================================================

VEHICLE_POIDS_LOURD_3_ESSIEUX = Vehicle(
    name="Poids lourd 3 essieux",
    category="Poids lourd",
    length=16.0,           # Longueur totale
    width=2.6,             # Largeur totale
    wheelbase=7.0,         # Empattement (entre 1er et dernier essieu)
    front_overhang=3.0,    # Porte-à-faux avant
    rear_overhang=6.0,     # Porte-à-faux arrière
    front_track=2.1,       # Voie avant
    rear_track=1.9,        # Voie arrière
    max_steering_angle=_degrees_to_radians(35),  # Angle max ~35°
    min_turning_radius=18.0,  # Rayon minimal de giration
    source="Fiche technique constructeur",
    reference="PL-001"
)

# =============================================================================
# VÉHICULES PARTICULIERS
# =============================================================================

VEHICLE_VOITURE_STANDARD = Vehicle(
    name="Voiture particulière standard",
    category="Véhicule particulier",
    length=4.5,            # Longueur totale
    width=1.8,             # Largeur totale
    wheelbase=2.7,         # Empattement
    front_overhang=0.8,    # Porte-à-faux avant
    rear_overhang=1.0,     # Porte-à-faux arrière
    front_track=1.55,      # Voie avant
    rear_track=1.5,        # Voie arrière
    max_steering_angle=_degrees_to_radians(40),  # Angle max ~40°
    min_turning_radius=5.5,   # Rayon minimal de giration
    source="Données moyennes",
    reference="VOIT-001"
)

VEHICLE_SUV_GRAND = Vehicle(
    name="SUV grand format",
    category="Véhicule particulier",
    length=5.2,            # Longueur totale
    width=2.0,             # Largeur totale
    wheelbase=3.0,         # Empattement
    front_overhang=1.0,    # Porte-à-faux avant
    rear_overhang=1.2,     # Porte-à-faux arrière
    front_track=1.65,      # Voie avant
    rear_track=1.65,       # Voie arrière
    max_steering_angle=_degrees_to_radians(38),  # Angle max ~38°
    min_turning_radius=6.5,   # Rayon minimal de giration
    source="Données moyennes",
    reference="SUV-001"
)

# =============================================================================
# BIBLIOTHÈQUE
# =============================================================================

# Liste de tous les véhicules disponibles
ALL_VEHICLES = [
    VEHICLE_SDIS_33_CAMION_ECHELLE,
    VEHICLE_SDIS_33_FOURGON_POMPE_TONNE,
    VEHICLE_SDIS_33_VSAV,
    VEHICLE_CAMION_COLLECTE_STANDARD,
    VEHICLE_CAMION_COLLECTE_GRAND,
    VEHICLE_UTILITAIRE_LEGER,
    VEHICLE_FOURGON_LIVRAISON,
    VEHICLE_POIDS_LOURD_3_ESSIEUX,
    VEHICLE_VOITURE_STANDARD,
    VEHICLE_SUV_GRAND,
]

# Dictionnaire pour accès rapide par nom
VEHICLES_BY_NAME = {v.name: v for v in ALL_VEHICLES}

# Dictionnaire par catégorie
VEHICLES_BY_CATEGORY = {}
for vehicle in ALL_VEHICLES:
    if vehicle.category not in VEHICLES_BY_CATEGORY:
        VEHICLES_BY_CATEGORY[vehicle.category] = []
    VEHICLES_BY_CATEGORY[vehicle.category].append(vehicle)


def get_vehicle_by_name(name):
    """
    Récupère un véhicule par son nom.
    
    Args:
        name: Nom du véhicule
        
    Returns:
        Vehicle: Instance du véhicule ou None si non trouvé
    """
    return VEHICLES_BY_NAME.get(name)


def get_vehicles_by_category(category):
    """
    Récupère tous les véhicules d'une catégorie.
    
    Args:
        category: Catégorie de véhicules
        
    Returns:
        list: Liste des véhicules de la catégorie
    """
    return VEHICLES_BY_CATEGORY.get(category, [])


def get_all_vehicles():
    """
    Récupère tous les véhicules disponibles.
    
    Returns:
        list: Liste de tous les véhicules
    """
    return list(ALL_VEHICLES)


def get_vehicle_names():
    """
    Récupère les noms de tous les véhicules.
    
    Returns:
        list: Liste des noms
    """
    return [v.name for v in ALL_VEHICLES]


def get_categories():
    """
    Récupère toutes les catégories de véhicules.
    
    Returns:
        list: Liste des catégories
    """
    return list(VEHICLES_BY_CATEGORY.keys())
