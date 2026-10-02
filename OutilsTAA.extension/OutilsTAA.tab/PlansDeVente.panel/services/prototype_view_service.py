# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Prototype contrôlé : vue dépendante + contour logement optimisé."""

from common.transaction import RevitTransaction


class PrototypeViewResult(object):
    def __init__(
        self,
        view_name,
        view_unique_id,
        source_view_name,
        housing_key,
        crop_mode="",
        warning="",
    ):
        self.view_name = view_name or ""
        self.view_unique_id = view_unique_id or ""
        self.source_view_name = source_view_name or ""
        self.housing_key = housing_key or ""
        self.crop_mode = crop_mode or ""
        self.warning = warning or ""


class PeripheralWallTypeCandidate(object):
    def __init__(
        self,
        unique_id,
        name,
        family_name="",
        source_label="Projet",
    ):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.family_name = family_name or ""
        self.source_label = source_label or "Projet"

        if self.family_name and self.family_name != self.name:
            type_label = "{} — {}".format(
                self.family_name,
                self.name,
            )
        else:
            type_label = self.name

        self.label = "[{}] {}".format(
            self.source_label,
            type_label,
        )


class PrototypeViewService(object):
    def __init__(self, document, plan_view_service, crop_geometry_service):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.plan_view_service = plan_view_service
        self.crop_geometry_service = crop_geometry_service

    def source_views_for_housing(self, housing):
        level_name = self._single_level_name(housing)
        return self.plan_view_service.list_primary_floor_plans(level_name)

    def list_peripheral_wall_types(self):
        from Autodesk.Revit.DB import (
            FilteredElementCollector,
            RevitLinkInstance,
            Wall,
        )

        candidates = {}

        self._append_wall_type_candidates(
            candidates,
            source_document=self.document,
            source_prefix="HOST",
            source_label="Projet",
            link_instance_unique_id="",
            wall_class=Wall,
            collector_class=FilteredElementCollector,
        )

        links = (
            FilteredElementCollector(self.document)
            .OfClass(RevitLinkInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        for link_instance in links:
            try:
                link_document = link_instance.GetLinkDocument()
            except Exception:
                link_document = None
            if link_document is None:
                continue

            link_uid = str(
                getattr(link_instance, "UniqueId", "") or ""
            )
            if not link_uid:
                continue

            link_name = str(
                getattr(link_instance, "Name", "") or ""
            )
            if not link_name:
                link_name = str(
                    getattr(link_document, "Title", "") or "Lien Revit"
                )

            self._append_wall_type_candidates(
                candidates,
                source_document=link_document,
                source_prefix="LINK",
                source_label="Lien : {}".format(link_name),
                link_instance_unique_id=link_uid,
                wall_class=Wall,
                collector_class=FilteredElementCollector,
            )

        values = list(candidates.values())
        values.sort(key=lambda item: item.label.lower())
        return values

    def _append_wall_type_candidates(
        self,
        candidates,
        source_document,
        source_prefix,
        source_label,
        link_instance_unique_id,
        wall_class,
        collector_class,
    ):
        walls = (
            collector_class(source_document)
            .OfClass(wall_class)
            .WhereElementIsNotElementType()
            .ToElements()
        )

        for wall in walls:
            wall_type = getattr(wall, "WallType", None)
            if wall_type is None:
                continue

            wall_type_uid = str(
                getattr(wall_type, "UniqueId", "") or ""
            )
            if not wall_type_uid:
                continue

            if source_prefix == "LINK":
                selection_key = "LINK|{}|{}".format(
                    link_instance_unique_id,
                    wall_type_uid,
                )
            else:
                selection_key = "HOST|{}".format(wall_type_uid)

            if selection_key in candidates:
                continue

            name = self._element_type_name(wall_type)
            if not name:
                continue

            family_name = str(
                getattr(wall_type, "FamilyName", "") or ""
            )
            candidates[selection_key] = PeripheralWallTypeCandidate(
                selection_key,
                name,
                family_name,
                source_label,
            )

    def create_dependent_crop_view(
        self,
        housing,
        source_view_unique_id,
        margin_mm=500.0,
        peripheral_wall_type_unique_id=None,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        level_name = self._single_level_name(housing)
        if not source_view_unique_id:
            raise ValueError("Sélectionnez une vue source.")
        if not peripheral_wall_type_unique_id:
            raise ValueError("Sélectionnez le type de mur périphérique.")

        source_view = self.document.GetElement(source_view_unique_id)
        if source_view is None:
            raise ValueError("La vue source n'existe plus dans le projet.")

        source_level = getattr(getattr(source_view, "GenLevel", None), "Name", None)
        if source_level != level_name:
            raise ValueError(
                "La vue source doit appartenir au niveau « {} ».".format(level_name)
            )

        from Autodesk.Revit.DB import ViewDuplicateOption

        if not source_view.CanViewBeDuplicated(ViewDuplicateOption.AsDependent):
            raise ValueError("Cette vue ne peut pas être dupliquée comme vue dépendante.")

        crop_result = self.crop_geometry_service.build_optimized_crop(
            housing.room_unique_ids,
            source_view,
            margin_mm,
            peripheral_wall_type_unique_id,
        )

        created_view = None
        with RevitTransaction(
            self.document,
            "Plans de vente - Prototype contour optimisé",
        ):
            new_view_id = source_view.Duplicate(ViewDuplicateOption.AsDependent)
            created_view = self.document.GetElement(new_view_id)
            if created_view is None:
                raise RuntimeError("Revit n'a pas retourné la vue dépendante créée.")

            created_view.Name = self._unique_view_name(
                "PDV PROTO - {} - {}".format(housing.key, level_name)
            )
            self.crop_geometry_service.apply_to_view(
                created_view,
                crop_result,
            )

            primary_id = created_view.GetPrimaryViewId()
            if primary_id != source_view.Id:
                raise RuntimeError(
                    "La vue créée n'est pas dépendante de la vue source attendue."
                )

        return PrototypeViewResult(
            view_name=created_view.Name,
            view_unique_id=str(getattr(created_view, "UniqueId", "") or ""),
            source_view_name=str(getattr(source_view, "Name", "") or ""),
            housing_key=housing.key,
            crop_mode=crop_result.mode,
            warning=crop_result.warning,
        )

    @staticmethod
    def _element_type_name(element_type):
        try:
            value = getattr(element_type, "Name", None)
            if value:
                return str(value)
        except Exception:
            pass

        try:
            from Autodesk.Revit.DB import BuiltInParameter
            parameter = element_type.get_Parameter(
                BuiltInParameter.SYMBOL_NAME_PARAM
            )
            if parameter is not None:
                value = parameter.AsString()
                if value:
                    return str(value)
        except Exception:
            pass
        return ""

    @staticmethod
    def _single_level_name(housing):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        levels = list(housing.level_names or [])
        if len(levels) != 1:
            raise ValueError(
                "Le prototype vues dépendantes est limité aux logements sur un seul "
                "niveau. Le logement « {} » utilise : {}.".format(
                    housing.key,
                    ", ".join(levels) if levels else "aucun niveau",
                )
            )
        return levels[0]

    def _unique_view_name(self, base_name):
        existing = set()
        try:
            from Autodesk.Revit.DB import FilteredElementCollector, View
            for view in (
                FilteredElementCollector(self.document)
                .OfClass(View)
                .WhereElementIsNotElementType()
                .ToElements()
            ):
                name = getattr(view, "Name", None)
                if name:
                    existing.add(str(name))
        except Exception:
            existing = set()

        if base_name not in existing:
            return base_name

        index = 2
        while True:
            candidate = "{} ({})".format(base_name, index)
            if candidate not in existing:
                return candidate
            index += 1
