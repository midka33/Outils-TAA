# -*- coding: utf-8 -*-
"""Persistance hors Revit des snapshots de résolution dynamique.

Ce module ne dépend ni de Revit, ni de WPF, ni du moteur PDF/DWG.
"""

import json
import os


class DynamicResolutionSnapshot(object):
    """État minimal d'une résolution dynamique à un instant donné."""

    VERSION = 1

    def __init__(self, project_key, carnet_key, definition_name,
                 included_keys=None, excluded_keys=None):
        self.project_key = project_key
        self.carnet_key = carnet_key
        self.definition_name = definition_name or ""
        self.included_keys = sorted(set(included_keys or []))
        self.excluded_keys = sorted(set(excluded_keys or []))

    def to_dict(self):
        return {
            "schema_version": self.VERSION,
            "project_key": self.project_key,
            "carnet_key": self.carnet_key,
            "definition_name": self.definition_name,
            "included_keys": self.included_keys,
            "excluded_keys": self.excluded_keys,
        }

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict):
            raise ValueError("Snapshot invalide : objet attendu.")
        if data.get("schema_version") != cls.VERSION:
            raise ValueError("Version de snapshot dynamique non supportée.")
        project_key = data.get("project_key")
        carnet_key = data.get("carnet_key")
        if not project_key or not carnet_key:
            raise ValueError("Snapshot invalide : identité projet/carnet manquante.")
        return cls(
            project_key,
            carnet_key,
            data.get("definition_name", ""),
            data.get("included_keys", []),
            data.get("excluded_keys", []),
        )

    @classmethod
    def from_resolution(cls, project_key, carnet_key, definition_name,
                        resolution):
        return cls(
            project_key,
            carnet_key,
            definition_name,
            resolution.included_keys,
            resolution.excluded_keys,
        )


class DynamicResolutionSnapshotStore(object):
    """Store JSON simple et déterministe, indexé par projet et carnet."""

    def __init__(self, path):
        self.path = path

    def load(self, project_key, carnet_key):
        data = self._read()
        key = self._entry_key(project_key, carnet_key)
        entry = data.get("snapshots", {}).get(key)
        if entry is None:
            return None
        return DynamicResolutionSnapshot.from_dict(entry)

    def save(self, snapshot):
        if not isinstance(snapshot, DynamicResolutionSnapshot):
            raise TypeError("Le snapshot doit être un DynamicResolutionSnapshot.")
        data = self._read()
        snapshots = data.setdefault("snapshots", {})
        snapshots[self._entry_key(snapshot.project_key, snapshot.carnet_key)] = snapshot.to_dict()
        self._write(data)

    def delete(self, project_key, carnet_key):
        data = self._read()
        snapshots = data.setdefault("snapshots", {})
        key = self._entry_key(project_key, carnet_key)
        if key in snapshots:
            del snapshots[key]
            self._write(data)

    def _entry_key(self, project_key, carnet_key):
        return "%s::%s" % (project_key, carnet_key)

    def _read(self):
        if not self.path or not os.path.isfile(self.path):
            return {"schema_version": 1, "snapshots": {}}
        try:
            with open(self.path, "r") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError):
            return {"schema_version": 1, "snapshots": {}}
        if not isinstance(data, dict):
            return {"schema_version": 1, "snapshots": {}}
        snapshots = data.get("snapshots")
        if not isinstance(snapshots, dict):
            data["snapshots"] = {}
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
