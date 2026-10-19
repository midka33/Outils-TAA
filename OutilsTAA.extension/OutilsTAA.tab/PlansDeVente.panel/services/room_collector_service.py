# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Adaptateur Revit chargé de collecter toutes les pièces du projet actif."""


class RoomCollectorService(object):
    """Collecte les pièces du document, indépendamment de la vue active."""

    def __init__(self, document, collector_factory=None, room_category=None):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self._collector_factory = collector_factory
        self._room_category = room_category
        self.warnings = []

    def collect_all_rooms(self):
        collector_factory, room_category = self._resolve_revit_dependencies()
        collector = collector_factory(self.document)
        collector = collector.OfCategory(room_category)
        collector = collector.WhereElementIsNotElementType()
        return list(collector.ToElements())

    def collect_source_rooms(self, link_instances=None):
        from plans_vente.source_room import SourceRoom, element_id_value
        self.warnings = []
        rooms = self.collect_all_rooms()
        inspect_nested = link_instances is None
        if link_instances is None:
            from Autodesk.Revit.DB import FilteredElementCollector, RevitLinkInstance
            link_instances = list(FilteredElementCollector(self.document).OfClass(RevitLinkInstance).ToElements())
        document_rooms = {}
        for link in link_instances:
            name = str(getattr(link, "Name", "Lien Revit"))
            try:
                source = link.GetLinkDocument()
                if source is None:
                    self.warnings.append("{} : lien déchargé ignoré.".format(name))
                    continue
                transform = link.GetTotalTransform()
                # Horizontal rotations/reflections are supported; tilted storeys are not.
                if abs(transform.BasisZ.X) > 1e-8 or abs(transform.BasisZ.Y) > 1e-8 or transform.BasisZ.Z < 0.999999:
                    raise ValueError("lien incliné ou renversé : niveaux non horizontaux")
                if source not in document_rooms:
                    collector = RoomCollectorService(source, self._collector_factory, self._room_category)
                    document_rooms[source] = collector.collect_all_rooms()
                    if inspect_nested:
                        nested_count = FilteredElementCollector(source).OfClass(RevitLinkInstance).GetElementCount()
                        if nested_count:
                            self.warnings.append("{} : {} lien(s) imbriqué(s) non analysé(s). "
                                                 "Lier directement les bâtiments à traiter dans SITE.".format(source.Title, nested_count))
                label = "{} [instance {}]".format(source.Title, element_id_value(link.Id))
                rooms.extend([SourceRoom(source, room, link, transform, label)
                              for room in document_rooms[source]])
            except Exception as error:
                self.warnings.append("{} : collecte du lien impossible : {}.".format(name, error))
        return rooms

    def _resolve_revit_dependencies(self):
        if self._collector_factory is not None and self._room_category is not None:
            return self._collector_factory, self._room_category

        from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory

        return (
            self._collector_factory or FilteredElementCollector,
            self._room_category or BuiltInCategory.OST_Rooms,
        )
