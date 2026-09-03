# -*- coding: utf-8 -*-
"""Orchestrateur de publication de l'outil Export."""

import os

from pdf_export_service import PdfExportService
from dwg_export_service import DwgExportService


class PublicationService(object):
    """Valide, prépare et exécute une publication."""

    def __init__(self, document):
        self.document = document
        self.pdf_service = PdfExportService(document)
        self.dwg_service = DwgExportService(document)

    def validate_publication_set(self, publication_set):
        """Retourne une liste d'erreurs fonctionnelles."""
        errors = []

        if publication_set is None:
            return ["Le carnet de publication est manquant."]

        if not publication_set.name:
            errors.append("Le carnet doit avoir un nom.")

        if not publication_set.items:
            errors.append("Le carnet ne contient aucun élément à publier.")

        for item in publication_set.items or []:
            if not getattr(item, "sheet_id", None):
                errors.append(
                    "Une feuille du carnet ne possède pas d'identifiant Revit valide."
                )
                break

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

    def publish_pdf(self, publication_set, output_directory):
        """Publie un carnet en un PDF combiné."""
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "PDF", "errors": errors}

        output_directory = os.path.abspath(output_directory)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        items = self.sort_items(publication_set)
        view_ids = [item.sheet_id for item in items]
        filename = publication_set.name

        try:
            success = self.pdf_service.export(
                view_ids,
                output_directory,
                filename
            )
            return {
                "success": bool(success),
                "format": "PDF",
                "file": os.path.join(output_directory, filename + ".pdf"),
                "count": len(items),
                "errors": [] if success else [
                    "Revit a signalé un échec pendant l'export PDF."
                ]
            }
        except Exception as exc:
            return {
                "success": False,
                "format": "PDF",
                "file": os.path.join(output_directory, filename + ".pdf"),
                "count": len(items),
                "errors": [str(exc)]
            }

    def publish_dwg(self, publication_set, output_directory, setup_name=None):
        """Publie les feuilles d'un carnet en DWG via une configuration Revit.

        Revit produit un fichier DWG par vue/feuille exportée. La notion de
        « DWG combiné » ne doit donc pas être simulée ici : elle nécessitera
        ultérieurement un traitement externe ou une définition fonctionnelle
        spécifique.
        """
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "DWG", "errors": errors}

        output_directory = os.path.abspath(output_directory)
        if not os.path.isdir(output_directory):
            os.makedirs(output_directory)

        items = self.sort_items(publication_set)
        view_ids = [item.sheet_id for item in items]

        try:
            success = self.dwg_service.export(
                view_ids,
                output_directory,
                publication_set.name,
                setup_name
            )
            return {
                "success": bool(success),
                "format": "DWG",
                "directory": output_directory,
                "count": len(items),
                "errors": [] if success else [
                    "Revit a signalé un échec pendant l'export DWG."
                ]
            }
        except Exception as exc:
            return {
                "success": False,
                "format": "DWG",
                "directory": output_directory,
                "count": len(items),
                "errors": [str(exc)]
            }

    def publish(self, publication_set, output_directory,
                export_pdf=True, export_dwg=False, dwg_setup_name=None):
        """Exécute les formats demandés et retourne un rapport synthétique."""
        if not export_pdf and not export_dwg:
            return {
                "success": False,
                "carnet": getattr(publication_set, "name", None),
                "results": [],
                "errors": ["Aucun format de publication n'est sélectionné."]
            }

        results = []
        if export_pdf:
            results.append(self.publish_pdf(publication_set, output_directory))
        if export_dwg:
            results.append(
                self.publish_dwg(
                    publication_set,
                    output_directory,
                    dwg_setup_name
                )
            )

        return {
            "success": all(result.get("success", False) for result in results),
            "carnet": publication_set.name if publication_set else None,
            "results": results,
            "errors": [
                error
                for result in results
                for error in result.get("errors", [])
            ]
        }
