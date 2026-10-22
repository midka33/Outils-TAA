# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Adaptateur WPF : synthèse de types dans une DataTable .NET."""

SUMMARY_COLUMNS = ("source", "family", "type", "count", "methods", "status")


def display_text(value):
    if value is None:
        return u""
    try:
        return unicode(value)
    except NameError:
        return str(value)


def _data_table_class():
    """Charge explicitement System.Data pour IronPython sous Revit .NET 8."""
    import clr
    errors = []
    for assembly in ("System.Data.Common", "System.Data"):
        try:
            clr.AddReference(assembly)
            from System.Data import DataTable
            return DataTable
        except Exception as error:
            errors.append("{}: {}".format(assembly, error))
    raise ImportError("System.Data.DataTable inaccessible après chargement explicite : {}".format(" ; ".join(errors)))


def build_type_table(items):
    """Renvoie une DataTable, avec une ligne .NET créée explicitement."""
    table = _data_table_class()("Types")
    for name in SUMMARY_COLUMNS:
        table.Columns.Add(name)
    for item in items:
        row = table.NewRow()
        for name in SUMMARY_COLUMNS:
            row[name] = display_text(item.get(name))
        table.Rows.Add(row)
    return table
