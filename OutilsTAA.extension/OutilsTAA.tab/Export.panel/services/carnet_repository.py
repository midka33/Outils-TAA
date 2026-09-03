# -*- coding: utf-8 -*-
"""Persistance locale des carnets Export."""

import json
import os

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource


class CarnetRepository(object):
    """Enregistre les carnets persistants dans un fichier JSON."""

    SCHEMA_VERSION = 1

    def __init__(self, storage_path):
        if not storage_path:
            raise ValueError("Le chemin de stockage est obligatoire.")
        self.storage_path = storage_path

    def list_all(self):
        """Retourne tous les carnets persistants enregistrés."""
        data = self._read()
        return [self._from_dict(value) for value in data.get("sets", [])]

    def get(self, set_id):
        """Retourne un carnet par son identifiant stable."""
        if not set_id:
            return None
        for publication_set in self.list_all():
            if publication_set.id == set_id:
                return publication_set
        return None

    def save(self, publication_set):
        """Crée ou met à jour un carnet persistant."""
        if publication_set is None:
            raise ValueError("Le carnet est manquant.")
        if not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant.")

        publication_set.persistent = True
        # Conserver la source réelle du carnet (PARAMETER ou MANUAL).
        # Ne pas transformer un carnet issu d'un paramètre en carnet manuel.
        if publication_set.source is None:
            publication_set.source = PublicationSource(PublicationSource.MANUAL)

        data = self._read()
        serialized = self._to_dict(publication_set)
        sets = data.get("sets", [])

        replaced = False
        for index, value in enumerate(sets):
            if value.get("id") == publication_set.id:
                sets[index] = serialized
                replaced = True
                break

        if not replaced:
            sets.append(serialized)

        data["schema_version"] = self.SCHEMA_VERSION
        data["sets"] = sets
        self._write(data)
        return publication_set

    def delete(self, set_id):
        """Supprime un carnet persistant. Retourne True s'il existait."""
        data = self._read()
        sets = data.get("sets", [])
        filtered = [value for value in sets if value.get("id") != set_id]

        if len(filtered) == len(sets):
            return False

        data["sets"] = filtered
        self._write(data)
        return True

    def _read(self):
        if not os.path.exists(self.storage_path):
            return {"schema_version": self.SCHEMA_VERSION, "sets": []}

        with open(self.storage_path, "r") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("Le fichier de carnets est invalide.")

        data.setdefault("schema_version", self.SCHEMA_VERSION)
        data.setdefault("sets", [])
        return data

    def _write(self, data):
        directory = os.path.dirname(self.storage_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        temporary_path = self.storage_path + ".tmp"
        with open(temporary_path, "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)

        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
        os.rename(temporary_path, self.storage_path)

    @staticmethod
    def _to_dict(publication_set):
        return {
            "id": publication_set.id,
            "name": publication_set.name,
            "persistent": True,
            "output_directory": publication_set.output_directory,
            "filename_template_id": publication_set.filename_template_id,
            "source": {
                "mode": publication_set.source.mode,
                "parameter_name": publication_set.source.parameter_name,
                "parameter_value": publication_set.source.parameter_value
            },
            "items": [
                {
                    "unique_id": item.unique_id,
                    "sheet_id": item.sheet_id,
                    "item_type": item.item_type,
                    "sheet_number": item.sheet_number,
                    "sheet_name": item.sheet_name,
                    "parameter_value": item.parameter_value
                }
                for item in publication_set.items
            ]
        }

    @staticmethod
    def _from_dict(value):
        source_data = value.get("source") or {}
        source = PublicationSource(
            source_data.get("mode", PublicationSource.MANUAL),
            source_data.get("parameter_name"),
            source_data.get("parameter_value")
        )

        items = []
        for item_data in value.get("items", []):
            items.append(
                PublicationItem(
                    item_data.get("unique_id"),
                    item_data.get("sheet_id"),
                    item_data.get("item_type", "SHEET"),
                    item_data.get("sheet_number"),
                    item_data.get("sheet_name"),
                    item_data.get("parameter_value")
                )
            )

        return PublicationSet(
            name=value.get("name", ""),
            items=items,
            source=source,
            output_directory=value.get("output_directory"),
            filename_template_id=value.get("filename_template_id"),
            set_id=value.get("id"),
            persistent=True
        )
