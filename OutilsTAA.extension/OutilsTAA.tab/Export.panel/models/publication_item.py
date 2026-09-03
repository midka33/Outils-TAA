# -*- coding: utf-8 -*-
"""Modèle représentant un élément à publier."""


class PublicationItem(object):
    """Représente une feuille ou un élément Revit publiable."""

    def __init__(self, unique_id, sheet_id, item_type, sheet_number,
                 sheet_name, parameter_value=None):
        self.unique_id = unique_id
        self.sheet_id = sheet_id
        self.item_type = item_type
        self.sheet_number = sheet_number
        self.sheet_name = sheet_name
        self.parameter_value = parameter_value
