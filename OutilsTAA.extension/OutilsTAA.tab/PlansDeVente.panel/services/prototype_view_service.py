# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Prototype contrôlé : vue dépendante + crop logement aligné à la vue."""

from common.transaction import RevitTransaction


class PrototypeViewResult(object):
    def __init__(self, view_name, view_unique_id, source_view_name, housing_key):
        self.view_name = view_name or ""
        self.view_unique_id = view_unique_id or ""
        self.source_view_name = source_view_name or ""
        self.housing_key = housing_key or ""


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

    def create_dependent_crop_view(self, housing, source_view_unique_id, margin_mm=500.0):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        level_name = self._single_level_name(housing)
        if not source_view_unique_id:
            raise ValueError("Sélectionnez une vue source.")

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

        world_corners = self.crop_geometry_service.build_view_aligned_corners(
            housing.room_unique_ids,
            source_view,
            margin_mm,
        )

        created_view = None
        with RevitTransaction(
            self.document,
            "Plans de vente - Prototype vue dépendante",
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
                world_corners,
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
        )

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
