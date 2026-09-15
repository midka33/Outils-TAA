# -*- coding: utf-8 -*-
"""Persistance JSON des configurations de carnets dynamiques."""
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
        values = [DynamicPublicationSetSerializer.deserialize(v) for v in entries.values()]
        return sorted(values, key=lambda item: (item.folder_id or "", item.name.lower(), item.id or ""))
    def get(self, project_key, set_id):
        if not project_key or not set_id:
            return None
        value = self._read().get("projects", {}).get(project_key, {}).get(set_id)
        return None if value is None else DynamicPublicationSetSerializer.deserialize(value)
    def save(self, project_key, publication_set):
        if not project_key:
            raise ValueError("La clé projet est obligatoire.")
        if not isinstance(publication_set, DynamicPublicationSet):
            raise TypeError("Le carnet doit être un DynamicPublicationSet.")
        if not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant.")
        publication_set.persistent = True
        data = self._read()
        data.setdefault("projects", {}).setdefault(project_key, {})[publication_set.id] = DynamicPublicationSetSerializer.serialize(publication_set)
        self._write(data)
        return publication_set
    def delete(self, project_key, set_id):
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
        if not project_key:
            raise ValueError("La clé projet est obligatoire.")
        entries = {}
        for publication_set in publication_sets or []:
            if not isinstance(publication_set, DynamicPublicationSet) or not publication_set.id:
                raise ValueError("Chaque carnet doit être valide et posséder un identifiant.")
            if publication_set.id in entries:
                raise ValueError("Identifiant de carnet dupliqué : {0}".format(publication_set.id))
            publication_set.persistent = True
            entries[publication_set.id] = DynamicPublicationSetSerializer.serialize(publication_set)
        data = self._read()
        projects = data.setdefault("projects", {})
        if entries:
            projects[project_key] = entries
        elif project_key in projects:
            del projects[project_key]
        self._write(data)
    def _read(self):
        empty = {"schema_version": self.SCHEMA_VERSION, "projects": {}}
        if not os.path.isfile(self.path):
            return empty
        try:
            with open(self.path, "r") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError):
            return empty
        if not isinstance(data, dict):
            return empty
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
