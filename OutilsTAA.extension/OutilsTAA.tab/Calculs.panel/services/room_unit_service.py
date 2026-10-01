# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Service d'unités pour les paramètres de pièces."""

from common.parameter_utils import forge_type_id_to_string
from common.unit_utils import (
    convert_from_internal_units,
    convert_to_internal_units,
    forge_type_id_from_string,
)
from calculation.unit_option import UnitOption


class RoomUnitService(object):
    """Convertit uniquement lorsqu'une unité Revit explicite est disponible."""

    def __init__(
        self,
        unit_utils=None,
        forge_type_factory=None,
        label_utils=None,
    ):
        self._unit_utils = unit_utils
        self._forge_type_factory = forge_type_factory
        self._label_utils = label_utils

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
        unit_id = forge_type_id_from_string(
            unit_id,
            forge_type_factory=self._forge_type_factory,
        )
        return convert_from_internal_units(
            value,
            unit_id,
            unit_utils=self._unit_utils,
        )

    def to_internal(self, value, parameter=None, unit_type_id=None):
        unit_id = unit_type_id or self.get_unit_type_id(parameter)
        if unit_id is None:
            raise ValueError("Le paramètre ne fournit pas d'unité Revit mesurable.")
        unit_id = forge_type_id_from_string(
            unit_id,
            forge_type_factory=self._forge_type_factory,
        )
        return convert_to_internal_units(
            value,
            unit_id,
            unit_utils=self._unit_utils,
        )


    def get_unit_options(self, source_descriptor):
        """Retourne Automatique + unités compatibles avec le type de donnée."""
        options = [UnitOption("Automatique", None)]

        if source_descriptor is None:
            return options
        if source_descriptor.storage_type != "Double":
            return options
        if not source_descriptor.data_type_id:
            return options

        spec_id = forge_type_id_from_string(
            source_descriptor.data_type_id,
            forge_type_factory=self._forge_type_factory,
        )
        api = self._unit_utils
        if api is None:
            from Autodesk.Revit.DB import UnitUtils
            api = UnitUtils

        try:
            checker = getattr(api, "IsMeasurableSpec", None)
            if checker is not None and not checker(spec_id):
                return options
            unit_ids = list(api.GetValidUnits(spec_id) or [])
        except Exception:
            return options

        label_api = self._label_utils
        if label_api is None:
            from Autodesk.Revit.DB import LabelUtils
            label_api = LabelUtils

        values = []
        for unit_id in unit_ids:
            type_id = forge_type_id_to_string(unit_id)
            if not type_id:
                continue
            try:
                label = label_api.GetLabelForUnit(unit_id)
            except Exception:
                label = type_id
            values.append(UnitOption(label, type_id))

        values.sort(key=lambda option: option.label.lower())
        options.extend(values)
        return options
