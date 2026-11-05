# -*- coding: utf-8 -*-
"""Choix du véhicule et du mode pour le prototype de placement par clics."""
import os
from pyrevit import forms
from giration_theme import apply_theme


class GirationMainWindow(forms.WPFWindow):
    def __init__(self, vehicles):
        path = os.path.join(os.path.dirname(__file__), 'giration_main_window.xaml')
        forms.WPFWindow.__init__(self, path)
        apply_theme(self)
        self.vehicle = None
        self.reverse = False
        self._vehicles = dict((v.name, v) for v in vehicles)
        self.VehicleCombo.ItemsSource = sorted(self._vehicles.keys())
        self.VehicleCombo.SelectionChanged += self._vehicle_changed
        self.StartButton.Click += self._start
        self.CloseButton.Click += self._close
        if vehicles:
            self.VehicleCombo.SelectedIndex = 0

    def _vehicle_changed(self, sender, args):
        vehicle = self._vehicles.get(self.VehicleCombo.SelectedItem)
        if vehicle:
            self.VehicleInfo.Text = ('{0:.2f} × {1:.2f} m ; empattement {2:.2f} m ; '
                                     'rayon d\'essieu minimal calculé : {3:.2f} m.\n'
                                     'Source : EXEMPLE, NON VERIFIÉ.').format(
                                         vehicle.length, vehicle.width, vehicle.wheelbase,
                                         vehicle.wheelbase / __import__('math').tan(vehicle.max_steering_angle))

    def _start(self, sender, args):
        if not self.AcknowledgeCheck.IsChecked:
            forms.alert('Veuillez confirmer le caractère provisoire des données.',
                        title='Giration')
            return
        self.vehicle = self._vehicles.get(self.VehicleCombo.SelectedItem)
        self.reverse = bool(self.ReverseCheck.IsChecked)
        if self.vehicle:
            self.DialogResult = True
            self.Close()

    def _close(self, sender, args):
        self.DialogResult = False
        self.Close()
