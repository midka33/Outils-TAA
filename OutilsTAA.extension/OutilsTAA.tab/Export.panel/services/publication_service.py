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
            sheet_id = getattr(item, "sheet_id", None)
            if sheet_id is None:
                errors.append(
                    "Une feuille du carnet ne possède pas d'identifiant Revit valide."
                )
                continue

            try:
                key = sheet_id.IntegerValue
            except Exception:
                key = str(sheet_id)

            if key in seen_ids:
                errors.append(
                    "Le carnet contient une feuille en double (ID {}).".format(key)
                )
            seen_ids.add(key)

            view = None
            try:
                view = self.document.GetElement(sheet_id)
            except Exception:
                pass

            if view is None:
                errors.append(
                    "La feuille '{}' est introuvable dans le document Revit."
                    .format(getattr(item, "sheet_number", None) or
                            getattr(item, "sheet_name", ""))
                )
            else:
                try:
                    if not view.CanBePrinted:
                        errors.append(
                            "La feuille '{}' n'est pas exportable/imprimable."
                            .format(getattr(item, "sheet_number", None) or
                                    getattr(item, "sheet_name", ""))
                        )
                except Exception:
                    # Si la propriété n'est pas disponible sur un objet inattendu,
                    # l'API d'export donnera le détail de l'erreur.
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
            return set(
                name for name in os.listdir(output_directory)
                if name.lower().endswith(extension.lower())
            )
        except Exception:
            return set()

    def _created_files(self, output_directory, before, extension):
        """Retourne les fichiers créés ou modifiés par l'export."""
        try:
            names = [
                name for name in os.listdir(output_directory)
                if name.lower().endswith(extension.lower())
            ]
        except Exception:
            return []

        created = [name for name in names if name not in before]
        if created:
            return [os.path.join(output_directory, name) for name in sorted(created)]

        # Un export peut remplacer un fichier existant. Dans ce cas, le chemin
        # attendu reste utile dans le rapport, même si aucun nouveau nom n'est créé.
        return []

    def publish_pdf(self, publication_set, output_directory,
                    combined=True):
        """Publie un carnet en PDF combiné ou en fichiers séparés."""
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "PDF", "errors": errors}

        output_directory = self._prepare_output_directory(output_directory)
        items = self.sort_items(publication_set)
        view_ids = [item.sheet_id for item in items]
        before = self._snapshot_files(output_directory, ".pdf")

        try:
            success = self.pdf_service.export(
                view_ids,
                output_directory,
                publication_set.name if combined else None,
                combined=combined
            )
            result = {
                "success": bool(success),
                "format": "PDF",
                "mode": "combined" if combined else "separate",
                "directory": output_directory,
                "count": len(items),
                "errors": [] if success else [
                    "Revit a signalé un échec pendant l'export PDF."
                ]
            }
            if combined:
                result["file"] = os.path.join(
                    output_directory,
                    publication_set.name + ".pdf"
                )
                result["files"] = [result["file"]]
            else:
                result["files"] = self._created_files(
                    output_directory, before, ".pdf"
                )
            return result
        except Exception as exc:
            return {
                "success": False,
                "format": "PDF",
                "mode": "combined" if combined else "separate",
                "directory": output_directory,
                "count": len(items),
                "errors": [str(exc)],
                "files": []
            }

    def publish_dwg(self, publication_set, output_directory,
                    setup_name=None, combined=False, true_color=True):
        """Publie un carnet en DWG combiné natif ou en fichiers séparés."""
        errors = self.validate_publication_set(publication_set)
        if errors:
            return {"success": False, "format": "DWG", "errors": errors}

        output_directory = self._prepare_output_directory(output_directory)
        items = self.sort_items(publication_set)
        view_ids = [item.sheet_id for item in items]
        before = self._snapshot_files(output_directory, ".dwg")

        try:
            success = self.dwg_service.export(
                view_ids,
                output_directory,
                publication_set.name,
                setup_name,
                merged_views=combined,
                true_color=true_color
            )
            result = {
                "success": bool(success),
                "format": "DWG",
                "mode": "combined" if combined else "separate",
                "directory": output_directory,
                "count": len(items),
                "errors": [] if success else [
                    "Revit a signalé un échec pendant l'export DWG."
                ]
            }
            if combined:
                result["file"] = os.path.join(
                    output_directory,
                    publication_set.name + ".dwg"
                )
                result["files"] = [result["file"]]
            else:
                result["files"] = self._created_files(
                    output_directory, before, ".dwg"
                )
            return result
        except Exception as exc:
            return {
                "success": False,
                "format": "DWG",
                "mode": "combined" if combined else "separate",
                "directory": output_directory,
                "count": len(items),
                "errors": [str(exc)],
                "files": []
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
            results.append(
                self.publish_pdf(
                    publication_set,
                    output_directory,
                    combined=pdf_combined
                )
            )
        if export_dwg:
            results.append(
                self.publish_dwg(
                    publication_set,
                    output_directory,
                    setup_name=dwg_setup_name,
                    combined=dwg_combined,
                    true_color=dwg_true_color
                )
            )

        return {
            "success": all(result.get("success", False) for result in results),
            "carnet": publication_set.name if publication_set else None,
            "output_directory": output_directory,
            "results": results,
            "errors": [
                error
                for result in results
                for error in result.get("errors", [])
            ]
        }
