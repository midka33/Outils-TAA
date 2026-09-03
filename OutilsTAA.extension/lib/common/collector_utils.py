# -*- coding: utf-8 -*-
"""Collecteurs Revit réutilisables."""


def collect_by_category(document, category):
    """Retourne les éléments d'une catégorie Revit."""
    from Autodesk.Revit.DB import FilteredElementCollector
    return list(FilteredElementCollector(document).OfCategory(category).WhereElementIsNotElementType())
