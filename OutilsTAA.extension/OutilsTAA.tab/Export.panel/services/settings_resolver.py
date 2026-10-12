# -*- coding: utf-8 -*-
"""Résolution centralisée de l'héritage des réglages Export."""

from publication_settings import PublicationSettings


class SettingsResolver(object):
    """Résout Profil → Dossier → Carnet, propriété par propriété."""

    def __init__(self, profile_service):
        self.profile_service = profile_service

    @staticmethod
    def _parent_id(value):
        if value is None:
            return None
        if hasattr(value, "parent_id"):
            return getattr(value, "parent_id", None)
        return getattr(value, "folder_id", None)

    @staticmethod
    def _settings(value):
        return getattr(value, "publication_settings", None)

    @classmethod
    def container_chain(cls, value, folders=None, publication_sets=None,
                        include_self=True):
        """Chaîne générique : dossier courant puis parents visuels.

        PublicationFolder et PublicationSet sont traités de façon identique pour
        l'héritage. Les IDs restent globaux dans le stockage Export.
        """
        by_id = {}
        for item in list(folders or []) + list(publication_sets or []):
            item_id = getattr(item, "id", None)
            if item_id is not None:
                by_id[str(item_id)] = item

        chain = []
        seen = set()
        current = value if include_self else by_id.get(
            str(cls._parent_id(value))
        )
        while current is not None:
            key = str(getattr(current, "id", ""))
            if key in seen:
                raise ValueError(
                    "Cycle dans les dossiers de publication : {0}".format(
                        getattr(current, "name", key)
                    )
                )
            seen.add(key)
            chain.append(current)
            parent_id = cls._parent_id(current)
            current = (
                by_id.get(str(parent_id))
                if parent_id is not None else None
            )
        return chain

    def resolve_node(self, value, folders=None, publication_sets=None,
                     profile_name=None):
        """Résout Profil → ancêtres → dossier courant, sans distinction de type."""
        chain = self.container_chain(
            value,
            folders=folders,
            publication_sets=publication_sets,
            include_self=True,
        )

        result = PublicationSettings.defaults()
        for field in PublicationSettings.FIELDS:
            resolved = False
            for node in chain:
                settings = self._settings(node)
                if settings is not None:
                    field_value = getattr(settings, field, None)
                    if field_value is not None:
                        setattr(result, field, field_value)
                        resolved = True
                        break
            if resolved:
                continue
            if profile_name:
                profile = self.profile_service.get(profile_name)
                if profile and profile.get(field) is not None:
                    setattr(result, field, profile.get(field))
        return result

    def source_for_node(self, value, field, folders=None,
                        publication_sets=None, profile_name=None):
        if field not in PublicationSettings.FIELDS:
            raise ValueError("Réglage inconnu : " + str(field))
        for node in self.container_chain(
                value,
                folders=folders,
                publication_sets=publication_sets,
                include_self=True):
            settings = self._settings(node)
            if settings is not None and getattr(settings, field, None) is not None:
                return node
        if (
            profile_name
            and self.profile_service.get(profile_name)
            and self.profile_service.get(profile_name).get(field) is not None
        ):
            return "Profil"
        return "Défaut"

    def source_label_node(self, value, field, folders=None,
                          publication_sets=None):
        source = self.source_for_node(
            value,
            field,
            folders=folders,
            publication_sets=publication_sets,
        )
        if source in ("Profil", "Défaut"):
            return source
        return "Dossier « {0} »".format(
            getattr(source, "name", "Publication")
        )

    @staticmethod
    def folder_chain(folder, folders=None):
        """Retourne le parent immédiat puis ses ancêtres sans boucler sur un cycle."""
        by_id = dict((str(value.id), value) for value in (folders or []))
        chain, seen = [], set()
        while folder is not None:
            key = str(folder.id)
            if key in seen:
                raise ValueError("Cycle dans les dossiers de publication : " + folder.name)
            seen.add(key)
            chain.append(folder)
            parent_id = getattr(folder, "parent_id", None)
            folder = by_id.get(str(parent_id)) if parent_id is not None else None
        return chain

    def resolve(self, publication_set, folder=None, profile_name=None, folders=None):
        """Retourne des réglages concrets sans modifier les objets sources."""
        layers = []
        if profile_name:
            profile = self.profile_service.get(profile_name)
            if profile:
                layers.append(PublicationSettings.from_dict(profile))
        for ancestor in reversed(self.folder_chain(folder, folders)):
            layers.append(getattr(ancestor, "publication_settings", None))
        layers.append(getattr(publication_set, "publication_settings", None))

        result = PublicationSettings.defaults()
        for field in PublicationSettings.FIELDS:
            for settings in reversed(layers):
                if settings is not None and getattr(settings, field, None) is not None:
                    setattr(result, field, getattr(settings, field))
                    break
        return result

    def source_for(self, publication_set, field, folder=None, profile_name=None, folders=None):
        """Indique le niveau qui fournit actuellement une valeur."""
        if field not in PublicationSettings.FIELDS:
            raise ValueError("Réglage inconnu : " + str(field))
        if publication_set is not None:
            settings = getattr(publication_set, "publication_settings", None)
            if settings is not None and getattr(settings, field, None) is not None:
                return "Carnet"
        for ancestor in self.folder_chain(folder, folders):
            settings = getattr(ancestor, "publication_settings", None)
            if settings is not None and getattr(settings, field, None) is not None:
                return "Dossier"
        if profile_name and self.profile_service.get(profile_name) and \
                self.profile_service.get(profile_name).get(field) is not None:
            return "Profil"
        return "Défaut"

    def source_label(self, publication_set, field, folder=None, folders=None):
        """Nomme le dossier effectif pour distinguer héritage proche et lointain."""
        source = self.source_for(publication_set, field, folder=folder, folders=folders)
        if source == "Carnet":
            return "Dossier « {0} »".format(
                getattr(publication_set, "name", "Publication")
            )
        if source == "Dossier":
            for ancestor in self.folder_chain(folder, folders):
                settings = getattr(ancestor, "publication_settings", None)
                if settings is not None and getattr(settings, field, None) is not None:
                    return "Dossier « {0} »".format(ancestor.name)
        return source
