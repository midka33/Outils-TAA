# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Découverte et lecture des paramètres texte utilisés pour identifier les logements."""

from common.parameter_utils import (
    get_built_in_parameter_type_id,
    get_definition_type_id,
    get_shared_parameter_guid,
)
from calculation.parameter_descriptor import RoomParameterDescriptor


class RoomParameterService(object):
    """Expose les paramètres texte pertinents pour l'identifiant logement."""

    # Les paramètres de catégorie Pièces sont liés au projet et leur schéma est
    # identique d'une pièce à l'autre. Scanner des centaines de pièces au simple
    # affichage de la fenêtre ne fournit donc quasiment aucune information
    # supplémentaire. Quelques pièces suffisent pour absorber les cas atypiques.
    DISCOVERY_SAMPLE_LIMIT = 8

    def get_text_parameter_descriptors(self, rooms):
        descriptors = {}

        sampled_rooms = list(rooms or [])[:self.DISCOVERY_SAMPLE_LIMIT]
        for room in sampled_rooms:
            for parameter in getattr(room, "Parameters", []) or []:
                descriptor = self.create_descriptor(parameter)
                if descriptor is None:
                    continue
                if descriptor.storage_type != "String":
                    continue
                descriptors.setdefault(descriptor.identity_key, descriptor)

        return sorted(
            descriptors.values(),
            key=lambda item: (item.name.lower(), item.identity_key),
        )

    def create_descriptor(self, parameter):
        if parameter is None:
            return None

        definition = getattr(parameter, "Definition", None)
        name = getattr(definition, "Name", None)
        if not name:
            return None

        shared_guid = get_shared_parameter_guid(parameter)
        built_in_type_id = get_built_in_parameter_type_id(parameter)
        definition_type_id = get_definition_type_id(parameter)

        if shared_guid:
            identity_kind = RoomParameterDescriptor.KIND_SHARED_GUID
            identity_value = shared_guid
        elif built_in_type_id:
            identity_kind = RoomParameterDescriptor.KIND_BUILT_IN
            identity_value = built_in_type_id
        elif definition_type_id:
            identity_kind = RoomParameterDescriptor.KIND_DEFINITION
            identity_value = definition_type_id
        else:
            identity_kind = RoomParameterDescriptor.KIND_NAME
            identity_value = name

        return RoomParameterDescriptor(
            name=name,
            identity_kind=identity_kind,
            identity_value=identity_value,
            storage_type=self._storage_type_name(parameter),
            writable=not bool(getattr(parameter, "IsReadOnly", True)),
        )

    def read_text_value(self, room, descriptor, default=""):
        parameter = self.get_parameter(room, descriptor)
        if parameter is None:
            return default

        try:
            value = parameter.AsString()
        except Exception:
            return default

        return default if value is None else value

    def get_parameter(self, room, descriptor):
        if room is None or descriptor is None:
            return None

        kind = descriptor.identity_kind

        if kind == RoomParameterDescriptor.KIND_SHARED_GUID:
            try:
                from System import Guid
                return room.get_Parameter(Guid(descriptor.identity_value))
            except Exception:
                return None

        if kind == RoomParameterDescriptor.KIND_BUILT_IN:
            try:
                from Autodesk.Revit.DB import ForgeTypeId
                return room.GetParameter(ForgeTypeId(descriptor.identity_value))
            except Exception:
                return None

        candidates = self._parameters_by_name(room, descriptor.name)
        if not candidates:
            return None

        if kind == RoomParameterDescriptor.KIND_DEFINITION:
            for parameter in candidates:
                candidate = self.create_descriptor(parameter)
                if (
                    candidate is not None
                    and candidate.identity_key == descriptor.identity_key
                ):
                    return parameter
            return None

        if len(candidates) == 1:
            return candidates[0]

        return None

    @staticmethod
    def _storage_type_name(parameter):
        storage_type = getattr(parameter, "StorageType", None)
        if storage_type is None:
            return "Unknown"
        value = str(storage_type)
        return value.split(".")[-1] if "." in value else value

    @staticmethod
    def _parameters_by_name(room, name):
        getter = getattr(room, "GetParameters", None)
        if getter is not None:
            return list(getter(name) or [])

        parameter = room.LookupParameter(name)
        return [parameter] if parameter is not None else []
