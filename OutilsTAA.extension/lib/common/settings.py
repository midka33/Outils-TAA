# -*- coding: utf-8 -*-
"""Gestion des préférences locales Outils TAA.

Le stockage concret sera branché sur le mécanisme retenu par le projet.
"""


class SettingsStore(object):
    """Interface minimale pour les préférences persistantes."""

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value):
        raise NotImplementedError
