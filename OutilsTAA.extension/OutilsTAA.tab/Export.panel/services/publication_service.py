# -*- coding: utf-8 -*-
"""Orchestrateur de publication de l'outil Export."""

import os

from PdfExportService import PdfExportService
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
        """Résout l'ElementId de la feuille dans le document Revit courant."""
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
        """Retourne les erreurs fonctionnelles bloquant la publication."""
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
                errors.append(
                    "La feuille '{}' est introuvable dans le document Revit."
                    .format(getattr(item, "sheet_number", None) or
                            getattr(item, "sheet_name", ""))
                )
                continue
            try:
                key = current_id.IntegerValue
            except Exception:
                key = str(current_id)
            if key in seen_ids:
                errors.append(
                    "Le carnet contient une feuille en double (ID {}).".format(key)
                )
            seen_ids.add(key)
            try:
                view = self.document.GetElement(current_id)
                if view is not None and not view.CanBePrinted:
                    errors.append(
                        "La feuille '{}' n'est pas exportable/imprimable."
                        .format(getattr(item, "sheet_number", None) or
                                getattr(item, "sheet_name", ""))
                    )
            except Exception:
                pass
        return errors

    def sort_items(self, publication_set):
        """Retourne les éléments triés par numéro de feuille."""
        if publication_set is None:
            return []
        return sorted(
            publication_set.items,
            key=lambda item: (
                item.sheet_number or "",
                item.sheet_name or "",
                item.unique_id or ""
            )
        )

    def _current_view_ids(self, publication_set):
        """Retourne les ElementId des feuilles du document courant."""
        view_ids = []
        for item in self.sort_items(publication_set):
            current_id = self._resolve_current_sheet_id(item)
            if current_id is not None:
                view_ids.append(current_id)
        return view_ids

    def _prepare_output_directory(self, output_directory):
        """Crée le dossier de sortie si nécessaire."""
        if not output_directory:
            raise ValueError("Le dossier de destination est manquant.")
        output_directory = os.path.abspath(output_directory)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)
        return output_directory

    def _snapshot_files(self, output_directory, extension):
        """Mémorise les fichiers existants avant un export."""
        try:
            return set(name for name in os.listdir(output_directory)
                       if name.lower().endswith(extension.lower()))
        except Exception:
            return set()

    def _created_files(self, output_directory, before, extension):
        """Retourne les fichiers créés ou modifiés par l'export."""
        try:
            names = [name for name in os.listdir(output_directory)
                     if name.lower().endswith(extension.lower())]
        except Exception:
            return []
        created = [name for name in names if name not in before]
        return [os.path.join(output_directory, name) for name in sorted(created)]

    def _folder_name(self, publication_set):
        """Retourne le nom du dossier parent lorsque disponible."""
        return getattr(publication_set, "folder_name", None)

    def _filename(self, publication_set, item, extension):
        """Résout le nom du livrable et retourne aussi les variables manquantes."""
        template = getattr(
            getattr(publication_set, "publication_settings", None),
            "filename_template",
            None
        ) or "{carnet}"
        return self.filename_service.filename(
            template,
            publication_set,
            item=item,
            folder_name=self._folder_name(publication_set),
            extension=extension
        )

    def publish_pdf(self, publication_set, output_directory, combined=True):
        """Publie un carnet en PDF combiné ou en fichiers séparés."""
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "PDF", "errors": errors}

        output_directory = self._prepare_output_directory(output_directory)
        items = self.sort_items(publication_set)
        view_ids = self._current_view_ids(publication_set)
        warnings = []
        files = []

        try:
            if combined:
                filename, unknown = self._filename(publication_set, None, ".pdf")
                if unknown:
                    warnings.append(
                        "Variables non résolues dans le nom PDF : {}."
                        .format(", ".join(unknown))
                    )
                base = os.path.splitext(filename)[0]
                success = self.pdf_service.export(
                    view_ids, output_directory, base, combined=True
                )
                files = [os.path.join(output_directory, filename)]
            else:
                success = True
                for item in items:
                    current_id = self._resolve_current_sheet_id(item)
                    filename, unknown = self._filename(publication_set, item, ".pdf")
                    if unknown:
                        warnings.append(
                            "Variables non résolues pour {} : {}."
                            .format(item.sheet_number or item.sheet_name or "feuille",
                                    ", ".join(unknown))
                        )
                    base = os.path.splitext(filename)[0]
                    item_success = self.pdf_service.export(
                        [current_id], output_directory, base, combined=True
                    )
                    success = success and bool(item_success)
                    files.append(os.path.join(output_directory, filename))

            return {
                "success": bool(success), "format": "PDF",
                "mode": "combined" if combined else "separate",
                "directory": output_directory, "count": len(items),
                "errors": [] if success else ["Revit a signalé un échec pendant l'export PDF."],
                "warnings": warnings, "files": files
            }
        except Exception as exc:
            return {
                "success": False, "format": "PDF",
                "mode": "combined" if combined else "separate",
                "directory": output_directory, "count": len(items),
                "errors": [str(exc)], "warnings": warnings, "files": files
            }

    def publish_dwg(self, publication_set, output_directory,
                    setup_name=None, combined=False, true_color=True):
        """Publie un carnet en DWG combiné natif ou en fichiers séparés."""
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "DWG", "errors": errors}

        output_directory = self._prepare_output_directory(output_directory)
        items = self.sort_items(publication_set)
        view_ids = self._current_view_ids(publication_set)
        warnings = []
        files = []

        try:
            if combined:
                filename, unknown = self._filename(publication_set, None, ".dwg")
                if unknown:
                    warnings.append(
                        "Variables non résolues dans le nom DWG : {}."
                        .format(", ".join(unknown))
                    )
                base = os.path.splitext(filename)[0]
                success = self.dwg_service.export(
                    view_ids, output_directory, base, setup_name,
                    merged_views=True, true_color=true_color
                )
                files = [os.path.join(output_directory, filename)]
            else:
                success = True
                for item in items:
                    current_id = self._resolve_current_sheet_id(item)
                    filename, unknown = self._filename(publication_set, item, ".dwg")
                    if unknown:
                        warnings.append(
                            "Variables non résolues pour {} : {}."
                            .format(item.sheet_number or item.sheet_name or "feuille",
                                    ", ".join(unknown))
                        )
                    base = os.path.splitext(filename)[0]
                    item_success = self.dwg_service.export(
                        [current_id], output_directory, base, setup_name,
                        merged_views=False, true_color=true_color
                    )
                    success = success and bool(item_success)
                    files.append(os.path.join(output_directory, filename))

            return {
                "success": bool(success), "format": "DWG",
                "mode": "combined" if combined else "separate",
                "directory": output_directory, "count": len(items),
                "errors": [] if success else ["Revit a signalé un échec pendant l'export DWG."],
                "warnings": warnings, "files": files
            }
        except Exception as exc:
            return {
                "success": False, "format": "DWG",
                "mode": "combined" if combined else "separate",
                "directory": output_directory, "count": len(items),
                "errors": [str(exc)], "warnings": warnings, "files": files
            }

    def publish(self, publication_set, output_directory,
                export_pdf=True, export_dwg=False,
                pdf_combined=True, dwg_combined=False,
                dwg_setup_name=None, dwg_true_color=True):
        """Exécute les formats demandés et retourne un rapport synthétique."""
        if not export_pdf and not export_dwg:
            return {
                "success": False,
                "carnet": getattr(publication_set, "name", None),
                "output_directory": output_directory,
                "results": [],
                "errors": ["Aucun format de publication n'est sélectionné."]
            }

        results = []
        if export_pdf:
            results.append(self.publish_pdf(
                publication_set, output_directory, combined=pdf_combined))
        if export_dwg:
            results.append(self.publish_dwg(
                publication_set, output_directory,
                setup_name=dwg_setup_name, combined=dwg_combined,
                true_color=dwg_true_color))

        return {
            "success": all(result.get("success", False) for result in results),
            "carnet": publication_set.name if publication_set else None,
            "output_directory": output_directory,
            "results": results,
            "errors": [error for result in results
                       for error in result.get("errors", [])],
            "warnings": [warning for result in results
                         for warning in result.get("warnings", [])]
        }
