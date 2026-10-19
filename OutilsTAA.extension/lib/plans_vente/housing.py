# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Modèles métier purs utilisés pendant l'analyse des logements."""


class RoomSnapshot(object):
    """Vue métier minimale d'une pièce Revit."""

    def __init__(self, unique_id, name="", number="", level_name="", housing_key="", source_room=None, include_links=False):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.number = number or ""
        self.level_name = level_name or ""
        self.housing_key = housing_key or ""
        self.include_links = bool(include_links)
        self.source_room = source_room
        self.source_key = source_room.source_key if source_room is not None else "HOST"
        self.source_name = source_room.source_name if source_room is not None else "Fichier actif"


class Housing(object):
    """Regroupement métier des pièces partageant un identifiant logement."""

    def __init__(self, key, rooms=None, filter_key=None):
        self.key = key or ""
        self.rooms = list(rooms or [])
        self.filter_key = (
            self.key
            if filter_key is None
            else (filter_key or "")
        )
        self.output_disambiguator = ""

    def set_output_disambiguator(self, value):
        """Ajoute un libellé visible seulement lorsqu'un numéro est en doublon."""
        label = str(value or "").strip()
        self.output_disambiguator = label
        self.key = (
            "{} - {}".format(self.filter_key, label)
            if label
            else self.filter_key
        )
        return self.key

    @property
    def source_name(self):
        return self.rooms[0].source_name if self.rooms else "Fichier actif"

    @property
    def source_key(self):
        return self.rooms[0].source_key if self.rooms else "HOST"

    @property
    def include_links(self):
        return any(getattr(room, "include_links", False) for room in self.rooms)

    @property
    def identity(self):
        return (self.source_key, self.filter_key)

    @property
    def display_key(self):
        return self.filter_key

    @property
    def report_label(self):
        return "{} / logement {}".format(self.source_name, self.key)

    @property
    def room_count(self):
        return len(self.rooms)

    @property
    def room_unique_ids(self):
        return [
            room.unique_id
            for room in self.rooms
            if getattr(room, "unique_id", None)
        ]

    @property
    def level_names(self):
        seen = {}
        for room in self.rooms:
            level_name = (room.level_name or "").strip()
            if level_name:
                lowered = level_name.lower()
                if lowered not in seen:
                    seen[lowered] = level_name
        return [seen[key] for key in sorted(seen.keys())]

    @property
    def levels_label(self):
        values = self.level_names
        return ", ".join(values) if values else "Niveau non déterminé"


class HousingAnalysisResult(object):
    """Résultat de regroupement exploitable par les étapes suivantes."""

    def __init__(self, parameter_name, housings=None, skipped_room_count=0, empty_value_count=0):
        self.parameter_name = parameter_name or ""
        self.housings = list(housings or [])
        self.skipped_room_count = int(skipped_room_count or 0)
        self.empty_value_count = int(empty_value_count or 0)

    @property
    def housing_count(self):
        return len(self.housings)

    @property
    def room_count(self):
        return sum(housing.room_count for housing in self.housings)
