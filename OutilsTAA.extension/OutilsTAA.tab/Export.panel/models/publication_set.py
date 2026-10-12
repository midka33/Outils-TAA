# -*- coding: utf-8 -*-
"""Modèle interne historique d'un dossier de publication."""


class PublicationSet(object):
    """Dossier feuille interne, conservé pour compatibilité des stockages existants."""

    def __init__(self, name, items=None, source=None, output_directory=None,
                 filename_template_id=None, set_id=None, persistent=False,
                 folder_id=None, publication_settings=None):
        self.id = set_id
        self.name = name
        self.items = list(items or [])
        self.source = source
        self.output_directory = output_directory
        self.filename_template_id = filename_template_id
        self.persistent = persistent
        # Dossier parent dans l'arborescence Export.
        self.folder_id = folder_id
        # Réglages persistants du dossier de publication.
        self.publication_settings = publication_settings
        # Compatibilité historique + ordre commun avec PublicationFolder.
        self.sort_order = 0
        self.tree_order = None

    def add_item(self, item):
        """Ajoute une mise en page au dossier si elle n'est pas déjà présente."""
        if item is None:
            return False

        for existing in self.items:
            if existing.unique_id == item.unique_id:
                return False

        self.items.append(item)
        return True

    def with_settings(self, settings):
        """Copie de travail pour la publication, sans écraser les réglages hérités."""
        from copy import copy
        target = copy(self)
        target.publication_settings = settings
        return target
