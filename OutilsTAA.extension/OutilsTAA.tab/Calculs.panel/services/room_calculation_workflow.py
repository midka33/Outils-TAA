# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Orchestration du workflow READ → DATA → CALCULATE → VALIDATE → WRITE."""

from common.exceptions import ValidationError
from common.transaction import RevitTransaction
from calculation.models import RoomCalculationItem
from group_member_alignment import (build_uniform_member_plan,
                                    validate_uniform_targets_by_member)
from calculation_diagnostics import (group_conflicts, design_option_summary,
                                     variant_group_key, variant_group_label,
                                     shared_apartments_across_variants)
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
        conflicts=None,
        design_options=None,
        shared_variant_apartments=None,
    ):
        self.request = request
        self.result = result
        self.room_by_key = dict(room_by_key or {})
        self.operations = list(operations or [])
        self.total_rooms = int(total_rooms)
        self.filtered_rooms = int(filtered_rooms)
        self.warnings = list(warnings or [])
        self.group_conflicts = list(conflicts or [])
        self.design_options = list(design_options or [])
        self.shared_variant_apartments = list(shared_variant_apartments or [])
        self.variant_separation_confirmed = False
        self.variant_combination_confirmed = False
        # Choix explicite par utilisateur; 'restore' preserve l'ancien comportement.
        self.group_mode = "restore"
        self.uniform_values = {}
        self.uniform_extra_members = []
        self.uniform_covered_ids = set()
        self.uniform_plan_error = None


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

        group_mode = getattr(request, "group_mode", "auto")
        if group_mode not in ("auto", "vary", "uniform"):
            raise ValidationError("Gestion des groupes inconnue.")
        mode = getattr(request, "variant_mode", "separate")
        if mode not in ("separate", "combine"):
            raise ValidationError("Mode de gestion des variantes inconnu.")
        rooms = self.collector_service.collect_all_rooms()
        filtered = self.room_filter.apply(
            rooms,
            parameter_name=request.filter_parameter,
            expected_value=request.filter_value,
            value_reader=self.parameter_service.read_value,
        )

        room_by_key = {}
        items = []
        separate_items = []

        for index, room in enumerate(filtered):
            room_key = self._room_key(room, index)
            room_by_key[room_key] = room
            group_value = self.parameter_service.read_value(
                room, request.group_parameter, default=None
            )
            source_value = self.parameter_service.read_value(
                room, request.source_parameter, default=None
            )
            separate_key = variant_group_key(room, group_value)
            separate_items.append(RoomCalculationItem(
                room_key, separate_key, source_value
            ))
            items.append(RoomCalculationItem(
                room_key,
                group_value if mode == "combine" else separate_key,
                source_value,
            ))

        result = self.calculator.calculate(items, progress=progress)
        separate_result = (
            self.calculator.calculate(separate_items)
            if mode == "combine" else result
        )
        operations = []

        for group_value, total in result.totals.items():
            for room_key in result.get_members(group_value):
                operations.append(
                    WriteOperation(
                        room_key=room_key,
                        group_value=(
                            group_value if mode == "combine"
                            else variant_group_label(group_value, self.document)
                        ),
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
                "Par défaut, Outils TAA le déverrouille temporairement puis "
                "restaure l'alignement. En cas de divergence connue, un choix "
                "explicite sera demandé avant écriture.".format(request.target_parameter.name)
            )

        conflicts = []
        if self._selection_requires_group_override(filtered, request.target_parameter):
            conflicts = group_conflicts(self.document, room_by_key, operations)
        variants = design_option_summary(self.document, filtered)
        if mode == "combine":
            variants.insert(0, "ATTENTION : toutes les variantes sont additionnées "
                            "pour un même numéro d'appartement.")
        else:
            variants.insert(0, "Les variantes secondaires sont calculées séparément.")

        prepared = PreparedCalculation(
            request=request,
            result=result,
            room_by_key=room_by_key,
            operations=operations,
            total_rooms=len(rooms),
            filtered_rooms=len(filtered),
            warnings=warnings,
            conflicts=conflicts,
            design_options=variants,
            shared_variant_apartments=shared_apartments_across_variants(
                separate_result, self.document
            ),
        )
        if group_mode != "auto":
            prepared.group_mode = group_mode
        if group_mode in ("uniform", "auto"):
            try:
                (prepared.uniform_extra_members,
                 prepared.uniform_covered_ids) = build_uniform_member_plan(
                    self.document, prepared.room_by_key, prepared.operations,
                    self.parameter_service, request.target_parameter,
                )
            except ValidationError as error:
                prepared.uniform_plan_error = str(error)
                if group_mode == "uniform":
                    raise
            if prepared.uniform_extra_members and group_mode == "uniform":
                prepared.warnings.append(
                    "Mode valeur commune : {} membre(s) correspondant(s) "
                    "supplementaire(s) seront mis a jour dans d'autres "
                    "occurrences du type de groupe, meme hors du filtre."
                    .format(len(prepared.uniform_extra_members))
                )
        return prepared

    def execute(self, prepared, progress=None):
        valid = []
        failed = []

        mode = getattr(prepared.request, "variant_mode", "separate")
        if mode not in ("separate", "combine"):
            raise ValidationError("Mode de gestion des variantes inconnu.")
        if prepared.shared_variant_apartments:
            if mode == "separate" and not prepared.variant_separation_confirmed:
                raise ValidationError(
                    "Confirmez explicitement la séparation des surfaces "
                    "de cet appartement entre variantes avant écriture."
                )
            if mode == "combine" and not prepared.variant_combination_confirmed:
                raise ValidationError(
                    "Confirmez explicitement l'addition des surfaces "
                    "des variantes avant écriture."
                )

        if prepared.group_conflicts and prepared.group_mode == "restore":
            raise ValidationError(
                "Conflits de valeurs entre occurrences : un choix utilisateur "
                "est obligatoire avant l'ecriture."
            )
        if prepared.group_mode not in ("restore", "vary", "uniform"):
            raise ValidationError("Mode de groupes non reconnu.")
        if prepared.group_mode == "uniform" and prepared.uniform_plan_error:
            raise ValidationError(prepared.uniform_plan_error)
        if prepared.group_mode == "uniform":
            required = set(item["type_key"] for item in prepared.group_conflicts)
            if set(prepared.uniform_values) != required:
                raise ValidationError("Une valeur commune doit etre choisie pour chaque type de groupe.")
            for item in prepared.group_conflicts:
                allowed = [candidate["value"] for candidate in item["candidates"]]
                if not item["uniform_safe"] or prepared.uniform_values[item["type_key"]] not in allowed:
                    raise ValidationError("Uniformisation non sure pour le type de groupe '{}' .".format(item["name"]))
            uniform_by_room = {}
            for item in prepared.group_conflicts:
                for room_key in item["room_keys"]:
                    uniform_by_room[room_key] = prepared.uniform_values[item["type_key"]]
        else:
            uniform_by_room = {}

        if prepared.group_mode == "uniform":
            validate_uniform_targets_by_member(
                self.document,
                prepared.room_by_key,
                prepared.operations,
                uniform_by_room,
            )

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
                    uniform_by_room.get(operation.room_key, operation.value),
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

        if prepared.group_mode == "uniform":
            # Les membres homologues d'autres occurrences doivent recevoir la
            # meme somme. Sans cela, le retour a l'alignement peut modifier
            # silencieusement les membres non selectionnes.
            for room, raw_value, type_key in prepared.uniform_extra_members:
                raw = prepared.uniform_values.get(type_key, raw_value)
                member_id = self._room_key(room, len(valid))
                operation = WriteOperation(
                    member_id, "type de groupe {}".format(type_key), raw
                )
                try:
                    prepared_value = self.writer.prepare_value(
                        prepared.request.source_parameter,
                        prepared.request.target_parameter,
                        raw,
                        prepared.request.output_unit_type_id,
                    )
                    parameter = self._validate_target_on_room(
                        room, prepared.request.target_parameter,
                    )
                    valid.append((operation, room, prepared_value, parameter))
                except Exception as error:
                    failed.append(WriteResult(
                        member_id, False, str(error), operation.group_value
                    ))
            if failed:
                # Pas de transaction si un membre de groupe ne peut etre ecrit.
                return CalculationExecutionReport(
                    failed_results=failed,
                    skipped=prepared.result.skipped,
                    warnings=prepared.warnings,
                )

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
                definitions = self._get_group_override_definitions(valid)
                initially_varying = []
                if prepared.group_mode == "uniform" and self.grouped_parameter_service:
                    initially_varying = (
                        self.grouped_parameter_service.get_varying_definitions(
                            [(room, parameter)
                             for op, room, value, parameter in valid]
                        )
                    )
                enabled_definitions = self._enable_group_override(definitions)
                if initially_varying:
                    enabled_definitions.extend(initially_varying)

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

                if prepared.group_mode in ("vary", "uniform") and failed:
                    raise ValidationError("Ecriture incomplete : annulation de securite.")
                if prepared.group_mode == "uniform" and enabled_definitions:
                    # Revit differe certaines mises a jour jusqu'a regeneration.
                    # Synchroniser toutes les valeurs AVANT d'imposer a
                    # nouveau l'alignement global du parametre de groupe.
                    regenerate = getattr(self.document, "Regenerate", None)
                    if regenerate is not None:
                        regenerate()
                values_before_alignment = {}
                if prepared.group_mode == "uniform":
                    values_before_alignment = self._snapshot_target_values(
                        valid, prepared.request.target_parameter
                    )
                if prepared.group_mode in ("restore", "uniform"):
                    realigned = self._restore_group_alignment(enabled_definitions)
                else:
                    realigned = []
                if prepared.group_mode == "uniform":
                    # Un realignement ne peut etre admis que s'il touche des
                    # membres explicitement prevus ET conserve leur valeur.
                    self._verify_uniform_alignment(
                        valid, realigned, prepared.request.target_parameter,
                        values_before_alignment, prepared.group_conflicts
                    )
                elif realigned:
                    raise ValidationError(
                        "La restauration de l'alignement par type de groupe "
                        "aurait modifié {} élément(s). Les occurrences de groupe "
                        "ne produisent donc pas toutes la même valeur ; aucune "
                        "modification n'a été conservée.".format(
                            len(realigned)
                        )
                    )

            successful = temporary_success
            if prepared.group_mode == "vary" and enabled_definitions:
                prepared.warnings.append(
                    "Reglage du parametre conserve : valeurs differentes "
                    "autorisees entre occurrences de groupes."
                )
            elif prepared.group_mode == "uniform" and prepared.group_conflicts:
                prepared.warnings.append(
                    "Valeurs communes retenues par type de groupe, "
                    "alignement du parametre preserve."
                )
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
                warnings=prepared.warnings,
                transaction_error=str(error),
            )

        return CalculationExecutionReport(
            success_results=successful,
            failed_results=failed,
            skipped=prepared.result.skipped,
            warnings=prepared.warnings,
        )

    def _snapshot_target_values(self, valid, target_descriptor):
        """Releve les valeurs apres ecriture/regeneration et avant realignement."""
        values = {}
        for operation, room, value, parameter in valid:
            identifier = self._element_id_value(getattr(room, "Id", None))
            if identifier is None:
                continue
            current = self.parameter_service.get_parameter(room, target_descriptor)
            if current is not None:
                values[str(identifier)] = self.parameter_service.read_parameter(current)
        return values

    def _verify_uniform_alignment(
        self, valid, realigned, target_descriptor,
        values_before_alignment=None, group_conflicts=None,
    ):
        """Valide toutes les valeurs apres restauration, sinon rollback.

        L'API Revit peut signaler des elements realignes meme quand leur
        nouvelle valeur est celle demandee. Seules les valeurs finales
        attendues ET les identifiants explicitement couverts sont admis.
        """
        expected = {}
        for operation, room, value, parameter in valid:
            element_id = self._element_id_value(getattr(room, "Id", None))
            if element_id is not None:
                expected[str(element_id)] = (room, value)
        for element_id in realigned:
            identifier = str(self._element_id_value(element_id))
            if identifier not in expected:
                raise ValidationError(
                    "L'alignement Revit modifierait un element hors du "
                    "perimetre prepare (id {}). Transaction annulee."
                    .format(identifier)
                )
        values_before_alignment = values_before_alignment or {}
        conflict_by_room = {}
        for conflict in group_conflicts or []:
            for key in conflict.get("room_keys", []):
                conflict_by_room[str(key)] = (
                    str(conflict.get("name", "inconnu")),
                    str(conflict.get("type_key", "?")),
                )
        for identifier, (room, value) in expected.items():
            parameter = self.parameter_service.get_parameter(
                room, target_descriptor
            )
            if parameter is None:
                raise ValidationError(
                    "Destination absente apres realignement (id {}).".format(
                        identifier
                    )
                )
            actual = self.parameter_service.read_parameter(parameter)
            if not self._same_value(actual, value):
                group_name = "inconnu"
                group_type_id = "?"
                group_id = getattr(room, "GroupId", None)
                group = None
                getter = getattr(self.document, "GetElement", None)
                if getter is not None and group_id is not None:
                    try:
                        group = getter(group_id)
                    except Exception:
                        group = None
                if group is not None:
                    group_type = getattr(group, "GroupType", None)
                    group_name = getattr(group_type, "Name", None) or "inconnu"
                    type_id = getattr(group_type, "Id", None)
                    if type_id is None:
                        getter = getattr(group, "GetTypeId", None)
                        if getter is not None:
                            type_id = getter()
                    if type_id is not None:
                        group_type_id = str(self._element_id_value(type_id))
                if group_name == "inconnu" or group_type_id == "?":
                    for operation, candidate_room, unused_value, unused_parameter in valid:
                        if candidate_room is room:
                            cached = conflict_by_room.get(str(operation.room_key))
                            if cached:
                                group_name, group_type_id = cached
                            break
                before = values_before_alignment.get(identifier)
                stage = (
                    "apres regeneration et avant restauration : {}".format(before)
                    if before is not None
                    else "valeur avant restauration non disponible"
                )
                raise ValidationError(
                    "Valeur commune non conservee par Revit sur l'element {} "
                    "(type de groupe '{}', id de type {}) : "
                    "valeur finale {}, attendue {} ; {}. "
                    "Revit a impose une valeur incompatible apres "
                    "SetAllowVaryBetweenGroups(False). "
                    "La transaction a ete annulee. Ce cas peut necessiter "
                    "une modification du contenu du type de groupe dans "
                    "l'editeur de groupes Revit ; le module ne doit pas "
                    "imposer une valeur apres realignement."
                    .format(
                        identifier, group_name, group_type_id,
                        actual, value, stage
                    )
                )

    @staticmethod
    def _same_value(actual, expected):
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            return abs(actual - expected) <= 1e-7 * max(1.0, abs(expected))
        return actual == expected

    @staticmethod
    def _element_id_value(element_id):
        if element_id is None:
            return None
        return getattr(element_id, "Value",
                       getattr(element_id, "IntegerValue", element_id))

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
