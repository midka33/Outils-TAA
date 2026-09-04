# -*- coding: utf-8 -*-
"""Prépare un aperçu de publication sans lancer d'export Revit."""

import os


class PublicationPreviewService(object):
    """Construit la liste des livrables attendus et détecte les risques."""

    def __init__(self, publication_service, filename_service):
        self.publication_service = publication_service
        self.filename_service = filename_service

    def build(self, publication_set, settings, history_service=None,
              current_states=None, classified=None, modified_only=False):
        """Retourne les lignes de prévisualisation et les diagnostics."""
        rows = []
        errors = []
        warnings = []
        if publication_set is None:
            return {"rows": [], "errors": ["Aucun carnet de publication sélectionné."], "warnings": []}
        if not settings.output_directory:
            errors.append("Le dossier de destination est manquant.")
        directory = os.path.abspath(settings.output_directory) if settings.output_directory else ""
        items = self.publication_service.sort_items(publication_set)
        if not items:
            errors.append("Aucune mise en page à publier dans le périmètre sélectionné.")

        seen_ids = set()
        valid_items = []
        item_states = current_states or {}
        item_status = {}
        for item in items:
            if classified and history_service is not None:
                key = history_service.item_key(item)
                for state_name in ("NEW", "MODIFIED", "UNCHANGED", "UNKNOWN"):
                    if item in classified.get(state_name, []):
                        item_status[key] = state_name
                        break
            current_id = self.publication_service._resolve_current_sheet_id(item)
            label = "{0} — {1}".format(item.sheet_number or "", item.sheet_name or "").strip(" —")
            if current_id is None:
                errors.append("Mise en page introuvable : {0}.".format(label))
                continue
            try:
                key_id = current_id.IntegerValue
            except Exception:
                key_id = str(current_id)
            if key_id in seen_ids:
                errors.append("Mise en page en double : {0}.".format(label))
                continue
            seen_ids.add(key_id)
            try:
                element = self.publication_service.document.GetElement(current_id)
                if element is not None and not element.CanBePrinted:
                    errors.append("Mise en page non imprimable : {0}.".format(label))
                    continue
            except Exception:
                pass
            valid_items.append(item)

        generated_paths = {}

        def add_row(fmt, mode, item, filename, unknown):
            path = os.path.join(directory, filename) if directory else filename
            normalized = os.path.normcase(os.path.abspath(path)) if directory else os.path.normcase(filename)
            duplicate = normalized in generated_paths
            if duplicate:
                warnings.append("Collision de nom dans la publication : {0}.".format(filename))
            generated_paths[normalized] = True
            exists = bool(directory) and os.path.exists(path)
            if exists:
                warnings.append("Le fichier existe déjà et pourra être remplacé : {0}.".format(path))
            if unknown:
                warnings.append("Variables inconnues pour {0} : {1}.".format(filename, ", ".join(unknown)))
            status = "⚠ Collision" if duplicate or exists else ("⚠ Variables" if unknown else "OK")
            if modified_only:
                if item is None:
                    status = "MODIFIÉ(S)" if valid_items else "AUCUN CHANGEMENT"
                else:
                    key = history_service.item_key(item) if history_service is not None else None
                    status = item_status.get(key, "UNKNOWN")
            rows.append(_PreviewRow(
                getattr(publication_set, "name", "—"),
                item.sheet_number if item is not None else "—",
                item.sheet_name if item is not None else "Publication du carnet",
                fmt, "Combiné" if mode == "COMBINED" else "Séparé", filename, path, status))

        if settings.pdf_enabled:
            if settings.pdf_mode == "COMBINED":
                filename, unknown = self.filename_service.filename(
                    settings.filename_template or "{carnet}", publication_set,
                    item=None, folder_name=getattr(publication_set, "folder_name", None), extension=".pdf")
                add_row("PDF", "COMBINED", None, filename, unknown)
            else:
                for item in valid_items:
                    filename, unknown = self.filename_service.filename(
                        settings.filename_template or "{carnet}", publication_set,
                        item=item, folder_name=getattr(publication_set, "folder_name", None), extension=".pdf")
                    add_row("PDF", "SEPARATE", item, filename, unknown)

        if settings.dwg_enabled:
            if settings.dwg_mode == "COMBINED":
                filename, unknown = self.filename_service.filename(
                    settings.filename_template or "{carnet}", publication_set,
                    item=None, folder_name=getattr(publication_set, "folder_name", None), extension=".dwg")
                add_row("DWG", "COMBINED", None, filename, unknown)
            else:
                for item in valid_items:
                    filename, unknown = self.filename_service.filename(
                        settings.filename_template or "{carnet}", publication_set,
                        item=item, folder_name=getattr(publication_set, "folder_name", None), extension=".dwg")
                    add_row("DWG", "SEPARATE", item, filename, unknown)

        if not settings.pdf_enabled and not settings.dwg_enabled:
            errors.append("Aucun format de publication n'est sélectionné.")

        summary = _state_summary(classified) if classified else {}
        if modified_only:
            warnings.append(
                "Mode « Modifiés uniquement » : NEW={0}, MODIFIED={1}, UNCHANGED={2}, UNKNOWN={3}.".format(
                    summary.get("NEW", 0), summary.get("MODIFIED", 0),
                    summary.get("UNCHANGED", 0), summary.get("UNKNOWN", 0)))

        return {"rows": rows, "errors": errors, "warnings": warnings,
                "directory": directory, "count": len(rows),
                "state_summary": summary, "modified_only": bool(modified_only)}


class _PreviewRow(object):
    """Objet simple compatible avec les bindings WPF du DataGrid."""

    def __init__(self, carnet, number, name, fmt, mode, filename, path, status):
        self.Carnet = carnet or "—"
        self.Number = number or "—"
        self.Name = name or "—"
        self.Format = fmt
        self.Mode = mode
        self.Filename = filename
        self.Path = path
        self.Status = status


def _state_summary(classified):
    return dict((name, len(classified.get(name, []) or []))
                for name in ("NEW", "MODIFIED", "UNCHANGED", "UNKNOWN"))
