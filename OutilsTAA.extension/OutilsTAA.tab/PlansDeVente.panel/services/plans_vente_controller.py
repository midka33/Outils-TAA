# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Contrôleur du module Plans de vente."""


class PlansVenteController(object):
    def __init__(self, analysis_service, prototype_view_service, schedule_service):
        self.analysis_service = analysis_service
        self.prototype_view_service = prototype_view_service
        self.schedule_service = schedule_service

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
