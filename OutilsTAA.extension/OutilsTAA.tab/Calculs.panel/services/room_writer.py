# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Écriture contrôlée des résultats dans les paramètres de pièces."""

from common.exceptions import ValidationError


class RoomWriter(object):
    """Prépare et écrit une valeur sans ouvrir de transaction."""

    def __init__(self, parameter_service, unit_service):
        self.parameter_service = parameter_service
        self.unit_service = unit_service

    def prepare_value(
        self,
        source_descriptor,
        target_descriptor,
        value,
        output_unit_type_id=None,
    ):
        storage_type = target_descriptor.storage_type

        if storage_type == "Double":
            return float(value)

        if storage_type == "Integer":
            normalized = self._normalize_non_double_target(
                source_descriptor,
                value,
                output_unit_type_id,
            )
            return int(round(normalized))

        if storage_type == "String":
            normalized = self._normalize_non_double_target(
                source_descriptor,
                value,
                output_unit_type_id,
            )
            if isinstance(normalized, float):
                return "{0:g}".format(normalized)
            return str(normalized)

        raise ValidationError(
            "Type de destination non pris en charge : {}.".format(storage_type)
        )

    def write_value(self, room, target_descriptor, value):
        parameter = self.parameter_service.get_parameter(room, target_descriptor)
        if parameter is None:
            raise ValidationError(
                "Le paramètre destination '{}' est absent de la pièce.".format(
                    target_descriptor.name
                )
            )
        if not self.parameter_service.is_writable(parameter):
            raise ValidationError(
                "Le paramètre destination '{}' est en lecture seule.".format(
                    target_descriptor.name
                )
            )

        actual_storage = self.parameter_service.get_storage_type_name(parameter)
        if actual_storage != target_descriptor.storage_type:
            raise ValidationError(
                "Le type de '{}' a changé : {} au lieu de {}.".format(
                    target_descriptor.name,
                    actual_storage,
                    target_descriptor.storage_type,
                )
            )

        result = parameter.Set(value)
        if result is False:
            raise ValidationError(
                "Revit a refusé l'écriture dans '{}'.".format(
                    target_descriptor.name
                )
            )
        return True

    def _normalize_non_double_target(
        self,
        source_descriptor,
        value,
        output_unit_type_id,
    ):
        if source_descriptor.storage_type != "Double":
            return value

        selected_unit = (
            output_unit_type_id
            or source_descriptor.unit_type_id
        )
        if not selected_unit:
            return value

        return self.unit_service.from_internal(
            value,
            unit_type_id=selected_unit,
        )
