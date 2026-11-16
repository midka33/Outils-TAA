# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Modèles purs du workflow Calculs des pièces."""


class CalculationRequest(object):
    """Configuration nécessaire à un calcul."""

    def __init__(
        self,
        group_parameter,
        source_parameter,
        target_parameter,
        filter_parameter=None,
        filter_value=None,
        output_unit_type_id=None,
    ):
        self.group_parameter = group_parameter
        self.source_parameter = source_parameter
        self.target_parameter = target_parameter
        self.filter_parameter = filter_parameter
        self.filter_value = filter_value
        self.output_unit_type_id = output_unit_type_id


class WriteOperation(object):
    """Écriture attendue pour une pièce."""

    def __init__(self, room_key, group_value, value):
        self.room_key = room_key
        self.group_value = group_value
        self.value = value


class WriteResult(object):
    """Résultat individuel d'une écriture."""

    def __init__(self, room_key, success, message="", group_value=None):
        self.room_key = room_key
        self.success = bool(success)
        self.message = message or ""
        self.group_value = group_value


class CalculationExecutionReport(object):
    """Rapport final après écriture."""

    def __init__(
        self,
        success_results=None,
        failed_results=None,
        skipped=None,
        warnings=None,
        transaction_error=None,
    ):
        self.success_results = list(success_results or [])
        self.failed_results = list(failed_results or [])
        self.skipped = list(skipped or [])
        self.warnings = list(warnings or [])
        self.transaction_error = transaction_error

    @property
    def success_count(self):
        return len(self.success_results)

    @property
    def failed_count(self):
        return len(self.failed_results)

    @property
    def is_success(self):
        return self.failed_count == 0 and not self.transaction_error
