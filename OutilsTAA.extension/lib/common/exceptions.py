# -*- coding: utf-8 -*-
"""Exceptions communes à Outils TAA."""


class OutilsTAAError(Exception):
    """Erreur racine contrôlée de l'application."""


class ValidationError(OutilsTAAError):
    """Donnée ou état métier invalide."""


class ExportError(OutilsTAAError):
    """Erreur lors d'une opération d'export/publication."""
