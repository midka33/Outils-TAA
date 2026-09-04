# -*- coding: utf-8 -*-
"""Historique et détection des mises en page modifiées pour Export.

Le service est volontairement indépendant de l'API Revit. L'UI et le moteur
Revit lui fournissent les informations courantes d'une mise en page.
"""

import json
import os
from datetime import datetime


class PublicationHistoryService(object):
    """Persiste le dernier état publié de chaque carnet et de ses feuilles."""

    SCHEMA_VERSION = 1

    def __init__(self, storage_path):
        if not storage_path:
            raise ValueError("Le chemin de stockage de l'historique est obligatoire.")
        self.storage_path = storage_path

    def _read(self):
        if not os.path.exists(self.storage_path):
            return {"schema_version": self.SCHEMA_VERSION, "sets": {}}
        with open(self.storage_path, "r") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError("Le fichier d'historique Export est invalide.")
        data.setdefault("sets", {})
        data.setdefault("schema_version", self.SCHEMA_VERSION)
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
    def item_key(item):
        """Retourne une clé stable pour une mise en page."""
        return getattr(item, "unique_id", None) or str(getattr(item, "sheet_id", ""))

    @staticmethod
    def fingerprint(item, version_guid=None):
        """Construit l'état d'une mise en page au moment du contrôle.

        `version_guid` doit provenir de `Element.VersionGuid` dans Revit.
        Les informations de secours servent à diagnostiquer les anciennes
        intégrations, mais ne sont pas présentées comme une détection fiable
        de modification Revit.
        """
        if version_guid is not None:
            version_guid = str(version_guid)
        return {
            "version_guid": version_guid,
            "sheet_number": getattr(item, "sheet_number", None),
            "sheet_name": getattr(item, "sheet_name", None),
        }

    def get_set_history(self, set_id):
        if not set_id:
            return None
        return self._read().get("sets", {}).get(str(set_id))

    def classify_items(self, publication_set, current_states):
        """Classe les éléments en NEW, MODIFIED, UNCHANGED ou UNKNOWN.

        `current_states` est un dictionnaire clé `item_key` -> fingerprint.
        Une entrée absente de l'historique est NEW. Une différence de
        `version_guid` est MODIFIED. Une absence de VersionGuid courant ou
        historique donne UNKNOWN plutôt que de déclarer à tort la feuille
        inchangée.
        """
        set_id = getattr(publication_set, "id", None)
        history = self.get_set_history(set_id) or {}
        previous = history.get("items", {})
        result = {"NEW": [], "MODIFIED": [], "UNCHANGED": [], "UNKNOWN": []}

        for item in getattr(publication_set, "items", []) or []:
            key = self.item_key(item)
            current = current_states.get(key) or {}
            old = previous.get(key)
            if old is None:
                result["NEW"].append(item)
                continue
            current_guid = current.get("version_guid")
            old_guid = old.get("version_guid")
            if not current_guid or not old_guid:
                result["UNKNOWN"].append(item)
            elif str(current_guid) != str(old_guid):
                result["MODIFIED"].append(item)
            else:
                result["UNCHANGED"].append(item)
        return result

    def candidates(self, publication_set, current_states, modified_only=False):
        """Retourne les éléments à publier selon le mode demandé."""
        classified = self.classify_items(publication_set, current_states)
        if not modified_only:
            return list(getattr(publication_set, "items", []) or []), classified
        # Une feuille jamais publiée doit toujours être produite. Une feuille
        # dont Revit ne permet pas de confirmer l'état est conservativement
        # republiée plutôt que silencieusement ignorée.
        selected = (classified["NEW"] + classified["MODIFIED"] +
                    classified["UNKNOWN"])
        return selected, classified

    def record_publication(self, publication_set, item_states, successful=True,
                           output_paths=None):
        """Enregistre l'état courant après une publication réussie."""
        if not successful or publication_set is None or not getattr(publication_set, "id", None):
            return False
        data = self._read()
        set_id = str(publication_set.id)
        items = {}
        for item in getattr(publication_set, "items", []) or []:
            key = self.item_key(item)
            state = item_states.get(key)
            if state is not None:
                items[key] = dict(state)
        data["sets"][set_id] = {
            "set_name": getattr(publication_set, "name", ""),
            "published_at": datetime.now().isoformat(),
            "items": items,
            "output_paths": list(output_paths or [])
        }
        self._write(data)
        return True

    def clear(self, set_id):
        data = self._read()
        if str(set_id) not in data.get("sets", {}):
            return False
        del data["sets"][str(set_id)]
        self._write(data)
        return True
