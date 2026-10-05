# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Valeurs par défaut métier du module Plans de vente."""


DEFAULT_HOUSING_PARAMETER_NAME = "N° Appartement"


def preferred_housing_parameter_index(descriptors, preferred_name=None):
    """Retourne l'index du paramètre partagé préféré, sinon le premier choix."""
    values = list(descriptors or [])
    if not values:
        return -1

    target = preferred_name or DEFAULT_HOUSING_PARAMETER_NAME
    for index, descriptor in enumerate(values):
        if (
            getattr(descriptor, "name", None) == target
            and getattr(descriptor, "identity_kind", None) == "SHARED_GUID"
        ):
            return index

    return 0
