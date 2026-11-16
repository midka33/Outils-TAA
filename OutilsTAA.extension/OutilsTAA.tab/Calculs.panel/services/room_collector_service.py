# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Collecte des pièces du projet selon une portée explicite de variantes."""

from common.exceptions import ValidationError


class RoomCollectorService(object):
    """Collecte de toutes les pièces ou de celles appartenant à une portée."""

    SCOPE_PRIMARY = "primary"
    SCOPE_VIEW = "view"

    def __init__(
        self,
        document,
        collector_factory=None,
        room_category=None,
        view=None,
    ):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self._collector_factory = collector_factory
        self._room_category = room_category
        # Capture de la vue au lancement, pas de bascule implicite de contexte.
        self.view = view

    def collect_all_rooms(self):
        collector_factory, room_category = self._resolve_revit_dependencies()
        collector = collector_factory(self.document)
        collector = collector.OfCategory(room_category)
        collector = collector.WhereElementIsNotElementType()
        return list(collector.ToElements())

    def collect_rooms_for_scope(self, scope):
        if scope == self.SCOPE_PRIMARY:
            return [
                room for room in self.collect_all_rooms()
                if self._is_primary_room(room)
            ]
        if scope == self.SCOPE_VIEW:
            return self._collect_visible_rooms()
        raise ValidationError("Portée de variantes inconnue : {}.".format(scope))

    @staticmethod
    def _is_primary_room(room):
        try:
            option = room.DesignOption
        except AttributeError:
            # Les doubles de test historiques ne disposent pas de DesignOption.
            return True
        except Exception as error:
            raise ValidationError(
                "Impossible de lire la variante de la pièce : {}.".format(error)
            )
        if option is None:
            return True
        try:
            return bool(option.IsPrimary)
        except Exception as error:
            raise ValidationError(
                "Statut principal/secondaire indisponible : {}.".format(error)
            )

    def _collect_visible_rooms(self):
        if self.view is None or getattr(self.view, "Id", None) is None:
            raise ValidationError(
                "La portée « Vue active » exige une vue Revit exploitable. "
                "Choisissez « Variantes principales » ou ouvrez une vue de plan."
            )
        # Les vues feuille, nomenclature, gabarit, etc. peuvent être invalides
        # pour un collecteur limité à la vue. Ne jamais revenir à tout le projet.
        try:
            collector_factory, room_category = self._resolve_revit_dependencies()
            collector = collector_factory(self.document, self.view.Id)
            collector = collector.OfCategory(room_category)
            collector = collector.WhereElementIsNotElementType()
            return list(collector.ToElements())
        except Exception as error:
            raise ValidationError(
                "Impossible de collecter les pièces visibles de la vue '{}': {}. "
                "Ouvrez une vue de plan compatible."
                .format(getattr(self.view, "Name", "?"), error)
            )

    def _resolve_revit_dependencies(self):
        if self._collector_factory is not None and self._room_category is not None:
            return self._collector_factory, self._room_category

        from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
        return (
            self._collector_factory or FilteredElementCollector,
            self._room_category or BuiltInCategory.OST_Rooms,
        )
