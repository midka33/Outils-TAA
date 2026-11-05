# -*- coding: utf-8 -*-
"""Catalogue de PROTOTYPES NON VERIFIES (aucun véhicule homologué SDIS).

Les dimensions sont reprises comme exemples de l'ancienne branche Giration.
Une fiche constructeur et son rayon clairement défini sont indispensables
avant un usage professionnel dans un dossier de conformité.
"""
import math
from ..models.vehicle import Vehicle

_EXAMPLES = [
    ('Exemple camion echelle', 'Secours (provisoire)', 12.0, 2.55, 6.5, 2.5, 3.0, 2.1, 1.85, 45),
    ('Exemple fourgon pompe-tonne', 'Secours (provisoire)', 9.5, 2.5, 5.0, 2.0, 2.5, 2.0, 1.8, 40),
    ('Exemple ambulance VSAV', 'Secours (provisoire)', 7.2, 2.2, 4.0, 1.5, 1.7, 1.8, 1.7, 45),
    ('Exemple camion collecte', 'Collecte (provisoire)', 10.0, 2.5, 5.5, 2.5, 2.0, 2.0, 1.8, 45),
    ('Exemple camion grand volume', 'Collecte (provisoire)', 12.0, 2.6, 6.0, 3.0, 3.0, 2.1, 1.9, 40),
    ('Exemple utilitaire leger', 'Utilitaires (provisoire)', 5.5, 2.0, 3.2, 0.8, 1.5, 1.6, 1.55, 45),
    ('Exemple fourgon de livraison', 'Utilitaires (provisoire)', 7.0, 2.2, 4.0, 1.2, 1.8, 1.8, 1.7, 42),
    ('Exemple voiture', 'Particuliers (provisoire)', 4.5, 1.8, 2.7, 0.8, 1.0, 1.55, 1.5, 40),
    ('Exemple SUV', 'Particuliers (provisoire)', 5.2, 2.0, 3.0, 1.0, 1.2, 1.65, 1.65, 38),
]


def get_all_vehicles():
    result = []
    for name, category, length, width, wb, front, rear, ft, rt, degrees in _EXAMPLES:
        result.append(Vehicle(name, category, length, width, wb, front, rear,
                              ft, rt, math.radians(degrees),
                              source='Gabarit illustratif issu du prototype initial',
                              reference='DONNEES NON VERIFIEES', verified=False))
    return result


def get_vehicle_by_name(name):
    for vehicle in get_all_vehicles():
        if vehicle.name == name:
            return vehicle
    return None
