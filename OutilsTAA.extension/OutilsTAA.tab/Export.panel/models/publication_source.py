"""Modèle décrivant l'origine d'un carnet de publication."""


class PublicationSource(object):
    """Décrit comment les éléments d'un carnet sont déterminés."""

    PARAMETER = "PARAMETER"
    MANUAL = "MANUAL"
    TEMPORARY = "TEMPORARY"
    DYNAMIC = "DYNAMIC"

    def __init__(self, mode, parameter_name=None, parameter_value=None):
        self.mode = mode
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
