# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Duplication et filtrage des nomenclatures modèles Plans de vente."""

from common.transaction import RevitTransaction
from plans_vente.placement_contract import PlacementRole, placement_artifact
from plans_vente.schedule_naming import schedule_name


class ScheduleTemplateCandidate(object):
    def __init__(self, unique_id, name):
        self.unique_id = unique_id or ""
        self.name = name or ""

    @property
    def label(self):
        return self.name


class SchedulePairResult(object):
    def __init__(
        self,
        housing_key,
        interior_name,
        interior_unique_id,
        exterior_name,
        exterior_unique_id,
        placements=None,
    ):
        self.housing_key = housing_key or ""
        self.interior_name = interior_name or ""
        self.interior_unique_id = interior_unique_id or ""
        self.exterior_name = exterior_name or ""
        self.exterior_unique_id = exterior_unique_id or ""
        self.placements = list(placements or [])


class GeneratedScheduleItem(object):
    def __init__(
        self,
        template_unique_id,
        template_name,
        schedule_unique_id,
        schedule_name,
        source_housing_value="",
    ):
        self.template_unique_id = template_unique_id or ""
        self.template_name = template_name or ""
        self.schedule_unique_id = schedule_unique_id or ""
        self.schedule_name = schedule_name or ""
        self.source_housing_value = source_housing_value or ""


class ScheduleBatchResult(object):
    def __init__(self, housing_key, items=None, warnings=None):
        self.housing_key = housing_key or ""
        self.items = list(items or [])
        self.warnings = list(warnings or [])


