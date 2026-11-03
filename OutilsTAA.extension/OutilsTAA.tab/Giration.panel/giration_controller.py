# -*- coding: utf-8 -*-
"""
Contrôleur principal du module Giration des véhicules.

Ce contrôleur orchestré les interactions entre:
- L'interface utilisateur
- Le moteur cinématique
- Les services Revit
- La persistance des données
"""

import os
import sys

# Assurer que le chemin vers lib/giration est dans sys.path
LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "lib"))
if LIB_DIR not in sys.path:
    sys.path.append(LIB_DIR)

from lib.giration.models.vehicle import Vehicle
from lib.giration.services.kinematics import AckermannKinematics, TrajectoryPoint
from lib.giration.data.vehicles import get_all_vehicles, get_vehicle_by_name


class GirationController:
    """
    Contrôleur principal pour la simulation de giration des véhicules.
    
    Ce contrôleur gère:
    - La sélection des véhicules
    - Le calcul des trajectoires
    - La création des éléments Revit
    - La persistance des simulations
    
    Attributs:
        doc: Document Revit actuel
        current_vehicle: Véhicule actuellement sélectionné
        kinematics: Moteur cinématique
        simulations: Liste des simulations enregistrées
    """
    
    def __init__(self, revit_doc):
        """
        Initialise le contrôleur.
        
        Args:
            revit_doc: Document Revit actuel
        """
        self.doc = revit_doc
        self.current_vehicle = None
        self.kinematics = None
        self.simulations = []
        self._initialize_vehicles()
    
    def _initialize_vehicles(self):
        """Initialise la liste des véhicules disponibles."""
        self.available_vehicles = get_all_vehicles()
        if self.available_vehicles:
            self.current_vehicle = self.available_vehicles[0]
            self.kinematics = AckermannKinematics(self.current_vehicle)
    
    def get_available_vehicles(self):
        """
        Retourne la liste des véhicules disponibles.
        
        Returns:
            list: Liste des instances Vehicle
        """
        return self.available_vehicles
    
    def get_vehicle_names(self):
        """
        Retourne les noms des véhicules disponibles.
        
        Returns:
            list: Liste des noms de véhicules
        """
        return [v.name for v in self.available_vehicles]
    
    def get_categories(self):
        """
        Retourne les catégories de véhicules disponibles.
        
        Returns:
            list: Liste des catégories
        """
        categories = set()
        for v in self.available_vehicles:
            categories.add(v.category)
        return sorted(categories)
    
    def set_current_vehicle(self, vehicle_name):
        """
        Définit le véhicule courant par son nom.
        
        Args:
            vehicle_name: Nom du véhicule
            
        Returns:
            bool: True si le véhicule a été trouvé et défini, False sinon
        """
        vehicle = get_vehicle_by_name(vehicle_name)
        if vehicle:
            self.current_vehicle = vehicle
            self.kinematics = AckermannKinematics(vehicle)
            return True
        return False
    
    def get_current_vehicle(self):
        """
        Retourne le véhicule actuellement sélectionné.
        
        Returns:
            Vehicle: Véhicule courant
        """
        return self.current_vehicle
    
    def calculate_trajectory(
        self,
        start_point,
        start_angle=0.0,
        segments=None
    ):
        """
        Calcule une trajectoire pour le véhicule courant.
        
        Args:
            start_point: Point de départ (tuple ou Vector2D)
            start_angle: Orientation initiale (radians)
            segments: Liste de segments de trajectoire
            
        Returns:
            list: Liste de TrajectoryPoint
        """
        if self.kinematics is None:
            return []
        
        return self.kinematics.calculate_path(
            start_point,
            start_angle,
            segments
        )
    
    def calculate_wheel_trajectories(self, trajectory):
        """
        Calcule les trajectoires des roues pour une trajectoire donnée.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            
        Returns:
            dict: Dictionnaire avec les trajectoires des 4 roues
        """
        if self.kinematics is None:
            return {}
        return self.kinematics.calculate_wheel_trajectories(trajectory)
    
    def calculate_swept_area(self, trajectory):
        """
        Calcule l'enveloppe balayée pour une trajectoire donnée.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            
        Returns:
            list: Liste de polygones représentant l'enveloppe
        """
        if self.kinematics is None:
            return []
        return self.kinematics.calculate_swept_area(trajectory)
    
    def validate_trajectory(self, trajectory):
        """
        Valide une trajectoire par rapport aux contraintes du véhicule.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            
        Returns:
            tuple: (is_valid, errors)
        """
        if self.kinematics is None:
            return False, ["Aucun véhicule sélectionné"]
        return self.kinematics.validate_trajectory(trajectory)
    
    def create_revit_elements(self, trajectory, wheel_trajectories, swept_area):
        """
        Crée les éléments Revit pour visualiser la trajectoire.
        
        NOTE: Cette méthode nécessite Revit et ne peut pas être testée
        sans l'environnement Revit. Elle sera implémentée dans une phase ultérieure.
        
        Args:
            trajectory: Liste de TrajectoryPoint
            wheel_trajectories: Dictionnaire des trajectoires des roues
            swept_area: Liste des polygones de l'enveloppe balayée
            
        Returns:
            list: Liste des éléments Revit créés
        """
        # TODO: Implémenter la création des éléments Revit
        # Cela nécessitera:
        # 1. Accès à l'API Revit via pyRevit
        # 2. Création de lignes, arcs, etc.
        # 3. Gestion des transactions
        # 4. Organisation des éléments dans des groupes ou sous-projets
        
        # Pour l'instant, retourner une liste vide
        # Cette méthode sera testée dans Revit lors de la phase P2
        return []
    
    def save_simulation(self, simulation_data):
        """
        Enregistre une simulation.
        
        Args:
            simulation_data: Dictionnaire contenant les données de la simulation
            
        Returns:
            bool: True si l'enregistrement a réussi
        """
        # TODO: Implémenter la persistance des simulations
        # Cela pourrait utiliser:
        # - Les paramètres de projet Revit
        # - Un fichier JSON externe
        # - Une base de données intégrée
        self.simulations.append(simulation_data)
        return True
    
    def load_simulation(self, simulation_id):
        """
        Charge une simulation enregistrée.
        
        Args:
            simulation_id: Identifiant de la simulation
            
        Returns:
            dict: Données de la simulation ou None si non trouvée
        """
        # TODO: Implémenter le chargement des simulations
        for sim in self.simulations:
            if sim.get('id') == simulation_id:
                return sim
        return None
    
    def get_simulations(self):
        """
        Retourne la liste des simulations enregistrées.
        
        Returns:
            list: Liste des simulations
        """
        return self.simulations
    
    def clear_simulations(self):
        """Efface toutes les simulations enregistrées."""
        self.simulations = []
