# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Gestion sûre des paramètres de pièces appartenant à des groupes Revit."""

from common.exceptions import ValidationError
from calculation.group_alignment import (
    GroupAlignmentAnalysis,
    GroupAlignmentCandidate,
    GroupAlignmentConflict,
)


class GroupedParameterService(object):
    """Gère l'alignement temporaire des paramètres de pièces groupées."""

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

    def analyze_conflicts(
        self,
        valid_entries,
        target_descriptor,
        parameter_service,
        value_formatter=None,
    ):
        """Analyse les valeurs projetées sur les membres correspondants.

        Group.GetMemberIds() fournit une liste ordonnée utilisable pour faire
        correspondre le même membre entre les différentes instances d'un type
        de groupe. L'analyse inclut les pièces qui ne font pas partie du calcul
        courant afin d'anticiper exactement ce que Revit devrait réaligner.
        """
        projected_by_element = {}
        seeds = []

        for operation, room, prepared_value, parameter in valid_entries or []:
            element_key = self._element_key(room)
            if element_key is not None:
                projected_by_element[element_key] = prepared_value

            if self.requires_temporary_override(room, parameter):
                seeds.append((room, parameter))

        conflicts = []
        visited = set()

        for room, parameter in seeds:
            alignment_set = self._get_alignment_set(room, parameter)
            if alignment_set is None:
                continue

            key = alignment_set["key"]
            if key in visited:
                continue
            visited.add(key)

            values = []
            elements = []
            for element in alignment_set["elements"]:
                element_key = self._element_key(element)
                target_parameter = parameter_service.get_parameter(
                    element,
                    target_descriptor,
                )
                if target_parameter is None:
                    raise ValidationError(
                        "Le paramètre destination '{}' est absent d'un membre "
                        "correspondant du groupe '{}'.".format(
                            target_descriptor.name,
                            alignment_set["group_type_name"],
                        )
                    )

                if element_key in projected_by_element:
                    value = projected_by_element[element_key]
                else:
                    value = parameter_service.read_parameter(
                        target_parameter,
                        default=None,
                    )

                values.append(value)
                elements.append(element)

            candidates = self._build_candidates(
                values,
                value_formatter=value_formatter,
            )
            if len(candidates) <= 1:
                continue

            conflicts.append(
                GroupAlignmentConflict(
                    key=key,
                    group_type_name=alignment_set["group_type_name"],
                    member_label=alignment_set["member_label"],
                    candidates=candidates,
                    elements=elements,
                )
            )

        return GroupAlignmentAnalysis(conflicts=conflicts)

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

    def _get_alignment_set(self, element, parameter):
        group_id = getattr(element, "GroupId", None)
        group = self.document.GetElement(group_id)
        if group is None:
            return None

        member_ids = list(group.GetMemberIds() or [])
        member_index = self._find_member_index(
            member_ids,
            getattr(element, "Id", None),
        )
        if member_index < 0:
            raise ValidationError(
                "Impossible de retrouver la pièce dans les membres de son groupe."
            )

        group_type = getattr(group, "GroupType", None)
        if group_type is None:
            raise ValidationError(
                "Impossible de déterminer le type du groupe contenant la pièce."
            )

        elements = []
        for instance in list(getattr(group_type, "Groups", []) or []):
            instance_members = list(instance.GetMemberIds() or [])
            if member_index >= len(instance_members):
                raise ValidationError(
                    "Les instances du type de groupe '{}' n'ont pas une "
                    "structure de membres cohérente.".format(
                        self._group_type_name(group_type)
                    )
                )

            corresponding = self.document.GetElement(
                instance_members[member_index]
            )
            if corresponding is not None:
                elements.append(corresponding)

        definition = self._get_supported_definition(parameter)
        definition_key = self._definition_key(definition)
        group_type_key = self._element_id_value(
            getattr(group_type, "Id", None)
        )

        return {
            "key": "{}|{}|{}".format(
                definition_key,
                group_type_key,
                member_index,
            ),
            "group_type_name": self._group_type_name(group_type),
            "member_label": self._member_label(element),
            "elements": elements,
        }

    @classmethod
    def _build_candidates(cls, values, value_formatter=None):
        buckets = []
        for value in values or []:
            bucket = None
            for item in buckets:
                if cls._values_equal(item["value"], value):
                    bucket = item
                    break

            if bucket is None:
                bucket = {"value": value, "count": 0}
                buckets.append(bucket)
            bucket["count"] += 1

        candidates = []
        for bucket in buckets:
            value = bucket["value"]
            display = (
                value_formatter(value)
                if value_formatter is not None
                else cls._default_display_value(value)
            )
            candidates.append(
                GroupAlignmentCandidate(
                    value=value,
                    count=bucket["count"],
                    display_value=display,
                )
            )
        return candidates

    @staticmethod
    def _values_equal(first, second):
        if first is None or second is None:
            return first is second

        if isinstance(first, float) or isinstance(second, float):
            try:
                return abs(float(first) - float(second)) <= 0.000001
            except (TypeError, ValueError):
                return False

        return first == second

    @staticmethod
    def _default_display_value(value):
        if isinstance(value, float):
            text = "{0:.3f}".format(value).rstrip("0").rstrip(".")
            return text.replace(".", ",")
        if value is None:
            return "(vide)"
        return str(value)

    @classmethod
    def _find_member_index(cls, member_ids, target_id):
        target_value = cls._element_id_value(target_id)
        for index, member_id in enumerate(member_ids or []):
            if cls._element_id_value(member_id) == target_value:
                return index
        return -1

    @classmethod
    def _element_key(cls, element):
        if element is None:
            return None
        return cls._element_id_value(getattr(element, "Id", None))

    @classmethod
    def _member_label(cls, element):
        number = getattr(element, "Number", None)
        name = getattr(element, "Name", None)

        parts = []
        if number:
            parts.append("Pièce {}".format(number))
        else:
            parts.append("Pièce")

        if name:
            parts.append(str(name))

        if len(parts) == 1:
            element_id = cls._element_key(element)
            if element_id is not None:
                parts.append("ID {}".format(element_id))

        return " — ".join(parts)

    @classmethod
    def _group_type_name(cls, group_type):
        name = getattr(group_type, "Name", None)
        if name:
            return str(name)

        element_id = cls._element_id_value(getattr(group_type, "Id", None))
        if element_id is not None:
            return "Type de groupe {}".format(element_id)

        return "Type de groupe"

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
        if definition is None:
            return "DEFINITION:UNKNOWN"

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
