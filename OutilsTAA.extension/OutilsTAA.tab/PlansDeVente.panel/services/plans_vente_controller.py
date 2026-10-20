# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from plans_vente.multilevel import split_housing_by_level

"""Contrôleur du module Plans de vente."""


class PlansVenteController(object):
    def __init__(
        self,
        analysis_service,
        prototype_view_service,
        schedule_service,
        location_plan_service,
        room_tag_service,
        dimension_service,
        sheet_assembly_service,
        full_generation_service=None,
    ):
        self.analysis_service = analysis_service
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service
        self.location_plan_service = location_plan_service
        self.room_tag_service = room_tag_service
        self.dimension_service = dimension_service
        self.sheet_assembly_service = sheet_assembly_service
        self.full_generation_service = full_generation_service

    def load_context(self, include_links=False):
        self.schedule_service._link_schedule_identities = None
        self.dimension_service._linked_services = {}
        return self.analysis_service.load_context(include_links=include_links)

    def analyze(self, descriptor):
        return self.analysis_service.analyze(descriptor)

    def filter_housings(
        self,
        housings,
        descriptor,
        operator_key,
        expected_value="",
    ):
        return self.analysis_service.filter_housings(
            housings,
            descriptor,
            operator_key,
            expected_value,
        )

    def split_housing_by_level(self, housing):
        return split_housing_by_level(housing)

    def source_views_for_housing(self, housing):
        return self.prototype_view_service.source_views_for_housing(housing)

    def create_view_prototype(
        self,
        housing,
        source_view_unique_id,
        margin_mm,
        target_scale,
    ):
        return self.prototype_view_service.create_dependent_crop_view(
            housing,
            source_view_unique_id,
            margin_mm,
            target_scale,
        )

    def schedule_templates(self, descriptor):
        return self.schedule_service.list_templates(descriptor)

    def create_schedule_prototype(
        self,
        housing,
        descriptor,
        interior_template_unique_id,
        exterior_template_unique_id,
    ):
        return self.schedule_service.create_pair(
            housing,
            descriptor,
            interior_template_unique_id,
            exterior_template_unique_id,
        )

    def location_source_views_for_housing(self, housing):
        return self.location_plan_service.source_views_for_housing(housing)

    def location_view_templates(self):
        return self.location_plan_service.list_view_templates()

    def location_filled_region_types(self):
        return self.location_plan_service.list_filled_region_types()

    def create_location_plan_prototype(
        self,
        housing,
        source_view_unique_id,
        filled_region_type_unique_id,
        template_unique_id=None,
    ):
        return self.location_plan_service.create_location_plan(
            housing,
            source_view_unique_id,
            filled_region_type_unique_id,
            template_unique_id,
        )


    def room_tag_types(self):
        return self.room_tag_service.list_tag_types()

    def room_tag_target_views(self, housing):
        return self.room_tag_service.target_views_for_housing(housing)

    def create_room_tags(
        self,
        housing,
        target_view_unique_id,
        room_tag_type_unique_id,
    ):
        return self.room_tag_service.create_tags(
            housing,
            target_view_unique_id,
            room_tag_type_unique_id,
        )


    def room_tag_build_id(self):
        return getattr(
            self.room_tag_service,
            "build_id",
            "room-tag-service-build-inconnu",
        )


    def dimension_types(self):
        return self.dimension_service.list_dimension_types()

    def dimension_target_views(self, housing):
        return self.dimension_service.target_views_for_housing(housing)

    def create_dimensions(
        self,
        housing,
        target_view_unique_id,
        dimension_type_unique_id,
    ):
        return self.dimension_service.create_dimensions(
            housing,
            target_view_unique_id,
            dimension_type_unique_id,
        )

    def dimension_build_id(self):
        return getattr(
            self.dimension_service,
            "build_id",
            "dimension-service-build-inconnu",
        )



    def plan_exists(self, housing_key):
        return self.sheet_assembly_service.plan_exists(housing_key)

    def sheet_templates(self):
        return self.sheet_assembly_service.list_sheet_templates()

    def export_sheet_preview(self, template_sheet_unique_id, output_base_path):
        """Exporte la feuille sélectionnée en image PNG temporaire."""
        if not template_sheet_unique_id:
            raise ValueError("Sélectionnez une feuille modèle.")
        if not output_base_path:
            raise ValueError("Chemin d'aperçu manquant.")

        document = self.full_generation_service.document
        sheet = document.GetElement(template_sheet_unique_id)
        if sheet is None:
            raise ValueError("La feuille modèle n'existe plus.")

        from Autodesk.Revit.DB import (
            ExportRange,
            ImageExportOptions,
            ImageFileType,
            ImageResolution,
            ZoomFitType,
        )
        from System.Collections.Generic import List
        from Autodesk.Revit.DB import ElementId

        options = ImageExportOptions()
        options.ExportRange = ExportRange.SetOfViews
        options.FilePath = output_base_path
        options.HLRandWFViewsFileType = ImageFileType.PNG
        options.ShadowViewsFileType = ImageFileType.PNG
        options.ImageResolution = ImageResolution.DPI_150
        options.ZoomType = ZoomFitType.FitToPage
        options.PixelSize = 1800

        view_ids = List[ElementId]()
        view_ids.Add(sheet.Id)
        options.SetViewsAndSheets(view_ids)
        document.ExportImage(options)

        import os

        folder = os.path.dirname(output_base_path)
        prefix = os.path.basename(output_base_path)
        candidates = []
        try:
            for name in os.listdir(folder):
                lowered = name.lower()
                if (
                    name.startswith(prefix)
                    and lowered.endswith(".png")
                ):
                    full_path = os.path.join(folder, name)
                    candidates.append(
                        (os.path.getmtime(full_path), full_path)
                    )
        except Exception:
            candidates = []

        if not candidates:
            direct = output_base_path + ".png"
            if os.path.exists(direct):
                return direct
            raise RuntimeError(
                "Revit n'a pas produit l'image PNG de la feuille modèle."
            )

        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def inspect_sheet_template(self, template_sheet_unique_id):
        return self.sheet_assembly_service.inspect_sheet_template(
            template_sheet_unique_id
        )

    def sheet_title_block_types(self):
        return self.sheet_assembly_service.list_title_block_types()

    def sheet_assembly_readiness(self, housing, main_view_unique_id):
        return self.sheet_assembly_service.readiness(
            housing,
            main_view_unique_id,
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
        return self.sheet_assembly_service.create_sheet_from_template(
            housing,
            template_sheet_unique_id,
            main_view_unique_id,
            template_main_viewport_unique_id,
            template_location_viewport_unique_id,
            template_interior_schedule_instance_unique_id,
            template_exterior_schedule_instance_unique_id,
            auto_fit_main_view=auto_fit_main_view,
            allowed_scales=allowed_scales,
        )

    def create_sheet_assembly(
        self,
        housing,
        title_block_type_unique_id,
        main_view_unique_id,
    ):
        return self.sheet_assembly_service.create_sheet(
            housing,
            title_block_type_unique_id,
            main_view_unique_id,
        )

    def sheet_assembly_build_id(self):
        return getattr(
            self.sheet_assembly_service,
            "build_id",
            "sheet-assembly-service-build-inconnu",
        )


    def inspect_full_generation_template(
        self,
        template_sheet_unique_id,
        descriptor,
    ):
        if self.full_generation_service is None:
            raise RuntimeError("Service de génération complète 07D indisponible.")
        return self.full_generation_service.inspect_template(
            template_sheet_unique_id,
            descriptor,
        )

    def generate_full_plan(
        self,
        housing,
        descriptor,
        template_sheet_unique_id,
        allowed_scales=None,
        crop_margin_mm=None,
        auto_fit_main_view=True,
        building_parameter_name="",
        typology_parameter_name="",
        main_view_zone_line_style="",
        progress_callback=None,
    ):
        if self.full_generation_service is None:
            raise RuntimeError("Service de génération complète 07D indisponible.")
        return self._generate_with_source_context(
            self.full_generation_service.generate, housing,
            descriptor,
            template_sheet_unique_id,
            allowed_scales=allowed_scales,
            crop_margin_mm=crop_margin_mm,
            auto_fit_main_view=auto_fit_main_view,
            building_parameter_name=building_parameter_name,
            typology_parameter_name=typology_parameter_name,
            main_view_zone_line_style=main_view_zone_line_style,
            progress_callback=progress_callback,
        )

    def diagnose_template_zones(
        self,
        template_sheet_unique_id,
        subcategory_name="Cartouches",
    ):
        if self.full_generation_service is None:
            raise RuntimeError(
                "Service de génération complète 07D indisponible."
            )
        return self.full_generation_service.diagnose_template_zones(
            template_sheet_unique_id,
            subcategory_name=subcategory_name,
        )

    def detect_multilevel_template_mode(self, template_sheet_unique_id):
        if self.full_generation_service is None:
            raise RuntimeError("Service de génération complète 07D indisponible.")
        return self.full_generation_service.detect_multilevel_template_mode(
            template_sheet_unique_id
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
        main_view_zone_line_style="",
        progress_callback=None,
    ):
        if self.full_generation_service is None:
            raise RuntimeError("Service de génération complète 07D indisponible.")
        return self._generate_with_source_context(
            self.full_generation_service.generate_multilevel_one_sheet, housing,
            descriptor=descriptor,
            template_sheet_unique_id=template_sheet_unique_id,
            allowed_scales=allowed_scales,
            crop_margin_mm=crop_margin_mm,
            auto_fit_main_view=auto_fit_main_view,
            building_parameter_name=building_parameter_name,
            typology_parameter_name=typology_parameter_name,
            main_view_zone_line_style=main_view_zone_line_style,
            progress_callback=progress_callback,
        )

    def _generate_with_source_context(self, method, housing, *args, **kwargs):
        if getattr(housing, "source_key", "HOST") == "HOST":
            return method(housing, *args, **kwargs)
        phase = ["Préparation"]
        callback = kwargs.get("progress_callback")
        def progress(*values, **named):
            phase[0] = str(named.get("phase") or (values[1] if len(values) > 1 else phase[0]))
            if callback is not None:
                callback(*values, **named)
        kwargs["progress_callback"] = progress
        try:
            return method(housing, *args, **kwargs)
        except Exception as error:
            # Trace the actual failing service, even between completed progress milestones.
            import sys
            stages = {"crop_geometry_service.py": "Crop", "prototype_view_service.py": "Vue logement",
                      "room_tag_service.py": "Étiquettes", "dimension_service.py": "Cotations",
                      "location_plan_service.py": "Repérage", "schedule_service.py": "Nomenclatures",
                      "sheet_assembly_service.py": "Assemblage / cartouche"}
            trace = sys.exc_info()[2]
            while trace is not None:
                filename = trace.tb_frame.f_code.co_filename.replace(chr(92), "/").rsplit("/", 1)[-1]
                phase[0] = stages.get(filename, phase[0])
                trace = trace.tb_next
            raise RuntimeError("{} — étape {} : {}".format(housing.report_label, phase[0], error))

    def full_generation_build_id(self):
        if self.full_generation_service is None:
            return "full-generation-service-indisponible"
        return getattr(
            self.full_generation_service,
            "build_id",
            "full-generation-service-build-inconnu",
        )
