# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Étape 08 — mise à jour d'un plan de vente déjà généré."""

from common.transaction import RevitTransaction


PLAN_UPDATE_BUILD = "stage08-regenerate-existing-plan-v1"


class ExistingPlanInspection(object):
    def __init__(
        self,
        housing_key,
        exists,
        is_updateable,
        sheet_unique_id="",
        sheet_number="",
        sheet_name="",
        main_view_name="",
        location_view_name="",
        managed_schedule_count=0,
        template_schedule_count=0,
        warnings=None,
        blocking_reason="",
    ):
        self.housing_key = housing_key or ""
        self.exists = bool(exists)
        self.is_updateable = bool(is_updateable)
        self.sheet_unique_id = sheet_unique_id or ""
        self.sheet_number = sheet_number or ""
        self.sheet_name = sheet_name or ""
        self.main_view_name = main_view_name or ""
        self.location_view_name = location_view_name or ""
        self.managed_schedule_count = int(managed_schedule_count or 0)
        self.template_schedule_count = int(template_schedule_count or 0)
        self.warnings = list(warnings or [])
        self.blocking_reason = blocking_reason or ""

    @property
    def label(self):
        if not self.exists:
            return "Aucun plan de vente existant."
        return "{} — {}".format(
            self.sheet_number or "Sans numéro",
            self.sheet_name or "",
        ).rstrip(" —")

    @property
    def summary(self):
        if not self.exists:
            return (
                "Aucune feuille « PDV-{} » n'existe encore.".format(
                    self.housing_key
                )
            )
        if not self.is_updateable:
            return self.blocking_reason or (
                "Le plan existant ne peut pas être mis à jour automatiquement."
            )
        return (
            "{} | {} nomenclature(s) gérée(s) | "
            "{} nomenclature(s) attendue(s) par le modèle."
        ).format(
            self.label,
            self.managed_schedule_count,
            self.template_schedule_count,
        )


class PlanUpdateResult(object):
    def __init__(
        self,
        housing_key,
        sheet_result,
        main_view_result,
        location_result,
        schedule_result,
        tag_result=None,
        dimension_result=None,
        warnings=None,
    ):
        self.housing_key = housing_key or ""
        self.sheet_result = sheet_result
        self.main_view_result = main_view_result
        self.location_result = location_result
        self.schedule_result = schedule_result
        self.tag_result = tag_result
        self.dimension_result = dimension_result
        self.warnings = list(warnings or [])


