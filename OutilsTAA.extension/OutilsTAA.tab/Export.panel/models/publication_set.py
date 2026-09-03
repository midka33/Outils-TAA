# -*- coding: utf-8 -*-
"""Modèle métier d'un carnet de publication."""


class PublicationSet(object):
    """Conteneur logique d'éléments publiables."""

    def __init__(self, name, items=None, source=None, output_directory=None,
                 filename_template_id=None, set_id=None, persistent=False):
        self.id = set_id
        self.name = name
        self.items = list(items or [])
        self.source = source
        self.output_directory = output_directory
        self.filename_template_id = filename_template_id
        self.persistent = persistent

    def add_item(self, item):
        """Ajoute un élément au carnet s'il n'est pas déjà présent."""
        if item is None:
            return False

        for existing in self.items:
            if existing.unique_id == item.unique_id:
                return False

        self.items.append(item)
        return True
