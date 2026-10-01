# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Découverte, identité et lecture des paramètres de pièces Revit."""

from common.exceptions import ValidationError
from common.parameter_utils import (
    get_built_in_parameter_type_id,
    get_definition_type_id,
    get_parameter_data_type_id,
    get_parameter_unit_type_id,
    get_shared_parameter_guid,
)
from calculation.parameter_descriptor import RoomParameterDescriptor


class RoomParameterService(object):
    """Découvre les paramètres disponibles et lit leur valeur Python.

    Les nouvelles fonctions utilisent RoomParameterDescriptor afin d'éviter de
    dépendre uniquement d'un nom affiché potentiellement ambigu.
    """

    NUMERIC_STORAGE_TYPES = ("Double", "Integer")

    def get_parameter_names(self, rooms, numeric_only=False):
        """Compatibilité : retourne une liste de noms uniques triés."""
        names = {}
        for descriptor in self.get_parameter_descriptors(
            rooms,
            numeric_only=numeric_only,
        ):
            key = descriptor.name.lower()
            if key not in names:
                names[key] = descriptor.name
        return sorted(names.values(), key=lambda value: value.lower())

    def get_parameter_descriptors(
        self,
        rooms,
        numeric_only=False,
        writable_only=False,
    ):
        """Retourne les paramètres distincts par identité stable disponible."""
        descriptors = {}

        for room in rooms or []:
            for parameter in getattr(room, "Parameters", []) or []:
                descriptor = self.create_descriptor(parameter)
                if descriptor is None or not descriptor.name:
                    continue
                if numeric_only and not descriptor.is_numeric:
                    continue

                existing = descriptors.get(descriptor.identity_key)
                if existing is None:
                    descriptors[descriptor.identity_key] = descriptor
                else:
                    # Un paramètre proposé comme destination doit rester
                    # considéré non sûr si une occurrence observée est readonly.
                    existing.writable = existing.writable and descriptor.writable

        values = list(descriptors.values())
        if writable_only:
            values = [descriptor for descriptor in values if descriptor.writable]

        return sorted(
            values,
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
            storage_type=self.get_storage_type_name(parameter),
            data_type_id=get_parameter_data_type_id(parameter),
            unit_type_id=get_parameter_unit_type_id(parameter),
            writable=self.is_writable(parameter),
        )

    def get_parameter(self, room, parameter_reference):
        """Résout un paramètre par descripteur ou, en compatibilité, par nom."""
        if room is None or parameter_reference is None:
            return None

        if isinstance(parameter_reference, RoomParameterDescriptor):
            return self._get_parameter_by_descriptor(room, parameter_reference)

        return room.LookupParameter(str(parameter_reference))

    def read_value(self, room, parameter_reference, default=None):
        parameter = self.get_parameter(room, parameter_reference)
        if parameter is None:
            return default
        return self.read_parameter(parameter, default=default)

    def read_parameter(self, parameter, default=None):
        storage_type = self.get_storage_type_name(parameter)

        try:
            if storage_type == "String":
                value = parameter.AsString()
                return default if value is None else value
            if storage_type == "Integer":
                return parameter.AsInteger()
            if storage_type == "Double":
                return parameter.AsDouble()
            if storage_type == "ElementId":
                element_id = parameter.AsElementId()
                return self._element_id_value(element_id, default)

            value = parameter.AsValueString()
            return default if value is None else value
        except Exception:
            return default

    @staticmethod
    def get_storage_type_name(parameter):
        storage_type = getattr(parameter, "StorageType", None)
        if storage_type is None:
            return "Unknown"
        text = str(storage_type)
        if "." in text:
            text = text.split(".")[-1]
        return text

    @staticmethod
    def is_writable(parameter):
        return parameter is not None and not bool(
            getattr(parameter, "IsReadOnly", True)
        )

    @staticmethod
    def _element_id_value(element_id, default=None):
        if element_id is None:
            return default
        if hasattr(element_id, "Value"):
            return element_id.Value
        if hasattr(element_id, "IntegerValue"):
            return element_id.IntegerValue
        return str(element_id)

    def _get_parameter_by_descriptor(self, room, descriptor):
        kind = descriptor.identity_kind

        if kind == RoomParameterDescriptor.KIND_SHARED_GUID:
            try:
                from System import Guid
                return room.get_Parameter(Guid(descriptor.identity_value))
            except Exception as error:
                raise ValidationError(
                    "Impossible de résoudre le paramètre partagé '{}': {}".format(
                        descriptor.name,
                        error,
                    )
                )

        if kind == RoomParameterDescriptor.KIND_BUILT_IN:
            try:
                from Autodesk.Revit.DB import ForgeTypeId
                return room.GetParameter(ForgeTypeId(descriptor.identity_value))
            except Exception as error:
                raise ValidationError(
                    "Impossible de résoudre le paramètre Revit intégré '{}': {}".format(
                        descriptor.name,
                        error,
                    )
                )

        candidates = self._get_parameters_by_name(room, descriptor.name)
        if not candidates:
            return None

        if kind == RoomParameterDescriptor.KIND_DEFINITION:
            matches = []
            for parameter in candidates:
                candidate = self.create_descriptor(parameter)
                if candidate and candidate.identity_key == descriptor.identity_key:
                    matches.append(parameter)
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise ValidationError(
                    "Plusieurs paramètres correspondent à l'identité de '{}'.".format(
                        descriptor.name
                    )
                )
            return None

        if len(candidates) == 1:
            return candidates[0]

        raise ValidationError(
            "Le paramètre '{}' est ambigu : {} paramètres portent ce nom.".format(
                descriptor.name,
                len(candidates),
            )
        )

    @staticmethod
    def _get_parameters_by_name(room, name):
        getter = getattr(room, "GetParameters", None)
        if getter is not None:
            return list(getter(name) or [])

        parameter = room.LookupParameter(name)
        return [parameter] if parameter is not None else []