class PlanUpdateService(object):
    """Régénère les artefacts PDV tout en conservant la feuille existante."""

    def __init__(
        self,
        document,
        full_generation_service,
        prototype_view_service,
        schedule_service,
        location_plan_service,
        room_tag_service,
        dimension_service,
        sheet_assembly_service,
    ):
        if document is None:
            raise ValueError("Document Revit manquant.")

        self.document = document
        self.full_generation_service = full_generation_service
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service
        self.location_plan_service = location_plan_service
        self.room_tag_service = room_tag_service
        self.dimension_service = dimension_service
        self.sheet_assembly_service = sheet_assembly_service
        self.build_id = PLAN_UPDATE_BUILD

    def inspect(
        self,
        housing,
        descriptor,
        template_sheet_unique_id,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        if descriptor is None:
            raise ValueError(
                "Choisissez et analysez d'abord le paramètre logement."
            )

        target_sheet = self._find_target_sheet(housing.key)
        if target_sheet is None:
            return ExistingPlanInspection(
                housing_key=housing.key,
                exists=False,
                is_updateable=False,
            )

        template_sheet = self._get_element(
            template_sheet_unique_id,
            "Sélectionnez une feuille modèle.",
        )
        if target_sheet.Id == template_sheet.Id:
            return ExistingPlanInspection(
                housing_key=housing.key,
                exists=True,
                is_updateable=False,
                sheet_unique_id=str(
                    getattr(target_sheet, "UniqueId", "") or ""
                ),
                sheet_number=str(
                    getattr(target_sheet, "SheetNumber", "") or ""
                ),
                sheet_name=str(getattr(target_sheet, "Name", "") or ""),
                blocking_reason=(
                    "La feuille existante ne peut pas être utilisée comme "
                    "son propre modèle de mise à jour."
                ),
            )

        template_inspection = (
            self.full_generation_service.inspect_template(
                template_sheet_unique_id,
                descriptor,
            )
        )

        state = self._existing_state(
            target_sheet,
            housing.key,
            template_inspection,
        )

        blocking = self._external_usage_blocking_reason(
            target_sheet,
            state,
        )

        warnings = list(state.get("warnings", []) or [])
        warnings.extend(template_inspection.warnings)

        return ExistingPlanInspection(
            housing_key=housing.key,
            exists=True,
            is_updateable=not bool(blocking),
            sheet_unique_id=str(
                getattr(target_sheet, "UniqueId", "") or ""
            ),
            sheet_number=str(
                getattr(target_sheet, "SheetNumber", "") or ""
            ),
            sheet_name=str(getattr(target_sheet, "Name", "") or ""),
            main_view_name=state.get("main_view_name", ""),
            location_view_name=state.get("location_view_name", ""),
            managed_schedule_count=len(
                state.get("managed_schedule_instances", []) or []
            ),
            template_schedule_count=len(
                template_inspection.schedule_instance_unique_ids
            ),
            warnings=warnings,
            blocking_reason=blocking,
        )

    def update(
        self,
        housing,
        descriptor,
        template_sheet_unique_id,
        allowed_scales=None,
    ):
        inspection = self.inspect(
            housing,
            descriptor,
            template_sheet_unique_id,
        )
        if not inspection.exists:
            raise ValueError(
                "Aucun plan de vente existant n'a été trouvé pour « {} ». "
                "Utilisez d'abord la génération complète 07D.".format(
                    housing.key
                )
            )
        if not inspection.is_updateable:
            raise ValueError(inspection.summary)

        target_sheet = self._get_element(
            inspection.sheet_unique_id,
            "La feuille à mettre à jour n'existe plus.",
        )
        template_sheet = self._get_element(
            template_sheet_unique_id,
            "La feuille modèle n'existe plus.",
        )

        template_inspection = (
            self.full_generation_service.inspect_template(
                template_sheet_unique_id,
                descriptor,
            )
        )
        main_info, location_info, classifier_warnings = (
            self.full_generation_service._classify_viewports(
                template_sheet
            )
        )

        source_candidate, source_warnings = (
            self.full_generation_service._resolve_source_view(
                housing,
                main_info.view,
            )
        )
        (
            location_source_candidate,
            location_source_warnings,
        ) = self.full_generation_service._resolve_location_source_view(
            housing,
            location_info.view,
        )

        tag_type = self.full_generation_service._dominant_element_type(
            main_info.view,
            "OST_RoomTags",
        )
        dimension_type = (
            self.full_generation_service._dominant_element_type(
                main_info.view,
                "OST_Dimensions",
            )
        )
        fill_type = self.full_generation_service._filled_region_type(
            location_info.view
        )
        if fill_type is None:
            raise ValueError(
                "Impossible de déterminer le type de zone remplie du repérage modèle."
            )

        location_template = (
            self.full_generation_service._view_template(
                location_info.view
            )
        )

        template_schedule_instances = (
            self.full_generation_service._schedule_instances(
                template_sheet
            )
        )
        template_schedule_ids = []
        instance_to_template = []
        for instance in template_schedule_instances:
            schedule = self.document.GetElement(instance.ScheduleId)
            if schedule is None:
                continue
            schedule_uid = str(
                getattr(schedule, "UniqueId", "") or ""
            )
            if schedule_uid not in template_schedule_ids:
                template_schedule_ids.append(schedule_uid)
            instance_to_template.append(
                (
                    str(getattr(instance, "UniqueId", "") or ""),
                    schedule_uid,
                )
            )

        state = self._existing_state(
            target_sheet,
            housing.key,
            template_inspection,
        )
        layout_override = self._layout_override(
            state,
            len(instance_to_template),
        )

        warnings = list(inspection.warnings or [])
        warnings.extend(classifier_warnings)
        warnings.extend(source_warnings)
        warnings.extend(location_source_warnings)

        from Autodesk.Revit.DB import TransactionGroup

        group = TransactionGroup(
            self.document,
            "Plans de vente - Mise à jour {}".format(housing.key),
        )
        group.Start()

        main_result = None
        location_result = None
        schedule_result = None
        tag_result = None
        dimension_result = None
        sheet_result = None

        try:
            self._delete_managed_artifacts(
                target_sheet,
                state,
                housing.key,
            )

            main_result = (
                self.prototype_view_service.create_dependent_crop_view(
                    housing=housing,
                    source_view_unique_id=source_candidate.unique_id,
                    margin_mm=(
                        self.full_generation_service.DEFAULT_CROP_MARGIN_MM
                    ),
                    target_scale=template_inspection.reference_scale,
                )
            )

            if tag_type is not None:
                tag_result = self.room_tag_service.create_tags(
                    housing,
                    main_result.view_unique_id,
                    str(getattr(tag_type, "UniqueId", "") or ""),
                )
                warnings.extend(tag_result.warnings)
            else:
                warnings.append(
                    "08 : étiquettes non régénérées, aucun type n'a été déduit du modèle."
                )

            if dimension_type is not None:
                dimension_result = self.dimension_service.create_dimensions(
                    housing,
                    main_result.view_unique_id,
                    str(
                        getattr(
                            dimension_type,
                            "UniqueId",
                            "",
                        )
                        or ""
                    ),
                )
                warnings.extend(dimension_result.warnings)
            else:
                warnings.append(
                    "08 : cotations non régénérées, aucun type n'a été déduit du modèle."
                )

            location_result = (
                self.location_plan_service.create_location_plan(
                    housing=housing,
                    source_view_unique_id=(
                        location_source_candidate.unique_id
                    ),
                    filled_region_type_unique_id=str(
                        getattr(fill_type, "UniqueId", "") or ""
                    ),
                    template_unique_id=(
                        str(
                            getattr(
                                location_template,
                                "UniqueId",
                                "",
                            )
                            or ""
                        )
                        if location_template is not None
                        else None
                    ),
                    target_scale=int(
                        getattr(location_info.view, "Scale", 0) or 0
                    ),
                    crop_reference_view_unique_id=str(
                        getattr(
                            location_info.view,
                            "UniqueId",
                            "",
                        )
                        or ""
                    ),
                )
            )

            schedule_result = (
                self.schedule_service.duplicate_templates_for_housing(
                    housing,
                    descriptor,
                    template_schedule_ids,
                    allow_unfiltered=True,
                )
            )
            warnings.extend(schedule_result.warnings)

            generated_by_template = dict(
                (
                    item.template_unique_id,
                    item.schedule_unique_id,
                )
                for item in schedule_result.items
            )

            bindings = []
            for instance_uid, template_uid in instance_to_template:
                generated_uid = generated_by_template.get(template_uid)
                if not generated_uid:
                    raise RuntimeError(
                        "Aucune nomenclature régénérée ne correspond au "
                        "modèle {}.".format(template_uid)
                    )
                bindings.append(
                    {
                        "template_instance_unique_id": instance_uid,
                        "schedule_unique_id": generated_uid,
                    }
                )

            sheet_result = (
                self.sheet_assembly_service.update_sheet_from_blueprint(
                    housing=housing,
                    target_sheet_unique_id=inspection.sheet_unique_id,
                    template_sheet_unique_id=template_sheet_unique_id,
                    main_view_unique_id=main_result.view_unique_id,
                    location_view_unique_id=location_result.view_unique_id,
                    template_main_viewport_unique_id=(
                        template_inspection.main_viewport_unique_id
                    ),
                    template_location_viewport_unique_id=(
                        template_inspection.location_viewport_unique_id
                    ),
                    schedule_bindings=bindings,
                    layout_override=layout_override,
                    auto_fit_main_view=True,
                    allowed_scales=allowed_scales,
                )
            )
            warnings.extend(sheet_result.warnings)

            group.Assimilate()
        except Exception:
            try:
                group.RollBack()
            except Exception:
                pass
            raise

        return PlanUpdateResult(
            housing_key=housing.key,
            sheet_result=sheet_result,
            main_view_result=main_result,
            location_result=location_result,
            schedule_result=schedule_result,
            tag_result=tag_result,
            dimension_result=dimension_result,
            warnings=warnings,
        )

    def _existing_state(
        self,
        sheet,
        housing_key,
        template_inspection,
    ):
        from Autodesk.Revit.DB import (
            FilteredElementCollector,
            ScheduleSheetInstance,
        )

        main_viewport = None
        location_viewport = None
        warnings = []

        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            if view is None:
                continue

            name = str(getattr(view, "Name", "") or "")
            if self._is_main_generated_name(name, housing_key):
                if main_viewport is None:
                    main_viewport = viewport
                else:
                    warnings.append(
                        "Plusieurs viewports logement gérés ont été trouvés "
                        "sur la feuille ; le premier sera utilisé comme repère."
                    )
            elif self._is_location_generated_name(
                name,
                housing_key,
            ):
                if location_viewport is None:
                    location_viewport = viewport
                else:
                    warnings.append(
                        "Plusieurs repérages gérés ont été trouvés sur la "
                        "feuille ; le premier sera utilisé comme repère."
                    )

        all_schedule_instances = []
        for instance in (
            FilteredElementCollector(self.document, sheet.Id)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            try:
                if bool(
                    getattr(
                        instance,
                        "IsTitleblockRevisionSchedule",
                        False,
                    )
                ):
                    continue
            except Exception:
                pass
            all_schedule_instances.append(instance)

        managed_schedule_instances = []
        for instance in all_schedule_instances:
            schedule = self.document.GetElement(instance.ScheduleId)
            schedule_name = str(
                getattr(schedule, "Name", "") or ""
            )
            if self._is_managed_schedule_name(
                schedule_name,
                housing_key,
            ):
                managed_schedule_instances.append(instance)

        expected_count = len(
            template_inspection.schedule_instance_unique_ids
        )
        if (
            not managed_schedule_instances
            and expected_count
            and len(all_schedule_instances) == expected_count
        ):
            managed_schedule_instances = list(
                all_schedule_instances
            )
            warnings.append(
                "Les nomenclatures existantes ne portent pas de nom PDV "
                "reconnaissable ; elles seront régénérées car leur nombre "
                "correspond exactement au modèle."
            )

        managed_schedule_instances = self._sort_schedule_instances(
            managed_schedule_instances
        )

        if main_viewport is None:
            warnings.append(
                "Aucun viewport logement géré n'a été identifié ; la position "
                "du modèle sera utilisée."
            )
        if location_viewport is None:
            warnings.append(
                "Aucun viewport de repérage géré n'a été identifié ; la "
                "position du modèle sera utilisée."
            )
        if len(managed_schedule_instances) != expected_count:
            warnings.append(
                "Le nombre de nomenclatures gérées ({}) diffère du modèle "
                "({}) ; les positions du modèle seront réappliquées.".format(
                    len(managed_schedule_instances),
                    expected_count,
                )
            )

        generated_views = self._generated_views(housing_key)

        return {
            "main_viewport": main_viewport,
            "location_viewport": location_viewport,
            "managed_schedule_instances": managed_schedule_instances,
            "generated_views": generated_views,
            "main_view_name": self._viewport_view_name(main_viewport),
            "location_view_name": self._viewport_view_name(
                location_viewport
            ),
            "warnings": warnings,
        }

    def _layout_override(self, state, template_schedule_count):
        result = {}

        main_viewport = state.get("main_viewport")
        if main_viewport is not None:
            center = main_viewport.GetBoxCenter()
            result["main_point"] = (
                float(center.X),
                float(center.Y),
            )
            try:
                result["main_viewport_type_id"] = (
                    main_viewport.GetTypeId()
                )
            except Exception:
                pass

        location_viewport = state.get("location_viewport")
        if location_viewport is not None:
            center = location_viewport.GetBoxCenter()
            result["location_point"] = (
                float(center.X),
                float(center.Y),
            )
            try:
                result["location_viewport_type_id"] = (
                    location_viewport.GetTypeId()
                )
            except Exception:
                pass

        schedule_instances = list(
            state.get("managed_schedule_instances", []) or []
        )
        if len(schedule_instances) == int(
            template_schedule_count or 0
        ):
            points = []
            for instance in schedule_instances:
                point = instance.Point
                points.append(
                    (float(point.X), float(point.Y))
                )
            result["schedule_points"] = points

        return result

    def _delete_managed_artifacts(
        self,
        target_sheet,
        state,
        housing_key,
    ):
        schedule_instances = list(
            state.get("managed_schedule_instances", []) or []
        )
        schedule_ids = []
        for instance in schedule_instances:
            schedule_id = getattr(instance, "ScheduleId", None)
            if schedule_id is not None:
                key = self._element_id_value(schedule_id)
                if key not in [
                    self._element_id_value(item)
                    for item in schedule_ids
                ]:
                    schedule_ids.append(schedule_id)

        viewport_ids = []
        for key in ("main_viewport", "location_viewport"):
            viewport = state.get(key)
            if viewport is not None:
                viewport_ids.append(viewport.Id)

        generated_views = list(
            state.get("generated_views", []) or []
        )

        with RevitTransaction(
            self.document,
            "Plans de vente - Nettoyage mise à jour {}".format(
                housing_key
            ),
        ):
            for viewport_id in viewport_ids:
                self.document.Delete(viewport_id)

            for instance in schedule_instances:
                self.document.Delete(instance.Id)

            for view in generated_views:
                self.document.Delete(view.Id)

            for schedule_id in schedule_ids:
                self.document.Delete(schedule_id)

    def _external_usage_blocking_reason(
        self,
        target_sheet,
        state,
    ):
        from Autodesk.Revit.DB import (
            FilteredElementCollector,
            ScheduleSheetInstance,
            Viewport,
        )

        target_sheet_id = self._element_id_value(target_sheet.Id)
        generated_view_ids = set(
            self._element_id_value(view.Id)
            for view in state.get("generated_views", []) or []
        )

        if generated_view_ids:
            for viewport in (
                FilteredElementCollector(self.document)
                .OfClass(Viewport)
                .WhereElementIsNotElementType()
                .ToElements()
            ):
                if self._element_id_value(
                    getattr(viewport, "ViewId", None)
                ) not in generated_view_ids:
                    continue
                sheet_id = self._element_id_value(
                    getattr(viewport, "SheetId", None)
                )
                if sheet_id != target_sheet_id:
                    return (
                        "Une vue PDV du logement est aussi placée sur une "
                        "autre feuille. La mise à jour automatique est bloquée "
                        "pour éviter de supprimer un usage manuel."
                    )

        managed_schedule_ids = set()
        for instance in (
            state.get("managed_schedule_instances", []) or []
        ):
            schedule_id = getattr(instance, "ScheduleId", None)
            if schedule_id is not None:
                managed_schedule_ids.add(
                    self._element_id_value(schedule_id)
                )

        if managed_schedule_ids:
            for instance in (
                FilteredElementCollector(self.document)
                .OfClass(ScheduleSheetInstance)
                .WhereElementIsNotElementType()
                .ToElements()
            ):
                schedule_id = self._element_id_value(
                    getattr(instance, "ScheduleId", None)
                )
                if schedule_id not in managed_schedule_ids:
                    continue
                owner_id = self._element_id_value(
                    getattr(instance, "OwnerViewId", None)
                )
                if owner_id != target_sheet_id:
                    return (
                        "Une nomenclature PDV du logement est aussi placée "
                        "sur une autre feuille. La mise à jour automatique "
                        "est bloquée pour éviter de supprimer un usage manuel."
                    )

        return ""

    def _generated_views(self, housing_key):
        from Autodesk.Revit.DB import FilteredElementCollector, View

        result = []
        for view in (
            FilteredElementCollector(self.document)
            .OfClass(View)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if bool(getattr(view, "IsTemplate", False)):
                continue

            name = str(getattr(view, "Name", "") or "")
            if (
                self._is_main_generated_name(name, housing_key)
                or self._is_location_generated_name(
                    name,
                    housing_key,
                )
            ):
                result.append(view)

        return result

    @staticmethod
    def _is_main_generated_name(name, housing_key):
        text = str(name or "")
        key = str(housing_key or "")
        return (
            text.startswith(
                "PDV PROTO - {} - ".format(key)
            )
            or text.startswith(
                "PDV SHEET - {} - AUTO".format(key)
            )
        )

    @staticmethod
    def _is_location_generated_name(name, housing_key):
        return str(name or "") == "PDV_{}_REP".format(
            str(housing_key or "")
        )

    @staticmethod
    def _is_managed_schedule_name(name, housing_key):
        text = str(name or "").upper()
        key = str(housing_key or "").upper()
        if not text or not key:
            return False

        tokens = (
            "PDV_{}_".format(key),
            "PDV-{}".format(key),
            "_{}_".format(key),
            "_{}".format(key),
            " - {}".format(key),
            " {}".format(key),
        )
        return any(token in text for token in tokens)

    def _find_target_sheet(self, housing_key):
        from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet

        expected_number = "PDV-{}".format(housing_key)
        expected_name = "Plan de vente - {}".format(housing_key)
        by_name = None

        for sheet in (
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            number = str(
                getattr(sheet, "SheetNumber", "") or ""
            )
            name = str(getattr(sheet, "Name", "") or "")
            if number == expected_number:
                return sheet
            if name == expected_name:
                by_name = sheet

        return by_name

    @staticmethod
    def _sort_schedule_instances(instances):
        return sorted(
            list(instances or []),
            key=lambda item: (
                -float(
                    getattr(
                        getattr(item, "Point", None),
                        "Y",
                        0.0,
                    )
                ),
                float(
                    getattr(
                        getattr(item, "Point", None),
                        "X",
                        0.0,
                    )
                ),
            ),
        )

    def _viewport_view_name(self, viewport):
        if viewport is None:
            return ""
        try:
            view = self.document.GetElement(viewport.ViewId)
            return str(getattr(view, "Name", "") or "")
        except Exception:
            return ""

    def _get_element(self, unique_id, message):
        if not unique_id:
            raise ValueError(message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(message)
        return element

    @staticmethod
    def _element_id_value(element_id):
        if element_id is None:
            return -1
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        try:
            return int(element_id.IntegerValue)
        except Exception:
            return -1
