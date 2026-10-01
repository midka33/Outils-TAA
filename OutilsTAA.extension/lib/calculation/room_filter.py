# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Filtrage métier pur des pièces avant calcul."""

try:
    text_type = unicode
except NameError:
    text_type = str


class RoomFilter(object):
    """Applique un filtre optionnel par paramètre sur un ensemble de pièces."""

    def apply(self, rooms, parameter_name=None, expected_value=None, value_reader=None):
        normalized_rooms = list(rooms or [])

        if not parameter_name or self._is_blank(expected_value):
            return normalized_rooms

        if value_reader is None:
            raise ValueError("Un lecteur de paramètre est requis pour appliquer un filtre.")

        expected = self._normalize(expected_value)
        result = []

        for room in normalized_rooms:
            current = value_reader(room, parameter_name)
            if self._normalize(current) == expected:
                result.append(room)

        return result

    @staticmethod
    def _is_blank(value):
        if value is None:
            return True
        if isinstance(value, text_type):
            return not value.strip()
        return False

    @staticmethod
    def _normalize(value):
        if value is None:
            return None
        if isinstance(value, text_type):
            return value.strip()
        return text_type(value)
