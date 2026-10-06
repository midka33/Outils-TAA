# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Orchestration du workflow READ → DATA → CALCULATE → VALIDATE → WRITE."""

from common.exceptions import ValidationError
from common.transaction import RevitTransaction
from calculation.group_alignment import GroupAlignmentResolution
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
        self.group_alignment_analysis = None


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
        grouped_parameter_service=None,
        transaction_factory=None,
    ):
        self.document = document
        self.collector_service = collector_service
        self.parameter_service = parameter_service
        self.parameter_validator = parameter_validator
        self.room_filter = room_filter
        self.calculator = calculator
        self.writer = writer
        self.grouped_parameter_service = grouped_parameter_service
        self.transaction_factory = transaction_factory

    def prepare(self, request, progress=None):
        validation = self.parameter_validator.validate_pair(
            request.source_parameter,
            request.target_parameter,
        )
        if not validation.is_valid:
            raise ValidationError("\n".join(validation.errors))

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

        warnings = list(validation.warnings)
        if self._selection_requires_group_override(
            filtered,
            request.target_parameter,
        ):
            warnings.append(
                "Le paramètre destination '{}' est aligné par type de groupe. "
                "Outils TAA analysera les occurrences correspondantes avant "
                "l'écriture et restaurera l'alignement si les valeurs sont "
                "compatibles.".format(request.target_parameter.name)
            )

        return PreparedCalculation(
            request=request,
            result=result,
            room_by_key=room_by_key,
            operations=operations,
            total_rooms=len(rooms),
            filtered_rooms=len(filtered),
            warnings=warnings,
        )

    def analyze_group_alignment(self, prepared):
        """Détecte avant transaction les valeurs incompatibles entre groupes."""
        valid, failed = self._prepare_valid_entries(prepared)
        if failed:
            # Les erreurs locales restent gérées au moment de l'exécution.
            pass

        if self.grouped_parameter_service is None:
            prepared.group_alignment_analysis = None
            return None

        analysis = self.grouped_parameter_service.analyze_conflicts(
            valid_entries=valid,
            target_descriptor=prepared.request.target_parameter,
            parameter_service=self.parameter_service,
            value_formatter=lambda value: self._format_group_value(
                prepared,
                value,
            ),
        )
        prepared.group_alignment_analysis = analysis
        return analysis

    def execute(
        self,
        prepared,
        progress=None,
        group_resolution=None,
    ):
        valid, failed = self._prepare_valid_entries(
            prepared,
            progress=progress,
        )

        if not valid:
            return CalculationExecutionReport(
                failed_results=failed,
                skipped=prepared.result.skipped,
                warnings=prepared.warnings,
            )

        analysis = prepared.group_alignment_analysis
        if analysis is None and self.grouped_parameter_service is not None:
            analysis = self.grouped_parameter_service.analyze_conflicts(
                valid_entries=valid,
                target_descriptor=prepared.request.target_parameter,
                parameter_service=self.parameter_service,
                value_formatter=lambda value: self._format_group_value(
                    prepared,
                    value,
                ),
            )
            prepared.group_alignment_analysis = analysis

        if analysis is not None and analysis.has_conflicts:
            if group_resolution is None:
                return CalculationExecutionReport(
                    failed_results=failed,
                    skipped=prepared.result.skipped,
                    warnings=prepared.warnings,
                    transaction_error=(
                        "Des occurrences d'un même type de groupe produisent "
                        "des valeurs différentes. Un choix utilisateur est "
                        "nécessaire avant l'écriture."
                    ),
                )
            if group_resolution.mode == GroupAlignmentResolution.CANCEL:
                return CalculationExecutionReport(
                    failed_results=failed,
                    skipped=prepared.result.skipped,
                    warnings=prepared.warnings,
                )

        successful = []
        temporary_success = []
        report_warnings = list(prepared.warnings)
        harmonized_count = 0

        try:
            with RevitTransaction(
                self.document,
                self.TRANSACTION_NAME,
                transaction_factory=self.transaction_factory,
            ):
                definitions = self._get_group_override_definitions(valid)
                enabled_definitions = self._enable_group_override(definitions)

                for operation, room, prepared_value, parameter in valid:
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

                keep_variable = (
                    analysis is not None
                    and analysis.has_conflicts
                    and group_resolution is not None
                    and group_resolution.mode
                    == GroupAlignmentResolution.KEEP_VARIABLE
                )

                if (
                    analysis is not None
                    and analysis.has_conflicts
                    and group_resolution is not None
                    and group_resolution.mode
                    == GroupAlignmentResolution.ALIGN_SELECTED
                ):
                    harmonized_count = self._apply_selected_alignment(
                        prepared,
                        analysis,
                        group_resolution,
                    )

                if keep_variable:
                    report_warnings.append(
                        "Le paramètre '{}' reste configuré pour permettre des "
                        "valeurs différentes entre les occurrences de groupes."
                        .format(prepared.request.target_parameter.name)
                    )
                else:
                    realigned = self._restore_group_alignment(
                        enabled_definitions
                    )
                    if realigned:
                        raise ValidationError(
                            "La restauration de l'alignement par type de groupe "
                            "aurait encore modifié {} élément(s). Aucune "
                            "modification n'a été conservée.".format(
                                len(realigned)
                            )
                        )

            successful = temporary_success
        except Exception as error:
            rollback_message = "Transaction annulée : {}.".format(error)
            for operation, room, prepared_value, parameter in valid:
                failed.append(
                    WriteResult(
                        operation.room_key,
                        False,
                        rollback_message,
                        operation.group_value,
                    )
                )
            return CalculationExecutionReport(
                success_results=[],
                failed_results=self._deduplicate_failed_results(failed),
                skipped=prepared.result.skipped,
                warnings=report_warnings,
                transaction_error=str(error),
            )

        if harmonized_count:
            report_warnings.append(
                "{} membre(s) de groupe ont été harmonisé(s) avec les valeurs "
                "choisies afin de conserver l'alignement du paramètre.".format(
                    harmonized_count
                )
            )

        return CalculationExecutionReport(
            success_results=successful,
            failed_results=failed,
            skipped=prepared.result.skipped,
            warnings=report_warnings,
        )

    def _prepare_valid_entries(self, prepared, progress=None):
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
                parameter = self._validate_target_on_room(
                    room,
                    prepared.request.target_parameter,
                )
                valid.append(
                    (operation, room, prepared_value, parameter)
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

            if progress is not None:
                progress(index, total_ops)

        return valid, failed

    def _apply_selected_alignment(
        self,
        prepared,
        analysis,
        group_resolution,
    ):
        written = 0

        for conflict in analysis.conflicts:
            if conflict.key not in group_resolution.selections:
                raise ValidationError(
                    "Aucune valeur n'a été choisie pour '{}' — '{}'.".format(
                        conflict.group_type_name,
                        conflict.member_label,
                    )
                )

            selected_value = group_resolution.selected_value(conflict)
            for element in conflict.elements:
                self.writer.write_value(
                    element,
                    prepared.request.target_parameter,
                    selected_value,
                )
                written += 1

        return written

    def _format_group_value(self, prepared, value):
        if value is None:
            return "(vide)"

        target = prepared.request.target_parameter
        if target.storage_type == "Double":
            unit_type_id = (
                target.unit_type_id
                or prepared.request.source_parameter.unit_type_id
            )
            display_value = value
            if unit_type_id:
                try:
                    display_value = self.writer.unit_service.from_internal(
                        value,
                        unit_type_id=unit_type_id,
                    )
                except Exception:
                    display_value = value

            text = "{0:.3f}".format(display_value)
            text = text.rstrip("0").rstrip(".")
            return text.replace(".", ",")

        return str(value)

    def _validate_target_on_room(self, room, target_descriptor):
        parameter = self.parameter_service.get_parameter(
            room,
            target_descriptor,
        )
        if parameter is None:
            raise ValidationError(
                "Le paramètre destination '{}' est absent.".format(
                    target_descriptor.name
                )
            )

        if self.parameter_service.is_writable(parameter):
            return parameter

        if (
            self.grouped_parameter_service is not None
            and self.grouped_parameter_service.can_temporarily_unlock(
                room,
                parameter,
            )
        ):
            return parameter

        raise ValidationError(
            "Le paramètre destination '{}' est en lecture seule.".format(
                target_descriptor.name
            )
        )

    def _selection_requires_group_override(
        self,
        rooms,
        target_descriptor,
    ):
        if self.grouped_parameter_service is None:
            return False

        for room in rooms or []:
            try:
                parameter = self.parameter_service.get_parameter(
                    room,
                    target_descriptor,
                )
            except Exception:
                continue

            if (
                parameter is not None
                and self.grouped_parameter_service.requires_temporary_override(
                    room,
                    parameter,
                )
            ):
                return True

        return False

    def _get_group_override_definitions(self, valid):
        if self.grouped_parameter_service is None:
            return []

        pairs = [
            (room, parameter)
            for operation, room, prepared_value, parameter in valid
        ]
        return self.grouped_parameter_service.get_required_definitions(pairs)

    def _enable_group_override(self, definitions):
        if self.grouped_parameter_service is None or not definitions:
            return []
        return self.grouped_parameter_service.enable_temporary_override(
            definitions
        )

    def _restore_group_alignment(self, definitions):
        if self.grouped_parameter_service is None or not definitions:
            return []
        return self.grouped_parameter_service.restore_group_alignment(
            definitions
        )

    @staticmethod
    def _deduplicate_failed_results(results):
        values = []
        seen = set()

        for item in results or []:
            key = (item.room_key, item.message, item.group_value)
            if key in seen:
                continue
            seen.add(key)
            values.append(item)

        return values

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
