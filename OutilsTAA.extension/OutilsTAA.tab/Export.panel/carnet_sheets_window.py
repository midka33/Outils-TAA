# -*- coding: utf-8 -*-
"""Fenêtre de consultation des mises en pages d'un carnet."""

import os

from pyrevit import forms


class CarnetSheetsWindow(forms.WPFWindow):
    """Affiche les mises en pages contenues dans un carnet."""

    def __init__(self, publication_set, owner=None):
        self.publication_set = publication_set
        xaml_path = os.path.join(
            os.path.dirname(__file__),
            "carnet_sheets_window.xaml"
        )
        forms.WPFWindow.__init__(self, xaml_path)

        if owner is not None:
            self.Owner = owner

        self.CarnetTitle.Text = publication_set.name
        items = list(publication_set.items or [])
        items.sort(key=lambda item: (
            item.sheet_number or "",
            item.sheet_name or ""
        ))
        self.SheetsGrid.ItemsSource = items
        self.SheetsInfo.Text = "{0} mise(s) en page dans ce carnet.".format(
            len(items)
        )

    def Close_Click(self, sender, args):
        self.Close()
