# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Choix des valeurs à harmoniser entre occurrences de groupes."""

import os

from pyrevit import forms

from System.Windows import Thickness
from System.Windows.Controls import (
    Border,
    ComboBox,
    DockPanel,
    StackPanel,
    TextBlock,
)

from common.wpf_resources import load_resource_dictionary


class GroupValueSelectionWindow(forms.WPFWindow):

    def __init__(self, analysis, owner=None):
        self.analysis = analysis
        self.selections = None
        self._combos = {}

        current_dir = os.path.dirname(__file__)
        xaml_path = os.path.join(
            current_dir,
            "group_value_selection.xaml",
        )
        forms.WPFWindow.__init__(self, xaml_path)

        if owner is not None:
            self.Owner = owner

        self._load_theme()
        self._render_rows()

    def _load_theme(self):
        panel_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..")
        )
        extension_dir = os.path.abspath(
            os.path.join(panel_dir, "..", "..")
        )
        resource_path = os.path.join(
            extension_dir,
            "resources",
            "ui",
            "taa_theme.xaml",
        )
        load_resource_dictionary(self, resource_path)

    def _render_rows(self):
        conflicts = list(getattr(self.analysis, "conflicts", []) or [])

        for conflict in conflicts:
            border = Border()
            border.Background = self.FindResource("TAAPanelBrush")
            border.BorderBrush = self.FindResource("TAABorderBrush")
            border.BorderThickness = Thickness(1)
            border.Padding = Thickness(10)
            border.Margin = Thickness(0, 0, 0, 8)

            dock = DockPanel()
            dock.LastChildFill = True

            combo = ComboBox()
            combo.Width = 300
            combo.MinHeight = 30
            combo.Margin = Thickness(16, 0, 0, 0)
            combo.ItemsSource = [
                candidate.display_label
                for candidate in conflict.candidates
            ]
            combo.SelectedIndex = conflict.recommended_index
            try:
                combo.Style = self.FindResource("TAAComboBox")
            except Exception:
                pass
            DockPanel.SetDock(combo, 1)
            dock.Children.Add(combo)

            labels = StackPanel()

            group_text = TextBlock()
            group_text.Text = conflict.group_type_name
            group_text.FontWeight = self._semi_bold()
            group_text.TextWrapping = 2
            labels.Children.Add(group_text)

            member_text = TextBlock()
            member_text.Text = conflict.member_label
            member_text.Margin = Thickness(0, 3, 0, 0)
            member_text.TextWrapping = 2
            member_text.Foreground = self.FindResource(
                "TAASecondaryTextBrush"
            )
            labels.Children.Add(member_text)

            dock.Children.Add(labels)
            border.Child = dock
            self.ConflictRowsPanel.Children.Add(border)
            self._combos[conflict.key] = (combo, conflict)

    @staticmethod
    def _semi_bold():
        try:
            from System.Windows import FontWeights
            return FontWeights.SemiBold
        except Exception:
            return None

    def Apply_Click(self, sender, args):
        selections = {}

        for key, data in self._combos.items():
            combo, conflict = data
            index = combo.SelectedIndex
            if index < 0 or index >= len(conflict.candidates):
                forms.alert(
                    "Choisissez une valeur pour chaque groupe.",
                    title="Calculs des pièces",
                    warn_icon=True,
                )
                return

            selections[key] = conflict.candidates[index].value

        self.selections = selections
        self.DialogResult = True
        self.Close()

    def Cancel_Click(self, sender, args):
        self.selections = None
        self.DialogResult = False
        self.Close()
