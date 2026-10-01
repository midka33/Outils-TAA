# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Utilitaires communs pour les unités Revit."""

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


def _get_unit_utils(unit_utils=None):
    if unit_utils is not None:
        return unit_utils
    from Autodesk.Revit.DB import UnitUtils
    return UnitUtils


def _require_unit_type_id(unit_type_id):
    if unit_type_id is None:
        raise ValueError("Identifiant d'unité Revit manquant.")
    return unit_type_id


def forge_type_id_from_string(type_id, forge_type_factory=None):
    """Reconstruit un ForgeTypeId depuis sa valeur sérialisée."""
    if type_id is None:
        return None
    if not isinstance(type_id, string_types):
        return type_id

    factory = forge_type_factory
    if factory is None:
        from Autodesk.Revit.DB import ForgeTypeId
        factory = ForgeTypeId

    return factory(type_id)


def convert_from_internal_units(value, unit_type_id, unit_utils=None):
    api = _get_unit_utils(unit_utils)
    return api.ConvertFromInternalUnits(
        float(value),
        _require_unit_type_id(unit_type_id),
    )


def convert_to_internal_units(value, unit_type_id, unit_utils=None):
    api = _get_unit_utils(unit_utils)
    return api.ConvertToInternalUnits(
        float(value),
        _require_unit_type_id(unit_type_id),
    )


def data_type_ids_are_compatible(source_data_type_id, target_data_type_id):
    if not source_data_type_id or not target_data_type_id:
        return True
    return str(source_data_type_id) == str(target_data_type_id)
