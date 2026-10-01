# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Orchestration du workflow READ → DATA → CALCULATE → VALIDATE → WRITE."""

from common.exceptions import ValidationError
from common.transaction import RevitTransaction
from calculation.models import RoomCalculationItem
from calculation.workflow_models import (
    CalculationExecutionReport,
    WriteOperation,
    WriteResult,
)


class PreparedCalculation(object):
    """Plan runtime contenant uniquement ce qui est nécessaire à l'écriture."""

    def __init__(
        self,
        request,
        result,
        room_by_key,
        operations,
        total_rooms,
        filtered_rooms,
        warnings=None,
    ):
        self.request = request
        self.result = result
        self.room_by_key = dict(room_by_key or {})
        self.operations = list(operations or [])
        self.total_rooms = int(total_rooms)
        self.filtered_rooms = int(filtered_rooms)
        self.warnings = list(warnings or [])


class RoomCalculationWorkflow(object):
    """Coordonne collecte, filtre, calcul, validation et écriture."""

    TRANSACTION_NAME = "Outils TAA - Calculs des pièces"

    def __init__(
        self,
        document,
        collector_service,
        parameter_service,
        parameter_validator,
        room_filter,
        calculator,
        writer,
        transaction_factory=None,
    ):
        self.document = document
        self.collector_service = collector_service
        self.parameter_service = parameter_service
        self.parameter_validator = parameter_validator
        self.room_filter = room_filter
        self.calculator = calculator
        self.writer = writer
        self.transaction_factory = transaction_factory

    def prepare(self, request, progress=None):
        validation = self.parameter_validator.validate_pair(
            request.source_parameter,
            request.target_parameter,
        )
        if not validation.is_valid:
            raise ValidationError("
".join(validation.errors))

        rooms = self.collector_service.collect_all_rooms()
        filtered = self.room_filter.apply(
            rooms,
            parameter_name=request.filter_parameter,
            expected_value=request.filter_value,
            value_reader=self.parameter_service.read_value,
        )

        room_by_key = {}
        items = []

        for index, room in enumerate(filtered):
            room_key = self._room_key(room, index)
            room_by_key[room_key] = room
            items.append(
                RoomCalculationItem(
                    room_key,
                    self.parameter_service.read_value(
                        room,
                        request.group_parameter,
                        default=None,
                    ),
                    self.parameter_service.read_value(
                        room,
                        request.source_parameter,
                        default=None,
                    ),
                )
            )

        result = self.calculator.calculate(items, progress=progress)
        operations = []

        for group_value, total in result.totals.items():
            for room_key in result.get_members(group_value):
                operations.append(
                    WriteOperation(
                        room_key=room_key,
                        group_value=group_value,
                        value=total,
                    )
                )

        return PreparedCalculation(
            request=request,
            result=result,
            room_by_key=room_by_key,
            operations=operations,
            total_rooms=len(rooms),
            filtered_rooms=len(filtered),
            warnings=validation.warnings,
        )

    def execute(self, prepared, progress=None):
        valid = []
        failed = []

        total_ops = len(prepared.operations)
        for index, operation in enumerate(prepared.operations, 1):
            room = prepared.room_by_key.get(operation.room_key)
            if room is None:
                failed.append(
                    WriteResult(
                        operation.room_key,
                        False,
                        "Pièce introuvable au moment de l'écriture.",
                        operation.group_value,
                    )
                )
                continue

            try:
                prepared_value = self.writer.prepare_value(
                    prepared.request.source_parameter,
                    prepared.request.target_parameter,
                    operation.value,
                    prepared.request.output_unit_type_id,
                )
                self._validate_target_on_room(
                    room,
                    prepared.request.target_parameter,
                )
                valid.append((operation, room, prepared_value))
            except Exception as error:
                failed.append(
                    WriteResult(
                        operation.room_key,
                        False,
                        str(error),
                        operation.group_value,
                    )
                )

            if progress is not None:
                progress(index, total_ops)

        if not valid:
            return CalculationExecutionReport(
                failed_results=failed,
                skipped=prepared.result.skipped,
                warnings=prepared.warnings,
            )

        successful = []
        temporary_success = []

        try:
            with RevitTransaction(
                self.document,
                self.TRANSACTION_NAME,
                transaction_factory=self.transaction_factory,
            ):
                for operation, room, prepared_value in valid:
                    try:
                        self.writer.write_value(
                            room,
                            prepared.request.target_parameter,
                            prepared_value,
                        )
                        temporary_success.append(
                            WriteResult(
                                operation.room_key,
                                True,
                                "Valeur écrite.",
                                operation.group_value,
                            )
                        )
                    except Exception as error:
                        failed.append(
                            WriteResult(
                                operation.room_key,
                                False,
                                str(error),
                                operation.group_value,
                            )
                        )

            successful = temporary_success
        except Exception as error:
            rollback_message = (
                "Transaction annulée : {}.".format(error)
            )
            for item in temporary_success:
                failed.append(
                    WriteResult(
                        item.room_key,
                        False,
                        rollback_message,
                        item.group_value,
                    )
                )
            return CalculationExecutionReport(
                success_results=[],
                failed_results=failed,
                skipped=prepared.result.skipped,
                warnings=prepared.warnings,
                transaction_error=str(error),
            )

        return CalculationExecutionReport(
            success_results=successful,
            failed_results=failed,
            skipped=prepared.result.skipped,
            warnings=prepared.warnings,
        )

    def _validate_target_on_room(self, room, target_descriptor):
        parameter = self.parameter_service.get_parameter(room, target_descriptor)
        if parameter is None:
            raise ValidationError(
                "Le paramètre destination '{}' est absent.".format(
                    target_descriptor.name
                )
            )
        if not self.parameter_service.is_writable(parameter):
            raise ValidationError(
                "Le paramètre destination '{}' est en lecture seule.".format(
                    target_descriptor.name
                )
            )

    @staticmethod
    def _room_key(room, fallback_index):
        unique_id = getattr(room, "UniqueId", None)
        if unique_id:
            return str(unique_id)

        element_id = getattr(room, "Id", None)
        if element_id is not None:
            if hasattr(element_id, "Value"):
                return str(element_id.Value)
            if hasattr(element_id, "IntegerValue"):
                return str(element_id.IntegerValue)

        return "runtime-room-{}".format(fallback_index)
