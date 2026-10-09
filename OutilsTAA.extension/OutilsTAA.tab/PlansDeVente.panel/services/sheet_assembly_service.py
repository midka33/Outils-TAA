# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Étapes 07B/07C — assemblage depuis modèle et ajustement de la vue logement."""

SHEET_ASSEMBLY_BUILD = "stage07c-reference-scale-collision-v6"

from common.transaction import RevitTransaction
from plans_vente.location_naming import location_view_name
from plans_vente.schedule_naming import schedule_name
from plans_vente.sheet_layout import default_sheet_anchors
from plans_vente.sheet_fit import (
    parse_allowed_scales,
    rectangles_overlap,
    scale_candidates_from_reference,
    segment_intersects_rectangle,
)


class TitleBlockTypeCandidate(object):
    def __init__(self, unique_id, family_name, type_name, element_id_value=None):
        self.unique_id = unique_id or ""
        self.family_name = family_name or ""
        self.type_name = type_name or ""
        self.element_id_value = element_id_value

    @property
    def label(self):
        if self.family_name and self.type_name:
            return "{} : {}".format(self.family_name, self.type_name)
        if self.type_name:
            return self.type_name
        if self.element_id_value is not None:
            return "Cartouche #{}".format(self.element_id_value)
        return "Cartouche"


class SheetTemplateCandidate(object):
    def __init__(
        self,
        unique_id,
        sheet_number,
        sheet_name,
        title_block_label,
    ):
        self.unique_id = unique_id or ""
        self.sheet_number = sheet_number or ""
        self.sheet_name = sheet_name or ""
        self.title_block_label = title_block_label or ""

    @property
    def label(self):
        prefix = self.sheet_number or "Sans numéro"
        if self.sheet_name:
            return "{} — {}".format(prefix, self.sheet_name)
        return prefix


class SheetPlacedViewCandidate(object):
    def __init__(self, viewport_unique_id, view_name):
        self.viewport_unique_id = viewport_unique_id or ""
        self.view_name = view_name or ""

    @property
    def label(self):
        return self.view_name or "Vue sans nom"


class SheetPlacedScheduleCandidate(object):
    def __init__(self, instance_unique_id, schedule_name):
        self.instance_unique_id = instance_unique_id or ""
        self.schedule_name = schedule_name or ""

    @property
    def label(self):
        return self.schedule_name or "Nomenclature sans nom"


class SheetTemplateInspection(object):
    def __init__(
        self,
        sheet_unique_id,
        sheet_label,
        is_valid,
        summary,
        title_block_label="",
        view_candidates=None,
        schedule_candidates=None,
    ):
        self.sheet_unique_id = sheet_unique_id or ""
        self.sheet_label = sheet_label or ""
        self.is_valid = bool(is_valid)
        self.summary = summary or ""
        self.title_block_label = title_block_label or ""
        self.view_candidates = list(view_candidates or [])
        self.schedule_candidates = list(schedule_candidates or [])


class _TemplateLayout(object):
    def __init__(
        self,
        sheet,
        title_block_type,
        points,
        viewport_type_ids,
        viewport_box_sizes=None,
        main_reference_scale=None,
    ):
        self.sheet = sheet
        self.title_block_type = title_block_type
        self.points = dict(points or {})
        self.viewport_type_ids = dict(viewport_type_ids or {})
        self.viewport_box_sizes = dict(viewport_box_sizes or {})
        self.main_reference_scale = main_reference_scale


class SheetAssemblyReadiness(object):
    def __init__(
        self,
        housing_key,
        main_view_name="",
        location_view_name_value="",
        interior_schedule_name="",
        exterior_schedule_name="",
        missing=None,
    ):
        self.housing_key = housing_key or ""
        self.main_view_name = main_view_name or ""
        self.location_view_name = location_view_name_value or ""
        self.interior_schedule_name = interior_schedule_name or ""
        self.exterior_schedule_name = exterior_schedule_name or ""
        self.missing = list(missing or [])

    @property
    def is_ready(self):
        return not self.missing

    @property
    def summary(self):
        if self.is_ready:
            return (
                "Prêt : vue logement, repérage et 2 nomenclatures détectés."
            )
        return "Manquant : {}.".format(", ".join(self.missing))


class SheetAssemblyResult(object):
    def __init__(
        self,
        housing_key,
        sheet_number,
        sheet_name,
        title_block_label,
        main_view_name,
        location_view_name_value,
        interior_schedule_name,
        exterior_schedule_name,
        template_sheet_label="",
        main_view_scale=None,
        main_view_auto_fitted=False,
        main_view_was_duplicated=False,
        warnings=None,
        schedule_names=None,
    ):
        self.housing_key = housing_key or ""
        self.sheet_number = sheet_number or ""
        self.sheet_name = sheet_name or ""
        self.title_block_label = title_block_label or ""
        self.main_view_name = main_view_name or ""
        self.location_view_name = location_view_name_value or ""
        self.interior_schedule_name = interior_schedule_name or ""
        self.exterior_schedule_name = exterior_schedule_name or ""
        self.template_sheet_label = template_sheet_label or ""
        self.main_view_scale = main_view_scale
        self.main_view_auto_fitted = bool(main_view_auto_fitted)
        self.main_view_was_duplicated = bool(main_view_was_duplicated)
        self.warnings = list(warnings or [])
        self.schedule_names = list(schedule_names or [])


