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

            groups.setdefault((getattr(room, "source_key", "HOST"), key), []).append(room)

        housings = []
        output_keys = set()
        for source_key, key in sorted(groups, key=lambda item: (self._sort_key(item[1]), item[0])):
            rooms = groups[(source_key, key)]
            source = getattr(rooms[0], "source_room", None)
            output_key = key + (source.output_suffix if source is not None else "")
            if output_key in output_keys:
                raise ValueError("Collision de nom de sortie « {} » entre deux sources. "
                                 "Modifier le numéro logement ambigu avant génération.".format(output_key))
            output_keys.add(output_key)
            housings.append(Housing(key=output_key, rooms=rooms, filter_key=key))

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
