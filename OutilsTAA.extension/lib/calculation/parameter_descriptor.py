# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Modèle sérialisable décrivant un paramètre de pièce."""


class RoomParameterDescriptor(object):
    """Identité et métadonnées d'un paramètre Revit."""

    KIND_SHARED_GUID = "SHARED_GUID"
    KIND_BUILT_IN = "BUILT_IN"
    KIND_DEFINITION = "DEFINITION"
    KIND_NAME = "NAME"

    def __init__(
        self,
        name,
        identity_kind,
        identity_value,
        storage_type,
        data_type_id=None,
        unit_type_id=None,
        writable=True,
    ):
        self.name = name or ""
        self.identity_kind = identity_kind or self.KIND_NAME
        self.identity_value = identity_value or self.name
        self.storage_type = storage_type or "Unknown"
        self.data_type_id = data_type_id
        self.unit_type_id = unit_type_id
        self.writable = bool(writable)

    @property
    def identity_key(self):
        return "{}:{}".format(self.identity_kind, self.identity_value)

    @property
    def is_numeric(self):
        return self.storage_type in ("Double", "Integer")

    def to_dict(self):
        return {
            "name": self.name,
            "identity_kind": self.identity_kind,
            "identity_value": self.identity_value,
            "storage_type": self.storage_type,
            "data_type_id": self.data_type_id,
            "unit_type_id": self.unit_type_id,
            "writable": self.writable,
        }

    @classmethod
    def from_dict(cls, data):
        data = data or {}
        return cls(
            name=data.get("name"),
            identity_kind=data.get("identity_kind"),
            identity_value=data.get("identity_value"),
            storage_type=data.get("storage_type"),
            data_type_id=data.get("data_type_id"),
            unit_type_id=data.get("unit_type_id"),
            writable=data.get("writable", True),
        )
