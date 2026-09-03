"""Journalisation centralisée d'Outils TAA."""

import logging


LOGGER_NAME = "OutilsTAA"


def get_logger(name=None):
    """Retourne un logger commun, sans imposer de configuration à l'appelant."""
    return logging.getLogger(name or LOGGER_NAME)
