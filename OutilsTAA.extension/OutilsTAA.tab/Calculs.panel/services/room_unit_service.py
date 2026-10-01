# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Service d'unités pour les paramètres de pièces."""

from common.unit_utils import (
    convert_from_internal_units,
    convert_to_internal_units,
)


class RoomUnitService(object):
    """Convertit uniquement lorsqu'une unité Revit explicite est disponible."""

    def __init__(self, unit_utils=None):
        self._unit_utils = unit_utils

    def get_unit_type_id(self, parameter):
        if parameter is None:
            return None
        getter = getattr(parameter, "GetUnitTypeId", None)
        if getter is None:
            return None
        try:
            return getter()
        except Exception:
            return None

    def from_internal(self, value, parameter=None, unit_type_id=None):
        unit_id = unit_type_id or self.get_unit_type_id(parameter)
        if unit_id is None:
            raise ValueError("Le paramètre ne fournit pas d'unité Revit mesurable.")
        return convert_from_internal_units(
            value,
            unit_id,
            unit_utils=self._unit_utils,
        )

    def to_internal(self, value, parameter=None, unit_type_id=None):
        unit_id = unit_type_id or self.get_unit_type_id(parameter)
        if unit_id is None:
            raise ValueError("Le paramètre ne fournit pas d'unité Revit mesurable.")
        return convert_to_internal_units(
            value,
            unit_id,
            unit_utils=self._unit_utils,
        )
