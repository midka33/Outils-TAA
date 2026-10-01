# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Moteur métier pur de regroupement et de somme des pièces."""

from calculation.models import CalculationResult, SkippedRoom

try:
    string_types = (basestring,)
except NameError:
    string_types = (str,)


class RoomCalculator(object):
    """Calcule une somme par groupe sans dépendre de Revit ni de WPF."""

    REASON_EMPTY_GROUP = "empty_group"
    REASON_NON_NUMERIC_SOURCE = "non_numeric_source"
    REASON_INVALID_GROUP = "invalid_group"

    def calculate(self, items, progress=None):
        normalized_items = list(items or [])
        totals = {}
        members_by_group = {}
        skipped = []
        calculated_items = 0
        total = len(normalized_items)

        for index, item in enumerate(normalized_items, 1):
            if progress is not None:
                progress(index, total)

            group_value = getattr(item, "group_value", None)
            source_value = getattr(item, "source_value", None)
            room_key = getattr(item, "room_key", None)

            if self._is_empty_group(group_value):
                skipped.append(SkippedRoom(room_key, self.REASON_EMPTY_GROUP))
                continue

            # Une pièce appartient au groupe dès que sa valeur de groupe est
            # valide. Même si sa source n'est pas numérique, elle recevra le
            # total du groupe si au moins une autre pièce permet de le calculer.
            try:
                members_by_group.setdefault(group_value, []).append(room_key)
            except TypeError:
                skipped.append(SkippedRoom(room_key, self.REASON_INVALID_GROUP))
                continue

            numeric_value = self._get_numeric_value(source_value)
            if numeric_value is None:
                skipped.append(SkippedRoom(room_key, self.REASON_NON_NUMERIC_SOURCE))
                continue

            try:
                current_total = totals.get(group_value, 0)
                totals[group_value] = current_total + numeric_value
            except TypeError:
                skipped.append(SkippedRoom(room_key, self.REASON_INVALID_GROUP))
                continue

            calculated_items += 1

        return CalculationResult(
            totals=totals,
            total_items=total,
            calculated_items=calculated_items,
            skipped=skipped,
            members_by_group=members_by_group,
        )

    @staticmethod
    def _is_empty_group(value):
        if value is None:
            return True
        if isinstance(value, string_types):
            return not value.strip()
        return False

    @staticmethod
    def _get_numeric_value(value):
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, string_types):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
