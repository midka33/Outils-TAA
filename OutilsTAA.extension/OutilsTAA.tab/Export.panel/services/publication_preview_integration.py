# -*- coding: utf-8 -*-
"""Intégration de l'aperçu dans le flux de publication Export."""

from publication_preview_service import PublicationPreviewService
from publication_preview_window import PublicationPreviewWindow


def install_preview_on_export_window(export_window_class):
    """Intercepte Publier pour afficher l'aperçu avant tout export Revit."""
    original_publish_click = export_window_class.Publish_Click

    def publish_click_with_preview(self, sender, args):
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
        elif self._selected_kind == "CARNET" and self._selected_set is not None:
            self._selected_set.folder_name = self._folder_name(self._selected_set)
            targets = [self._selected_set]
        else:
            return original_publish_click(self, sender, args)

        preview_service = PublicationPreviewService(
            self.controller.publication_service, self.filename_service)
        previews = []
        for target in targets:
            settings = self._resolve_settings(target)
            target.folder_name = self._folder_name(target)
            previews.append(preview_service.build(target, settings))

        preview = _merge_previews(previews)
        window = PublicationPreviewWindow(preview, owner=self)
        window.ShowDialog()
        if not window.confirmed:
            return

        # L'export réel reste entièrement confié au flux existant.
        return original_publish_click(self, sender, args)

    export_window_class.Publish_Click = publish_click_with_preview


def _merge_previews(previews):
    rows = []
    errors = []
    warnings = []
    directory = ""
    for preview in previews:
        rows.extend(preview.get("rows", []))
        errors.extend(preview.get("errors", []))
        warnings.extend(preview.get("warnings", []))
        if preview.get("directory"):
            directory = preview.get("directory")
    return {"rows": rows, "errors": errors, "warnings": warnings,
            "directory": directory, "count": len(rows)}