class ScheduleService(object):
    """Service Revit de l'Étape 04A."""

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document

    def list_templates(self, descriptor):
        if descriptor is None:
            return []

        from Autodesk.Revit.DB import FilteredElementCollector, ViewDuplicateOption, ViewSchedule

        result = []
        schedules = (FilteredElementCollector(self.document)
                     .OfClass(ViewSchedule)
                     .WhereElementIsNotElementType()
                     .ToElements())

        for schedule in schedules:
            if bool(getattr(schedule, "IsTemplate", False)):
                continue
            name = str(getattr(schedule, "Name", "") or "")
            if name.startswith("PDV_"):
                continue
            try:
                if not schedule.CanViewBeDuplicated(ViewDuplicateOption.Duplicate):
                    continue
            except Exception:
                continue
            try:
                field_id = self._find_housing_field_id(schedule.Definition, descriptor)
            except Exception:
                field_id = None
            if field_id is None:
                continue
            result.append(ScheduleTemplateCandidate(
                unique_id=str(getattr(schedule, "UniqueId", "") or ""),
                name=name,
            ))

        return sorted(result, key=lambda item: item.name.lower())

    def create_pair(self, housing, descriptor, interior_template_unique_id, exterior_template_unique_id):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        if descriptor is None:
            raise ValueError("Paramètre logement manquant.")

        interior_template = self._get_schedule(interior_template_unique_id)
        exterior_template = self._get_schedule(exterior_template_unique_id)
        interior_name = schedule_name(housing.key, "INT")
        exterior_name = schedule_name(housing.key, "EXT")

        self._ensure_name_available(interior_name)
        self._ensure_name_available(exterior_name)
        self._validate_template(interior_template, descriptor)
        self._validate_template(exterior_template, descriptor)

        from Autodesk.Revit.DB import ViewDuplicateOption

        interior = None
        exterior = None
        with RevitTransaction(self.document, "Plans de vente - Nomenclatures {}".format(housing.key)):
            interior_id = interior_template.Duplicate(ViewDuplicateOption.Duplicate)
            interior = self.document.GetElement(interior_id)
            if interior is None:
                raise RuntimeError("Revit n'a pas retourné la nomenclature intérieure dupliquée.")
            interior.Name = interior_name
            self._apply_housing_filter(interior, descriptor, housing.key)

            exterior_id = exterior_template.Duplicate(ViewDuplicateOption.Duplicate)
            exterior = self.document.GetElement(exterior_id)
            if exterior is None:
                raise RuntimeError("Revit n'a pas retourné la nomenclature extérieure dupliquée.")
            exterior.Name = exterior_name
            self._apply_housing_filter(exterior, descriptor, housing.key)

        return SchedulePairResult(
            housing_key=housing.key,
            interior_name=interior.Name,
            interior_unique_id=str(getattr(interior, "UniqueId", "") or ""),
            exterior_name=exterior.Name,
            exterior_unique_id=str(getattr(exterior, "UniqueId", "") or ""),
            placements=[
                placement_artifact(
                    housing.key,
                    PlacementRole.INTERIOR_SCHEDULE,
                    str(getattr(interior, "UniqueId", "") or ""),
                    interior.Name,
                ),
                placement_artifact(
                    housing.key,
                    PlacementRole.EXTERIOR_SCHEDULE,
                    str(getattr(exterior, "UniqueId", "") or ""),
                    exterior.Name,
                ),
            ],
        )

    def duplicate_templates_for_housing(
        self,
        housing,
        descriptor,
        template_schedule_unique_ids,
    ):
        """Duplique N nomenclatures modèles et remplace leur filtre logement."""
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        if descriptor is None:
            raise ValueError("Paramètre logement manquant.")

        template_ids = []
        for unique_id in template_schedule_unique_ids or []:
            value = str(unique_id or "")
            if value and value not in template_ids:
                template_ids.append(value)

        if not template_ids:
            return ScheduleBatchResult(housing.key, [])

        templates = [self._get_schedule(unique_id) for unique_id in template_ids]
        for schedule in templates:
            self._validate_template(schedule, descriptor)

        from Autodesk.Revit.DB import ViewDuplicateOption

        items = []
        warnings = []
        reserved_names = set()

        with RevitTransaction(
            self.document,
            "Plans de vente - Nomenclatures {}".format(housing.key),
        ):
            for index, template in enumerate(templates, 1):
                source_value = self._housing_filter_value(
                    template,
                    descriptor,
                )
                target_name = self._automatic_schedule_name(
                    template,
                    housing.key,
                    source_value,
                    index,
                    reserved_names,
                )

                new_id = template.Duplicate(ViewDuplicateOption.Duplicate)
                created = self.document.GetElement(new_id)
                if created is None:
                    raise RuntimeError(
                        "Revit n'a pas retourné la nomenclature dupliquée « {} ».".format(
                            getattr(template, "Name", "")
                        )
                    )

                created.Name = target_name
                self._apply_housing_filter(
                    created,
                    descriptor,
                    housing.key,
                )
                reserved_names.add(target_name)

                items.append(
                    GeneratedScheduleItem(
                        template_unique_id=str(
                            getattr(template, "UniqueId", "") or ""
                        ),
                        template_name=str(
                            getattr(template, "Name", "") or ""
                        ),
                        schedule_unique_id=str(
                            getattr(created, "UniqueId", "") or ""
                        ),
                        schedule_name=str(
                            getattr(created, "Name", "") or ""
                        ),
                        source_housing_value=source_value,
                    )
                )

        return ScheduleBatchResult(
            housing_key=housing.key,
            items=items,
            warnings=warnings,
        )

    def _housing_filter_value(self, schedule, descriptor):
        """Lit la valeur logement du modèle quand elle est accessible."""
        definition = schedule.Definition
        field_id = self._find_housing_field_id(definition, descriptor)
        if field_id is None:
            return ""

        for index in range(definition.GetFilterCount()):
            current = definition.GetFilter(index)
            if not self._same_schedule_field_id(current.FieldId, field_id):
                continue

            for getter_name in (
                "GetStringValue",
                "GetIntegerValue",
                "GetDoubleValue",
            ):
                getter = getattr(current, getter_name, None)
                if getter is None:
                    continue
                try:
                    value = getter()
                except Exception:
                    continue
                if value is None:
                    continue
                text = str(value).strip()
                if text:
                    return text
        return ""

    def _automatic_schedule_name(
        self,
        template,
        housing_key,
        source_housing_value,
        index,
        reserved_names,
    ):
        template_name = str(getattr(template, "Name", "") or "").strip()
        target_key = str(housing_key or "").strip()

        if source_housing_value and source_housing_value in template_name:
            base_name = template_name.replace(
                source_housing_value,
                target_key,
            )
        elif template_name.startswith("PDV_"):
            base_name = "PDV_{}_{}".format(
                target_key,
                self._schedule_suffix(template_name, index),
            )
        else:
            base_name = "{} - {}".format(
                template_name or "Nomenclature",
                target_key,
            )

        existing = self._existing_schedule_names()
        candidate = base_name
        suffix = 2
        while candidate in existing or candidate in reserved_names:
            candidate = "{} ({})".format(base_name, suffix)
            suffix += 1
        return candidate

    @staticmethod
    def _schedule_suffix(template_name, index):
        parts = [part for part in str(template_name or "").split("_") if part]
        if len(parts) >= 3:
            return "_".join(parts[2:])
        return "NOM{:02d}".format(int(index))

    def _existing_schedule_names(self):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSchedule

        return set(
            str(getattr(schedule, "Name", "") or "")
            for schedule in (
                FilteredElementCollector(self.document)
                .OfClass(ViewSchedule)
                .WhereElementIsNotElementType()
                .ToElements()
            )
        )

    def _get_schedule(self, unique_id):
        if not unique_id:
            raise ValueError("Sélectionnez une nomenclature modèle.")
        schedule = self.document.GetElement(unique_id)
        if schedule is None or not hasattr(schedule, "Definition"):
            raise ValueError("La nomenclature modèle sélectionnée n'existe plus.")
        return schedule

    def _validate_template(self, schedule, descriptor):
        field_id = self._find_housing_field_id(schedule.Definition, descriptor)
        if field_id is None:
            raise ValueError(
                "La nomenclature modèle « {} » ne contient pas le champ « {} ». "
                "Ajoutez ce paramètre à la nomenclature modèle avant de continuer.".format(
                    getattr(schedule, "Name", ""), descriptor.name))
        can_filter = getattr(schedule.Definition, "CanFilterByValue", None)
        if can_filter is not None and not bool(can_filter(field_id)):
            raise ValueError(
                "Le champ « {} » de la nomenclature « {} » ne peut pas être utilisé comme filtre de valeur.".format(
                    descriptor.name, getattr(schedule, "Name", "")))
        return field_id

    def _apply_housing_filter(self, schedule, descriptor, housing_key):
        from Autodesk.Revit.DB import ScheduleFilter, ScheduleFilterType

        definition = schedule.Definition
        field_id = self._validate_template(schedule, descriptor)
        housing_filter = ScheduleFilter(field_id, ScheduleFilterType.Equal, str(housing_key))

        matching = []
        for index in range(definition.GetFilterCount()):
            current = definition.GetFilter(index)
            if self._same_schedule_field_id(current.FieldId, field_id):
                matching.append(index)

        if matching:
            definition.SetFilter(matching[0], housing_filter)
            for index in reversed(matching[1:]):
                definition.RemoveFilter(index)
        else:
            definition.AddFilter(housing_filter)

    def _find_housing_field_id(self, definition, descriptor):
        for field_id in definition.GetFieldOrder():
            field = definition.GetField(field_id)
            if self._field_matches_descriptor(field, descriptor):
                return field_id
        return None

    def _field_matches_descriptor(self, field, descriptor):
        kind = getattr(descriptor, "identity_kind", "")
        expected = str(getattr(descriptor, "identity_value", "") or "")
        try:
            schedulable = field.GetSchedulableField()
            parameter_id = schedulable.ParameterId
        except Exception:
            return False

        if kind == "SHARED_GUID":
            element = self.document.GetElement(parameter_id)
            guid = getattr(element, "GuidValue", None) if element is not None else None
            return guid is not None and str(guid).lower() == expected.lower()

        if kind == "BUILT_IN":
            try:
                from Autodesk.Revit.DB import BuiltInParameter, ParameterUtils
                from System import Enum
                if not ParameterUtils.IsBuiltInParameter(parameter_id):
                    return False
                built_in = Enum.ToObject(BuiltInParameter, self._element_id_value(parameter_id))
                type_id = ParameterUtils.GetParameterTypeId(built_in)
                return str(type_id.TypeId) == expected
            except Exception:
                return False

        if kind == "DEFINITION":
            element = self.document.GetElement(parameter_id)
            getter = getattr(element, "GetDefinition", None) if element is not None else None
            if getter is None:
                return False
            try:
                definition = getter()
                type_id = definition.GetTypeId()
                return str(type_id.TypeId) == expected
            except Exception:
                return False

        try:
            return str(field.GetName()).lower() == str(descriptor.name).lower()
        except Exception:
            return False

    def _ensure_name_available(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSchedule
        for schedule in (FilteredElementCollector(self.document)
                         .OfClass(ViewSchedule)
                         .WhereElementIsNotElementType()
                         .ToElements()):
            if str(getattr(schedule, "Name", "") or "") == target_name:
                raise ValueError(
                    "La nomenclature « {} » existe déjà. La mise à jour des éléments existants sera traitée à l'Étape 08.".format(
                        target_name))

    @staticmethod
    def _same_schedule_field_id(left, right):
        try:
            return int(left.IntegerValue) == int(right.IntegerValue)
        except Exception:
            return left == right

    @staticmethod
    def _element_id_value(element_id):
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        return int(element_id.IntegerValue)
