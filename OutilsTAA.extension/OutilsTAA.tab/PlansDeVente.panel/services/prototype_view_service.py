# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Prototype contrôlé : vue dépendante + contour logement optimisé."""

from common.transaction import RevitTransaction
from plans_vente.placement_contract import PlacementRole, placement_artifact
from plans_vente.view_grouping import master_view_name, normalize_scale


class PrototypeViewResult(object):
    def __init__(
        self,
        view_name,
        view_unique_id,
        source_view_name,
        housing_key,
        crop_mode="",
        warning="",
        master_view_name="",
        target_scale=0,
        master_created=False,
        placement=None,
    ):
        self.view_name = view_name or ""
        self.view_unique_id = view_unique_id or ""
        self.source_view_name = source_view_name or ""
        self.housing_key = housing_key or ""
        self.crop_mode = crop_mode or ""
        self.warning = warning or ""
        self.master_view_name = master_view_name or ""
        self.target_scale = int(target_scale or 0)
        self.master_created = bool(master_created)
        self.placement = placement


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

    def create_dependent_crop_view(
        self,
        housing,
        source_view_unique_id,
        margin_mm=500.0,
        target_scale=50,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        level_name = self._single_level_name(housing)
        if not source_view_unique_id:
            raise ValueError("Sélectionnez une vue source.")
        target_scale = normalize_scale(target_scale)

        source_view = self.document.GetElement(source_view_unique_id)
        if source_view is None:
            raise ValueError("La vue source n'existe plus dans le projet.")

        source_level = getattr(getattr(source_view, "GenLevel", None), "Name", None)
        if source_level != level_name:
            raise ValueError(
                "La vue source doit appartenir au niveau « {} ».".format(level_name)
            )

        from Autodesk.Revit.DB import ViewDuplicateOption

        if not source_view.CanViewBeDuplicated(ViewDuplicateOption.Duplicate):
            raise ValueError(
                "Cette vue ne peut pas être dupliquée pour créer une vue principale PDV."
            )

        crop_result = self.crop_geometry_service.build_optimized_crop(
            housing.room_unique_ids,
            source_view,
            margin_mm,
        )

        created_view = None
        master_view = None
        master_created = False
        with RevitTransaction(
            self.document,
            "Plans de vente - Prototype contour optimisé",
        ):
            master_view, master_created = self._ensure_master_view(
                source_view,
                level_name,
                target_scale,
            )

            if not master_view.CanViewBeDuplicated(ViewDuplicateOption.AsDependent):
                raise ValueError(
                    "La vue principale PDV ne peut pas être dupliquée comme vue dépendante."
                )

            new_view_id = master_view.Duplicate(ViewDuplicateOption.AsDependent)
            created_view = self.document.GetElement(new_view_id)
            if created_view is None:
                raise RuntimeError("Revit n'a pas retourné la vue dépendante créée.")

            created_view.Name = self._unique_view_name(
                "PDV PROTO - {} - {} - 1-{}".format(
                    housing.key,
                    level_name,
                    target_scale,
                )
            )
            self.crop_geometry_service.apply_to_view(
                created_view,
                crop_result,
            )

            primary_id = created_view.GetPrimaryViewId()
            if primary_id != master_view.Id:
                raise RuntimeError(
                    "La vue créée n'est pas dépendante de la vue principale PDV attendue."
                )

        return PrototypeViewResult(
            view_name=created_view.Name,
            view_unique_id=str(getattr(created_view, "UniqueId", "") or ""),
            source_view_name=str(getattr(source_view, "Name", "") or ""),
            housing_key=housing.key,
            crop_mode=crop_result.mode,
            warning=crop_result.warning,
            master_view_name=str(getattr(master_view, "Name", "") or ""),
            target_scale=target_scale,
            master_created=master_created,
            placement=placement_artifact(
                housing.key,
                PlacementRole.MAIN_VIEW,
                str(getattr(created_view, "UniqueId", "") or ""),
                created_view.Name,
            ),
        )


    def _ensure_master_view(self, source_view, level_name, target_scale):
        """Réutilise ou crée la vue principale technique du groupe d'échelle."""
        from Autodesk.Revit.DB import (
            ElementId,
            FilteredElementCollector,
            ViewDuplicateOption,
            ViewPlan,
            ViewType,
        )

        expected_name = master_view_name(
            level_name,
            target_scale,
            getattr(source_view, "UniqueId", ""),
        )

        for view in (
            FilteredElementCollector(self.document)
            .OfClass(ViewPlan)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if str(getattr(view, "Name", "") or "") != expected_name:
                continue

            if bool(getattr(view, "IsTemplate", False)):
                raise RuntimeError(
                    "Le nom de la vue principale PDV est déjà utilisé par un gabarit."
                )
            if getattr(view, "ViewType", None) != ViewType.FloorPlan:
                raise RuntimeError(
                    "Le nom de la vue principale PDV est déjà utilisé par une vue incompatible."
                )

            level = getattr(view, "GenLevel", None)
            if getattr(level, "Name", None) != level_name:
                raise RuntimeError(
                    "La vue principale PDV existante n'appartient plus au niveau attendu."
                )

            if view.GetPrimaryViewId() != ElementId.InvalidElementId:
                raise RuntimeError(
                    "La vue principale PDV existante est devenue une vue dépendante."
                )

            if int(getattr(view, "Scale", 0) or 0) != target_scale:
                raise RuntimeError(
                    "La vue principale PDV existante n'a plus l'échelle 1:{}.".format(
                        target_scale
                    )
                )
            return view, False

        new_master_id = source_view.Duplicate(ViewDuplicateOption.Duplicate)
        master_view = self.document.GetElement(new_master_id)
        if master_view is None:
            raise RuntimeError(
                "Revit n'a pas retourné la vue principale PDV créée."
            )

        master_view.Name = expected_name
        try:
            master_view.Scale = target_scale
        except Exception as error:
            raise RuntimeError(
                "Impossible d'appliquer l'échelle 1:{} à la vue principale PDV : {}".format(
                    target_scale,
                    error,
                )
            )

        if int(getattr(master_view, "Scale", 0) or 0) != target_scale:
            raise RuntimeError(
                "Revit n'a pas conservé l'échelle 1:{} sur la vue principale PDV.".format(
                    target_scale
                )
            )
        return master_view, True

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
