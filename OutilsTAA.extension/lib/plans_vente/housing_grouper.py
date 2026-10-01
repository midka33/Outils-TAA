# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Regroupement pur des pièces par identifiant logement."""

from plans_vente.housing import Housing, HousingAnalysisResult


class HousingGrouper(object):
    """Transforme des RoomSnapshot en logements, sans dépendance Revit/WPF."""

    def group(self, room_snapshots, parameter_name):
        groups = {}
        empty_value_count = 0
        skipped_room_count = 0

        for room in room_snapshots or []:
            if room is None:
                skipped_room_count += 1
                continue

            key = self._normalize_key(room.housing_key)
            if not key:
                empty_value_count += 1
                continue

            groups.setdefault(key, []).append(room)

        housings = [
            Housing(key=key, rooms=groups[key])
            for key in sorted(groups.keys(), key=self._sort_key)
        ]

        return HousingAnalysisResult(
            parameter_name=parameter_name,
            housings=housings,
            skipped_room_count=skipped_room_count,
            empty_value_count=empty_value_count,
        )

    @staticmethod
    def _normalize_key(value):
        if value is None:
            return ""
        return str(value).strip()

    @staticmethod
    def _sort_key(value):
        return (value.lower(), value)
