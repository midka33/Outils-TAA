# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Lecture et métadonnées de paramètres Revit.

Les fonctions historiques par nom sont conservées pour compatibilité.
Les nouveaux outils doivent privilégier les identifiants stables lorsqu'ils
sont disponibles.
"""


def get_parameter(element, name):
    """Retourne le paramètre demandé par nom ou None.

    Cette méthode reste utile comme fallback mais peut être ambiguë si plusieurs
    paramètres portent le même nom.
    """
    if element is None or not name:
        return None
    return element.LookupParameter(name)


def get_parameter_value(element, name, default=None):
    """Retourne la valeur affichable d'un paramètre recherché par nom."""
    parameter = get_parameter(element, name)
    if parameter is None:
        return default
    try:
        return parameter.AsValueString() or parameter.AsString() or default
    except Exception:
        return default


def forge_type_id_to_string(forge_type_id):
    """Retourne la chaîne stable d'un ForgeTypeId ou None s'il est vide."""
    if forge_type_id is None:
        return None

    type_id = getattr(forge_type_id, "TypeId", None)
    if type_id:
        return str(type_id)

    return None


def get_parameter_data_type_id(parameter):
    """Retourne le TypeId du type de donnée de la définition du paramètre."""
    if parameter is None:
        return None

    definition = getattr(parameter, "Definition", None)
    getter = getattr(definition, "GetDataType", None)
    if getter is None:
        return None

    try:
        return forge_type_id_to_string(getter())
    except Exception:
        return None


def get_parameter_unit_type_id(parameter):
    """Retourne le TypeId de l'unité du paramètre lorsqu'elle existe."""
    if parameter is None:
        return None

    getter = getattr(parameter, "GetUnitTypeId", None)
    if getter is None:
        return None

    try:
        return forge_type_id_to_string(getter())
    except Exception:
        # Les paramètres sans valeur mesurable peuvent lever InvalidOperationException.
        return None


def get_shared_parameter_guid(parameter):
    """Retourne le GUID d'un paramètre partagé sous forme de chaîne."""
    if parameter is None or not bool(getattr(parameter, "IsShared", False)):
        return None

    try:
        guid = parameter.GUID
        return str(guid) if guid is not None else None
    except Exception:
        return None


def get_built_in_parameter_type_id(parameter):
    """Retourne l'identifiant ForgeTypeId d'un paramètre intégré Revit."""
    if parameter is None:
        return None

    definition = getattr(parameter, "Definition", None)
    getter = getattr(definition, "GetParameterTypeId", None)
    if getter is None:
        return None

    try:
        return forge_type_id_to_string(getter())
    except Exception:
        return None


def get_definition_type_id(parameter):
    """Retourne l'identifiant de définition Revit pour un paramètre interne."""
    if parameter is None:
        return None

    definition = getattr(parameter, "Definition", None)
    getter = getattr(definition, "GetTypeId", None)
    if getter is None:
        return None

    try:
        return forge_type_id_to_string(getter())
    except Exception:
        return None
