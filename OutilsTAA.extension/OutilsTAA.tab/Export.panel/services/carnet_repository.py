# -*- coding: utf-8 -*-
"""Persistance locale de l'arborescence Export.

Le stockage historique conserve deux types internes :
- PublicationFolder : dossier d'organisation ;
- PublicationSet : dossier de publication contenant des mises en page.

L'interface présente désormais les deux comme des dossiers. Le champ tree_order
fournit un ordre commun entre les deux types pour retrouver un comportement proche
de l'Explorateur Windows sans casser les anciens JSON.
"""

import json
import os

from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource
from publication_folder import PublicationFolder
from publication_settings import PublicationSettings


class CarnetRepository(object):
    """Enregistre l'arborescence Export dans un fichier JSON isolé par projet."""

    SCHEMA_VERSION = 8
    DEFAULT_FOLDER_ID = "default"
    DEFAULT_FOLDER_NAME = "Général"

    def __init__(self, storage_path, project_identity=None):
        if not storage_path:
            raise ValueError("Le chemin de stockage est obligatoire.")
        self.storage_path = storage_path
        self.project_identity = project_identity

    def _empty_data(self):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "project_identity": self.project_identity,
            "folders": [{
                "id": self.DEFAULT_FOLDER_ID,
                "name": self.DEFAULT_FOLDER_NAME,
                "parent_id": None,
                "persistent": True,
                "sort_order": 0,
                "tree_order": 0,
            }],
            "sets": [],
        }

    @staticmethod
    def _same_parent(left, right):
        return str(left) == str(right)

    def _children(self, data, parent_id, excluded=None):
        excluded = set(excluded or [])
        result = []

        for value in data.get("folders", []):
            key = ("FOLDER", str(value.get("id")))
            if key in excluded:
                continue
            if self._same_parent(value.get("parent_id"), parent_id):
                result.append(("FOLDER", value))

        for value in data.get("sets", []):
            key = ("CARNET", str(value.get("id")))
            if key in excluded:
                continue
            if self._same_parent(
                    value.get("folder_id", self.DEFAULT_FOLDER_ID),
                    parent_id):
                result.append(("CARNET", value))

        return result

    @staticmethod
    def _legacy_sort_key(entry):
        kind, value = entry
        return (
            0 if kind == "FOLDER" else 1,
            value.get("sort_order", 0),
            str(value.get("name", "")),
        )

    @staticmethod
    def _tree_sort_key(entry):
        kind, value = entry
        order = value.get("tree_order")
        if order is None:
            order = 10 ** 9
        return (
            order,
            0 if kind == "FOLDER" else 1,
            value.get("sort_order", 0),
            str(value.get("name", "")),
        )

    def _assign_orders(self, entries):
        """Normalise ordre commun et ordres historiques par type."""
        ordered = list(entries or [])
        ordered.sort(key=self._tree_sort_key)

        folder_index = 0
        set_index = 0
        for index, entry in enumerate(ordered):
            kind, value = entry
            value["tree_order"] = index
            if kind == "FOLDER":
                value["sort_order"] = folder_index
                folder_index += 1
            else:
                value["sort_order"] = set_index
                set_index += 1
        return ordered

    def _normalize_tree_order(self, data):
        """Migre sans perte l'ancien ordre dossiers puis carnets vers schema 7."""
        folders = data.get("folders", [])
        sets = data.get("sets", [])

        parent_ids = set([None])
        for folder in folders:
            parent_ids.add(folder.get("id"))
            parent_ids.add(folder.get("parent_id"))
        for value in sets:
            # Un dossier de publication peut désormais être parent lui-même.
            parent_ids.add(value.get("id"))
            parent_ids.add(
                value.get("folder_id", self.DEFAULT_FOLDER_ID)
            )

        for parent_id in parent_ids:
            entries = self._children(data, parent_id)
            if not entries:
                continue

            if not any(
                    entry[1].get("tree_order") is not None
                    for entry in entries):
                # Migration : reproduire exactement l'affichage historique,
                # c.-à-d. sous-dossiers d'abord puis dossiers de publication.
                entries.sort(key=self._legacy_sort_key)
                for index, entry in enumerate(entries):
                    entry[1]["tree_order"] = index

            self._assign_orders(entries)

        return data

    def _ensure_structure(self, data):
        if (
            self.project_identity
            and data.get("project_identity") != self.project_identity
        ):
            raise ValueError(
                "Le stockage Export ne correspond pas au projet Revit courant."
            )

        if "folders" not in data:
            data["folders"] = []
        if "sets" not in data:
            data["sets"] = []

        if not data["folders"]:
            data["folders"].append({
                "id": self.DEFAULT_FOLDER_ID,
                "name": self.DEFAULT_FOLDER_NAME,
                "parent_id": None,
                "persistent": True,
                "sort_order": 0,
                "tree_order": 0,
            })

        if not any(
                str(value.get("id")) == self.DEFAULT_FOLDER_ID
                for value in data["folders"]):
            data["folders"].insert(0, {
                "id": self.DEFAULT_FOLDER_ID,
                "name": self.DEFAULT_FOLDER_NAME,
                "parent_id": None,
                "persistent": True,
                "sort_order": 0,
                "tree_order": 0,
            })

        for index, value in enumerate(data.get("folders", [])):
            value.setdefault("sort_order", index)
            value.setdefault("tree_order", None)

        for index, value in enumerate(data.get("sets", [])):
            value.setdefault("folder_id", self.DEFAULT_FOLDER_ID)
            value.setdefault("sort_order", index)
            value.setdefault("tree_order", None)

        self._normalize_tree_order(data)
        data["schema_version"] = self.SCHEMA_VERSION
        return data

    def list_all(self):
        values = self._read().get("sets", [])
        values = sorted(
            values,
            key=lambda value: (
                str(value.get("folder_id", self.DEFAULT_FOLDER_ID)),
                value.get("tree_order", value.get("sort_order", 0)),
            ),
        )
        return [self._from_dict(value) for value in values]

    def list_folders(self):
        values = self._read().get("folders", [])
        values = sorted(
            values,
            key=lambda value: (
                str(value.get("parent_id") or ""),
                value.get("tree_order", value.get("sort_order", 0)),
            ),
        )
        return [self._folder_from_dict(value) for value in values]

    def get(self, set_id):
        if not set_id:
            return None
        for publication_set in self.list_all():
            if publication_set.id == set_id:
                return publication_set
        return None

    def _append_tree_order(self, data, parent_id):
        entries = self._children(data, parent_id)
        if not entries:
            return 0
        return max(
            entry[1].get("tree_order", 0)
            for entry in entries
        ) + 1

    def save(self, publication_set):
        if publication_set is None or not publication_set.id:
            raise ValueError(
                "Le dossier de publication doit posséder un identifiant."
            )

        publication_set.persistent = True
        if publication_set.source is None:
            publication_set.source = PublicationSource(
                PublicationSource.MANUAL
            )
        if not publication_set.folder_id:
            publication_set.folder_id = self.DEFAULT_FOLDER_ID
        if publication_set.publication_settings is None:
            publication_set.publication_settings = PublicationSettings(
                output_directory=publication_set.output_directory
            )

        data = self._ensure_structure(self._read())
        sets = data.get("sets", [])
        existing_index = None
        existing = None

        for index, value in enumerate(sets):
            if str(value.get("id")) == str(publication_set.id):
                existing_index = index
                existing = value
                break

        if getattr(publication_set, "tree_order", None) is None:
            if existing is not None:
                publication_set.tree_order = existing.get("tree_order")
            else:
                publication_set.tree_order = self._append_tree_order(
                    data,
                    publication_set.folder_id,
                )

        if getattr(publication_set, "sort_order", None) is None:
            publication_set.sort_order = 0

        serialized = self._to_dict(publication_set)
        if existing_index is not None:
            sets[existing_index] = serialized
        else:
            sets.append(serialized)

        data["sets"] = sets
        self._normalize_tree_order(data)
        self._write(data)
        return publication_set

    def save_folder(self, folder):
        if folder is None or not folder.id:
            raise ValueError("Le dossier doit posséder un identifiant.")

        folder.persistent = True
        data = self._ensure_structure(self._read())
        folders = data.get("folders", [])
        existing_index = None
        existing = None

        for index, value in enumerate(folders):
            if str(value.get("id")) == str(folder.id):
                existing_index = index
                existing = value
                break

        if getattr(folder, "tree_order", None) is None:
            if existing is not None:
                folder.tree_order = existing.get("tree_order")
            else:
                folder.tree_order = self._append_tree_order(
                    data,
                    folder.parent_id,
                )

        serialized = self._folder_to_dict(folder)
        if existing_index is not None:
            folders[existing_index] = serialized
        else:
            folders.append(serialized)

        data["folders"] = folders
        self._normalize_tree_order(data)
        self._write(data)
        return folder

    def _record(self, data, kind, item_id):
        item_id = str(item_id)
        values = (
            data.get("folders", [])
            if kind == "FOLDER"
            else data.get("sets", [])
        )
        for value in values:
            if str(value.get("id")) == item_id:
                return value
        return None

    def move_tree_nodes(self, nodes, parent_id, before_node=None):
        """Déplace/reclasse des dossiers de types internes différents.

        nodes : liste de tuples ("FOLDER"|"CARNET", id)
        parent_id : identifiant de n'importe quel dossier visuel destination
        before_node : tuple (kind, id) ou None pour ajouter en fin

        Depuis le schéma 8, PublicationFolder et PublicationSet peuvent tous
        deux servir de parent. L'ID parent reste stocké dans parent_id/folder_id
        pour compatibilité avec les anciens JSON.
        """
        nodes = list(nodes or [])
        if not nodes:
            return False

        data = self._ensure_structure(self._read())
        folders = data.get("folders", [])
        sets = data.get("sets", [])
        container_map = {}
        container_kind = {}
        for value in folders:
            key = str(value.get("id"))
            container_map[key] = value
            container_kind[key] = "FOLDER"
        for value in sets:
            key = str(value.get("id"))
            container_map[key] = value
            container_kind[key] = "CARNET"

        if (
            parent_id is not None
            and str(parent_id) not in container_map
        ):
            return False

        normalized = []
        seen = set()
        for kind, item_id in nodes:
            kind = str(kind)
            item_id = str(item_id)
            if kind not in ("FOLDER", "CARNET"):
                return False
            key = (kind, item_id)
            if key in seen:
                continue
            seen.add(key)
            value = self._record(data, kind, item_id)
            if value is None:
                return False
            if (
                kind == "FOLDER"
                and item_id == self.DEFAULT_FOLDER_ID
            ):
                return False
            normalized.append((kind, value))

        if not normalized:
            return False

        moving_keys = set(
            (kind, str(value.get("id")))
            for kind, value in normalized
        )

        if before_node is not None:
            before_key = (str(before_node[0]), str(before_node[1]))
            if before_key in moving_keys:
                return False
        else:
            before_key = None

        if any(kind == "CARNET" for kind, value in normalized):
            if parent_id is None:
                return False

        # Interdire qu'un dossier visuel (quel que soit son type interne)
        # devienne son propre descendant.
        for kind, value in normalized:
            source_id = str(value.get("id"))
            current = str(parent_id) if parent_id is not None else None
            visited = set()
            while current is not None and current not in visited:
                if current == source_id:
                    return False
                visited.add(current)
                parent = container_map.get(current)
                if parent is None:
                    current = None
                    continue
                parent_kind = container_kind.get(current)
                parent_id_value = (
                    parent.get("parent_id")
                    if parent_kind == "FOLDER"
                    else parent.get("folder_id", self.DEFAULT_FOLDER_ID)
                )
                current = (
                    str(parent_id_value)
                    if parent_id_value is not None
                    else None
                )

        source_parents = set()
        for kind, value in normalized:
            if kind == "FOLDER":
                source_parents.add(value.get("parent_id"))
                value["parent_id"] = parent_id
            else:
                source_parents.add(
                    value.get("folder_id", self.DEFAULT_FOLDER_ID)
                )
                value["folder_id"] = parent_id

        destination = self._children(
            data,
            parent_id,
            excluded=moving_keys,
        )
        destination.sort(key=self._tree_sort_key)

        insert_at = len(destination)
        if before_key is not None:
            for index, entry in enumerate(destination):
                key = (entry[0], str(entry[1].get("id")))
                if key == before_key:
                    insert_at = index
                    break
            else:
                return False

        destination[insert_at:insert_at] = normalized

        # Destination : ordre mixte explicite.
        for index, entry in enumerate(destination):
            entry[1]["tree_order"] = index
        self._assign_orders(destination)

        # Sources quittées : refermer les trous.
        source_parents.add(parent_id)
        for source_parent in source_parents:
            if self._same_parent(source_parent, parent_id):
                continue
            self._assign_orders(
                self._children(data, source_parent)
            )

        self._write(data)
        return True

    def move_set(self, set_id, folder_id, before_set_id=None):
        return self.move_sets([set_id], folder_id, before_set_id)

    def move_sets(self, set_ids, folder_id, before_set_id=None):
        set_ids = list(set_ids or [])
        if not set_ids or not folder_id:
            return False
        before = (
            ("CARNET", before_set_id)
            if before_set_id else None
        )
        return self.move_tree_nodes(
            [("CARNET", value) for value in set_ids],
            folder_id,
            before,
        )

    def move_folders(self, folder_ids, parent_id=None, before_folder_id=None):
        folder_ids = list(folder_ids or [])
        if not folder_ids:
            return False
        before = (
            ("FOLDER", before_folder_id)
            if before_folder_id else None
        )
        return self.move_tree_nodes(
            [("FOLDER", value) for value in folder_ids],
            parent_id,
            before,
        )

    def delete(self, set_id):
        data = self._ensure_structure(self._read())
        set_id = str(set_id)

        # Un dossier contenant des sous-dossiers ne peut pas être supprimé
        # directement, même s'il est historiquement stocké comme PublicationSet.
        if any(
                str(value.get("parent_id")) == set_id
                for value in data.get("folders", [])):
            return False
        if any(
                str(value.get("folder_id")) == set_id
                for value in data.get("sets", [])
                if str(value.get("id")) != set_id):
            return False

        sets = data.get("sets", [])
        filtered = [
            value for value in sets
            if str(value.get("id")) != set_id
        ]
        if len(filtered) == len(sets):
            return False
        data["sets"] = filtered
        self._normalize_tree_order(data)
        self._write(data)
        return True

    def delete_folder(self, folder_id):
        if str(folder_id) == self.DEFAULT_FOLDER_ID:
            return False

        data = self._ensure_structure(self._read())
        folders = data.get("folders", [])

        if any(
                str(value.get("parent_id")) == str(folder_id)
                for value in folders):
            return False

        if any(
                str(value.get("folder_id")) == str(folder_id)
                for value in data.get("sets", [])):
            return False

        filtered = [
            value for value in folders
            if str(value.get("id")) != str(folder_id)
        ]
        if len(filtered) == len(folders):
            return False

        data["folders"] = filtered
        self._normalize_tree_order(data)
        self._write(data)
        return True

    def _read(self):
        if not os.path.exists(self.storage_path):
            return self._empty_data()

        with open(self.storage_path, "r") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError(
                "Le fichier d'arborescence Export est invalide."
            )

        data.setdefault("sets", [])
        if (
            self.project_identity
            and data.get("project_identity") != self.project_identity
        ):
            return self._empty_data()

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
        return {
            "id": folder.id,
            "name": folder.name,
            "parent_id": folder.parent_id,
            "persistent": True,
            "sort_order": getattr(folder, "sort_order", 0),
            "tree_order": getattr(folder, "tree_order", None),
            "publication_settings": (
                folder.publication_settings.to_dict()
                if folder.publication_settings else None
            ),
        }

    @staticmethod
    def _to_dict(publication_set):
        settings = publication_set.publication_settings
        return {
            "id": publication_set.id,
            "name": publication_set.name,
            "persistent": True,
            "folder_id": publication_set.folder_id,
            "sort_order": getattr(publication_set, "sort_order", 0),
            "tree_order": getattr(publication_set, "tree_order", None),
            "output_directory": publication_set.output_directory,
            "filename_template_id": publication_set.filename_template_id,
            "publication_settings": (
                settings.to_dict() if settings else None
            ),
            "source": {
                "mode": publication_set.source.mode,
                "parameter_name": publication_set.source.parameter_name,
                "parameter_value": publication_set.source.parameter_value,
            },
            "items": [{
                "unique_id": item.unique_id,
                "sheet_id": item.sheet_id,
                "item_type": item.item_type,
                "sheet_number": item.sheet_number,
                "sheet_name": item.sheet_name,
                "parameter_value": item.parameter_value,
            } for item in publication_set.items],
        }

    @staticmethod
    def _from_dict(value):
        source_data = value.get("source") or {}
        source = PublicationSource(
            source_data.get("mode", PublicationSource.MANUAL),
            source_data.get("parameter_name"),
            source_data.get("parameter_value"),
        )
        items = [
            PublicationItem(
                item_data.get("unique_id"),
                item_data.get("sheet_id"),
                item_data.get("item_type", "SHEET"),
                item_data.get("sheet_number"),
                item_data.get("sheet_name"),
                item_data.get("parameter_value"),
            )
            for item_data in value.get("items", [])
        ]
        settings = PublicationSettings.from_dict(
            value.get("publication_settings")
        )
        if value.get("publication_settings") is None:
            settings.output_directory = value.get("output_directory")

        publication_set = PublicationSet(
            name=value.get("name", ""),
            items=items,
            source=source,
            output_directory=value.get("output_directory"),
            filename_template_id=value.get("filename_template_id"),
            set_id=value.get("id"),
            persistent=True,
            folder_id=value.get(
                "folder_id",
                CarnetRepository.DEFAULT_FOLDER_ID,
            ),
            publication_settings=settings,
        )
        publication_set.sort_order = value.get("sort_order", 0)
        publication_set.tree_order = value.get("tree_order")
        return publication_set

    @staticmethod
    def _folder_from_dict(value):
        return PublicationFolder(
            value.get("name", ""),
            value.get("id"),
            value.get("parent_id"),
            True,
            PublicationSettings.from_dict(
                value.get("publication_settings")
            ),
            value.get("sort_order", 0),
            value.get("tree_order"),
        )
