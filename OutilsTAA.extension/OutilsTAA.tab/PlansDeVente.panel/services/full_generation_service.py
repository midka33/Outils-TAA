# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Étape 07D — génération complète d'un plan de vente depuis une feuille modèle."""

from plans_vente.multilevel import split_housing_by_level

FULL_GENERATION_BUILD = "stage07d-template-driven-full-generation-v4"


class FullGenerationInspection(object):
    def __init__(
        self,
        template_sheet_unique_id,
        template_sheet_label,
        main_viewport_unique_id,
        main_view_name,
        location_viewport_unique_id,
        location_view_name,
        schedule_instance_unique_ids=None,
        schedule_names=None,
        reference_scale=0,
        room_tag_type_name="",
        dimension_type_name="",
        filled_region_type_name="",
        warnings=None,
        preview_bounds=None,
        preview_items=None,
    ):
        self.template_sheet_unique_id = template_sheet_unique_id or ""
        self.template_sheet_label = template_sheet_label or ""
        self.main_viewport_unique_id = main_viewport_unique_id or ""
        self.main_view_name = main_view_name or ""
        self.location_viewport_unique_id = location_viewport_unique_id or ""
        self.location_view_name = location_view_name or ""
        self.schedule_instance_unique_ids = list(
            schedule_instance_unique_ids or []
        )
        self.schedule_names = list(schedule_names or [])
        self.reference_scale = int(reference_scale or 0)
        self.room_tag_type_name = room_tag_type_name or ""
        self.dimension_type_name = dimension_type_name or ""
        self.filled_region_type_name = filled_region_type_name or ""
        self.warnings = list(warnings or [])
        self.preview_bounds = tuple(preview_bounds or ())
        self.preview_items = list(preview_items or [])

    @property
    def summary(self):
        return (
            "{} | vue logement : {} | repérage : {} | "
            "{} nomenclature(s) | référence 1:{}"
        ).format(
            self.template_sheet_label,
            self.main_view_name,
            self.location_view_name,
            len(self.schedule_names),
            self.reference_scale or "?",
        )


class FullGenerationResult(object):
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


class _TemplateViewportInfo(object):
    def __init__(
        self,
        viewport,
        view,
        area,
        filled_regions=0,
        room_tags=0,
        dimensions=0,
    ):
        self.viewport = viewport
        self.view = view
        self.area = float(area or 0.0)
        self.filled_regions = int(filled_regions or 0)
        self.room_tags = int(room_tags or 0)
        self.dimensions = int(dimensions or 0)


