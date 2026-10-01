# -*- coding: utf-8 -*-
"""Dialogue PDF : saisie isolée, sans sauvegarde avant Appliquer."""
import os
from pyrevit import forms
from System.Windows import Thickness, TextWrapping
from System.Windows.Controls import CheckBox, TextBlock
from taa_ui_theme import apply_theme
from pdf_options import PDF_OPTIONS, defaults, capabilities, changed_options


class PdfSettingsWindow(forms.WPFWindow):
    def __init__(self, settings, owner=None):
        self.result = None
        self.initial = dict((field, getattr(settings, field)) for field, prop, default, label in PDF_OPTIONS)
        self.controls = {}
        self.supported = capabilities()
        forms.WPFWindow.__init__(self, os.path.join(os.path.dirname(__file__), "pdf_settings.xaml"))
        apply_theme(self)
        if owner is not None:
            self.Owner = owner
        for index, (field, prop, default, label) in enumerate(PDF_OPTIONS[:-1]):
            control = CheckBox(Content=TextBlock(Text=label, TextWrapping=TextWrapping.Wrap), Margin=Thickness(0, 0, 12, 12))
            control.IsEnabled = self.supported[field]
            if not control.IsEnabled:
                control.ToolTip = "Option indisponible dans la version de Revit chargée."
            (self.LeftOptions if index < 4 else self.RightOptions).Children.Add(control)
            self.controls[field] = control
        self.VectorRadio.IsEnabled = self.supported['pdf_raster']
        self.RasterRadio.IsEnabled = self.supported['pdf_raster']
        self._display(self.initial)

    def _display(self, values):
        for field, control in self.controls.items():
            control.IsChecked = values[field]
        self.RasterRadio.IsChecked = values['pdf_raster']
        self.VectorRadio.IsChecked = not values['pdf_raster']
        self.ProcessingChanged(None, None)

    def ProcessingChanged(self, sender, args):
        control = self.controls.get("pdf_mask_coincident_lines")
        if control is not None:
            control.IsEnabled = self.supported["pdf_mask_coincident_lines"] and not bool(self.RasterRadio.IsChecked)

    def Defaults_Click(self, sender, args):
        self._display(defaults())

    def Cancel_Click(self, sender, args):
        self.Close()

    def Apply_Click(self, sender, args):
        current = dict((field, bool(control.IsChecked)) for field, control in self.controls.items()
                       if self.supported[field])
        if self.supported['pdf_raster']:
            current['pdf_raster'] = bool(self.RasterRadio.IsChecked)
        self.result = changed_options(self.initial, current)
        self.Close()
