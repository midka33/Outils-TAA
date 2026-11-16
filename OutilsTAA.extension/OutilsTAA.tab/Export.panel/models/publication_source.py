# -*- coding: utf-8 -*-
"""Modèle décrivant l'origine d'un carnet de publication."""


class PublicationSource(object):
    """Décrit comment les éléments d'un carnet sont déterminés."""

    PARAMETER = "PARAMETER"
    MANUAL = "MANUAL"
    TEMPORARY = "TEMPORARY"
    DYNAMIC = "DYNAMIC"

    def __init__(self, mode, parameter_name=None, parameter_value=None,
                 group_parameter=None, frozen_group_ids=None):
        self.mode = mode
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.group_parameter = group_parameter

        # IDs des groupes convertis individuellement en dossiers manuels.
        self.frozen_group_ids = list(frozen_group_ids or [])
