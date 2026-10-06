# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Gestion sûre des paramètres de pièces appartenant à des groupes Revit."""

from common.exceptions import ValidationError


class GroupedParameterService(object):
    """Gère l'autorisation temporaire des valeurs variant entre groupes.

    Revit peut empêcher l'écriture d'un paramètre de pièce lorsque la pièce
    appartient à un groupe et que la définition impose des valeurs alignées par
    type de groupe. Ce service isole ce comportement API et permet au workflow
    d'ouvrir temporairement l'écriture, puis de restaurer l'état initial avant
    la validation de la transaction.
    """

    INVALID_ELEMENT_ID = -1

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document

    def is_grouped(self, element):
        if element is None:
            return False
        group_id = getattr(element, "GroupId", None)
        value = self._element_id_value(group_id)
        return value is not None and value != self.INVALID_ELEMENT_ID

    def can_temporarily_unlock(self, element, parameter):
        """Indique si un readonly peut provenir de l'alignement de groupe."""
        if not self.is_grouped(element):
            return False

        definition = self._get_supported_definition(parameter)
        if definition is None:
            return False

        try:
            return not bool(definition.VariesAcrossGroups)
        except Exception:
            return False

    def requires_temporary_override(self, element, parameter):
        """Indique si la définition doit être passée temporairement à True."""
        return self.can_temporarily_unlock(element, parameter)

    def get_required_definitions(self, room_parameter_pairs):
        """Retourne les définitions distinctes à déverrouiller dans la transaction."""
        definitions = []
        seen = set()

        for room, parameter in room_parameter_pairs or []:
            if not self.requires_temporary_override(room, parameter):
                continue

            definition = self._get_supported_definition(parameter)
            if definition is None:
                continue

            key = self._definition_key(definition)
            if key in seen:
                continue

            seen.add(key)
            definitions.append(definition)

        return definitions

    def enable_temporary_override(self, definitions):
        """Autorise temporairement les valeurs différentes entre groupes."""
        enabled = []
        for definition in definitions or []:
            try:
                definition.SetAllowVaryBetweenGroups(self.document, True)
                if not bool(definition.VariesAcrossGroups):
                    raise ValidationError(
                        "Revit n'a pas autorisé les valeurs variables pour '{}'."
                        .format(getattr(definition, "Name", "paramètre"))
                    )
                enabled.append(definition)
            except Exception as error:
                raise ValidationError(
                    "Impossible de déverrouiller temporairement le paramètre "
                    "'{}' pour les groupes : {}.".format(
                        getattr(definition, "Name", "paramètre"),
                        error,
                    )
                )
        return enabled

    def restore_group_alignment(self, definitions):
        """Restaure l'alignement et retourne les éléments réalignés par Revit."""
        realigned = []

        for definition in reversed(list(definitions or [])):
            try:
                changed = definition.SetAllowVaryBetweenGroups(
                    self.document,
                    False,
                )
                if changed:
                    realigned.extend(list(changed))
                if bool(definition.VariesAcrossGroups):
                    raise ValidationError(
                        "Revit n'a pas restauré l'alignement du paramètre '{}'."
                        .format(getattr(definition, "Name", "paramètre"))
                    )
            except Exception as error:
                raise ValidationError(
                    "Impossible de restaurer l'alignement du paramètre "
                    "'{}' après calcul : {}.".format(
                        getattr(definition, "Name", "paramètre"),
                        error,
                    )
                )

        return realigned

    @staticmethod
    def _element_id_value(element_id):
        if element_id is None:
            return None
        if hasattr(element_id, "Value"):
            return element_id.Value
        if hasattr(element_id, "IntegerValue"):
            return element_id.IntegerValue
        try:
            return int(element_id)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _definition_key(definition):
        get_type_id = getattr(definition, "GetTypeId", None)
        if get_type_id is not None:
            try:
                type_id = get_type_id()
                value = getattr(type_id, "TypeId", None)
                if value:
                    return "TYPE:{}".format(value)
            except Exception:
                pass

        definition_id = getattr(definition, "Id", None)
        if definition_id is not None:
            value = GroupedParameterService._element_id_value(definition_id)
            if value is not None:
                return "ID:{}".format(value)

        return "NAME:{}".format(getattr(definition, "Name", id(definition)))

    @staticmethod
    def _get_supported_definition(parameter):
        if parameter is None:
            return None

        definition = getattr(parameter, "Definition", None)
        if definition is None:
            return None

        if not hasattr(definition, "VariesAcrossGroups"):
            return None
        if not hasattr(definition, "SetAllowVaryBetweenGroups"):
            return None

        # Autodesk limite SetAllowVaryBetweenGroups aux paramètres non intégrés.
        built_in = getattr(definition, "BuiltInParameter", None)
        if built_in is not None:
            try:
                if int(built_in) != -1:
                    return None
            except Exception:
                text = str(built_in).upper()
                if "INVALID" not in text:
                    return None

        return definition
