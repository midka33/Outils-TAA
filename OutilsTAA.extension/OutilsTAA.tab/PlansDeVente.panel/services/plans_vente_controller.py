# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
    ):
        self.analysis_service = analysis_service
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service
        self.location_plan_service = location_plan_service
        self.room_tag_service = room_tag_service
        self.dimension_service = dimension_service
        self.sheet_assembly_service = sheet_assembly_service

    def load_context(self):
        return self.analysis_service.load_context()

    def analyze(self, descriptor):
        return self.analysis_service.analyze(descriptor)

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



    def sheet_templates(self):
        return self.sheet_assembly_service.list_sheet_templates()

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
