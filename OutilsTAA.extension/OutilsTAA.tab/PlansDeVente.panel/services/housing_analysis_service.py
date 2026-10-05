# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Prépare les données de détection des logements depuis le document Revit."""

from plans_vente.housing import RoomSnapshot


class HousingAnalysisContext(object):
    def __init__(self, rooms, parameters):
        self.rooms = list(rooms or [])
        self.parameters = list(parameters or [])

    @property
    def rooms_count(self):
        return len(self.rooms)


class HousingAnalysisService(object):
    """Pont entre Revit et le moteur métier pur de regroupement."""

    def __init__(self, collector_service, parameter_service, grouper):
        self.collector_service = collector_service
        self.parameter_service = parameter_service
        self.grouper = grouper
        self._context = None

    def load_context(self):
        rooms = self.collector_service.collect_all_rooms()
        parameters = self.parameter_service.get_text_parameter_descriptors(rooms)
        self._context = HousingAnalysisContext(rooms, parameters)
        return self._context

    def analyze(self, descriptor):
        if descriptor is None:
            raise ValueError("Sélectionnez le paramètre identifiant les logements.")

        context = self._context or self.load_context()
        snapshots = []

        for room in context.rooms:
            snapshots.append(
                RoomSnapshot(
                    unique_id=self._unique_id(room),
                    name=self._room_name(room),
                    number=self._room_number(room),
                    level_name=self._level_name(room),
                    housing_key=self.parameter_service.read_text_value(
                        room,
                        descriptor,
                        default="",
                    ),
                )
            )

        return self.grouper.group(
            snapshots,
            parameter_name=descriptor.name,
        )

    @staticmethod
    def _unique_id(room):
        return str(getattr(room, "UniqueId", "") or "")

    @staticmethod
    def _room_name(room):
        value = getattr(room, "Name", None)
        return str(value) if value is not None else ""

    @staticmethod
    def _room_number(room):
        value = getattr(room, "Number", None)
        return str(value) if value is not None else ""

    @staticmethod
    def _level_name(room):
        level = getattr(room, "Level", None)
        if level is None:
            return ""
        value = getattr(level, "Name", None)
        return str(value) if value is not None else ""
