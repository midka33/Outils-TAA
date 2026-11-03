# -*- coding: utf-8 -*-
"""
Fenêtre principale du module Giration des véhicules.

Cette fenêtre permet à l'utilisateur de:
- Sélectionner un véhicule
- Visualiser ses caractéristiques
- Démarrer le tracé de la trajectoire
- Configurer les options d'affichage
"""

import os
import sys
import math

# Configuration des chemins
CURRENT_DIR = os.path.dirname(__file__)
PANEL_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
EXTENSION_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
LIB_DIR = os.path.join(EXTENSION_DIR, "lib")

for path in (EXTENSION_DIR, LIB_DIR, PANEL_DIR):
    if path not in sys.path:
        sys.path.append(path)

from pyrevit import forms
from lib.common import logger
from services.taa_ui_theme import apply_theme


class GirationMainWindow(forms.WPFWindow):
    """
    Fenêtre WPF principale pour la giration des véhicules.
    
    Cette fenêtre s'intègre à la charte graphique Outils TAA et permet
    de contrôler la simulation de giration.
    """
    
    def __init__(self, controller):
        """
        Initialise la fenêtre.
        
        Args:
            controller: Instance de GirationController
        """
        self.controller = controller
        self._is_tracing = False
        self._current_trajectory = []
        
        # Charger le XAML
        xaml_path = os.path.join(os.path.dirname(__file__), "giration_main_window.xaml")
        forms.WPFWindow.__init__(self, xaml_path)
        
        # Appliquer le thème Outils TAA
        apply_theme(self)
        
        # Initialiser l'interface
        self._initialize_ui()
        
        # Connexion des événements
        self._connect_events()
    
    def _initialize_ui(self):
        """Initialise les éléments de l'interface."""
        # Charger les catégories de véhicules
        categories = self.controller.get_categories()
        self.CategoryCombo.ItemsSource = categories
        
        if categories:
            self.CategoryCombo.SelectedIndex = 0
        
        # Mettre à jour la liste des véhicules
        self._update_vehicle_list()
        
        # Mettre à jour les informations du véhicule sélectionné
        self._update_vehicle_info()
        
        # Mettre à jour le texte de statut
        self._update_status()
    
    def _connect_events(self):
        """Connecte les gestionnaires d'événements."""
        # Ces connexions sont faites directement dans le XAML
        # Les méthodes sont appelées automatiquement par WPF
        pass
    
    def CategoryCombo_SelectionChanged(self, sender, args):
        """Gestionnaire de l'événement de changement de catégorie."""
        self._update_vehicle_list()
    
    def VehicleCombo_SelectionChanged(self, sender, args):
        """Gestionnaire de l'événement de changement de véhicule."""
        if self.VehicleCombo.SelectedItem:
            vehicle = self.VehicleCombo.SelectedItem
            self.controller.set_current_vehicle(vehicle.name)
            self._update_vehicle_info()
    
    def _update_vehicle_list(self):
        """Met à jour la liste des véhicules en fonction de la catégorie sélectionnée."""
        if self.CategoryCombo.SelectedItem is None:
            self.VehicleCombo.ItemsSource = self.controller.get_available_vehicles()
        else:
            category = self.CategoryCombo.SelectedItem
            vehicles = [v for v in self.controller.get_available_vehicles() if v.category == category]
            self.VehicleCombo.ItemsSource = vehicles
        
        # Sélectionner le premier véhicule
        if self.VehicleCombo.ItemsSource and len(self.VehicleCombo.ItemsSource) > 0:
            self.VehicleCombo.SelectedIndex = 0
    
    def _update_vehicle_info(self):
        """Met à jour les informations du véhicule sélectionné."""
        vehicle = self.controller.get_current_vehicle()
        
        if vehicle:
            self.LengthValue.Text = "{0:.2f} m".format(vehicle.length)
            self.WidthValue.Text = "{0:.2f} m".format(vehicle.width)
            self.WheelbaseValue.Text = "{0:.2f} m".format(vehicle.wheelbase)
            
            if vehicle.min_turning_radius:
                self.MinRadiusValue.Text = "{0:.2f} m".format(vehicle.min_turning_radius)
            else:
                self.MinRadiusValue.Text = "N/A"
            
            # Convertir l'angle de radians en degrés
            max_steering_deg = math.degrees(vehicle.max_steering_angle)
            self.MaxSteeringValue.Text = "{0:.1f}°".format(max_steering_deg)
        else:
            self.LengthValue.Text = "0.0 m"
            self.WidthValue.Text = "0.0 m"
            self.WheelbaseValue.Text = "0.0 m"
            self.MinRadiusValue.Text = "0.0 m"
            self.MaxSteeringValue.Text = "0°"
    
    def _update_status(self, message="Prêt"):
        """Met à jour le texte de statut."""
        self.StatusText.Text = message
    
    def StartButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Démarrer."""
        if self._is_tracing:
            # Déjà en cours de tracé, terminer
            self._is_tracing = False
            self._update_status("Prêt")
            self.StartButton.Content = "Démarrer le tracé"
            self.CancelButton.IsEnabled = False
            self.FinishButton.IsEnabled = True
        else:
            # Commencer le tracé
            self._is_tracing = True
            self._current_trajectory = []
            self._update_status("Tracé en cours - Cliquez dans la vue Revit")
            self.StartButton.Content = "Arrêter"
            self.CancelButton.IsEnabled = True
            self.FinishButton.IsEnabled = False
            
            # TODO: Activer le mode de tracé interactif dans Revit
            # Cela nécessitera l'implémentation de:
            # - ExternalEvent pour capturer les clics souris
            # - Prévisualisation dynamique
            # - Gestion des segments de trajectoire
            
            # Pour l'instant, afficher un message
            forms.alert(
                "Le mode de tracé interactif nécessite Revit 2025.4.\n\n"
                "Cette fonctionnalité sera implémentée dans une phase ultérieure.\n\n"
                "Pour l'instant, vous pouvez utiliser les boutons de test ci-dessous.",
                title="Tracé interactif"
            )
            self._is_tracing = False
            self._update_status("Prêt")
            self.StartButton.Content = "Démarrer le tracé"
            self.CancelButton.IsEnabled = False
    
    def CancelButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Annuler."""
        self._is_tracing = False
        self._current_trajectory = []
        self._update_status("Tracé annulé")
        self.StartButton.Content = "Démarrer le tracé"
        self.CancelButton.IsEnabled = False
        self.FinishButton.IsEnabled = False
        
        # TODO: Effacer la prévisualisation dans Revit
    
    def UndoButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Annuler dernier."""
        if self._current_trajectory:
            self._current_trajectory.pop()
            self._update_trajectory_info()
            
            # TODO: Mettre à jour la prévisualisation dans Revit
            
            self._update_status("Dernier segment annulé - {0} segments restants".format(len(self._current_trajectory)))
    
    def ClearButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Effacer tout."""
        self._current_trajectory = []
        self._update_trajectory_info()
        self._update_status("Trajectoire effacée")
        
        # TODO: Effacer tous les éléments de prévisualisation dans Revit
    
    def FinishButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Terminer."""
        if not self._current_trajectory:
            forms.alert("Aucune trajectoire à enregistrer.", title="Terminer")
            return
        
        # TODO: Enregistrer la simulation
        # Pour l'instant, afficher un message
        forms.alert(
            "La fonctionnalité d'enregistrement sera implémentée dans une phase ultérieure.",
            title="Enregistrement"
        )
        
        self._update_status("Simulation terminée")
    
    def HelpButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Aide."""
        help_text = """
        **Giration des véhicules - Aide**
        
        1. **Sélection du véhicule**
           - Choisissez une catégorie dans la liste
           - Sélectionnez un véhicule spécifique
           - Les caractéristiques s'affichent automatiquement
        
        2. **Tracé de la trajectoire**
           - Cliquez sur "Démarrer le tracé"
           - Cliquez dans la vue de plan Revit pour définir le point de départ
           - Déplacez la souris pour définir la direction
           - Cliquez pour valider chaque segment
           - Utilisez "Annuler dernier" pour corriger
        
        3. **Options d'affichage**
           - Cochez/décochez les options pour afficher/masquer:
             * Le véhicule
             * Les trajectoires des roues
             * L'enveloppe balayée
             * Les positions intermédiaires
        
        4. **Terminer et enregistrer**
           - Cliquez sur "Terminer" pour finaliser la simulation
           - La trajectoire sera enregistrée et pourra être modifiée plus tard
        
        **Note:** Certaines fonctionnalités nécessitent Revit 2025.4 et seront
        implémentées dans les phases suivantes.
        """
        forms.alert(help_text, title="Aide - Giration des véhicules", exits=['OK'])
    
    def CloseButton_Click(self, sender, args):
        """Gestionnaire du clic sur le bouton Fermer."""
        self.Close()
    
    def _update_trajectory_info(self):
        """Met à jour les informations sur la trajectoire."""
        num_segments = len(self._current_trajectory)
        if num_segments == 0:
            self.TrajectoryInfo.Text = "Aucune trajectoire"
        elif num_segments == 1:
            self.TrajectoryInfo.Text = "1 segment"
        else:
            self.TrajectoryInfo.Text = "{0} segments".format(num_segments)
    
    def _test_trajectory(self):
        """
        Méthode de test pour générer une trajectoire d'exemple.
        
        Cette méthode peut être utilisée pour tester le moteur cinématique
        sans nécessiter l'interaction Revit.
        """
        if not self.controller.get_current_vehicle():
            forms.alert("Aucun véhicule sélectionné.", title="Test")
            return
        
        # Créer une trajectoire de test
        segments = [
            {'distance': 5.0, 'steering_angle': 0.0, 'is_reverse': False, 'num_points': 10},
            {'distance': 3.0, 'steering_angle': math.radians(30), 'is_reverse': False, 'num_points': 10},
            {'distance': 2.0, 'steering_angle': 0.0, 'is_reverse': False, 'num_points': 10},
        ]
        
        trajectory = self.controller.calculate_trajectory(
            start_point=(0.0, 0.0),
            start_angle=0.0,
            segments=segments
        )
        
        self._current_trajectory = trajectory
        self._update_trajectory_info()
        
        # Calculer les trajectoires des roues
        wheel_trajectories = self.controller.calculate_wheel_trajectories(trajectory)
        
        # Calculer l'enveloppe balayée
        swept_area = self.controller.calculate_swept_area(trajectory)
        
        # Valider la trajectoire
        is_valid, errors = self.controller.validate_trajectory(trajectory)
        
        if is_valid:
            self._update_status("Test réussi: {0} points générés".format(len(trajectory)))
            
            # Afficher les résultats
            result_text = """
            **Résultats du test**
            
            - Points de trajectoire: {0}
            - Trajectoires des roues: {1} roues
            - Polygones balayés: {2}
            - Validation: ✓ Valide
            """.format(len(trajectory), len(wheel_trajectories), len(swept_area))
            forms.alert(result_text, title="Résultats du test")
        else:
            self._update_status("Test échoué: erreurs de validation")
            error_text = "Erreurs:\n" + "\n".join(errors)
            forms.alert(error_text, title="Erreurs de validation")
