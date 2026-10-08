# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Contrôleur de la fenêtre Calculs des pièces."""

from calculation.workflow_models import CalculationRequest


class CalculationContext(object):
    def __init__(
        self,
        rooms_count,
        all_parameters,
        numeric_parameters,
        target_parameters,
    ):
        self.rooms_count = int(rooms_count)
        self.all_parameters = list(all_parameters or [])
        self.numeric_parameters = list(numeric_parameters or [])
        self.target_parameters = list(target_parameters or [])


class CalculationController(object):
    """Façade UI sans dépendance WPF."""

    def __init__(
        self,
        collector_service,
        parameter_service,
        parameter_validator,
        unit_service,
        workflow,
        settings_service,
    ):
        self.collector_service = collector_service
        self.parameter_service = parameter_service
        self.parameter_validator = parameter_validator
        self.unit_service = unit_service
        self.workflow = workflow
        self.settings_service = settings_service

    def load_context(self):
        """Charge le contexte UI en un seul parcours des pièces.

        get_parameter_descriptors() calcule déjà toutes les métadonnées utiles
        (type, écriture, déverrouillage de groupe). Refaire le même parcours
        avec numeric_only puis writable_only multipliait inutilement les appels
        à l'API Revit, particulièrement coûteux sur les gros projets.
        """
        rooms = self.collector_service.collect_all_rooms()
        all_parameters = self.parameter_service.get_parameter_descriptors(
            rooms
        )

        numeric = [
            descriptor
            for descriptor in all_parameters
            if descriptor.is_numeric
        ]

        targets = [
            descriptor
            for descriptor in all_parameters
            if (
                descriptor.write_supported
                and descriptor.storage_type
                in self.parameter_validator.SUPPORTED_TARGET_TYPES
            )
        ]

        return CalculationContext(
            len(rooms),
            all_parameters,
            numeric,
            targets,
        )

    def create_request(
        self,
        group_parameter,
        source_parameter,
        target_parameter,
        filter_parameter=None,
        filter_value=None,
        output_unit_type_id=None,
    ):
        return CalculationRequest(
            group_parameter=group_parameter,
            source_parameter=source_parameter,
            target_parameter=target_parameter,
            filter_parameter=filter_parameter,
            filter_value=filter_value,
            output_unit_type_id=output_unit_type_id,
        )

    def prepare(self, request, progress=None):
        return self.workflow.prepare(request, progress=progress)

    def execute(self, prepared, progress=None):
        return self.workflow.execute(prepared, progress=progress)

    def unit_options(self, source_descriptor):
        return self.unit_service.get_unit_options(source_descriptor)

    def load_settings(self):
        return self.settings_service.load()

    def save_settings(self, request):
        return self.settings_service.save_request(request)

    def match_saved_descriptor(self, saved_data, available):
        return self.settings_service.match_descriptor(saved_data, available)
