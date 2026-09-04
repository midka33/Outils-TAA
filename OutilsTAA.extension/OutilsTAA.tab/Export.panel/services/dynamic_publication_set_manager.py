# -*- coding: utf-8 -*-
"""Gestionnaire pur Python des carnets dynamiques."""

from models.dynamic_publication_set import DynamicPublicationSet, DynamicPublicationSetSerializer


class DynamicPublicationSetManager(object):
    """Gère le cycle de vie des carnets sans accès à Revit ni à l'interface."""

    def __init__(self, publication_sets=None):
        self._sets = {}
        for publication_set in publication_sets or []:
            self.add(publication_set)

    def list(self):
        return list(self._sets.values())

    def get(self, set_id):
        return self._sets.get(set_id)

    def add(self, publication_set):
        self._validate_object(publication_set)
        if not publication_set.id:
            raise ValueError("Un carnet doit avoir un identifiant.")
        if publication_set.id in self._sets:
            raise ValueError("Identifiant de carnet déjà utilisé : {0}".format(publication_set.id))
        self._sets[publication_set.id] = publication_set
        return publication_set

    def update(self, publication_set):
        self._validate_object(publication_set)
        if publication_set.id not in self._sets:
            raise KeyError("Carnet introuvable : {0}".format(publication_set.id))
        self._sets[publication_set.id] = publication_set
        return publication_set

    def delete(self, set_id):
        if set_id not in self._sets:
            return False
        del self._sets[set_id]
        return True

    def duplicate(self, set_id, new_set_id, new_name=None):
        source = self.get(set_id)
        if source is None:
            raise KeyError("Carnet introuvable : {0}".format(set_id))
        if new_set_id in self._sets:
            raise ValueError("Identifiant de carnet déjà utilisé : {0}".format(new_set_id))
        data = DynamicPublicationSetSerializer.serialize(source)
        data["id"] = new_set_id
        data["name"] = new_name or "{0} - Copie".format(source.name)
        copy = DynamicPublicationSetSerializer.deserialize(data)
        self._sets[new_set_id] = copy
        return copy

    def serialize_all(self):
        return [DynamicPublicationSetSerializer.serialize(item) for item in self.list()]

    def load_all(self, data):
        if not isinstance(data, list):
            raise TypeError("Les carnets doivent être fournis sous forme de liste.")
        loaded = [DynamicPublicationSetSerializer.deserialize(item) for item in data]
        manager = DynamicPublicationSetManager()
        for item in loaded:
            manager.add(item)
        self._sets = manager._sets
        return self.list()

    @staticmethod
    def _validate_object(publication_set):
        if not isinstance(publication_set, DynamicPublicationSet):
            raise TypeError("Le carnet doit être un DynamicPublicationSet.")
        errors = publication_set.validate()
        if errors:
            raise ValueError("Carnet invalide : {0}".format(", ".join(errors)))
