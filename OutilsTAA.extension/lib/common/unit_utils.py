# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Utilitaires communs pour les unités Revit.

Les calculs métier doivent conserver les valeurs Double en unités internes
Revit. Les conversions sont réservées aux entrées/sorties nécessitant une unité
explicite.
"""


def _get_unit_utils(unit_utils=None):
    if unit_utils is not None:
        return unit_utils

    from Autodesk.Revit.DB import UnitUtils
    return UnitUtils


def _require_unit_type_id(unit_type_id):
    if unit_type_id is None:
        raise ValueError("Identifiant d'unité Revit manquant.")
    return unit_type_id


def convert_from_internal_units(value, unit_type_id, unit_utils=None):
    """Convertit une valeur interne Revit vers l'unité demandée."""
    api = _get_unit_utils(unit_utils)
    return api.ConvertFromInternalUnits(
        float(value),
        _require_unit_type_id(unit_type_id),
    )


def convert_to_internal_units(value, unit_type_id, unit_utils=None):
    """Convertit une valeur exprimée dans une unité vers les unités Revit."""
    api = _get_unit_utils(unit_utils)
    return api.ConvertToInternalUnits(
        float(value),
        _require_unit_type_id(unit_type_id),
    )


def data_type_ids_are_compatible(source_data_type_id, target_data_type_id):
    """Compare deux types de données Revit déjà normalisés en chaînes.

    Une valeur inconnue n'est pas déclarée incompatible : la validation Revit
    finale reste nécessaire. Deux identifiants connus différents sont
    incompatibles pour une écriture Double directe.
    """
    if not source_data_type_id or not target_data_type_id:
        return True
    return str(source_data_type_id) == str(target_data_type_id)