class SheetAssemblyService(object):
    """07B/07C : reproduit le modèle et ajuste la vue logement à sa zone."""

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.build_id = SHEET_ASSEMBLY_BUILD

    def list_sheet_templates(self):
        """Liste toutes les feuilles ; l'utilisateur choisit explicitement.

        Aucun contenu de feuille n'est inspecté ici. La validation des vues,
        nomenclatures et du cartouche n'est faite qu'après sélection d'une
        feuille par l'utilisateur.
        """
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet

        result = []
        for sheet in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            result.append(
                SheetTemplateCandidate(
                    unique_id=str(getattr(sheet, "UniqueId", "") or ""),
                    sheet_number=str(
                        getattr(sheet, "SheetNumber", "") or ""
                    ),
                    sheet_name=str(getattr(sheet, "Name", "") or ""),
                    title_block_label="",
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def inspect_sheet_template(self, template_sheet_unique_id):
        if not template_sheet_unique_id:
            return SheetTemplateInspection(
                "",
                "",
                False,
                "Sélectionnez une feuille modèle.",
            )

        sheet = self.document.GetElement(template_sheet_unique_id)
        if sheet is None:
            return SheetTemplateInspection(
                template_sheet_unique_id,
                "",
                False,
                "La feuille sélectionnée n'existe plus.",
            )

        sheet_label = "{} — {}".format(
            getattr(sheet, "SheetNumber", "") or "Sans numéro",
            getattr(sheet, "Name", "") or "",
        ).rstrip(" —")

        try:
            title_block_type = self._template_title_block_type(sheet)
            views = self._placed_view_candidates(sheet)
            schedules = self._placed_schedule_candidates(sheet)
        except Exception as error:
            return SheetTemplateInspection(
                template_sheet_unique_id,
                sheet_label,
                False,
                str(error) or repr(error),
            )

        title_block_label = "{} : {}".format(
            self._family_name(title_block_type),
            self._element_type_name(title_block_type),
        ).strip(" :")

        problems = []
        if len(views) < 2:
            problems.append("au moins 2 vues placées")
        if len(schedules) < 2:
            problems.append("au moins 2 nomenclatures placées")

        if problems:
            return SheetTemplateInspection(
                template_sheet_unique_id,
                sheet_label,
                False,
                "Feuille modèle incomplète : {}.".format(
                    ", ".join(problems)
                ),
                title_block_label=title_block_label,
                view_candidates=views,
                schedule_candidates=schedules,
            )

        return SheetTemplateInspection(
            template_sheet_unique_id,
            sheet_label,
            True,
            (
                "Feuille lisible : {} vue(s) et {} nomenclature(s) placée(s). "
                "Attribuez maintenant les 4 rôles."
            ).format(len(views), len(schedules)),
            title_block_label=title_block_label,
            view_candidates=views,
            schedule_candidates=schedules,
        )

    def create_sheet_from_template(
        self,
        housing,
        template_sheet_unique_id,
        main_view_unique_id,
        template_main_viewport_unique_id,
        template_location_viewport_unique_id,
        template_interior_schedule_instance_unique_id,
        template_exterior_schedule_instance_unique_id,
        auto_fit_main_view=True,
        allowed_scales=None,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        fit_scales = parse_allowed_scales(allowed_scales)

        template_sheet = self._get_element(
            template_sheet_unique_id,
            "Sélectionnez une feuille modèle valide.",
        )
        layout = self._template_layout_from_mapping(
            template_sheet,
            template_main_viewport_unique_id,
            template_location_viewport_unique_id,
            template_interior_schedule_instance_unique_id,
            template_exterior_schedule_instance_unique_id,
        )

        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        readiness = self.readiness(housing, main_view_unique_id)
        if not readiness.is_ready:
            raise ValueError(
                "La feuille ne peut pas être assemblée. {}".format(
                    readiness.summary
                )
            )

        location = self._find_named_view(location_view_name(housing.key))
        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))

        self._validate_placeable_view(main_view, "vue logement")
        self._validate_placeable_view(location, "plan de repérage")
        self._validate_schedule_not_placed(interior, "nomenclature intérieure")
        self._validate_schedule_not_placed(exterior, "nomenclature extérieure")

        sheet_number = "PDV-{}".format(housing.key)
        sheet_name = "Plan de vente - {}".format(housing.key)
        self._ensure_sheet_identity_available(sheet_number, sheet_name)

        from Autodesk.Revit.DB import (
            ScheduleSheetInstance,
            ViewSheet,
            Viewport,
            XYZ,
        )

        sheet = None
        main_view_for_sheet = main_view
        fit_scale = int(getattr(main_view, "Scale", 0) or 0)
        fit_adjusted = False
        fit_duplicated = False
        fit_warnings = []
        with RevitTransaction(
            self.document,
            "Plans de vente - Feuille {}".format(housing.key),
        ):
            sheet = ViewSheet.Create(
                self.document,
                layout.title_block_type.Id,
            )
            if sheet is None:
                raise RuntimeError("Revit n'a pas retourné la feuille créée.")

            sheet.SheetNumber = sheet_number
            sheet.Name = sheet_name

            main_point = layout.points["main_view"]
            location_point = layout.points["location_view"]
            interior_point = layout.points["interior_schedule"]
            exterior_point = layout.points["exterior_schedule"]

            location_viewport = Viewport.Create(
                self.document,
                sheet.Id,
                location.Id,
                XYZ(location_point[0], location_point[1], 0.0),
            )
            self._apply_viewport_type(
                location_viewport,
                layout.viewport_type_ids.get("location_view"),
            )

            interior_instance = ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                interior.Id,
                XYZ(interior_point[0], interior_point[1], 0.0),
            )
            exterior_instance = ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                exterior.Id,
                XYZ(exterior_point[0], exterior_point[1], 0.0),
            )

            main_viewport = None
            if auto_fit_main_view:
                (
                    main_view_for_sheet,
                    main_viewport,
                    fit_scale,
                    fit_adjusted,
                    fit_duplicated,
                    fit_warnings,
                ) = self._create_reference_scale_main_viewport(
                    sheet=sheet,
                    housing_key=housing.key,
                    source_view=main_view,
                    point=main_point,
                    viewport_type_id=layout.viewport_type_ids.get(
                        "main_view"
                    ),
                    reference_scale=layout.main_reference_scale,
                    allowed_scales=fit_scales,
                    obstacle_elements=(
                        location_viewport,
                        interior_instance,
                        exterior_instance,
                    ),
                )
            else:
                main_viewport = Viewport.Create(
                    self.document,
                    sheet.Id,
                    main_view.Id,
                    XYZ(main_point[0], main_point[1], 0.0),
                )
                self._apply_viewport_type(
                    main_viewport,
                    layout.viewport_type_ids.get("main_view"),
                )

        template_label = "{} — {}".format(
            getattr(template_sheet, "SheetNumber", "") or "Sans numéro",
            getattr(template_sheet, "Name", "") or "",
        ).rstrip(" —")

        return SheetAssemblyResult(
            housing_key=housing.key,
            sheet_number=sheet.SheetNumber,
            sheet_name=sheet.Name,
            title_block_label="{} : {}".format(
                self._family_name(layout.title_block_type),
                self._element_type_name(layout.title_block_type),
            ),
            main_view_name=str(
                getattr(main_view_for_sheet, "Name", "") or ""
            ),
            location_view_name_value=str(getattr(location, "Name", "") or ""),
            interior_schedule_name=str(getattr(interior, "Name", "") or ""),
            exterior_schedule_name=str(getattr(exterior, "Name", "") or ""),
            template_sheet_label=template_label,
            main_view_scale=fit_scale,
            main_view_auto_fitted=fit_adjusted,
            main_view_was_duplicated=fit_duplicated,
            warnings=fit_warnings,
        )

    def create_sheet_from_blueprint(
        self,
        housing,
        template_sheet_unique_id,
        main_view_unique_id,
        location_view_unique_id,
        template_main_viewport_unique_id,
        template_location_viewport_unique_id,
        schedule_bindings,
        auto_fit_main_view=True,
        allowed_scales=None,
    ):
        """07D : assemble la feuille avec N nomenclatures issues du modèle."""
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        fit_scales = parse_allowed_scales(allowed_scales)
        template_sheet = self._get_element(
            template_sheet_unique_id,
            "Sélectionnez une feuille modèle valide.",
        )
        main_viewport_model = self._get_element(
            template_main_viewport_unique_id,
            "Le viewport modèle de la vue logement n'existe plus.",
        )
        location_viewport_model = self._get_element(
            template_location_viewport_unique_id,
            "Le viewport modèle du repérage n'existe plus.",
        )

        self._ensure_owned_by_sheet(
            main_viewport_model,
            template_sheet,
            "vue logement",
        )
        self._ensure_owned_by_sheet(
            location_viewport_model,
            template_sheet,
            "repérage",
        )

        main_view = self._get_element(
            main_view_unique_id,
            "La vue logement générée n'existe plus.",
        )
        location_view = self._get_element(
            location_view_unique_id,
            "Le plan de repérage généré n'existe plus.",
        )
        self._validate_placeable_view(main_view, "vue logement")
        self._validate_placeable_view(location_view, "plan de repérage")

        bindings = list(schedule_bindings or [])
        resolved_schedules = []
        for binding in bindings:
            template_instance_id = (
                binding.get("template_instance_unique_id")
                if isinstance(binding, dict)
                else getattr(binding, "template_instance_unique_id", "")
            )
            schedule_unique_id = (
                binding.get("schedule_unique_id")
                if isinstance(binding, dict)
                else getattr(binding, "schedule_unique_id", "")
            )
            template_instance = self._get_element(
                template_instance_id,
                "Une instance de nomenclature modèle n'existe plus.",
            )
            self._ensure_owned_by_sheet(
                template_instance,
                template_sheet,
                "nomenclature",
            )
            schedule = self._get_element(
                schedule_unique_id,
                "Une nomenclature générée n'existe plus.",
            )
            self._validate_schedule_not_placed(
                schedule,
                "nomenclature générée",
            )
            resolved_schedules.append((template_instance, schedule))

        sheet_number = "PDV-{}".format(housing.key)
        sheet_name = "Plan de vente - {}".format(housing.key)
        self._ensure_sheet_identity_available(sheet_number, sheet_name)

        from Autodesk.Revit.DB import ScheduleSheetInstance, ViewSheet, Viewport, XYZ

        main_center = main_viewport_model.GetBoxCenter()
        location_center = location_viewport_model.GetBoxCenter()

        template_main_view = self.document.GetElement(
            main_viewport_model.ViewId
        )
        reference_scale = int(
            getattr(template_main_view, "Scale", 0) or 0
        )

        try:
            main_viewport_type_id = main_viewport_model.GetTypeId()
        except Exception:
            main_viewport_type_id = None
        try:
            location_viewport_type_id = location_viewport_model.GetTypeId()
        except Exception:
            location_viewport_type_id = None

        sheet = None
        main_view_for_sheet = main_view
        fit_scale = int(getattr(main_view, "Scale", 0) or 0)
        fit_adjusted = False
        fit_duplicated = False
        fit_warnings = []
        placed_schedule_instances = []

        with RevitTransaction(
            self.document,
            "Plans de vente - Feuille complète {}".format(housing.key),
        ):
            title_block_type = self._template_title_block_type(template_sheet)
            sheet = ViewSheet.Create(
                self.document,
                title_block_type.Id,
            )
            if sheet is None:
                raise RuntimeError("Revit n'a pas retourné la feuille créée.")

            sheet.SheetNumber = sheet_number
            sheet.Name = sheet_name

            location_viewport = Viewport.Create(
                self.document,
                sheet.Id,
                location_view.Id,
                XYZ(
                    float(location_center.X),
                    float(location_center.Y),
                    0.0,
                ),
            )
            self._apply_viewport_type(
                location_viewport,
                location_viewport_type_id,
            )

            for template_instance, schedule in resolved_schedules:
                point = template_instance.Point
                created_instance = ScheduleSheetInstance.Create(
                    self.document,
                    sheet.Id,
                    schedule.Id,
                    XYZ(float(point.X), float(point.Y), 0.0),
                )
                placed_schedule_instances.append(created_instance)

            main_point = (
                float(main_center.X),
                float(main_center.Y),
            )
            if auto_fit_main_view:
                (
                    main_view_for_sheet,
                    main_viewport,
                    fit_scale,
                    fit_adjusted,
                    fit_duplicated,
                    fit_warnings,
                ) = self._create_reference_scale_main_viewport(
                    sheet=sheet,
                    housing_key=housing.key,
                    source_view=main_view,
                    point=main_point,
                    viewport_type_id=main_viewport_type_id,
                    reference_scale=reference_scale,
                    allowed_scales=fit_scales,
                    obstacle_elements=tuple(
                        [location_viewport] + placed_schedule_instances
                    ),
                )
            else:
                main_viewport = Viewport.Create(
                    self.document,
                    sheet.Id,
                    main_view.Id,
                    XYZ(main_point[0], main_point[1], 0.0),
                )
                self._apply_viewport_type(
                    main_viewport,
                    main_viewport_type_id,
                )

        template_label = "{} — {}".format(
            getattr(template_sheet, "SheetNumber", "") or "Sans numéro",
            getattr(template_sheet, "Name", "") or "",
        ).rstrip(" —")

        return SheetAssemblyResult(
            housing_key=housing.key,
            sheet_number=sheet.SheetNumber,
            sheet_name=sheet.Name,
            title_block_label="{} : {}".format(
                self._family_name(
                    self._template_title_block_type(template_sheet)
                ),
                self._element_type_name(
                    self._template_title_block_type(template_sheet)
                ),
            ),
            main_view_name=str(
                getattr(main_view_for_sheet, "Name", "") or ""
            ),
            location_view_name_value=str(
                getattr(location_view, "Name", "") or ""
            ),
            interior_schedule_name="",
            exterior_schedule_name="",
            template_sheet_label=template_label,
            main_view_scale=fit_scale,
            main_view_auto_fitted=fit_adjusted,
            main_view_was_duplicated=fit_duplicated,
            warnings=fit_warnings,
            schedule_names=[
                str(getattr(schedule, "Name", "") or "")
                for _, schedule in resolved_schedules
            ],
        )

    def list_title_block_types(self):
        from Autodesk.Revit.DB import (
            BuiltInCategory,
            FamilySymbol,
            FilteredElementCollector,
        )

        result = []
        symbols = (
            FilteredElementCollector(self.document)
            .OfClass(FamilySymbol)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsElementType()
            .ToElements()
        )

        for symbol in symbols:
            result.append(
                TitleBlockTypeCandidate(
                    unique_id=str(getattr(symbol, "UniqueId", "") or ""),
                    family_name=self._family_name(symbol),
                    type_name=self._element_type_name(symbol),
                    element_id_value=self._element_id_value(symbol.Id),
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def readiness(self, housing, main_view_unique_id):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        missing = []
        if not self._is_placeable_main_view(main_view, housing.key):
            missing.append("vue logement compatible")

        location = self._find_named_view(location_view_name(housing.key))
        if location is None:
            missing.append("plan de repérage")

        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        if interior is None:
            missing.append("nomenclature intérieure")

        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))
        if exterior is None:
            missing.append("nomenclature extérieure")

        return SheetAssemblyReadiness(
            housing_key=housing.key,
            main_view_name=str(getattr(main_view, "Name", "") or ""),
            location_view_name_value=str(getattr(location, "Name", "") or "")
            if location is not None else "",
            interior_schedule_name=str(getattr(interior, "Name", "") or "")
            if interior is not None else "",
            exterior_schedule_name=str(getattr(exterior, "Name", "") or "")
            if exterior is not None else "",
            missing=missing,
        )

    def create_sheet(
        self,
        housing,
        title_block_type_unique_id,
        main_view_unique_id,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        title_block = self._get_title_block_type(title_block_type_unique_id)
        main_view = self._get_element(
            main_view_unique_id,
            "Sélectionnez une vue logement générée.",
        )

        readiness = self.readiness(housing, main_view_unique_id)
        if not readiness.is_ready:
            raise ValueError(
                "La feuille ne peut pas être assemblée. {}".format(
                    readiness.summary
                )
            )

        location = self._find_named_view(location_view_name(housing.key))
        interior = self._find_named_schedule(schedule_name(housing.key, "INT"))
        exterior = self._find_named_schedule(schedule_name(housing.key, "EXT"))

        self._validate_placeable_view(main_view, "vue logement")
        self._validate_placeable_view(location, "plan de repérage")
        self._validate_schedule_not_placed(interior, "nomenclature intérieure")
        self._validate_schedule_not_placed(exterior, "nomenclature extérieure")

        sheet_number = "PDV-{}".format(housing.key)
        sheet_name = "Plan de vente - {}".format(housing.key)
        self._ensure_sheet_identity_available(sheet_number, sheet_name)

        from Autodesk.Revit.DB import (
            ScheduleSheetInstance,
            ViewSheet,
            Viewport,
            XYZ,
        )

        sheet = None
        with RevitTransaction(
            self.document,
            "Plans de vente - Feuille {}".format(housing.key),
        ):
            sheet = ViewSheet.Create(self.document, title_block.Id)
            if sheet is None:
                raise RuntimeError("Revit n'a pas retourné la feuille créée.")

            sheet.SheetNumber = sheet_number
            sheet.Name = sheet_name

            outline = sheet.Outline
            anchors = default_sheet_anchors(
                outline.Min.U,
                outline.Min.V,
                outline.Max.U,
                outline.Max.V,
            )

            main_anchor = anchors["main_view"]
            location_anchor = anchors["location_view"]
            interior_anchor = anchors["interior_schedule"]
            exterior_anchor = anchors["exterior_schedule"]

            Viewport.Create(
                self.document,
                sheet.Id,
                main_view.Id,
                XYZ(main_anchor.x, main_anchor.y, 0.0),
            )
            Viewport.Create(
                self.document,
                sheet.Id,
                location.Id,
                XYZ(location_anchor.x, location_anchor.y, 0.0),
            )
            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                interior.Id,
                XYZ(interior_anchor.x, interior_anchor.y, 0.0),
            )
            ScheduleSheetInstance.Create(
                self.document,
                sheet.Id,
                exterior.Id,
                XYZ(exterior_anchor.x, exterior_anchor.y, 0.0),
            )

        return SheetAssemblyResult(
            housing_key=housing.key,
            sheet_number=sheet.SheetNumber,
            sheet_name=sheet.Name,
            title_block_label="{} : {}".format(
                self._family_name(title_block),
                self._element_type_name(title_block),
            ),
            main_view_name=str(getattr(main_view, "Name", "") or ""),
            location_view_name_value=str(getattr(location, "Name", "") or ""),
            interior_schedule_name=str(getattr(interior, "Name", "") or ""),
            exterior_schedule_name=str(getattr(exterior, "Name", "") or ""),
        )

    def _validate_placeable_view(self, view, role_label):
        from Autodesk.Revit.DB import FilteredElementCollector, Viewport

        for viewport in (
            FilteredElementCollector(self.document)
            .OfClass(Viewport)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if getattr(viewport, "ViewId", None) == view.Id:
                raise ValueError(
                    "La {} « {} » est déjà placée sur une feuille.".format(
                        role_label,
                        getattr(view, "Name", ""),
                    )
                )

    def _validate_schedule_not_placed(self, schedule, role_label):
        from Autodesk.Revit.DB import FilteredElementCollector, ScheduleSheetInstance

        for instance in (
            FilteredElementCollector(self.document)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if getattr(instance, "ScheduleId", None) == schedule.Id:
                raise ValueError(
                    "La {} « {} » est déjà placée sur une feuille.".format(
                        role_label,
                        getattr(schedule, "Name", ""),
                    )
                )

    def _is_placeable_main_view(self, view, housing_key):
        name = str(getattr(view, "Name", "") or "")
        return name.startswith("PDV PROTO - {} - ".format(housing_key))

    def _find_named_view(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, View

        for view in (
            FilteredElementCollector(self.document)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if bool(getattr(view, "IsTemplate", False)):
                continue
            if str(getattr(view, "Name", "") or "") == target_name:
                return view
        return None

    def _find_named_schedule(self, target_name):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSchedule

        for schedule in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSchedule)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if str(getattr(schedule, "Name", "") or "") == target_name:
                return schedule
        return None

    def _placed_view_candidates(self, sheet):
        result = []
        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            result.append(
                SheetPlacedViewCandidate(
                    viewport_unique_id=str(
                        getattr(viewport, "UniqueId", "") or ""
                    ),
                    view_name=str(getattr(view, "Name", "") or ""),
                )
            )
        return sorted(result, key=lambda item: item.label.lower())

    def _placed_schedule_candidates(self, sheet):
        from Autodesk.Revit.DB import (
            FilteredElementCollector,
            ScheduleSheetInstance,
        )

        result = []
        for instance in (
            FilteredElementCollector(self.document, sheet.Id)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            schedule = self.document.GetElement(instance.ScheduleId)
            result.append(
                SheetPlacedScheduleCandidate(
                    instance_unique_id=str(
                        getattr(instance, "UniqueId", "") or ""
                    ),
                    schedule_name=str(
                        getattr(schedule, "Name", "") or ""
                    ),
                )
            )
        return sorted(result, key=lambda item: item.label.lower())

    def _template_title_block_type(self, sheet):
        from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

        title_blocks = list(
            FilteredElementCollector(self.document, sheet.Id)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsNotElementType()
            .ToElements()
        )
        if len(title_blocks) != 1:
            raise ValueError(
                "La feuille modèle doit contenir exactement un cartouche."
            )

        title_block_type = self.document.GetElement(
            title_blocks[0].GetTypeId()
        )
        if title_block_type is None:
            raise ValueError(
                "Impossible de retrouver le type de cartouche de la feuille modèle."
            )
        return title_block_type

    def _template_layout_from_mapping(
        self,
        sheet,
        main_viewport_unique_id,
        location_viewport_unique_id,
        interior_schedule_instance_unique_id,
        exterior_schedule_instance_unique_id,
    ):
        from Autodesk.Revit.DB import ViewSheet

        if sheet is None or not isinstance(sheet, ViewSheet):
            raise ValueError("La feuille modèle sélectionnée n'est plus valide.")

        if not main_viewport_unique_id or not location_viewport_unique_id:
            raise ValueError(
                "Attribuez une vue modèle au logement et une au repérage."
            )
        if main_viewport_unique_id == location_viewport_unique_id:
            raise ValueError(
                "La vue logement et le repérage doivent utiliser deux viewports différents."
            )
        if (
            not interior_schedule_instance_unique_id
            or not exterior_schedule_instance_unique_id
        ):
            raise ValueError(
                "Attribuez une nomenclature intérieure et une extérieure."
            )
        if (
            interior_schedule_instance_unique_id
            == exterior_schedule_instance_unique_id
        ):
            raise ValueError(
                "Les nomenclatures intérieure et extérieure doivent être différentes."
            )

        main_viewport = self._get_element(
            main_viewport_unique_id,
            "Le viewport modèle de la vue logement n'existe plus.",
        )
        location_viewport = self._get_element(
            location_viewport_unique_id,
            "Le viewport modèle du repérage n'existe plus.",
        )
        interior_instance = self._get_element(
            interior_schedule_instance_unique_id,
            "La nomenclature modèle intérieure n'existe plus.",
        )
        exterior_instance = self._get_element(
            exterior_schedule_instance_unique_id,
            "La nomenclature modèle extérieure n'existe plus.",
        )

        self._ensure_owned_by_sheet(main_viewport, sheet, "vue logement")
        self._ensure_owned_by_sheet(location_viewport, sheet, "repérage")
        self._ensure_owned_by_sheet(
            interior_instance,
            sheet,
            "nomenclature intérieure",
        )
        self._ensure_owned_by_sheet(
            exterior_instance,
            sheet,
            "nomenclature extérieure",
        )

        main_center = main_viewport.GetBoxCenter()
        location_center = location_viewport.GetBoxCenter()
        interior_point = interior_instance.Point
        exterior_point = exterior_instance.Point

        viewport_box_sizes = {
            "main_view": self._viewport_box_size(main_viewport),
            "location_view": self._viewport_box_size(location_viewport),
        }

        points = {
            "main_view": (float(main_center.X), float(main_center.Y)),
            "location_view": (
                float(location_center.X),
                float(location_center.Y),
            ),
            "interior_schedule": (
                float(interior_point.X),
                float(interior_point.Y),
            ),
            "exterior_schedule": (
                float(exterior_point.X),
                float(exterior_point.Y),
            ),
        }

        viewport_type_ids = {}
        try:
            viewport_type_ids["main_view"] = main_viewport.GetTypeId()
        except Exception:
            viewport_type_ids["main_view"] = None
        try:
            viewport_type_ids["location_view"] = location_viewport.GetTypeId()
        except Exception:
            viewport_type_ids["location_view"] = None

        template_main_view = self.document.GetElement(
            main_viewport.ViewId
        )
        main_reference_scale = int(
            getattr(template_main_view, "Scale", 0) or 0
        )

        return _TemplateLayout(
            sheet=sheet,
            title_block_type=self._template_title_block_type(sheet),
            points=points,
            viewport_type_ids=viewport_type_ids,
            viewport_box_sizes=viewport_box_sizes,
            main_reference_scale=main_reference_scale,
        )

    def _create_reference_scale_main_viewport(
        self,
        sheet,
        housing_key,
        source_view,
        point,
        viewport_type_id,
        reference_scale,
        allowed_scales,
        obstacle_elements,
    ):
        """07C : référence = échelle du modèle ; réduction seulement si collision."""
        from Autodesk.Revit.DB import ViewDuplicateOption, Viewport, XYZ

        warnings = []
        reference_scale = int(reference_scale or 0)
        if reference_scale <= 0:
            reference_scale = int(getattr(source_view, "Scale", 0) or 0)

        candidates = scale_candidates_from_reference(
            reference_scale,
            allowed_scales,
        )

        source_scale = int(getattr(source_view, "Scale", 0) or 0)
        working_view = source_view
        was_duplicated = False

        # Pour respecter l'échelle du modèle sans toucher la vue de production,
        # on crée une copie uniquement si l'échelle doit être modifiée.
        if source_scale != reference_scale:
            if not source_view.CanViewBeDuplicated(
                ViewDuplicateOption.WithDetailing
            ):
                warnings.append(
                    "07C : impossible de dupliquer la vue logement ; "
                    "échelle d'origine conservée."
                )
                viewport = Viewport.Create(
                    self.document,
                    sheet.Id,
                    source_view.Id,
                    XYZ(point[0], point[1], 0.0),
                )
                self._apply_viewport_type(viewport, viewport_type_id)
                return (
                    source_view,
                    viewport,
                    source_scale,
                    False,
                    False,
                    warnings,
                )

            copied_id = source_view.Duplicate(
                ViewDuplicateOption.WithDetailing
            )
            working_view = self.document.GetElement(copied_id)
            if working_view is None:
                raise RuntimeError(
                    "07C : Revit n'a pas retourné la copie de la vue logement."
                )
            working_view.Name = self._unique_view_name(
                "PDV SHEET - {} - AUTO".format(housing_key)
            )
            was_duplicated = True

        viewport = None
        selected_scale = None
        collision_labels = []

        for scale in candidates:
            if working_view is source_view and scale != source_scale:
                # La première collision impose désormais une réduction :
                # dupliquer la vue avant de modifier son échelle.
                if not source_view.CanViewBeDuplicated(
                    ViewDuplicateOption.WithDetailing
                ):
                    warnings.append(
                        "07C : collision détectée mais la vue ne peut pas être "
                        "dupliquée ; échelle d'origine conservée."
                    )
                    break

                if viewport is not None:
                    self.document.Delete(viewport.Id)
                    viewport = None

                copied_id = source_view.Duplicate(
                    ViewDuplicateOption.WithDetailing
                )
                working_view = self.document.GetElement(copied_id)
                if working_view is None:
                    raise RuntimeError(
                        "07C : Revit n'a pas retourné la copie de la vue logement."
                    )
                working_view.Name = self._unique_view_name(
                    "PDV SHEET - {} - AUTO".format(housing_key)
                )
                was_duplicated = True

            try:
                if int(getattr(working_view, "Scale", 0) or 0) != int(scale):
                    working_view.Scale = int(scale)
            except Exception:
                continue

            if viewport is None:
                viewport = Viewport.Create(
                    self.document,
                    sheet.Id,
                    working_view.Id,
                    XYZ(point[0], point[1], 0.0),
                )
                self._apply_viewport_type(viewport, viewport_type_id)

            self.document.Regenerate()
            collision_labels = self._main_viewport_collisions(
                sheet,
                viewport,
                obstacle_elements,
            )
            selected_scale = int(scale)

            if not collision_labels:
                return (
                    working_view,
                    viewport,
                    selected_scale,
                    selected_scale != source_scale,
                    was_duplicated,
                    warnings,
                )

        if viewport is None:
            viewport = Viewport.Create(
                self.document,
                sheet.Id,
                source_view.Id,
                XYZ(point[0], point[1], 0.0),
            )
            self._apply_viewport_type(viewport, viewport_type_id)
            selected_scale = source_scale
            working_view = source_view
            was_duplicated = False

        if collision_labels:
            warnings.append(
                "07C : collision restante à l'échelle 1:{} avec {}.".format(
                    selected_scale,
                    ", ".join(sorted(set(collision_labels))),
                )
            )

        return (
            working_view,
            viewport,
            selected_scale,
            selected_scale != source_scale,
            was_duplicated,
            warnings,
        )

    def _main_viewport_collisions(
        self,
        sheet,
        main_viewport,
        obstacle_elements,
    ):
        clearance = self._millimeters_to_internal(2.0)
        rectangle = self._viewport_rectangle(main_viewport)
        labels = []

        for element in obstacle_elements or []:
            if element is None:
                continue
            other = self._element_rectangle(element, sheet)
            if other is None:
                continue
            if rectangles_overlap(
                rectangle,
                other,
                clearance=clearance,
            ):
                labels.append(self._obstacle_label(element))

        for start, end in self._title_block_segments(sheet):
            if segment_intersects_rectangle(
                start,
                end,
                rectangle,
                clearance=clearance,
            ):
                labels.append("géométrie du cartouche")
                break

        return labels

    @staticmethod
    def _viewport_rectangle(viewport):
        outline = viewport.GetBoxOutline()
        minimum = outline.MinimumPoint
        maximum = outline.MaximumPoint
        return (
            float(minimum.X),
            float(minimum.Y),
            float(maximum.X),
            float(maximum.Y),
        )

    def _element_rectangle(self, element, sheet):
        if hasattr(element, "GetBoxOutline"):
            try:
                return self._viewport_rectangle(element)
            except Exception:
                pass

        box = None
        try:
            box = element.get_BoundingBox(sheet)
        except Exception:
            try:
                box = element.get_BoundingBox(None)
            except Exception:
                box = None

        if box is None:
            return None

        return (
            float(box.Min.X),
            float(box.Min.Y),
            float(box.Max.X),
            float(box.Max.Y),
        )

    def _title_block_segments(self, sheet):
        from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector, Options

        segments = []
        options = Options()

        for title_block in (
            FilteredElementCollector(self.document, sheet.Id)
            .OfCategory(BuiltInCategory.OST_TitleBlocks)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            try:
                geometry = title_block.get_Geometry(options)
            except Exception:
                geometry = None
            self._collect_geometry_segments(geometry, segments)

        return segments

    def _collect_geometry_segments(self, geometry, output):
        if geometry is None:
            return

        try:
            items = list(geometry)
        except Exception:
            items = []

        for item in items:
            if item is None:
                continue

            if hasattr(item, "GetInstanceGeometry"):
                try:
                    self._collect_geometry_segments(
                        item.GetInstanceGeometry(),
                        output,
                    )
                    continue
                except Exception:
                    pass

            points = []
            if hasattr(item, "Tessellate"):
                try:
                    points = list(item.Tessellate() or [])
                except Exception:
                    points = []
            elif hasattr(item, "GetCoordinates"):
                try:
                    points = list(item.GetCoordinates() or [])
                except Exception:
                    points = []

            if len(points) < 2:
                continue

            for first, second in zip(points, points[1:]):
                output.append(
                    (
                        (float(first.X), float(first.Y)),
                        (float(second.X), float(second.Y)),
                    )
                )

    @staticmethod
    def _obstacle_label(element):
        try:
            name = str(getattr(element, "Name", "") or "")
            if name:
                return name
        except Exception:
            pass
        return "un autre élément de la feuille"

    @staticmethod
    def _millimeters_to_internal(value):
        try:
            from Autodesk.Revit.DB import UnitTypeId, UnitUtils
            return float(
                UnitUtils.ConvertToInternalUnits(
                    float(value),
                    UnitTypeId.Millimeters,
                )
            )
        except Exception:
            return float(value) / 304.8

    def _unique_view_name(self, base_name):
        from Autodesk.Revit.DB import FilteredElementCollector, View

        existing = set()
        for view in (
            FilteredElementCollector(self.document)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            existing.add(str(getattr(view, "Name", "") or ""))

        if base_name not in existing:
            return base_name

        index = 2
        while True:
            candidate = "{} ({})".format(base_name, index)
            if candidate not in existing:
                return candidate
            index += 1

    @staticmethod
    def _viewport_box_size(viewport):
        outline = viewport.GetBoxOutline()
        minimum = outline.MinimumPoint
        maximum = outline.MaximumPoint
        return (
            abs(float(maximum.X) - float(minimum.X)),
            abs(float(maximum.Y) - float(minimum.Y)),
        )

    def _ensure_owned_by_sheet(self, element, sheet, role_label):
        owner_id = getattr(element, "OwnerViewId", None)
        if owner_id is None:
            owner_id = getattr(element, "SheetId", None)
        if owner_id != sheet.Id:
            raise ValueError(
                "L'élément modèle « {} » n'appartient pas à la feuille choisie.".format(
                    role_label
                )
            )

    @staticmethod
    def _apply_viewport_type(viewport, viewport_type_id):
        if viewport is None or viewport_type_id is None:
            return
        try:
            viewport.ChangeTypeId(viewport_type_id)
        except Exception:
            pass

    def _get_title_block_type(self, unique_id):
        if not unique_id:
            raise ValueError("Sélectionnez un type de cartouche.")

        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError("Le type de cartouche sélectionné n'existe plus.")

        try:
            from Autodesk.Revit.DB import BuiltInCategory
            category_id = element.Category.Id
            expected = int(BuiltInCategory.OST_TitleBlocks)
            actual = self._element_id_value(category_id)
            if actual != expected:
                raise ValueError("L'élément sélectionné n'est pas un cartouche.")
        except ValueError:
            raise
        except Exception:
            raise ValueError("Impossible de valider le type de cartouche.")

        return element

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    def _ensure_sheet_identity_available(self, sheet_number, sheet_name):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet

        for sheet in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if str(getattr(sheet, "SheetNumber", "") or "") == sheet_number:
                raise ValueError(
                    "La feuille numéro « {} » existe déjà. "
                    "La mise à jour sera traitée à l'Étape 08.".format(
                        sheet_number
                    )
                )
            if str(getattr(sheet, "Name", "") or "") == sheet_name:
                raise ValueError(
                    "La feuille « {} » existe déjà. "
                    "La mise à jour sera traitée à l'Étape 08.".format(
                        sheet_name
                    )
                )

    @staticmethod
    def _family_name(element_type):
        try:
            family = getattr(element_type, "Family", None)
            value = getattr(family, "Name", None)
            if value:
                return str(value)
        except Exception:
            pass
        try:
            value = getattr(element_type, "FamilyName", None)
            if value:
                return str(value)
        except Exception:
            pass
        return ""

    @staticmethod
    def _element_type_name(element_type):
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
    def _element_id_value(element_id):
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        return int(element_id.IntegerValue)
