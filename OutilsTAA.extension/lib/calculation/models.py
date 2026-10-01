# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Modèles métier purs pour les calculs des pièces."""


class RoomCalculationItem(object):
    """Donnée normalisée nécessaire au calcul pour une pièce.

    Le modèle ne dépend pas de l'API Revit. Les adaptateurs Revit sont
    responsables de convertir les paramètres en valeurs Python avant calcul.
    """

    def __init__(self, room_key, group_value, source_value):
        self.room_key = room_key
        self.group_value = group_value
        self.source_value = source_value


class SkippedRoom(object):
    """Décrit une pièce ignorée par le moteur de calcul."""

    def __init__(self, room_key, reason):
        self.room_key = room_key
        self.reason = reason


class CalculationResult(object):
    """Résultat immutable par convention d'un calcul de regroupement/somme."""

    def __init__(self, totals=None, total_items=0, calculated_items=0, skipped=None):
        self._totals = dict(totals or {})
        self.total_items = int(total_items)
        self.calculated_items = int(calculated_items)
        self.skipped = list(skipped or [])

    @property
    def totals(self):
        """Retourne une copie des totaux par groupe."""
        return dict(self._totals)

    @property
    def skipped_items(self):
        return len(self.skipped)

    @property
    def group_count(self):
        return len(self._totals)

    def get_total(self, group_value, default=None):
        return self._totals.get(group_value, default)
