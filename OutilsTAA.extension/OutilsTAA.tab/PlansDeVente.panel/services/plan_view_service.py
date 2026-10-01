# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Découverte des vues plan pouvant servir de vues principales au prototype."""


class PlanViewCandidate(object):
    def __init__(self, unique_id, name, level_name):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.level_name = level_name or ""

    @property
    def label(self):
        return "{} — {}".format(self.name, self.level_name)


class PlanViewService(object):
    def __init__(self, document, collector_factory=None):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self._collector_factory = collector_factory

    def list_primary_floor_plans(self, level_name):
        if not level_name:
            return []

        collector_factory, view_plan_type, view_type_enum, duplicate_option, element_id = (
            self._resolve_revit_dependencies()
        )

        collector = collector_factory(self.document).OfClass(view_plan_type)
        views = list(collector.WhereElementIsNotElementType().ToElements())
        result = []

        for view in views:
            if bool(getattr(view, "IsTemplate", False)):
                continue
            if getattr(view, "ViewType", None) != view_type_enum.FloorPlan:
                continue

            level = getattr(view, "GenLevel", None)
            current_level_name = getattr(level, "Name", None) if level is not None else None
            if current_level_name != level_name:
                continue

            try:
                if view.GetPrimaryViewId() != element_id.InvalidElementId:
                    continue
            except Exception:
                continue

            try:
                if not view.CanViewBeDuplicated(duplicate_option.AsDependent):
                    continue
            except Exception:
                continue

            result.append(
                PlanViewCandidate(
                    unique_id=str(getattr(view, "UniqueId", "") or ""),
                    name=str(getattr(view, "Name", "") or ""),
                    level_name=current_level_name,
                )
            )

        return sorted(result, key=lambda item: item.name.lower())

    def _resolve_revit_dependencies(self):
        from Autodesk.Revit.DB import (
            ElementId,
            FilteredElementCollector,
            ViewDuplicateOption,
            ViewPlan,
            ViewType,
        )
        return (
            self._collector_factory or FilteredElementCollector,
            ViewPlan,
            ViewType,
            ViewDuplicateOption,
            ElementId,
        )
