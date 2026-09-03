# -*- coding: utf-8 -*-
"""Modèle de rapport d'exécution d'une publication Export."""


class PublicationResult(object):
    """Résultat d'une publication de carnet."""

    def __init__(self, publication_set):
        self.publication_set = publication_set
        self.success = False
        self.errors = []
        self.warnings = []
        self.files = []

    @property
    def status(self):
        if self.errors:
            return "Erreur"
        if self.warnings:
            return "Terminé avec avertissements"
        return "Terminé"

    def add_file(self, path):
        if path and path not in self.files:
            self.files.append(path)
