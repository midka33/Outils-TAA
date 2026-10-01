# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Lecture normalisée des paramètres de pièces Revit."""


class RoomParameterService(object):
    """Découvre les paramètres disponibles et lit leur valeur Python."""

    NUMERIC_STORAGE_TYPES = ("Double", "Integer")

    def get_parameter_names(self, rooms, numeric_only=False):
        names = {}

        for room in rooms or []:
            for parameter in getattr(room, "Parameters", []) or []:
                definition = getattr(parameter, "Definition", None)
                name = getattr(definition, "Name", None)
                if not name:
                    continue

                if numeric_only and self.get_storage_type_name(parameter) not in self.NUMERIC_STORAGE_TYPES:
                    continue

                key = name.lower()
                if key not in names:
                    names[key] = name

        return sorted(names.values(), key=lambda value: value.lower())

    def get_parameter(self, room, parameter_name):
        if room is None or not parameter_name:
            return None
        return room.LookupParameter(parameter_name)

    def read_value(self, room, parameter_name, default=None):
        parameter = self.get_parameter(room, parameter_name)
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
        return parameter is not None and not bool(getattr(parameter, "IsReadOnly", True))

    @staticmethod
    def _element_id_value(element_id, default=None):
        if element_id is None:
            return default
        if hasattr(element_id, "Value"):
            return element_id.Value
        if hasattr(element_id, "IntegerValue"):
            return element_id.IntegerValue
        return str(element_id)
