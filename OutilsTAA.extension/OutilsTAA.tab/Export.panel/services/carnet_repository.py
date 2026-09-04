# -*- coding: utf-8 -*-
"""Persistance locale des carnets et dossiers Export."""

import json
import os

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource
from publication_folder import PublicationFolder
from publication_settings import PublicationSettings


class CarnetRepository(object):
    """Enregistre l'arborescence Export dans un fichier JSON."""

    SCHEMA_VERSION = 4
    DEFAULT_FOLDER_ID = "default"
    DEFAULT_FOLDER_NAME = "Général"

    def __init__(self, storage_path):
        if not storage_path:
            raise ValueError("Le chemin de stockage est obligatoire.")
        self.storage_path = storage_path

    def _ensure_structure(self, data):
        if "folders" not in data:
            data["folders"] = [{"id": self.DEFAULT_FOLDER_ID,
                                "name": self.DEFAULT_FOLDER_NAME,
                                "parent_id": None, "persistent": True}]
            for index, value in enumerate(data.get("sets", [])):
                value.setdefault("folder_id", self.DEFAULT_FOLDER_ID)
                value.setdefault("sort_order", index)
        elif not data["folders"]:
            data["folders"].append({"id": self.DEFAULT_FOLDER_ID,
                                    "name": self.DEFAULT_FOLDER_NAME,
                                    "parent_id": None, "persistent": True})
        for index, value in enumerate(data.get("sets", [])):
            value.setdefault("folder_id", self.DEFAULT_FOLDER_ID)
            value.setdefault("sort_order", index)
        data["schema_version"] = self.SCHEMA_VERSION
        return data

    def list_all(self):
        values = self._read().get("sets", [])
        values = sorted(values, key=lambda v: (v.get("folder_id", self.DEFAULT_FOLDER_ID),
                                               v.get("sort_order", 0)))
        return [self._from_dict(value) for value in values]

    def list_folders(self):
        return [self._folder_from_dict(value) for value in self._read().get("folders", [])]

    def get(self, set_id):
        if not set_id:
            return None
        for publication_set in self.list_all():
            if publication_set.id == set_id:
                return publication_set
        return None

    def save(self, publication_set):
        if publication_set is None or not publication_set.id:
            raise ValueError("Le carnet doit posséder un identifiant.")
        publication_set.persistent = True
        if publication_set.source is None:
            publication_set.source = PublicationSource(PublicationSource.MANUAL)
        if not publication_set.folder_id:
            publication_set.folder_id = self.DEFAULT_FOLDER_ID
        if publication_set.publication_settings is None:
            publication_set.publication_settings = PublicationSettings(output_directory=publication_set.output_directory)
        data = self._ensure_structure(self._read())
        sets = data.get("sets", [])
        existing_index = None
        for index, value in enumerate(sets):
            if value.get("id") == publication_set.id:
                existing_index = index
                break
        if getattr(publication_set, "sort_order", None) is None:
            siblings = [v.get("sort_order", 0) for v in sets
                        if v.get("folder_id", self.DEFAULT_FOLDER_ID) == publication_set.folder_id
                        and v.get("id") != publication_set.id]
            publication_set.sort_order = (max(siblings) + 1) if siblings else 0
        serialized = self._to_dict(publication_set)
        if existing_index is not None:
            sets[existing_index] = serialized
        else:
            sets.append(serialized)
        data["sets"] = sets
        self._write(data)
        return publication_set

    def move_set(self, set_id, folder_id, before_set_id=None):
        """Déplace un carnet vers un dossier et/ou change sa position."""
        data = self._ensure_structure(self._read())
        sets = data.get("sets", [])
        moving = None
        for value in sets:
            if value.get("id") == set_id:
                moving = value
                break
        if moving is None:
            return False
        if not any(folder.get("id") == folder_id for folder in data.get("folders", [])):
            return False
        moving["folder_id"] = folder_id
        same = [value for value in sets if value.get("id") != set_id and
                value.get("folder_id", self.DEFAULT_FOLDER_ID) == folder_id]
        if before_set_id:
            insert_at = len(same)
            for index, value in enumerate(same):
                if value.get("id") == before_set_id:
                    insert_at = index
                    break
            same.insert(insert_at, moving)
        else:
            same.append(moving)
        order = 0
        for value in same:
            value["sort_order"] = order
            order += 1
        # Réindexer les autres dossiers sans changer leur ordre.
        for folder in data.get("folders", []):
            if folder.get("id") == folder_id:
                continue
            siblings = [value for value in sets if value.get("folder_id", self.DEFAULT_FOLDER_ID) == folder.get("id")]
            siblings.sort(key=lambda value: value.get("sort_order", 0))
            for index, value in enumerate(siblings):
                value["sort_order"] = index
        self._write(data)
        return True

    def save_folder(self, folder):
        if folder is None or not folder.id:
            raise ValueError("Le dossier doit posséder un identifiant.")
        folder.persistent = True
        data = self._ensure_structure(self._read())
        serialized = self._folder_to_dict(folder)
        folders = data.get("folders", [])
        for index, value in enumerate(folders):
            if value.get("id") == folder.id:
                folders[index] = serialized
                break
        else:
            folders.append(serialized)
        data["folders"] = folders
        self._write(data)
        return folder

    def delete(self, set_id):
        data = self._ensure_structure(self._read())
        sets = data.get("sets", [])
        filtered = [value for value in sets if value.get("id") != set_id]
        if len(filtered) == len(sets):
            return False
        data["sets"] = filtered
        self._ensure_structure(data)
        self._write(data)
        return True

    def delete_folder(self, folder_id):
        if folder_id == self.DEFAULT_FOLDER_ID:
            return False
        data = self._ensure_structure(self._read())
        folders = data.get("folders", [])
        if any(value.get("parent_id") == folder_id for value in folders):
            return False
        if any(value.get("folder_id") == folder_id for value in data.get("sets", [])):
            return False
        filtered = [value for value in folders if value.get("id") != folder_id]
        if len(filtered) == len(folders):
            return False
        data["folders"] = filtered
        self._write(data)
        return True

    def _read(self):
        if not os.path.exists(self.storage_path):
            return {"schema_version": self.SCHEMA_VERSION,
                    "folders": [{"id": self.DEFAULT_FOLDER_ID,
                                  "name": self.DEFAULT_FOLDER_NAME,
                                  "parent_id": None, "persistent": True}],
                    "sets": []}
        with open(self.storage_path, "r") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("Le fichier de carnets est invalide.")
        data.setdefault("sets", [])
        return self._ensure_structure(data)

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
    def _folder_to_dict(folder):
        return {"id": folder.id, "name": folder.name,
                "parent_id": folder.parent_id, "persistent": True,
                "publication_settings": (folder.publication_settings.to_dict() if folder.publication_settings else None)}

    @staticmethod
    def _to_dict(publication_set):
        settings = publication_set.publication_settings
        return {
            "id": publication_set.id, "name": publication_set.name,
            "persistent": True, "folder_id": publication_set.folder_id,
            "sort_order": getattr(publication_set, "sort_order", 0),
            "output_directory": publication_set.output_directory,
            "filename_template_id": publication_set.filename_template_id,
            "publication_settings": settings.to_dict() if settings else None,
            "source": {"mode": publication_set.source.mode,
                       "parameter_name": publication_set.source.parameter_name,
                       "parameter_value": publication_set.source.parameter_value},
            "items": [{"unique_id": item.unique_id, "sheet_id": item.sheet_id,
                       "item_type": item.item_type, "sheet_number": item.sheet_number,
                       "sheet_name": item.sheet_name, "parameter_value": item.parameter_value}
                      for item in publication_set.items]
        }

    @staticmethod
    def _from_dict(value):
        source_data = value.get("source") or {}
        source = PublicationSource(source_data.get("mode", PublicationSource.MANUAL),
                                   source_data.get("parameter_name"), source_data.get("parameter_value"))
        items = [PublicationItem(item_data.get("unique_id"), item_data.get("sheet_id"),
                                 item_data.get("item_type", "SHEET"), item_data.get("sheet_number"),
                                 item_data.get("sheet_name"), item_data.get("parameter_value"))
                 for item_data in value.get("items", [])]
        settings = PublicationSettings.from_dict(value.get("publication_settings"))
        if value.get("publication_settings") is None:
            settings.output_directory = value.get("output_directory")
        publication_set = PublicationSet(name=value.get("name", ""), items=items, source=source,
                                         output_directory=value.get("output_directory"),
                                         filename_template_id=value.get("filename_template_id"),
                                         set_id=value.get("id"), persistent=True,
                                         folder_id=value.get("folder_id", CarnetRepository.DEFAULT_FOLDER_ID),
                                         publication_settings=settings)
        publication_set.sort_order = value.get("sort_order", 0)
        return publication_set

    @staticmethod
    def _folder_from_dict(value):
        return PublicationFolder(value.get("name", ""), value.get("id"), value.get("parent_id"), True,
                                 PublicationSettings.from_dict(value.get("publication_settings")))
