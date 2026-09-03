# -*- coding: utf-8 -*-
"""Moteur de création et de résolution des carnets Export."""

import uuid

from carnet_resolution import CarnetResolution
from publication_item import PublicationItem
from publication_set import PublicationSet
from publication_source import PublicationSource


class CarnetService(object):
    """Construit et résout les carnets à partir des sources V1."""

    def __init__(self, export_service):
        self.export_service = export_service

    def create_from_parameter(self, parameter_name, name_template=None):
        """Crée un carnet par valeur distincte d'un paramètre de feuille."""
        if not parameter_name:
            raise ValueError("Le nom du paramètre est obligatoire.")

        items = self.export_service.get_publication_items(parameter_name)
        groups = {}

        for item in items:
            value = self._normalize_value(item.parameter_value)
            if not value:
                continue
            groups.setdefault(value, []).append(item)

        result = []
        for value in sorted(groups.keys(), key=lambda x: x.lower()):
            name = self._build_name(value, name_template)
            source = PublicationSource(
                PublicationSource.PARAMETER,
                parameter_name,
                value
            )
            result.append(
                PublicationSet(
                    name=name,
                    items=self._sort_items(groups[value]),
                    source=source,
                    set_id=self._new_id(),
                    persistent=False
                )
            )

        return result

    def create_manual(self, name, items, persistent=False,
                      output_directory=None, filename_template_id=None):
        """Crée un carnet manuel, persistant ou temporaire."""
        if not name or not str(name).strip():
            raise ValueError("Le carnet doit avoir un nom.")

        normalized_items = self._unique_items(items)
        source_mode = (
            PublicationSource.MANUAL
            if persistent
            else PublicationSource.TEMPORARY
        )

        return PublicationSet(
            name=str(name).strip(),
            items=self._sort_items(normalized_items),
            source=PublicationSource(source_mode),
            output_directory=output_directory,
            filename_template_id=filename_template_id,
            set_id=self._new_id(),
            persistent=persistent
        )

    def create_manual_persistent(self, name, items, output_directory=None,
                                 filename_template_id=None):
        """Crée explicitement un carnet manuel destiné à être enregistré."""
        return self.create_manual(
            name,
            items,
            persistent=True,
            output_directory=output_directory,
            filename_template_id=filename_template_id
        )

    def create_manual_temporary(self, name, items):
        """Crée un carnet manuel utilisable uniquement pour la session."""
        return self.create_manual(name, items, persistent=False)

    def resolve_persistent_carnet(self, publication_set, sheets):
        """Résout un carnet sauvegardé avec les feuilles du document courant.

        Le UniqueId est la référence principale. Les éléments absents ne sont
        jamais supprimés silencieusement : ils sont retournés dans missing_items.
        """
        if publication_set is None:
            raise ValueError("Le carnet est manquant.")

        current_by_unique_id = {}
        for sheet in sheets or []:
            if sheet is None:
                continue
            try:
                unique_id = sheet.UniqueId
            except Exception:
                continue
            if unique_id:
                current_by_unique_id[unique_id] = sheet

        resolved = []
        missing = []

        for saved_item in publication_set.items:
            if saved_item is None or not saved_item.unique_id:
                missing.append(saved_item)
                continue

            sheet = current_by_unique_id.get(saved_item.unique_id)
            if sheet is None:
                missing.append(saved_item)
                continue

            try:
                resolved.append(
                    PublicationItem(
                        sheet.UniqueId,
                        sheet.Id.IntegerValue,
                        saved_item.item_type or "SHEET",
                        sheet.SheetNumber,
                        sheet.Name,
                        saved_item.parameter_value
                    )
                )
            except Exception:
                missing.append(saved_item)

        return CarnetResolution(
            items=self._sort_items(resolved),
            missing_items=missing
        )

    @staticmethod
    def _new_id():
        return str(uuid.uuid4())

    @staticmethod
    def _normalize_value(value):
        if value is None:
            return None
        text = str(value).strip()
        return text if text else None

    @staticmethod
    def _build_name(value, name_template):
        if not name_template:
            return value
        return str(name_template).replace("{value}", value)

    @staticmethod
    def _unique_items(items):
        result = []
        known_ids = set()
        for item in items or []:
            if item is None or not item.unique_id:
                continue
            if item.unique_id in known_ids:
                continue
            known_ids.add(item.unique_id)
            result.append(item)
        return result

    def _sort_items(self, items):
        return sorted(
            items,
            key=lambda item: (
                item.sheet_number or "",
                item.sheet_name or "",
                item.unique_id or ""
            )
        )
