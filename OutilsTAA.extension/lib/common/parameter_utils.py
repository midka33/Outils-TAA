# -*- coding: utf-8 -*-
"""Lecture et validation des paramètres Revit."""


def get_parameter(element, name):
    """Retourne le paramètre demandé ou None."""
    if element is None or not name:
        return None
    return element.LookupParameter(name)


def get_parameter_value(element, name, default=None):
    """Retourne la valeur brute exploitable d'un paramètre."""
    parameter = get_parameter(element, name)
    if parameter is None:
        return default
    try:
        return parameter.AsValueString() or parameter.AsString() or default
    except Exception:
        return default
