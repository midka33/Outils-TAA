# -*- coding: utf-8 -*-
"""Cycle de vie métier des carnets dynamiques.

Cette couche orchestre validation, persistance et duplication sans dépendre
ni de Revit ni de WPF.
"""

from models.dynamic_publication_set import DynamicPublicationSet
from models.dynamic_publication_set import DynamicPublicationSetSerializer


class DynamicPublicationSetLifecycle(object):
    """Gère création, chargement, mise à jour, duplication et suppression."""

    def __init__(self, store):
        if store is None:
            raise ValueError("Le store est obligatoire.")
        self.store = store

    def list(self, project_key):
        return self.store.list(project_key)

    def get(self, project_key, set_id):
        return self.store.get(project_key, set_id)

    def create(self, project_key, publication_set):
        self._validate(publication_set)
        if not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant avant sa création.")
        if self.store.get(project_key, publication_set.id) is not None:
            raise ValueError("Un carnet existe déjà avec l'identifiant : {0}".format(publication_set.id))
        return self.store.save(project_key, publication_set)

    def update(self, project_key, publication_set):
        self._validate(publication_set)
        if not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant avant sa mise à jour.")
        if self.store.get(project_key, publication_set.id) is None:
            raise ValueError("Carnet introuvable : {0}".format(publication_set.id))
        return self.store.save(project_key, publication_set)

    def duplicate(self, project_key, set_id, new_id, new_name=None):
        source = self.store.get(project_key, set_id)
        if source is None:
            raise ValueError("Carnet source introuvable : {0}".format(set_id))
        if not new_id:
            raise ValueError("Le nouvel identifiant est obligatoire.")
        if self.store.get(project_key, new_id) is not None:
            raise ValueError("Un carnet existe déjà avec l'identifiant : {0}".format(new_id))

        # Le passage par la sérialisation garantit une copie indépendante de
        # toute la configuration imbriquée (règles, exclusions, paramètres).
        copied = DynamicPublicationSetSerializer.deserialize(
            DynamicPublicationSetSerializer.serialize(source)
        )
        copied.id = new_id
        if new_name:
            copied.name = new_name
        return self.store.save(project_key, copied)

    def delete(self, project_key, set_id):
        return self.store.delete(project_key, set_id)

    @staticmethod
    def _validate(publication_set):
        if not isinstance(publication_set, DynamicPublicationSet):
            raise TypeError("Le carnet doit être un DynamicPublicationSet.")
        errors = publication_set.validate()
        if errors:
            raise ValueError("Carnet invalide : {0}".format(", ".join(errors)))