class FullGenerationService(object):
    """Orchestre les étapes 03 à 07C depuis une seule feuille modèle."""

    DEFAULT_CROP_MARGIN_MM = 500.0

    def __init__(
        self,
        document,
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
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service
        self.location_plan_service = location_plan_service
        self.room_tag_service = room_tag_service
        self.dimension_service = dimension_service
        self.sheet_assembly_service = sheet_assembly_service
        self.build_id = FULL_GENERATION_BUILD

    def inspect_template(self, template_sheet_unique_id, descriptor):
        if descriptor is None:
            raise ValueError(
                "Choisissez et analysez d'abord le paramètre logement."
            )

        sheet = self._get_element(
            template_sheet_unique_id,
            "Sélectionnez une feuille modèle.",
        )
        main_info, location_info, warnings = self._classify_viewports(sheet)

        schedule_instances = self._schedule_instances(sheet)
        schedule_names = []
        schedule_instance_ids = []
        for instance in schedule_instances:
            schedule = self.document.GetElement(instance.ScheduleId)
            if schedule is None:
                continue
            schedule_instance_ids.append(
                str(getattr(instance, "UniqueId", "") or "")
            )
            schedule_names.append(
                str(getattr(schedule, "Name", "") or "")
            )

        tag_type = self._dominant_element_type(
            main_info.view,
            "OST_RoomTags",
        )
        dimension_type = self._dominant_element_type(
            main_info.view,
            "OST_Dimensions",
        )
        fill_type = (
            self._filled_region_type(location_info.view)
            if location_info is not None
            else None
        )

        if tag_type is None:
            warnings.append(
                "Aucun type d'étiquette de pièce n'a été trouvé dans la vue logement modèle."
            )
        if dimension_type is None:
            warnings.append(
                "Aucun type de cote n'a été trouvé dans la vue logement modèle."
            )
        if location_info is not None and fill_type is None:
            warnings.append(
                "Le repérage modèle ne contient aucune zone remplie exploitable."
            )
        if not schedule_instances:
            warnings.append(
                "Aucune nomenclature placée n'a été trouvée sur la feuille modèle."
            )

        return FullGenerationInspection(
            template_sheet_unique_id=str(
                getattr(sheet, "UniqueId", "") or ""
            ),
            template_sheet_label=self._sheet_label(sheet),
            main_viewport_unique_id=str(
                getattr(main_info.viewport, "UniqueId", "") or ""
            ),
            main_view_name=str(
                getattr(main_info.view, "Name", "") or ""
            ),
            location_viewport_unique_id=(
                str(getattr(location_info.viewport, "UniqueId", "") or "")
                if location_info is not None
                else ""
            ),
            location_view_name=(
                str(getattr(location_info.view, "Name", "") or "")
                if location_info is not None
                else ""
            ),
            schedule_instance_unique_ids=schedule_instance_ids,
            schedule_names=schedule_names,
            reference_scale=int(
                getattr(main_info.view, "Scale", 0) or 0
            ),
            room_tag_type_name=self._element_type_name(tag_type),
            dimension_type_name=self._element_type_name(dimension_type),
            filled_region_type_name=(
                self._element_type_name(fill_type)
                if fill_type is not None
                else ""
            ),
            warnings=warnings,
            preview_bounds=self._sheet_preview_bounds(sheet),
            preview_items=self._sheet_preview_items(
                sheet,
                main_info,
                location_info,
                schedule_instances,
            ),
        )

    @staticmethod
    def _sheet_preview_bounds(sheet):
        try:
            outline = sheet.Outline
            return (
                float(outline.Min.U),
                float(outline.Min.V),
                float(outline.Max.U),
                float(outline.Max.V),
            )
        except Exception:
            return ()

    def _sheet_preview_items(
        self,
        sheet,
        main_info,
        location_info,
        schedule_instances,
    ):
        items = []

        def add_viewport(info, role, label):
            if info is None or info.viewport is None:
                return
            try:
                outline = info.viewport.GetBoxOutline()
                items.append({
                    "kind": role,
                    "label": label,
                    "min_x": float(outline.MinimumPoint.X),
                    "min_y": float(outline.MinimumPoint.Y),
                    "max_x": float(outline.MaximumPoint.X),
                    "max_y": float(outline.MaximumPoint.Y),
                })
            except Exception:
                pass

        add_viewport(
            main_info,
            "main_view",
            "Vue logement — {}".format(
                str(getattr(main_info.view, "Name", "") or "sans nom")
            ),
        )
        add_viewport(
            location_info,
            "location_view",
            "Repérage — {}".format(
                str(getattr(location_info.view, "Name", "") or "sans nom")
            ),
        )

        known_ids = set([main_info.viewport.Id])
        if location_info is not None:
            known_ids.add(location_info.viewport.Id)
        extra_index = 2
        for viewport_id in list(sheet.GetAllViewports() or []):
            if viewport_id in known_ids:
                continue
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            if view is None:
                continue
            try:
                outline = viewport.GetBoxOutline()
                items.append({
                    "kind": "main_view_extra",
                    "label": "Vue logement {} — {}".format(
                        extra_index,
                        str(getattr(view, "Name", "") or "sans nom"),
                    ),
                    "min_x": float(outline.MinimumPoint.X),
                    "min_y": float(outline.MinimumPoint.Y),
                    "max_x": float(outline.MaximumPoint.X),
                    "max_y": float(outline.MaximumPoint.Y),
                })
                extra_index += 1
            except Exception:
                pass

        for index, instance in enumerate(schedule_instances or [], 1):
            try:
                box = instance.get_BoundingBox(sheet)
            except Exception:
                box = None
            if box is None:
                continue

            schedule = None
            try:
                schedule = self.document.GetElement(instance.ScheduleId)
            except Exception:
                schedule = None
            label = "Nomenclature — {}".format(
                str(
                    getattr(schedule, "Name", "")
                    or "Nomenclature {}".format(index)
                )
            )
            items.append({
                "kind": "schedule",
                "label": label,
                "min_x": float(box.Min.X),
                "min_y": float(box.Min.Y),
                "max_x": float(box.Max.X),
                "max_y": float(box.Max.Y),
            })

        try:
            from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector
            title_blocks = list(
                FilteredElementCollector(self.document, sheet.Id)
                .OfCategory(BuiltInCategory.OST_TitleBlocks)
                .WhereElementIsNotElementType()
                .ToElements()
            )
        except Exception:
            title_blocks = []

        for title_block in title_blocks:
            try:
                box = title_block.get_BoundingBox(sheet)
            except Exception:
                box = None
            if box is None:
                continue
            items.append({
                "kind": "title_block",
                "label": "Cartouche",
                "min_x": float(box.Min.X),
                "min_y": float(box.Min.Y),
                "max_x": float(box.Max.X),
                "max_y": float(box.Max.Y),
            })

        return items

    def generate(
        self,
        housing,
        descriptor,
        template_sheet_unique_id,
        allowed_scales=None,
        crop_margin_mm=None,
        auto_fit_main_view=True,
        building_parameter_name="",
        typology_parameter_name="",
        main_view_unique_id=None,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        if descriptor is None:
            raise ValueError(
                "Choisissez et analysez d'abord le paramètre logement."
            )

        inspection = self.inspect_template(
            template_sheet_unique_id,
            descriptor,
        )
        sheet = self._get_element(
            inspection.template_sheet_unique_id,
            "La feuille modèle n'existe plus.",
        )
        main_info, location_info, classifier_warnings = (
            self._classify_viewports(sheet)
        )

        source_candidate, source_warnings = self._resolve_source_view(
            housing,
            main_info.view,
        )
        location_source_candidate = None
        location_source_warnings = []
        if location_info is not None:
            (
                location_source_candidate,
                location_source_warnings,
            ) = self._resolve_location_source_view(
                housing,
                location_info.view,
            )

        tag_type = self._dominant_element_type(
            main_info.view,
            "OST_RoomTags",
        )
        dimension_type = self._dominant_element_type(
            main_info.view,
            "OST_Dimensions",
        )
        fill_type = (
            self._filled_region_type(location_info.view)
            if location_info is not None
            else None
        )

        main_template = self._view_template(main_info.view)
        location_template = (
            self._view_template(location_info.view)
            if location_info is not None
            else None
        )
        schedule_instances = self._schedule_instances(sheet)
        template_schedule_ids = []
        instance_to_template = []

        for instance in schedule_instances:
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

        warnings = []
        warnings.extend(inspection.warnings)
        warnings.extend(classifier_warnings)
        warnings.extend(source_warnings)
        warnings.extend(location_source_warnings)

        from Autodesk.Revit.DB import TransactionGroup

        group = TransactionGroup(
            self.document,
            "Plans de vente - Génération complète {}".format(housing.key),
        )
        group.Start()

        main_result = None
        location_result = None
        schedule_result = None
        tag_result = None
        dimension_result = None
        sheet_result = None

        try:
            main_result = (
                self.prototype_view_service.create_dependent_crop_view(
                    housing=housing,
                    source_view_unique_id=source_candidate.unique_id,
                    margin_mm=(
                        float(crop_margin_mm)
                        if crop_margin_mm is not None
                        else self.DEFAULT_CROP_MARGIN_MM
                    ),
                    target_scale=inspection.reference_scale,
                    view_template_unique_id=(
                        str(
                            getattr(main_template, "UniqueId", "")
                            or ""
                        )
                        if main_template is not None
                        else None
                    ),
                )
            )

            room_metadata, metadata_warnings = self._room_metadata(
                housing,
                building_parameter_name=building_parameter_name,
                typology_parameter_name=typology_parameter_name,
                main_view_unique_id=main_result.view_unique_id,
            )
            warnings.extend(metadata_warnings)

            if tag_type is not None:
                tag_result = self.room_tag_service.create_tags(
                    housing,
                    main_result.view_unique_id,
                    str(getattr(tag_type, "UniqueId", "") or ""),
                )
                warnings.extend(tag_result.warnings)
            else:
                warnings.append(
                    "07D : étiquettes non créées, aucun type n'a été déduit du modèle."
                )

            if dimension_type is not None:
                dimension_result = self.dimension_service.create_dimensions(
                    housing,
                    main_result.view_unique_id,
                    str(getattr(dimension_type, "UniqueId", "") or ""),
                )
                warnings.extend(dimension_result.warnings)
            else:
                warnings.append(
                    "07D : cotations non créées, aucun type n'a été déduit du modèle."
                )

            if (
                location_info is not None
                and location_source_candidate is not None
                and fill_type is not None
            ):
                location_result = (
                    self.location_plan_service.create_location_plan(
                        housing=housing,
                        source_view_unique_id=location_source_candidate.unique_id,
                        filled_region_type_unique_id=str(
                            getattr(fill_type, "UniqueId", "") or ""
                        ),
                        template_unique_id=(
                            str(
                                getattr(location_template, "UniqueId", "")
                                or ""
                            )
                            if location_template is not None
                            else None
                        ),
                        target_scale=int(
                            getattr(location_info.view, "Scale", 0) or 0
                        ),
                        crop_reference_view_unique_id=str(
                            getattr(location_info.view, "UniqueId", "") or ""
                        ),
                    )
                )
            else:
                warnings.append(
                    "Repérage non créé : aucun repérage exploitable n'est présent "
                    "sur la feuille modèle."
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
                        "Aucune nomenclature générée ne correspond au modèle {}.".format(
                            template_uid
                        )
                    )
                bindings.append(
                    {
                        "template_instance_unique_id": instance_uid,
                        "schedule_unique_id": generated_uid,
                    }
                )

            sheet_result = self.sheet_assembly_service.create_sheet_from_blueprint(
                housing=housing,
                template_sheet_unique_id=inspection.template_sheet_unique_id,
                main_view_unique_id=main_result.view_unique_id,
                location_view_unique_id=(
                    location_result.view_unique_id
                    if location_result is not None
                    else None
                ),
                template_main_viewport_unique_id=inspection.main_viewport_unique_id,
                template_location_viewport_unique_id=(
                    inspection.location_viewport_unique_id
                    or None
                ),
                schedule_bindings=bindings,
                auto_fit_main_view=bool(auto_fit_main_view),
                allowed_scales=allowed_scales,
                housing_display_value=(
                    getattr(housing, "filter_key", None)
                    or housing.key
                ),
                housing_parameter_name=str(
                    getattr(descriptor, "name", "") or ""
                ),
                room_metadata=room_metadata,
            )
            warnings.extend(sheet_result.warnings)

            group.Assimilate()
        except Exception:
            try:
                group.RollBack()
            except Exception:
                pass
            raise

        return FullGenerationResult(
            housing_key=housing.key,
            sheet_result=sheet_result,
            main_view_result=main_result,
            location_result=location_result,
            schedule_result=schedule_result,
            tag_result=tag_result,
            dimension_result=dimension_result,
            warnings=warnings,
        )

    def generate_multilevel_one_sheet(
        self,
        housing,
        descriptor,
        template_sheet_unique_id,
        allowed_scales=None,
        crop_margin_mm=None,
        auto_fit_main_view=True,
        building_parameter_name="",
        typology_parameter_name="",
    ):
        """09B.2 : génère une feuille unique avec une vue logement par niveau."""
        if housing is None:
            raise ValueError("Sélectionnez un logement.")
        if descriptor is None:
            raise ValueError(
                "Choisissez et analysez d'abord le paramètre logement."
            )

        level_housings = list(split_housing_by_level(housing) or [])
        try:
            level_housings.sort(
                key=lambda item: int(
                    self._floor_number(
                        (item.level_names or [""])[0]
                    )
                    or 9999
                )
            )
        except Exception:
            pass

        if len(level_housings) < 2:
            return self.generate(
                housing=housing,
                descriptor=descriptor,
                template_sheet_unique_id=template_sheet_unique_id,
                allowed_scales=allowed_scales,
                crop_margin_mm=crop_margin_mm,
                auto_fit_main_view=auto_fit_main_view,
                building_parameter_name=building_parameter_name,
                typology_parameter_name=typology_parameter_name,
            )

        inspection = self.inspect_template(
            template_sheet_unique_id,
            descriptor,
        )
        sheet = self._get_element(
            inspection.template_sheet_unique_id,
            "La feuille modèle n'existe plus.",
        )
        (
            main_infos,
            location_info,
            reference_scale,
            layout_mode,
            classifier_warnings,
        ) = self._classify_multilevel_viewports(
            sheet,
            expected_levels=len(level_housings),
        )

        tag_type = self._dominant_element_type(
            main_infos[0].view,
            "OST_RoomTags",
        )
        dimension_type = self._dominant_element_type(
            main_infos[0].view,
            "OST_Dimensions",
        )
        fill_type = (
            self._filled_region_type(location_info.view)
            if location_info is not None
            else None
        )

        main_templates = [
            self._view_template(info.view)
            for info in main_infos
        ]
        location_template = (
            self._view_template(location_info.view)
            if location_info is not None
            else None
        )
        schedule_instances = self._schedule_instances(sheet)
        template_schedule_ids = []
        instance_to_template = []

        for instance in schedule_instances:
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

        warnings = []
        warnings.extend(inspection.warnings)
        warnings.extend(classifier_warnings)

        from Autodesk.Revit.DB import TransactionGroup

        group = TransactionGroup(
            self.document,
            "Plans de vente - Génération multi-niveaux {}".format(
                housing.key
            ),
        )
        group.Start()

        main_results = []
        tag_results = []
        dimension_results = []
        location_result = None
        schedule_result = None
        sheet_result = None

        try:
            for level_index, level_housing in enumerate(level_housings):
                model_main_info = main_infos[level_index]
                source_candidate, source_warnings = self._resolve_source_view(
                    level_housing,
                    model_main_info.view,
                )
                warnings.extend(source_warnings)

                main_result = (
                    self.prototype_view_service.create_dependent_crop_view(
                        housing=level_housing,
                        source_view_unique_id=source_candidate.unique_id,
                        margin_mm=(
                            float(crop_margin_mm)
                            if crop_margin_mm is not None
                            else self.DEFAULT_CROP_MARGIN_MM
                        ),
                        target_scale=reference_scale,
                        view_template_unique_id=(
                            str(
                                getattr(
                                    main_templates[level_index],
                                    "UniqueId",
                                    "",
                                )
                                or ""
                            )
                            if main_templates[level_index] is not None
                            else None
                        ),
                    )
                )
                main_results.append(main_result)

                if tag_type is not None:
                    tag_result = self.room_tag_service.create_tags(
                        level_housing,
                        main_result.view_unique_id,
                        str(getattr(tag_type, "UniqueId", "") or ""),
                    )
                    tag_results.append(tag_result)
                    warnings.extend(tag_result.warnings)
                else:
                    warnings.append(
                        "09B.2 : étiquettes non créées, aucun type "
                        "n'a été déduit du modèle."
                    )

                if dimension_type is not None:
                    dimension_result = self.dimension_service.create_dimensions(
                        level_housing,
                        main_result.view_unique_id,
                        str(
                            getattr(dimension_type, "UniqueId", "")
                            or ""
                        ),
                    )
                    dimension_results.append(dimension_result)
                    warnings.extend(dimension_result.warnings)
                else:
                    warnings.append(
                        "09B.2 : cotations non créées, aucun type "
                        "n'a été déduit du modèle."
                    )

            lower_housing = level_housings[0]
            try:
                level_housings.sort(
                    key=lambda item: int(
                        self._floor_number(
                            (item.level_names or [""])[0]
                        )
                        or 9999
                    )
                )
                lower_housing = level_housings[0]
            except Exception:
                pass

            if location_info is not None and fill_type is not None:
                (
                    location_source_candidate,
                    location_source_warnings,
                ) = self._resolve_location_source_view(
                    lower_housing,
                    location_info.view,
                )
                warnings.extend(location_source_warnings)

                location_result = (
                    self.location_plan_service.create_location_plan(
                        housing=lower_housing,
                        source_view_unique_id=location_source_candidate.unique_id,
                        filled_region_type_unique_id=str(
                            getattr(fill_type, "UniqueId", "") or ""
                        ),
                        template_unique_id=(
                            str(
                                getattr(location_template, "UniqueId", "")
                                or ""
                            )
                            if location_template is not None
                            else None
                        ),
                        target_scale=int(
                            getattr(location_info.view, "Scale", 0) or 0
                        ),
                        crop_reference_view_unique_id=str(
                            getattr(location_info.view, "UniqueId", "") or ""
                        ),
                    )
                )
            else:
                warnings.append(
                    "09B.2 : repérage non créé, aucun repérage exploitable "
                    "n'est présent sur la feuille modèle."
                )

            schedule_result = (
                self.schedule_service.duplicate_templates_for_housing(
                    housing,
                    descriptor,
                    template_schedule_ids,
                    allow_unfiltered=True,
                    all_levels=True,
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
                        "Aucune nomenclature générée ne correspond au modèle {}."
                        .format(template_uid)
                    )
                bindings.append(
                    {
                        "template_instance_unique_id": instance_uid,
                        "schedule_unique_id": generated_uid,
                    }
                )

            room_metadata, metadata_warnings = self._room_metadata(
                housing,
                building_parameter_name=building_parameter_name,
                typology_parameter_name=typology_parameter_name,
                main_view_unique_id=None,
            )
            warnings.extend(metadata_warnings)

            sheet_result = (
                self.sheet_assembly_service
                .create_multilevel_sheet_from_blueprint(
                    housing=housing,
                    template_sheet_unique_id=inspection.template_sheet_unique_id,
                    main_view_unique_ids=[
                        item.view_unique_id
                        for item in main_results
                    ],
                    location_view_unique_id=(
                        location_result.view_unique_id
                        if location_result is not None
                        else None
                    ),
                    template_main_viewport_unique_ids=[
                        str(
                            getattr(info.viewport, "UniqueId", "")
                            or ""
                        )
                        for info in main_infos
                    ],
                    template_location_viewport_unique_id=(
                        str(
                            getattr(
                                location_info.viewport,
                                "UniqueId",
                                "",
                            )
                            or ""
                        )
                        if location_info is not None
                        else None
                    ),
                    schedule_bindings=bindings,
                    auto_fit_main_view=bool(auto_fit_main_view),
                    allowed_scales=allowed_scales,
                    housing_display_value=(
                        getattr(housing, "filter_key", None)
                        or housing.key
                    ),
                    housing_parameter_name=str(
                        getattr(descriptor, "name", "") or ""
                    ),
                    room_metadata=room_metadata,
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

        return FullGenerationResult(
            housing_key=housing.key,
            sheet_result=sheet_result,
            main_view_result=main_results,
            location_result=location_result,
            schedule_result=schedule_result,
            tag_result=tag_results,
            dimension_result=dimension_results,
            warnings=warnings,
        )

    def _room_metadata(
        self,
        housing,
        building_parameter_name="",
        typology_parameter_name="",
        main_view_unique_id=None,
    ):
        """Lit les informations de cartouche depuis les pièces du logement."""
        rooms = []
        for unique_id in list(
            getattr(housing, "room_unique_ids", []) or []
        ):
            try:
                room = self.document.GetElement(unique_id)
            except Exception:
                room = None
            if room is not None:
                rooms.append(room)

        warnings = []
        result = {}

        sources = (
            ("building", building_parameter_name, "Bâtiment"),
            ("typology", typology_parameter_name, "Typologie"),
        )

        for key, parameter_name, label in sources:
            name = str(parameter_name or "").strip()
            if not name:
                continue

            values = []
            for room in rooms:
                value = self._room_parameter_value(room, name)
                if value and value not in values:
                    values.append(value)

            if len(values) == 1:
                result[key] = values[0]
            elif len(values) > 1:
                warnings.append(
                    "09B : plusieurs valeurs trouvées dans les pièces pour "
                    "{} (paramètre « {} ») : {}. Le cartouche n'a pas été "
                    "renseigné pour ce champ.".format(
                        label,
                        name,
                        ", ".join(values),
                    )
                )

        floor_label = self._main_view_level_name(main_view_unique_id)
        if floor_label:
            floor = self._floor_number(floor_label)
            if floor != "":
                result["floor"] = floor
            else:
                warnings.append(
                    "09B : impossible d'extraire le numéro d'étage depuis "
                    "le niveau Revit « {} ».".format(floor_label)
                )
        else:
            levels = list(getattr(housing, "level_names", []) or [])
            floors = self._floor_numbers(levels)
            if floors:
                result["floor"] = " / ".join(floors)

        return result, warnings

    def _main_view_level_name(self, view_unique_id):
        if not view_unique_id:
            return ""
        try:
            view = self.document.GetElement(view_unique_id)
        except Exception:
            view = None
        if view is None:
            return ""
        level = getattr(view, "GenLevel", None)
        return str(getattr(level, "Name", "") or "").strip()

    @classmethod
    def _floor_numbers(cls, levels):
        values = []
        for level_name in levels or []:
            number = cls._floor_number(level_name)
            if number == "":
                continue
            try:
                numeric = int(number)
            except Exception:
                continue
            values.append((numeric, str(number)))
        values.sort(key=lambda item: item[0])

        result = []
        for _, number in values:
            if number not in result:
                result.append(number)
        return result

    @staticmethod
    def _room_parameter_value(room, name):
        try:
            parameter = room.LookupParameter(name)
        except Exception:
            parameter = None
        if parameter is None:
            return ""

        value = ""
        try:
            value = parameter.AsString() or ""
        except Exception:
            value = ""
        if not value:
            try:
                value = parameter.AsValueString() or ""
            except Exception:
                value = ""
        return str(value or "").strip()

    @staticmethod
    def _floor_number(level_name):
        import re

        text = str(level_name or "").strip()
        if not text:
            return ""

        lowered = text.lower()
        if (
            "rdc" in lowered
            or "rez-de-chaussée" in lowered
            or "rez de chaussée" in lowered
            or "rez-de-chaussee" in lowered
            or "rez de chaussee" in lowered
        ):
            return "0"

        match = re.search(r"[-+]?\d+", text)
        if not match:
            return ""

        try:
            return str(int(match.group(0)))
        except Exception:
            return match.group(0).lstrip("+")

    def _classify_viewports(self, sheet):
        infos = []
        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            if view is None:
                continue

            outline = viewport.GetBoxOutline()
            width = abs(
                float(outline.MaximumPoint.X)
                - float(outline.MinimumPoint.X)
            )
            height = abs(
                float(outline.MaximumPoint.Y)
                - float(outline.MinimumPoint.Y)
            )

            infos.append(
                _TemplateViewportInfo(
                    viewport=viewport,
                    view=view,
                    area=width * height,
                    filled_regions=self._filled_region_count(view),
                    room_tags=self._view_category_count(
                        view,
                        "OST_RoomTags",
                    ),
                    dimensions=self._view_category_count(
                        view,
                        "OST_Dimensions",
                    ),
                )
            )

        if not infos:
            raise ValueError(
                "La feuille modèle doit contenir au moins une vue logement."
            )

        warnings = []

        if len(infos) == 1:
            warnings.append(
                "Aucun viewport de repérage n'a été détecté sur la feuille modèle."
            )
            return infos[0], None, warnings

        location_candidates = [
            info for info in infos
            if info.filled_regions > 0
        ]
        if location_candidates:
            location_candidates.sort(
                key=lambda item: (
                    -item.filled_regions,
                    item.area,
                )
            )
            location = location_candidates[0]
        else:
            location = min(infos, key=lambda item: item.area)
            warnings.append(
                "07D : repérage déduit par la plus petite emprise de viewport, "
                "car aucune zone remplie n'a été détectée."
            )

        main_candidates = [
            info for info in infos
            if info.viewport.Id != location.viewport.Id
        ]
        if not main_candidates:
            raise ValueError(
                "Impossible de distinguer la vue logement du repérage."
            )

        main_candidates.sort(
            key=lambda item: (
                -(item.room_tags + item.dimensions),
                -item.area,
            )
        )
        main = main_candidates[0]

        if len(infos) > 2:
            warnings.append(
                "07D V1 : {} vue(s) placée(s) détectée(s). "
                "La vue logement et le repérage sont générés automatiquement ; "
                "les autres viewports seront traités dans l'extension multi-vues.".format(
                    len(infos)
                )
            )

        return main, location, warnings

    def detect_multilevel_template_mode(self, template_sheet_unique_id):
        """Déduit le comportement multi-niveaux depuis la feuille modèle.

        1 vue logement + 1 repérage  -> une feuille par niveau
        2 vues logement + 1 repérage -> une feuille unique avec deux niveaux
        """
        sheet = self._get_element(
            template_sheet_unique_id,
            "La feuille modèle n'existe plus.",
        )

        infos = []
        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            if view is None:
                continue

            outline = viewport.GetBoxOutline()
            width = abs(
                float(outline.MaximumPoint.X)
                - float(outline.MinimumPoint.X)
            )
            height = abs(
                float(outline.MaximumPoint.Y)
                - float(outline.MinimumPoint.Y)
            )
            infos.append(
                _TemplateViewportInfo(
                    viewport=viewport,
                    view=view,
                    area=width * height,
                    filled_regions=self._filled_region_count(view),
                    room_tags=self._view_category_count(
                        view,
                        "OST_RoomTags",
                    ),
                    dimensions=self._view_category_count(
                        view,
                        "OST_Dimensions",
                    ),
                )
            )

        if not infos:
            raise ValueError(
                "La feuille modèle doit contenir au moins une vue logement."
            )

        location_candidates = [
            info for info in infos
            if info.filled_regions > 0
        ]
        if location_candidates:
            location_candidates.sort(
                key=lambda item: (
                    -item.filled_regions,
                    item.area,
                )
            )
            location = location_candidates[0]
            main_infos = [
                info for info in infos
                if info.viewport.Id != location.viewport.Id
            ]
        else:
            location = None
            main_infos = list(infos)

            # Avec 3 viewports ou plus, conserver le comportement historique :
            # la plus petite vue est probablement le repérage.
            if len(infos) >= 3:
                location = min(infos, key=lambda item: item.area)
                main_infos = [
                    info for info in infos
                    if info.viewport.Id != location.viewport.Id
                ]

        count = len(main_infos)
        if count == 1:
            return {
                "mode": "sheet_per_level",
                "main_view_count": 1,
                "summary": (
                    "Modèle 1 vue détecté : pour un logement sur plusieurs "
                    "niveaux, une feuille sera créée par niveau."
                ),
            }

        if count == 2:
            scales = sorted(
                set(
                    int(getattr(info.view, "Scale", 0) or 0)
                    for info in main_infos
                )
            )
            if len(scales) != 1 or not scales[0]:
                raise ValueError(
                    "Les deux vues logement du modèle doivent être à la même échelle."
                )
            return {
                "mode": "one_sheet",
                "main_view_count": 2,
                "summary": (
                    "Modèle 2 vues détecté : les deux niveaux seront placés "
                    "sur une seule feuille, aux positions du modèle."
                ),
            }

        raise ValueError(
            "Le modèle contient {} vues logement. L'Étape 09 prend en charge "
            "1 vue logement (une feuille par niveau) ou 2 vues logement "
            "(une seule feuille multi-niveaux).".format(count)
        )

    def _classify_multilevel_viewports(self, sheet, expected_levels=2):
        """09B.2 : détecte les viewports logement d'un modèle multi-niveaux.

        Le repérage est identifié comme en 07D. Tous les autres viewports sont
        considérés comme vues logement et doivent être au même nombre que les
        niveaux à représenter.
        """
        infos = []
        for viewport_id in list(sheet.GetAllViewports() or []):
            viewport = self.document.GetElement(viewport_id)
            if viewport is None:
                continue
            view = self.document.GetElement(viewport.ViewId)
            if view is None:
                continue

            outline = viewport.GetBoxOutline()
            width = abs(
                float(outline.MaximumPoint.X)
                - float(outline.MinimumPoint.X)
            )
            height = abs(
                float(outline.MaximumPoint.Y)
                - float(outline.MinimumPoint.Y)
            )

            infos.append(
                _TemplateViewportInfo(
                    viewport=viewport,
                    view=view,
                    area=width * height,
                    filled_regions=self._filled_region_count(view),
                    room_tags=self._view_category_count(
                        view,
                        "OST_RoomTags",
                    ),
                    dimensions=self._view_category_count(
                        view,
                        "OST_Dimensions",
                    ),
                )
            )

        if len(infos) < int(expected_levels or 0):
            raise ValueError(
                "Le modèle multi-niveaux doit contenir au moins {} vues logement."
                .format(expected_levels)
            )

        warnings = []
        location_candidates = [
            info for info in infos
            if info.filled_regions > 0
        ]
        if location_candidates:
            location_candidates.sort(
                key=lambda item: (
                    -item.filled_regions,
                    item.area,
                )
            )
            location = location_candidates[0]
            mains = [
                info for info in infos
                if info.viewport.Id != location.viewport.Id
            ]
        else:
            location = None
            mains = list(infos)
            if len(infos) > int(expected_levels or 0):
                location = min(infos, key=lambda item: item.area)
                mains = [
                    info for info in infos
                    if info.viewport.Id != location.viewport.Id
                ]
                warnings.append(
                    "09B.2 : repérage déduit par la plus petite emprise de viewport."
                )
            else:
                warnings.append(
                    "09B.2 : aucun repérage détecté sur le modèle multi-niveaux."
                )
        if len(mains) != int(expected_levels or 0):
            raise ValueError(
                "Le modèle multi-niveaux doit contenir exactement {} vues "
                "logement en plus du repérage ; {} ont été détectées."
                .format(expected_levels, len(mains))
            )

        scales = sorted(
            set(
                int(getattr(info.view, "Scale", 0) or 0)
                for info in mains
            )
        )
        if len(scales) != 1 or not scales[0]:
            raise ValueError(
                "Les vues logement du modèle multi-niveaux doivent utiliser "
                "exactement la même échelle."
            )

        centers = []
        for info in mains:
            center = info.viewport.GetBoxCenter()
            centers.append(
                (
                    info,
                    float(center.X),
                    float(center.Y),
                )
            )

        if len(centers) >= 2:
            x_span = max(item[1] for item in centers) - min(
                item[1] for item in centers
            )
            y_span = max(item[2] for item in centers) - min(
                item[2] for item in centers
            )
        else:
            x_span = 0.0
            y_span = 0.0

        if x_span >= y_span:
            centers.sort(key=lambda item: item[1])
            layout_mode = "horizontal"
        else:
            centers.sort(key=lambda item: -item[2])
            layout_mode = "vertical"

        ordered_mains = [item[0] for item in centers]
        return ordered_mains, location, scales[0], layout_mode, warnings

    def _resolve_source_view(self, housing, model_main_view):
        candidates = list(
            self.prototype_view_service.source_views_for_housing(housing)
            or []
        )
        if not candidates:
            raise ValueError(
                "Aucune vue source plan duplicable n'a été trouvée au niveau du logement."
            )

        warnings = []
        primary = self._primary_view(model_main_view)
        primary_name = str(getattr(primary, "Name", "") or "")
        source_token = ""
        if primary_name.startswith("PDV MASTER - "):
            parts = primary_name.rsplit(" - ", 1)
            if len(parts) == 2:
                source_token = parts[1].strip().lower()

        if source_token:
            matching = [
                candidate for candidate in candidates
                if self._source_token(candidate.unique_id) == source_token
            ]
            if len(matching) == 1:
                return matching[0], warnings

        model_template_id = getattr(primary, "ViewTemplateId", None)
        model_type_id = None
        try:
            model_type_id = primary.GetTypeId()
        except Exception:
            model_type_id = None

        ranked = []
        for candidate in candidates:
            view = self.document.GetElement(candidate.unique_id)
            score = 0
            if view is not None:
                try:
                    if (
                        model_template_id is not None
                        and view.ViewTemplateId == model_template_id
                    ):
                        score += 100
                except Exception:
                    pass
                try:
                    if (
                        model_type_id is not None
                        and view.GetTypeId() == model_type_id
                    ):
                        score += 20
                except Exception:
                    pass
            if int(getattr(candidate, "scale", 0) or 0) == int(
                getattr(model_main_view, "Scale", 0) or 0
            ):
                score += 5
            ranked.append((score, candidate))

        ranked.sort(
            key=lambda item: (
                -item[0],
                item[1].name.lower(),
            )
        )
        best_score = ranked[0][0]
        ties = [item for item in ranked if item[0] == best_score]
        chosen = ranked[0][1]

        if len(ties) > 1:
            warnings.append(
                "07D : plusieurs vues sources équivalentes ont été trouvées ; "
                "« {} » a été retenue automatiquement.".format(chosen.name)
            )

        return chosen, warnings

    def _resolve_location_source_view(
        self,
        housing,
        model_location_view,
    ):
        """Choisit une vue de niveau large pour reconstruire le repérage.

        Le repérage ne doit jamais reprendre une vue logement recadrée d'un
        autre étage. On privilégie le même gabarit/type que le modèle, puis la
        plus grande emprise de crop disponible au niveau cible.
        """
        candidates = list(
            self.location_plan_service.source_views_for_housing(housing)
            or []
        )
        if not candidates:
            raise ValueError(
                "Aucune vue source de repérage n'a été trouvée au niveau du logement."
            )

        warnings = []
        model_template_id = getattr(
            model_location_view,
            "ViewTemplateId",
            None,
        )
        model_type_id = None
        try:
            model_type_id = model_location_view.GetTypeId()
        except Exception:
            model_type_id = None

        ranked = []
        for candidate in candidates:
            view = self.document.GetElement(candidate.unique_id)
            score = 0
            crop_area = 0.0

            if view is not None:
                try:
                    if (
                        model_template_id is not None
                        and view.ViewTemplateId == model_template_id
                    ):
                        score += 100
                except Exception:
                    pass

                try:
                    if (
                        model_type_id is not None
                        and view.GetTypeId() == model_type_id
                    ):
                        score += 20
                except Exception:
                    pass

                try:
                    if not bool(getattr(view, "CropBoxActive", False)):
                        score += 15
                except Exception:
                    pass

                crop_area = self._view_crop_area(view)

            ranked.append((score, crop_area, candidate))

        ranked.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                item[2].name.lower(),
            )
        )
        chosen = ranked[0][2]

        if len(ranked) > 1:
            best = ranked[0]
            second = ranked[1]
            if best[0] == second[0] and abs(best[1] - second[1]) <= 1e-9:
                warnings.append(
                    "07D : plusieurs vues sources de repérage équivalentes ; "
                    "« {} » a été retenue automatiquement.".format(
                        chosen.name
                    )
                )

        return chosen, warnings

    @staticmethod
    def _view_crop_area(view):
        try:
            box = view.CropBox
            if box is None:
                return 0.0
            width = abs(float(box.Max.X) - float(box.Min.X))
            height = abs(float(box.Max.Y) - float(box.Min.Y))
            return width * height
        except Exception:
            return 0.0

    def _primary_view(self, view):
        try:
            primary_id = view.GetPrimaryViewId()
            from Autodesk.Revit.DB import ElementId
            if primary_id != ElementId.InvalidElementId:
                primary = self.document.GetElement(primary_id)
                if primary is not None:
                    return primary
        except Exception:
            pass
        return view

    def _schedule_instances(self, sheet):
        from Autodesk.Revit.DB import FilteredElementCollector, ScheduleSheetInstance

        result = []
        for instance in (
            FilteredElementCollector(self.document, sheet.Id)
            .OfClass(ScheduleSheetInstance)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            try:
                if bool(getattr(instance, "IsTitleblockRevisionSchedule", False)):
                    continue
            except Exception:
                pass
            result.append(instance)

        return sorted(
            result,
            key=lambda item: (
                -float(getattr(getattr(item, "Point", None), "Y", 0.0)),
                float(getattr(getattr(item, "Point", None), "X", 0.0)),
            ),
        )

    def _filled_region_count(self, view):
        from Autodesk.Revit.DB import FilledRegion, FilteredElementCollector

        count = 0
        seen = set()
        for view_id in self._annotation_view_ids(view):
            try:
                regions = (
                    FilteredElementCollector(self.document, view_id)
                    .OfClass(FilledRegion)
                    .WhereElementIsNotElementType()
                    .ToElements()
                )
            except Exception:
                regions = []

            for region in regions:
                key = self._element_id_value(region.Id)
                if key in seen:
                    continue
                seen.add(key)
                count += 1
        return count

    def _annotation_view_ids(self, view):
        result = [view.Id]
        try:
            from Autodesk.Revit.DB import ElementId
            primary_id = view.GetPrimaryViewId()
            if (
                primary_id is not None
                and primary_id != ElementId.InvalidElementId
            ):
                result.append(primary_id)
        except Exception:
            pass
        return result

    def _view_category_count(self, view, built_in_name):
        from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

        try:
            category = getattr(BuiltInCategory, built_in_name)
            return len(
                list(
                    FilteredElementCollector(self.document, view.Id)
                    .OfCategory(category)
                    .WhereElementIsNotElementType()
                    .ToElements()
                )
            )
        except Exception:
            return 0

    def _dominant_element_type(self, view, built_in_name):
        from Autodesk.Revit.DB import BuiltInCategory, FilteredElementCollector

        elements = []
        try:
            category = getattr(BuiltInCategory, built_in_name)
            seen = set()
            for view_id in self._annotation_view_ids(view):
                current = (
                    FilteredElementCollector(self.document, view_id)
                    .OfCategory(category)
                    .WhereElementIsNotElementType()
                    .ToElements()
                )
                for element in current:
                    key = self._element_id_value(element.Id)
                    if key in seen:
                        continue
                    seen.add(key)
                    elements.append(element)
        except Exception:
            elements = []

        counts = {}
        type_ids = {}
        for element in elements:
            try:
                type_id = element.GetTypeId()
                key = self._element_id_value(type_id)
            except Exception:
                continue
            counts[key] = counts.get(key, 0) + 1
            type_ids[key] = type_id

        if not counts:
            return None

        key = sorted(
            counts,
            key=lambda value: (-counts[value], value),
        )[0]
        return self.document.GetElement(type_ids[key])

    def _filled_region_type(self, view):
        from Autodesk.Revit.DB import FilledRegion, FilteredElementCollector

        regions = []
        seen = set()
        for view_id in self._annotation_view_ids(view):
            try:
                current = (
                    FilteredElementCollector(self.document, view_id)
                    .OfClass(FilledRegion)
                    .WhereElementIsNotElementType()
                    .ToElements()
                )
            except Exception:
                current = []

            for region in current:
                key = self._element_id_value(region.Id)
                if key in seen:
                    continue
                seen.add(key)
                regions.append(region)

        if not regions:
            return None
        return self.document.GetElement(regions[0].GetTypeId())

    def _view_template(self, view):
        try:
            from Autodesk.Revit.DB import ElementId
            template_id = view.ViewTemplateId
            if (
                template_id is None
                or template_id == ElementId.InvalidElementId
            ):
                return None
            return self.document.GetElement(template_id)
        except Exception:
            return None

    def _get_element(self, unique_id, message):
        if not unique_id:
            raise ValueError(message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(message)
        return element

    @staticmethod
    def _sheet_label(sheet):
        return "{} — {}".format(
            getattr(sheet, "SheetNumber", "") or "Sans numéro",
            getattr(sheet, "Name", "") or "",
        ).rstrip(" —")

    @staticmethod
    def _source_token(unique_id):
        text = "".join(
            char for char in str(unique_id or "")
            if char.isalnum()
        )
        return text[-8:].lower() if text else ""

    @staticmethod
    def _element_id_value(element_id):
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        return int(element_id.IntegerValue)

    @staticmethod
    def _element_type_name(element_type):
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
            return str(getattr(element_type, "Name", "") or "")
        except Exception:
            return ""
