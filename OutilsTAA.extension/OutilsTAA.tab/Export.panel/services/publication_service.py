# -*- coding: utf-8 -*-
"""Orchestrateur de publication de l'outil Export."""

import os

from pdf_export_service import PdfExportService
from dwg_export_service import DwgExportService
from filename_service import FilenameService


class PublicationService(object):
    """Valide, prépare et exécute une publication."""

    def __init__(self, document):
        self.document = document
        self.pdf_service = PdfExportService(document)
        self.dwg_service = DwgExportService(document)
        self.filename_service = FilenameService(document)

    def _resolve_current_sheet_id(self, item):
        if item is None:
            return None
        unique_id = getattr(item, "unique_id", None)
        if unique_id:
            try:
                element = self.document.GetElement(unique_id)
                if element is not None:
                    return element.Id
            except Exception:
                pass
        sheet_id = getattr(item, "sheet_id", None)
        if sheet_id is not None:
            try:
                element = self.document.GetElement(sheet_id)
                if element is not None:
                    return element.Id
            except Exception:
                pass
        return None

    def validate_publication_set(self, publication_set):
        errors = []
        if publication_set is None:
            return ["Le carnet de publication est manquant."]
        if not publication_set.name:
            errors.append("Le carnet doit avoir un nom.")
        if not publication_set.items:
            errors.append("Le carnet ne contient aucun élément à publier.")
            return errors
        seen_ids = set()
        for item in publication_set.items:
            current_id = self._resolve_current_sheet_id(item)
            if current_id is None:
                errors.append("La feuille '{}' est introuvable dans le document Revit.".format(
                    getattr(item, "sheet_number", None) or getattr(item, "sheet_name", "")))
                continue
            try:
                key = current_id.IntegerValue
            except Exception:
                key = str(current_id)
            if key in seen_ids:
                errors.append("Le carnet contient une feuille en double (ID {}).".format(key))
            seen_ids.add(key)
            try:
                view = self.document.GetElement(current_id)
                if view is not None and not view.CanBePrinted:
                    errors.append("La feuille '{}' n'est pas exportable/imprimable.".format(
                        getattr(item, "sheet_number", None) or getattr(item, "sheet_name", "")))
            except Exception:
                pass
        return errors

    def sort_items(self, publication_set):
        if publication_set is None:
            return []
        return sorted(publication_set.items, key=lambda item: (
            item.sheet_number or "", item.sheet_name or "", item.unique_id or ""))

    def _current_view_ids(self, publication_set, items=None):
        source_items = items if items is not None else self.sort_items(publication_set)
        return [self._resolve_current_sheet_id(item) for item in source_items
                if self._resolve_current_sheet_id(item) is not None]

    def _prepare_output_directory(self, output_directory):
        if not output_directory:
            raise ValueError("Le dossier de destination est manquant.")
        output_directory = os.path.abspath(output_directory)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        return output_directory

    def _folder_name(self, publication_set):
        return getattr(publication_set, "folder_name", None)

    def _filename(self, publication_set, item, extension):
        settings = getattr(publication_set, "publication_settings", None)
        template = getattr(settings, "filename_template", None) or "{carnet}"
        return self.filename_service.filename(template, publication_set, item=item,
                                               folder_name=self._folder_name(publication_set),
                                               extension=extension)

    def _publish_items(self, publication_set, items, output_directory,
                       export_pdf=True, export_dwg=False, pdf_combined=True,
                       dwg_combined=False, dwg_setup_name=None, dwg_true_color=True):
        """Publie uniquement les éléments fournis sans modifier le carnet source."""
        if not items:
            return {"success": True, "results": [], "errors": [], "warnings": [], "files": []}
        output_directory = self._prepare_output_directory(output_directory)
        warnings = []
        results = []
        files = []
        view_ids = self._current_view_ids(publication_set, items)

        if export_pdf:
            if pdf_combined:
                filename, unknown = self._filename(publication_set, None, ".pdf")
                if unknown:
                    warnings.append("Variables non résolues dans le nom PDF : {}.".format(", ".join(unknown)))
                success = self.pdf_service.export(view_ids, output_directory,
                                                   os.path.splitext(filename)[0], combined=True)
                files.append(os.path.join(output_directory, filename))
                results.append({"success": bool(success), "format": "PDF", "mode": "combined",
                                "count": len(items), "path": os.path.join(output_directory, filename)})
            else:
                for item in items:
                    current_id = self._resolve_current_sheet_id(item)
                    filename, unknown = self._filename(publication_set, item, ".pdf")
                    if unknown:
                        warnings.append("Variables non résolues pour {} : {}.".format(
                            item.sheet_number or item.sheet_name or "feuille", ", ".join(unknown)))
                    success = self.pdf_service.export([current_id], output_directory,
                                                      os.path.splitext(filename)[0], combined=True)
                    path = os.path.join(output_directory, filename)
                    files.append(path)
                    results.append({"success": bool(success), "format": "PDF", "mode": "separate",
                                    "count": 1, "path": path, "sheet_key": getattr(item, "unique_id", None)})

        if export_dwg:
            if dwg_combined:
                filename, unknown = self._filename(publication_set, None, ".dwg")
                if unknown:
                    warnings.append("Variables non résolues dans le nom DWG : {}.".format(", ".join(unknown)))
                success = self.dwg_service.export(view_ids, output_directory,
                                                   os.path.splitext(filename)[0], dwg_setup_name,
                                                   merged_views=True, true_color=dwg_true_color)
                path = os.path.join(output_directory, filename)
                files.append(path)
                results.append({"success": bool(success), "format": "DWG", "mode": "combined",
                                "count": len(items), "path": path})
            else:
                for item in items:
                    current_id = self._resolve_current_sheet_id(item)
                    filename, unknown = self._filename(publication_set, item, ".dwg")
                    if unknown:
                        warnings.append("Variables non résolues pour {} : {}.".format(
                            item.sheet_number or item.sheet_name or "feuille", ", ".join(unknown)))
                    success = self.dwg_service.export([current_id], output_directory,
                                                      os.path.splitext(filename)[0], dwg_setup_name,
                                                      merged_views=False, true_color=dwg_true_color)
                    path = os.path.join(output_directory, filename)
                    files.append(path)
                    results.append({"success": bool(success), "format": "DWG", "mode": "separate",
                                    "count": 1, "path": path, "sheet_key": getattr(item, "unique_id", None)})

        return {"success": all(r.get("success", False) for r in results) if results else True,
                "results": results, "errors": ["Revit a signalé un échec pendant l'export."]
                if any(not r.get("success") for r in results) else [],
                "warnings": warnings, "files": files}

    def publish_pdf(self, publication_set, output_directory, combined=True, items=None):
        items = self.sort_items(publication_set) if items is None else list(items)
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "PDF", "errors": errors}
        return self._publish_items(publication_set, items, output_directory,
                                   export_pdf=True, export_dwg=False, pdf_combined=combined)

    def publish_dwg(self, publication_set, output_directory, setup_name=None,
                    combined=False, true_color=True, items=None):
        items = self.sort_items(publication_set) if items is None else list(items)
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "DWG", "errors": errors}
        return self._publish_items(publication_set, items, output_directory,
                                   export_pdf=False, export_dwg=True,
                                   dwg_combined=combined, dwg_setup_name=setup_name,
                                   dwg_true_color=true_color)

    def publish(self, publication_set, output_directory, export_pdf=True,
                export_dwg=False, pdf_combined=True, dwg_combined=False,
                dwg_setup_name=None, dwg_true_color=True, items=None):
        """Exécute les formats demandés, éventuellement sur un sous-ensemble de feuilles."""
        if not export_pdf and not export_dwg:
            return {"success": False, "carnet": getattr(publication_set, "name", None),
                    "output_directory": output_directory, "results": [],
                    "errors": ["Aucun format de publication n'est sélectionné."]}
        if items is None:
            items = self.sort_items(publication_set)
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "carnet": getattr(publication_set, "name", None),
                    "output_directory": output_directory, "results": [], "errors": errors,
                    "warnings": []}
        result = self._publish_items(publication_set, list(items), output_directory,
                                     export_pdf=export_pdf, export_dwg=export_dwg,
                                     pdf_combined=pdf_combined, dwg_combined=dwg_combined,
                                     dwg_setup_name=dwg_setup_name, dwg_true_color=dwg_true_color)
        result["carnet"] = publication_set.name if publication_set else None
        result["output_directory"] = output_directory
        return result
