# -*- coding: utf-8 -*-
"""Résolution centralisée de l'héritage des réglages Export."""

from publication_settings import PublicationSettings


class SettingsResolver(object):
    """Résout Profil → Dossier → Carnet, propriété par propriété."""

    def __init__(self, profile_service):
        self.profile_service = profile_service

    def resolve(self, publication_set, folder=None, profile_name=None):
        """Retourne des réglages concrets sans modifier les objets sources."""
        layers = []
        if profile_name:
            profile = self.profile_service.get(profile_name)
            if profile:
                layers.append(PublicationSettings.from_dict(profile))
        if folder is not None:
            layers.append(getattr(folder, "publication_settings", None))
        layers.append(getattr(publication_set, "publication_settings", None))

        result = PublicationSettings.defaults()
        for field in PublicationSettings.FIELDS:
            for settings in reversed(layers):
                if settings is not None and getattr(settings, field, None) is not None:
                    setattr(result, field, getattr(settings, field))
                    break
        return result

    def source_for(self, publication_set, field, folder=None, profile_name=None):
        """Indique le niveau qui fournit actuellement une valeur."""
        if field not in PublicationSettings.FIELDS:
            raise ValueError("Réglage inconnu : " + str(field))
        if publication_set is not None:
            settings = getattr(publication_set, "publication_settings", None)
            if settings is not None and getattr(settings, field, None) is not None:
                return "Carnet"
        if folder is not None:
            settings = getattr(folder, "publication_settings", None)
            if settings is not None and getattr(settings, field, None) is not None:
                return "Dossier"
        if profile_name and self.profile_service.get(profile_name) and \
                self.profile_service.get(profile_name).get(field) is not None:
            return "Profil"
        return "Défaut"
