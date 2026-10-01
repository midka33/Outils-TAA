# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Adaptateur Revit chargé de collecter les pièces du projet actif."""


class RoomCollectorService(object):
    """Collecte toujours toutes les pièces du document, sans filtre de vue."""

    def __init__(self, document, collector_factory=None, room_category=None):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self._collector_factory = collector_factory
        self._room_category = room_category

    def collect_all_rooms(self):
        collector_factory, room_category = self._resolve_revit_dependencies()
        collector = collector_factory(self.document)
        collector = collector.OfCategory(room_category)
        collector = collector.WhereElementIsNotElementType()
        return list(collector.ToElements())

    def _resolve_revit_dependencies(self):
        if self._collector_factory is not None and self._room_category is not None:
            return self._collector_factory, self._room_category

        from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

        return (
            self._collector_factory or FilteredElementCollector,
            self._room_category or BuiltInCategory.OST_Rooms,
        )
