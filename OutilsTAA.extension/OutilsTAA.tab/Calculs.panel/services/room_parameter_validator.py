# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Validation des paramètres source et destination avant écriture."""

from common.unit_utils import data_type_ids_are_compatible


class ParameterValidationResult(object):
    def __init__(self, errors=None, warnings=None):
        self.errors = list(errors or [])
        self.warnings = list(warnings or [])

    @property
    def is_valid(self):
        return not self.errors


class RoomParameterValidator(object):
    """Valide la compatibilité métier avant la future phase WRITE."""

    NUMERIC_TYPES = ("Double", "Integer")
    SUPPORTED_TARGET_TYPES = ("Double", "Integer", "String")

    def validate_source(self, descriptor):
        errors = []
        if descriptor is None:
            errors.append("Paramètre source manquant.")
        elif descriptor.storage_type not in self.NUMERIC_TYPES:
            errors.append(
                "Le paramètre source '{}' n'est pas numérique.".format(
                    descriptor.name
                )
            )
        return ParameterValidationResult(errors=errors)

    def validate_target(self, descriptor):
        errors = []
        if descriptor is None:
            errors.append("Paramètre de destination manquant.")
        else:
            if descriptor.storage_type not in self.SUPPORTED_TARGET_TYPES:
                errors.append(
                    "Le paramètre de destination '{}' a un type non pris en charge : {}.".format(
                        descriptor.name,
                        descriptor.storage_type,
                    )
                )
            if not descriptor.writable:
                errors.append(
                    "Le paramètre de destination '{}' est en lecture seule.".format(
                        descriptor.name
                    )
                )
        return ParameterValidationResult(errors=errors)

    def validate_pair(self, source, target):
        source_result = self.validate_source(source)
        target_result = self.validate_target(target)
        errors = source_result.errors + target_result.errors
        warnings = source_result.warnings + target_result.warnings

        if errors:
            return ParameterValidationResult(errors=errors, warnings=warnings)

        if source.storage_type == "Double" and target.storage_type == "Double":
            if not data_type_ids_are_compatible(
                source.data_type_id,
                target.data_type_id,
            ):
                errors.append(
                    "Les paramètres '{}' et '{}' n'ont pas le même type de donnée Revit.".format(
                        source.name,
                        target.name,
                    )
                )

        if source.storage_type == "Double" and target.storage_type == "Integer":
            warnings.append(
                "L'écriture vers '{}' arrondira une valeur décimale en entier.".format(
                    target.name
                )
            )

        if source.storage_type == "Integer" and target.storage_type == "Double":
            warnings.append(
                "Une valeur entière sera écrite dans le paramètre décimal '{}'. "
                "Vérifiez que sa signification métier est compatible.".format(
                    target.name
                )
            )

        if target.storage_type == "String":
            warnings.append(
                "Le résultat numérique sera écrit comme texte dans '{}'.".format(
                    target.name
                )
            )

        return ParameterValidationResult(errors=errors, warnings=warnings)
