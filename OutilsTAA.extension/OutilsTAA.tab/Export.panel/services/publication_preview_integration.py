# -*- coding: utf-8 -*-
"""Intégration des flux avancés de publication dans Export."""

from pyrevit import forms

from publication_preview_service import PublicationPreviewService
from publication_preview_window import PublicationPreviewWindow
from publication_batch_service import PublicationBatchService
from export_report_window import PublicationReportWindow
from carnet_manager_window import CarnetManagerWindow
from publication_tree_drag_drop import PublicationTreeDragDrop


def install_preview_on_export_window(export_window_class):
    """Installe aperçu, publication de dossier et réorganisation par glisser-déposer."""
    original_publish_click = export_window_class.Publish_Click
    original_selection_changed = export_window_class.Tree_SelectedItemChanged
    original_manager_click = export_window_class.OpenCarnetManager_Click
    original_init = export_window_class.__init__

    def init_with_tree_features(self, controller, repository):
        original_init(self, controller, repository)
        if not hasattr(self, "_publication_tree_drag_drop"):
            self._publication_tree_drag_drop = PublicationTreeDragDrop(self)

    def selection_changed_with_folder_action(self, sender, args):
        original_selection_changed(self, sender, args)
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            count = len(_folder_targets(self, self._selected_folder))
            self.PublishButton.Content = "Publier le dossier « {0} »".format(self._selected_folder.name)
            self.PublishButton.IsEnabled = count > 0

    def manager_click_with_folder(self, sender, args):
        # Le dossier actuellement sélectionné devient le dossier cible des nouveaux carnets.
        target_folder_id = "default"
        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            target_folder_id = self._selected_folder.id
        elif self._selected_set is not None:
            target_folder_id = getattr(self._selected_set, "folder_id", None) or "default"

        manager = CarnetManagerWindow(
            self.controller, owner=self, target_folder_id=target_folder_id
        )
        manager.ShowDialog()
        if manager.result:
            for carnet in manager.result:
                if not carnet.persistent:
                    self.session_carnets.append(carnet)
            self._refresh_tree()

    def publish_click_with_preview(self, sender, args):
        if self._selected_kind == "SHEET" and self._selected_item is not None:
            targets = [self._make_sheet_target()]
            return _preview_then_publish_single(self, targets, original_publish_click)

        if self._selected_kind == "CARNET" and self._selected_set is not None:
            self._selected_set.folder_name = self._folder_name(self._selected_set)
            targets = [self._selected_set]
            return _preview_then_publish_single(self, targets, original_publish_click)

        if self._selected_kind == "FOLDER" and self._selected_folder is not None:
            targets = _folder_targets(self, self._selected_folder)
            return _preview_then_publish_folder(self, targets)

        return original_publish_click(self, sender, args)

    export_window_class.__init__ = init_with_tree_features
    export_window_class.Tree_SelectedItemChanged = selection_changed_with_folder_action
    export_window_class.OpenCarnetManager_Click = manager_click_with_folder
    export_window_class.Publish_Click = publish_click_with_preview


def _folder_targets(window, folder):
    """Retourne les carnets du dossier et de ses sous-dossiers, sans doublons."""
    if folder is None:
        return []
    descendant_ids = set([folder.id])
    changed = True
    while changed:
        changed = False
        for candidate in window._folders:
            if candidate.id in descendant_ids:
                continue
            if candidate.parent_id in descendant_ids:
                descendant_ids.add(candidate.id)
                changed = True

    targets = []
    seen = set()
    for carnet in window._carnets:
        if carnet.folder_id not in descendant_ids:
            continue
        key = carnet.id or id(carnet)
        if key in seen:
            continue
        carnet.folder_name = window._folder_name(carnet)
        targets.append(carnet)
        seen.add(key)
    return targets


def _build_preview(window, targets):
    preview_service = PublicationPreviewService(
        window.controller.publication_service, window.filename_service)
    previews = []
    for target in targets:
        settings = window._resolve_settings(target)
        target.folder_name = window._folder_name(target)
        previews.append(preview_service.build(target, settings))
    return _merge_previews(previews)


def _preview_then_publish_single(window, targets, original_publish_click):
    preview = _build_preview(window, targets)
    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return
    return original_publish_click(window, None, None)


def _preview_then_publish_folder(window, targets):
    preview = _build_preview(window, targets)
    if not targets:
        preview["errors"].append(
            "Le dossier « {0} » ne contient aucun carnet publiable.".format(
                window._selected_folder.name
            )
        )

    dialog = PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return

    batch_service = PublicationBatchService(window.controller.publication_service)
    report_data = batch_service.publish(
        targets, window._resolve_settings, window._folder_for_set
    )
    report = {
        "success": report_data.get("success", False),
        "carnet": "Publication : dossier « {0} »".format(window._selected_folder.name),
        "results": report_data.get("results", []),
        "errors": report_data.get("errors", []),
        "warnings": report_data.get("warnings", []),
        "output_directory": "; ".join(report_data.get("output_directories", []))
    }
    PublicationReportWindow(report, owner=window).ShowDialog()


def _merge_previews(previews):
    rows = []
    errors = []
    warnings = []
    directories = []
    for preview in previews:
        rows.extend(preview.get("rows", []))
        errors.extend(preview.get("errors", []))
        warnings.extend(preview.get("warnings", []))
        directory = preview.get("directory")
        if directory and directory not in directories:
            directories.append(directory)

    if len(directories) == 1:
        directory = directories[0]
    elif directories:
        directory = "Plusieurs destinations ({0})".format(len(directories))
    else:
        directory = ""

    return {"rows": rows, "errors": errors, "warnings": warnings,
            "directory": directory, "count": len(rows)}
