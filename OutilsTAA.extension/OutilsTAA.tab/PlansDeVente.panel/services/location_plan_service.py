# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Création du plan de repérage et surbrillance du logement."""

from common.transaction import RevitTransaction
from plans_vente.location_naming import location_view_name


class LocationTemplateCandidate(object):
    def __init__(self, unique_id, name):
        self.unique_id = unique_id or ""
        self.name = name or ""

    @property
    def label(self):
        return self.name


class FilledRegionTypeCandidate(object):
    def __init__(self, unique_id, name):
        self.unique_id = unique_id or ""
        self.name = name or ""

    @property
    def label(self):
        return self.name


class LocationPlanResult(object):
    def __init__(self, housing_key, view_name, view_unique_id, region_count, template_name, fill_type_name):
        self.housing_key = housing_key or ""
        self.view_name = view_name or ""
        self.view_unique_id = view_unique_id or ""
        self.region_count = int(region_count or 0)
        self.template_name = template_name or ""
        self.fill_type_name = fill_type_name or ""


class LocationPlanService(object):
    """Service Revit de l'Étape 04B."""

    def __init__(self, document, plan_view_service):
        if document is None:
            raise ValueError("Document Revit manquant.")
        if plan_view_service is None:
            raise ValueError("Service de vues plan manquant.")
        self.document = document
        self.plan_view_service = plan_view_service

    def source_views_for_housing(self, housing):
        level_name = self._single_level_name(housing)
        return [
            item for item in self.plan_view_service.list_primary_floor_plans(level_name)
            if not item.name.startswith("PDV_")
        ]

    def list_view_templates(self):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewPlan, ViewType

        result = []
        for view in (FilteredElementCollector(self.document)
                     .OfClass(ViewPlan)
                     .WhereElementIsNotElementType()
                     .ToElements()):
            if not bool(getattr(view, "IsTemplate", False)):
                continue
            if getattr(view, "ViewType", None) != ViewType.FloorPlan:
                continue
            result.append(LocationTemplateCandidate(
                unique_id=str(getattr(view, "UniqueId", "") or ""),
                name=str(getattr(view, "Name", "") or ""),
            ))
        return sorted(result, key=lambda item: item.name.lower())

    def list_filled_region_types(self):
        from Autodesk.Revit.DB import FilledRegionType, FilteredElementCollector

        result = []
        for region_type in (FilteredElementCollector(self.document)
                            .OfClass(FilledRegionType)
                            .WhereElementIsElementType()
                            .ToElements()):
            result.append(FilledRegionTypeCandidate(
                unique_id=str(getattr(region_type, "UniqueId", "") or ""),
                name=self._element_type_name(region_type),
            ))
        return sorted(result, key=lambda item: item.name.lower())

    def create_location_plan(self, housing, source_view_unique_id, filled_region_type_unique_id, template_unique_id=None):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        level_name = self._single_level_name(housing)
        source_view = self._get_element(source_view_unique_id, "Sélectionnez une vue source de repérage.")
        region_type = self._get_element(filled_region_type_unique_id, "Sélectionnez un type de zone remplie.")
        template = self.document.GetElement(template_unique_id) if template_unique_id else None

        source_level = getattr(getattr(source_view, "GenLevel", None), "Name", None)
        if source_level != level_name:
            raise ValueError("La vue source de repérage doit appartenir au niveau « {} ».".format(level_name))

        from Autodesk.Revit.DB import ViewDuplicateOption
        if not source_view.CanViewBeDuplicated(ViewDuplicateOption.Duplicate):
            raise ValueError("Cette vue ne peut pas être dupliquée pour le plan de repérage.")

        target_name = location_view_name(housing.key)
        self._ensure_view_name_available(target_name)

        if template is not None:
            if not bool(getattr(template, "IsTemplate", False)):
                raise ValueError("Le gabarit de repérage sélectionné n'est plus un gabarit de vue.")

        created_view = None
        region_count = 0
        with RevitTransaction(self.document, "Plans de vente - Repérage {}".format(housing.key)):
            new_view_id = source_view.Duplicate(ViewDuplicateOption.Duplicate)
            created_view = self.document.GetElement(new_view_id)
            if created_view is None:
                raise RuntimeError("Revit n'a pas retourné la vue de repérage dupliquée.")
            created_view.Name = target_name

            if template is not None:
                try:
                    created_view.ViewTemplateId = template.Id
                except Exception as error:
                    raise ValueError("Impossible d'appliquer le gabarit de repérage : {}".format(error))

            for room_unique_id in housing.room_unique_ids:
                room = self.document.GetElement(room_unique_id)
                if room is None:
                    raise ValueError("Une pièce du logement n'existe plus dans le projet.")
                boundaries = self._room_boundaries(room)
                if boundaries.Count == 0:
                    raise ValueError(
                        "La pièce « {} » ne possède pas de contour exploitable pour le repérage.".format(
                            getattr(room, "Number", "") or getattr(room, "Name", "") or room_unique_id))
                self._create_filled_region(created_view, region_type, boundaries)
                region_count += 1

        return LocationPlanResult(
            housing_key=housing.key,
            view_name=created_view.Name,
            view_unique_id=str(getattr(created_view, "UniqueId", "") or ""),
            region_count=region_count,
            template_name=str(getattr(template, "Name", "") or "") if template is not None else "Conserver la vue source",
            fill_type_name=self._element_type_name(region_type),
        )

    def _room_boundaries(self, room):
        from Autodesk.Revit.DB import CurveLoop, SpatialElementBoundaryLocation, SpatialElementBoundaryOptions
        from System.Collections.Generic import List

        options = SpatialElementBoundaryOptions()
        options.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
        loops = List[CurveLoop]()

        boundary_sets = room.GetBoundarySegments(options)
        for segment_loop in boundary_sets or []:
            curve_loop = CurveLoop()
            count = 0
            for segment in segment_loop or []:
                curve = segment.GetCurve()
                if curve is None:
                    continue
                curve_loop.Append(curve)
                count += 1
            if count >= 3 and not curve_loop.IsOpen():
                loops.Add(curve_loop)
        return loops

    def _create_filled_region(self, view, region_type, boundaries):
        from Autodesk.Revit.DB import FilledRegion
        try:
            return FilledRegion.Create(self.document, region_type.Id, view.Id, boundaries)
        except Exception as error:
            raise ValueError("Revit n'a pas pu créer la zone remplie de repérage : {}".format(error))

    def _ensure_view_name_available(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, View
        for view in (FilteredElementCollector(self.document)
                     .OfClass(View)
                     .WhereElementIsNotElementType()
                     .ToElements()):
            if str(getattr(view, "Name", "") or "") == target_name:
                raise ValueError(
                    "La vue « {} » existe déjà. La mise à jour sera traitée à l'Étape 08.".format(target_name))

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    @staticmethod
    def _element_type_name(element_type):
        """Lit le nom d'un ElementType de façon fiable sous IronPython/pyRevit."""
        if element_type is None:
            return ""

        try:
            from Autodesk.Revit.DB import Element
            value = Element.Name.GetValue(element_type)
            if value:
                return str(value)
        except Exception:
            pass

        try:
            value = getattr(element_type, "Name", None)
            if value:
                return str(value)
        except Exception:
            pass

        return ""

    @staticmethod
    def _single_level_name(housing):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        levels = list(getattr(housing, "level_names", []) or [])
        if len(levels) != 1:
            raise ValueError(
                "Le prototype de repérage V1 attend un logement sur un seul niveau. Niveaux détectés : {}.".format(
                    ", ".join(levels) if levels else "aucun"))
        return levels[0]
