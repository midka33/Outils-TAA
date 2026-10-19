# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Découverte des vues plan pouvant servir de vues principales au prototype."""


class PlanViewCandidate(object):
    def __init__(self, unique_id, name, level_name, scale=0):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.level_name = level_name or ""
        self.scale = int(scale or 0)

    @property
    def label(self):
        scale_label = "1:{}".format(self.scale) if self.scale else "échelle inconnue"
        return "{} — {} — {}".format(self.name, self.level_name, scale_label)


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

            view_name = str(getattr(view, "Name", "") or "")
            if view_name.startswith("PDV MASTER - "):
                # Les vues principales techniques générées ne doivent pas devenir
                # à leur tour des sources de nouveaux groupes.
                continue

            try:
                if not view.CanViewBeDuplicated(duplicate_option.AsDependent):
                    continue
            except Exception:
                continue

            result.append(
                PlanViewCandidate(
                    unique_id=str(getattr(view, "UniqueId", "") or ""),
                    name=view_name,
                    level_name=current_level_name,
                    scale=int(getattr(view, "Scale", 0) or 0),
                )
            )

        return sorted(result, key=lambda item: item.name.lower())

    def ensure_primary_floor_plan(self, level_name):
        """Retourne une source PDV dédiée, sans réutiliser une vue métier de SITE.

        Les logements liés doivent être générés depuis une vue technique neutre.
        Réutiliser une vue SITE existante peut hériter de réglages de visibilité,
        de phase, de filtre ou de lien qui masquent le bâtiment, notamment au RDC.
        """
        technical_base_name = "PDV SOURCE - {}".format(level_name)
        existing = self.list_primary_floor_plans(level_name)
        technical_existing = [
            item for item in existing
            if item.name == technical_base_name
            or item.name.startswith(technical_base_name + " (")
        ]
        if technical_existing:
            technical_existing.sort(
                key=lambda item: (
                    0 if item.name == technical_base_name else 1,
                    item.name.lower(),
                )
            )
            return [technical_existing[0]]

        from Autodesk.Revit.DB import (
            FilteredElementCollector,
            Level,
            Transaction,
            View,
            ViewFamily,
            ViewFamilyType,
            ViewPlan,
        )

        levels = [
            level for level in (
                FilteredElementCollector(self.document)
                .OfClass(Level)
                .ToElements()
            )
            if str(getattr(level, "Name", "") or "") == str(level_name or "")
        ]
        if len(levels) != 1:
            raise RuntimeError(
                "Impossible de résoudre le niveau SITE « {} » pour créer la vue plan technique.".format(
                    level_name
                )
            )
        level = levels[0]

        view_types = [
            view_type for view_type in (
                FilteredElementCollector(self.document)
                .OfClass(ViewFamilyType)
                .WhereElementIsElementType()
                .ToElements()
            )
            if getattr(view_type, "ViewFamily", None) == ViewFamily.FloorPlan
        ]
        if not view_types:
            raise RuntimeError(
                "Aucun type de vue Plan d'étage n'est disponible dans SITE."
            )
        view_types.sort(
            key=lambda item: str(getattr(item, "Name", "") or "").lower()
        )
        view_type = view_types[0]

        existing_names = set(
            str(getattr(view, "Name", "") or "")
            for view in (
                FilteredElementCollector(self.document)
                .OfClass(View)
                .WhereElementIsNotElementType()
                .ToElements()
            )
        )
        base_name = technical_base_name
        view_name = base_name
        index = 2
        while view_name in existing_names:
            view_name = "{} ({})".format(base_name, index)
            index += 1

        def create_view():
            view = ViewPlan.Create(
                self.document,
                view_type.Id,
                level.Id,
            )
            if view is None:
                raise RuntimeError(
                    "Revit n'a pas retourné la vue plan technique créée."
                )
            view.Name = view_name
            return view

        if bool(getattr(self.document, "IsModifiable", False)):
            create_view()
        else:
            transaction = Transaction(
                self.document,
                "Plans de vente - Création vue plan SITE",
            )
            transaction.Start()
            try:
                create_view()
                transaction.Commit()
            except Exception:
                try:
                    transaction.RollBack()
                except Exception:
                    pass
                raise

        result = [
            item for item in self.list_primary_floor_plans(level_name)
            if item.name == view_name
        ]
        if not result:
            raise RuntimeError(
                "La vue plan SITE dédiée a été créée mais n'est pas exploitable "
                "comme source Plans de vente."
            )
        return result

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
