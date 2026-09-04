# -*- coding: utf-8 -*-
"""Persistance JSON des configurations de carnets dynamiques.

Le store ne persiste jamais les objets Revit ni les feuilles résolues.
Il conserve uniquement la configuration métier sérialisable du carnet.
"""

import json
import os

from models.dynamic_publication_set import DynamicPublicationSet
from models.dynamic_publication_set import DynamicPublicationSetSerializer


class DynamicPublicationSetStore(object):
    """Store déterministe, versionné et isolé par projet."""

    SCHEMA_VERSION = 1

    def __init__(self, path):
        if not path:
            raise ValueError("Le chemin de stockage est obligatoire.")
        self.path = path

    def list(self, project_key):
        data = self._read()
        entries = data.get("projects", {}).get(project_key, {})
        values = [DynamicPublicationSetSerializer.deserialize(value)
                  for value in entries.values()]
        return sorted(values, key=lambda item: (
            item.folder_id or "", item.name.lower(), item.id or ""))

    def get(self, project_key, set_id):
        if not project_key or not set_id:
            return None
        data = self._read()
        value = data.get("projects", {}).get(project_key, {}).get(set_id)
        if value is None:
            return None
        return DynamicPublicationSetSerializer.deserialize(value)

    def save(self, project_key, publication_set):
        if not project_key:
            raise ValueError("La clé projet est obligatoire.")
        if not isinstance(publication_set, DynamicPublicationSet):
            raise TypeError("Le carnet doit être un DynamicPublicationSet.")
        if not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant.")
        publication_set.persistent = True
        serialized = DynamicPublicationSetSerializer.serialize(publication_set)
        data = self._read()
        projects = data.setdefault("projects", {})
        project = projects.setdefault(project_key, {})
        project[publication_set.id] = serialized
        self._write(data)
        return publication_set

    def delete(self, project_key, set_id):
        if not project_key or not set_id:
            return False
        data = self._read()
        project = data.get("projects", {}).get(project_key)
        if not project or set_id not in project:
            return False
        del project[set_id]
        if not project:
            del data["projects"][project_key]
        self._write(data)
        return True

    def replace_project(self, project_key, publication_sets):
        """Remplace l'ensemble des carnets d'un projet en une seule écriture."""
        if not project_key:
            raise ValueError("La clé projet est obligatoire.")
        entries = {}
        for publication_set in publication_sets or []:
            if not isinstance(publication_set, DynamicPublicationSet):
                raise TypeError("Tous les carnets doivent être des DynamicPublicationSet.")
            if not publication_set.id:
                raise ValueError("Tous les carnets doivent posséder un identifiant.")
            publication_set.persistent = True
            if publication_set.id in entries:
                raise ValueError("Identifiant de carnet dupliqué : {0}".format(publication_set.id))
            entries[publication_set.id] = DynamicPublicationSetSerializer.serialize(publication_set)
        data = self._read()
        projects = data.setdefault("projects", {})
        if entries:
            projects[project_key] = entries
        elif project_key in projects:
            del projects[project_key]
        self._write(data)

    def _read(self):
        if not os.path.isfile(self.path):
            return {"schema_version": self.SCHEMA_VERSION, "projects": {}}
        try:
            with open(self.path, "r") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError):
            return {"schema_version": self.SCHEMA_VERSION, "projects": {}}
        if not isinstance(data, dict):
            return {"schema_version": self.SCHEMA_VERSION, "projects": {}}
        version = data.get("schema_version", 0)
        if version > self.SCHEMA_VERSION:
            raise ValueError("Schéma de carnets dynamiques non supporté : {0}".format(version))
        data.setdefault("projects", {})
        if not isinstance(data["projects"], dict):
            data["projects"] = {}
        data["schema_version"] = self.SCHEMA_VERSION
        return data

    def _write(self, data):
        directory = os.path.dirname(self.path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        temporary = self.path + ".tmp"
        with open(temporary, "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        if os.path.isfile(self.path):
            os.remove(self.path)
        os.rename(temporary, self.path)
