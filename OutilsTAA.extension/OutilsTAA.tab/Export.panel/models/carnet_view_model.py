# -*- coding: utf-8 -*-
"""Modèles simples destinés à alimenter l'interface WPF du module Export."""


class ParameterOption(object):
    """Paramètre sélectionnable dans l'interface."""

    def __init__(self, name, sheet_count):
        self.name = name
        self.sheet_count = sheet_count

    def __str__(self):
        return self.name


class ParameterValueOption(object):
    """Valeur de paramètre affichée avec son nombre de feuilles."""

    def __init__(self, value, count):
        self.value = value
        self.count = count
        self.is_selected = True

    def __str__(self):
        return "{0} ({1} feuille{2})".format(
            self.value,
            self.count,
            "s" if self.count != 1 else ""
        )


class CarnetListItem(object):
    """Représentation légère d'un carnet pour la liste WPF."""

    def __init__(self, publication_set, missing_count=0):
        self.id = publication_set.id
        self.name = publication_set.name
        self.item_count = len(publication_set.items)
        self.persistent = publication_set.persistent
        self.missing_count = missing_count
        self.status = self._build_status()

    def _build_status(self):
        if self.missing_count:
            return "{0} élément(s) introuvable(s)".format(self.missing_count)
        return "{0} élément(s)".format(self.item_count)
