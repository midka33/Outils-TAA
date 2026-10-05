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
    ):
        self.analysis_service = analysis_service
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service
        self.location_plan_service = location_plan_service
        self.room_tag_service = room_tag_service

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
