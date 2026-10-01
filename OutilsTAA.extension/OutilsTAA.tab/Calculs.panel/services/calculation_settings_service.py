# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Persistance des choix utilisateur de Calculs des pièces."""

import codecs
import json
import os

from common.settings import JsonSettingsStore
from calculation.parameter_descriptor import RoomParameterDescriptor


class CalculationSettingsService(object):
    """Sauvegarde des choix sans persister d'objet Revit."""

    SCHEMA_VERSION = 1

    def __init__(self, storage_path=None, legacy_path=None):
        self.storage_path = storage_path or self.default_storage_path()
        self.legacy_path = legacy_path or self.default_legacy_path()
        self.store = JsonSettingsStore(self.storage_path)

    @staticmethod
    def default_storage_path():
        app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(
            app_data,
            "Outils-TAA",
            "Calculs",
            "settings.json",
        )

    @staticmethod
    def default_legacy_path():
        app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(app_data, "RoomTools", "settings.json")

    def load(self):
        data = self.store.as_dict()
        if data:
            return data

        legacy = self._read_legacy()
        if not legacy:
            return {}

        migrated = self._migrate_legacy(legacy)
        self.store.replace(migrated)
        return migrated

    def save_request(self, request):
        data = {
            "schema_version": self.SCHEMA_VERSION,
            "group_parameter": self._descriptor_to_dict(
                request.group_parameter
            ),
            "source_parameter": self._descriptor_to_dict(
                request.source_parameter
            ),
            "target_parameter": self._descriptor_to_dict(
                request.target_parameter
            ),
            "filter_parameter": self._descriptor_to_dict(
                request.filter_parameter
            ),
            "filter_value": request.filter_value or "",
            "output_unit_type_id": request.output_unit_type_id,
        }
        self.store.replace(data)
        return data

    def match_descriptor(self, saved_data, available_descriptors):
        if not saved_data:
            return None

        available = list(available_descriptors or [])
        restored = RoomParameterDescriptor.from_dict(saved_data)

        for descriptor in available:
            if descriptor.identity_key == restored.identity_key:
                return descriptor

        matching_names = [
            descriptor
            for descriptor in available
            if descriptor.name == restored.name
        ]
        if len(matching_names) == 1:
            return matching_names[0]

        return None

    @staticmethod
    def _descriptor_to_dict(descriptor):
        return descriptor.to_dict() if descriptor is not None else None

    def _read_legacy(self):
        if not self.legacy_path or not os.path.exists(self.legacy_path):
            return None
        try:
            with codecs.open(self.legacy_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (IOError, OSError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _migrate_legacy(self, data):
        return {
            "schema_version": self.SCHEMA_VERSION,
            "group_parameter": self._legacy_descriptor(data.get("group")),
            "source_parameter": self._legacy_descriptor(data.get("sum")),
            "target_parameter": self._legacy_descriptor(data.get("target")),
            "filter_parameter": self._legacy_descriptor(
                data.get("filter_param")
                if data.get("filter_param") not in ("", "Aucun filtre")
                else None
            ),
            "filter_value": data.get("filter_value") or "",
            # Les anciens tags d'unités reposaient sur des facteurs manuels.
            # Ils ne sont volontairement pas migrés vers un ForgeTypeId.
            "output_unit_type_id": None,
            "legacy_unit_tag": data.get("unit") or "none",
        }

    @staticmethod
    def _legacy_descriptor(name):
        if not name:
            return None
        return RoomParameterDescriptor(
            name=name,
            identity_kind=RoomParameterDescriptor.KIND_NAME,
            identity_value=name,
            storage_type="Unknown",
        ).to_dict()
