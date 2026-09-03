# -*- coding: utf-8 -*-
"""Découverte des paramètres et valeurs disponibles pour Export."""


class ParameterService(object):
    """Expose les paramètres de feuilles utiles à l'interface du module."""

    def __init__(self, parameter_utils):
        self.parameter_utils = parameter_utils

    def get_sheet_parameter_names(self, sheets):
        """Retourne les noms de paramètres présents sur les feuilles."""
        names = {}

        for sheet in sheets or []:
            if sheet is None:
                continue

            try:
                parameters = sheet.Parameters
            except Exception:
                continue

            for parameter in parameters:
                try:
                    definition = parameter.Definition
                    name = definition.Name if definition else None
                except Exception:
                    continue

                name = self._normalize_value(name)
                if name:
                    names.setdefault(name.lower(), name)

        return sorted(names.values(), key=lambda value: value.lower())

    def get_parameter_values(self, sheets, parameter_name):
        """Retourne les valeurs distinctes et non vides d'un paramètre."""
        values = {}

        if not parameter_name:
            return []

        for sheet in sheets or []:
            if sheet is None:
                continue

            try:
                value = self.parameter_utils.get_parameter_value(
                    sheet,
                    parameter_name,
                    None
                )
            except Exception:
                continue

            value = self._normalize_value(value)
            if value:
                values.setdefault(value.lower(), value)

        return sorted(values.values(), key=lambda value: value.lower())

    def get_parameter_summary(self, sheets, parameter_name):
        """Retourne les valeurs d'un paramètre avec leur nombre de feuilles."""
        counts = {}

        if not parameter_name:
            return []

        for sheet in sheets or []:
            if sheet is None:
                continue

            try:
                value = self.parameter_utils.get_parameter_value(
                    sheet,
                    parameter_name,
                    None
                )
            except Exception:
                continue

            value = self._normalize_value(value)
            if not value:
                continue

            key = value.lower()
            if key not in counts:
                counts[key] = {"value": value, "count": 0}
            counts[key]["count"] += 1

        result = list(counts.values())
        return sorted(result, key=lambda item: item["value"].lower())

    @staticmethod
    def _normalize_value(value):
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None
