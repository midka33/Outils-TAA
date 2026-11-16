# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Persistance locale par projet des options Plans de vente."""

import hashlib
import ntpath
import os

from common.settings import JsonSettingsStore
from calculation.parameter_descriptor import RoomParameterDescriptor


class PlansVenteSettingsService(object):
    """Mémorise uniquement des valeurs sérialisables, jamais des objets Revit."""

    SCHEMA_VERSION = 1
    SETTING_KEYS = (
        "skip_existing",
        "crop_margin_mm",
        "auto_scale",
        "allowed_scales",
        "detailed_report",
        "log_warnings",
        "building_parameter_name",
        "typology_parameter_name",
        "main_view_template_unique_id",
        "location_view_template_unique_id",
        "room_tag_type_unique_id",
        "dimension_type_unique_id",
    )

    def __init__(
        self,
        document=None,
        storage_path=None,
        project_identity=None,
    ):
        self.project_identity = (
            str(project_identity)
            if project_identity
            else self._project_identity(document)
        )
        self.storage_path = (
            storage_path
            if storage_path
            else self.default_storage_path(self.project_identity)
        )
        self.store = JsonSettingsStore(self.storage_path)

    @classmethod
    def default_storage_path(cls, project_identity):
        app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
        key = hashlib.sha1(
            str(project_identity or "UNKNOWN").encode("utf-8")
        ).hexdigest()
        return os.path.join(
            app_data,
            "Outils-TAA",
            "PlansDeVente",
            "Projects",
            "{}.json".format(key),
        )

    @classmethod
    def _project_identity(cls, document):
        if document is None:
            return "UNKNOWN:DOCUMENT"

        try:
            from Autodesk.Revit.DB import ModelPathUtils
            central = document.GetWorksharingCentralModelPath()
            if central:
                path = ModelPathUtils.ConvertModelPathToUserVisiblePath(
                    central
                )
                if path:
                    return "CENTRAL:" + cls._normalize_windows_path(path)
        except Exception:
            pass

        try:
            path = str(document.PathName or "")
        except Exception:
            path = ""
        if path:
            return "FILE:" + cls._normalize_windows_path(path)

        try:
            return "UNSAVED_DOCUMENT:" + str(document.GetHashCode())
        except Exception:
            return "UNSAVED_INSTANCE:" + str(id(document))

    @staticmethod
    def _normalize_windows_path(path):
        text = str(path or "").replace("/", "\\")
        try:
            return ntpath.normcase(ntpath.normpath(text))
        except Exception:
            return text.lower()

    def load(self):
        data = self.store.as_dict()
        if not isinstance(data, dict):
            return {}
        if data.get("project_identity") not in (None, self.project_identity):
            return {}
        settings = data.get("settings")
        if not isinstance(settings, dict):
            settings = {}
        return {
            "schema_version": data.get("schema_version"),
            "project_identity": self.project_identity,
            "settings": dict(settings),
            "active_parameter": data.get("active_parameter"),
        }

    def save(self, settings, active_descriptor):
        values = {}
        source = dict(settings or {})
        for key in self.SETTING_KEYS:
            if key in source:
                value = source.get(key)
                if key == "allowed_scales":
                    value = list(value or [])
                values[key] = value

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "project_identity": self.project_identity,
            "settings": values,
            "active_parameter": (
                active_descriptor.to_dict()
                if active_descriptor is not None
                else None
            ),
        }
        self.store.replace(payload)
        return payload

    @staticmethod
    def match_descriptor(saved_data, available_descriptors):
        if not saved_data:
            return None

        restored = RoomParameterDescriptor.from_dict(saved_data)
        available = list(available_descriptors or [])

        for descriptor in available:
            if descriptor.identity_key == restored.identity_key:
                return descriptor

        matching_names = [
            descriptor
            for descriptor in available
            if str(getattr(descriptor, "name", "") or "")
            == str(restored.name or "")
        ]
        if len(matching_names) == 1:
            return matching_names[0]
        return None
