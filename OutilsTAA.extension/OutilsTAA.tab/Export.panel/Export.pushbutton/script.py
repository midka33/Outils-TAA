# -*- coding: utf-8 -*-
"""Entry point for the Export module."""

import hashlib
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
EXTENSION_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
PANEL_DIR = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
MODEL_DIR = os.path.join(PANEL_DIR, "models")
SERVICE_DIR = os.path.join(PANEL_DIR, "services")
for path in (EXTENSION_DIR, MODEL_DIR, SERVICE_DIR, PANEL_DIR):
    if path not in sys.path:
        sys.path.append(path)

from lib.common import parameter_utils
from export_service import ExportService
from carnet_service import CarnetService
from parameter_service import ParameterService
from publication_service import PublicationService
from carnet_controller import CarnetController
from carnet_repository import CarnetRepository
from export_window import ExportWindow
import publication_preview_integration
from publication_preview_integration import install_preview_on_export_window
from publication_tree_drag_drop import PublicationTreeDragDrop
from publication_history_service import PublicationHistoryService

install_preview_on_export_window(ExportWindow)


def _get_project_identity(document):
    """Retourne une identité stable du projet Revit courant."""
    if document is None:
        return "unknown-project"
    try:
        from Autodesk.Revit.DB import ModelPathUtils
        central_path = document.GetWorksharingCentralModelPath()
        if central_path:
            return ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
    except Exception:
        pass
    try:
        if document.PathName:
            return document.PathName
    except Exception:
        pass
    try:
        if document.Title:
            return "UNSAVED:" + document.Title
    except Exception:
        pass
    return "unknown-project"


def _get_storage_path(document):
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    directory = os.path.join(app_data, "Outils-TAA", "Export", "Projects")
    project_key = hashlib.sha1(_get_project_identity(document).encode("utf-8")).hexdigest()
    return os.path.join(directory, project_key + "_carnets.json")


def _get_history_path(document):
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    directory = os.path.join(app_data, "Outils-TAA", "Export", "History")
    project_key = hashlib.sha1(_get_project_identity(document).encode("utf-8")).hexdigest()
    return os.path.join(directory, project_key + "_history.json")


def _history_service(window):
    return PublicationHistoryService(_get_history_path(window.controller.document))


def _current_states(window, publication_set):
    history = _history_service(window)
    states = {}
    service = window.controller.publication_service
    for item in getattr(publication_set, "items", []) or []:
        key = history.item_key(item)
        current_id = service._resolve_current_sheet_id(item)
        version_guid = None
        if current_id is not None:
            try:
                version_guid = getattr(service.document.GetElement(current_id), "VersionGuid", None)
            except Exception:
                pass
        states[key] = history.fingerprint(item, version_guid)
    return states


def _install_modified_only_value_support(window):
    """Ajoute le champ Stage 07 au mécanisme générique de sauvegarde UI."""
    original = window._control_value
    def control_value(field):
        if field == "modified_only":
            return bool(window.ModifiedOnlyCheckBox.IsChecked)
        return original(field)
    window._control_value = control_value


def _install_modified_only_selection_sync(window):
    def on_selection_changed(sender, args):
        try:
            if window._selected_kind == "FOLDER" and window._selected_folder is not None:
                settings = window._selected_folder.publication_settings
                value = bool(getattr(settings, "modified_only", False)) if settings is not None else False
            elif window._selected_set is not None:
                value = bool(getattr(window._resolve_settings(window._selected_set), "modified_only", False))
            else:
                value = False
            window._loading_settings = True
            window.ModifiedOnlyCheckBox.IsChecked = value
            window._loading_settings = False
        except Exception:
            try:
                window._loading_settings = False
            except Exception:
                pass
    window.PublicationTree.SelectedItemChanged += on_selection_changed
    window._modified_only_selection_sync = on_selection_changed


def _build_preview_stage07(window, targets):
    service = publication_preview_integration.PublicationPreviewService(
        window.controller.publication_service, window.filename_service)
    previews = []
    for target in targets:
        settings = window._resolve_settings(target)
        try:
            target.folder_name = window._folder_name(target)
        except Exception:
            pass
        history = _history_service(window)
        states = _current_states(window, target)
        candidates, classified = history.candidates(target, states, settings.modified_only)
        previews.append(service.build(target, settings, history_service=history,
                                      current_states=states, classified=classified,
                                      modified_only=settings.modified_only))
    return publication_preview_integration._merge_previews(previews)


def _publish_targets_stage07(window, targets):
    all_results, all_errors, all_warnings = [], [], []
    all_success = True
    output_directory = None
    history = _history_service(window)
    for publication_set in targets:
        settings = window._resolve_settings(publication_set)
        errors = settings.validate()
        if errors:
            all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in errors])
            all_success = False
            continue
        states = _current_states(window, publication_set)
        candidates, classified = history.candidates(publication_set, states, settings.modified_only)
        if settings.modified_only and not candidates:
            all_warnings.append("{0} : aucune mise en page nouvelle ou modifiée à publier.".format(publication_set.name))
            continue
        output_directory = settings.output_directory
        try:
            result = window.controller.publish(
                publication_set, settings.output_directory,
                export_pdf=settings.pdf_enabled, export_dwg=settings.dwg_enabled,
                pdf_combined=settings.pdf_mode == "COMBINED",
                dwg_combined=settings.dwg_mode == "COMBINED",
                dwg_setup_name=settings.dwg_setup_name,
                dwg_true_color=settings.dwg_true_color, items=candidates)
        except Exception as exc:
            result = {"success": False, "results": [], "errors": [str(exc)], "warnings": []}
        for item_result in result.get("results", []):
            row = dict(item_result)
            row["carnet"] = publication_set.name
            all_results.append(row)
        all_errors.extend(["{0} : {1}".format(publication_set.name, e) for e in result.get("errors", [])])
        all_warnings.extend(["{0} : {1}".format(publication_set.name, w) for w in result.get("warnings", [])])
        target_success = bool(result.get("success"))
        all_success = all_success and target_success
        if target_success:
            history.record_publication(publication_set, states, successful=True,
                                       output_paths=[r.get("path") for r in result.get("results", []) if r.get("path")])
    report = {"success": all_success, "carnet": "Publication : carnet/mise en page",
              "results": all_results, "errors": all_errors, "warnings": all_warnings,
              "output_directory": output_directory or ""}
    publication_preview_integration.PublicationReportWindow(report, owner=window).ShowDialog()


def _preview_then_publish_folder_stage07(window, targets):
    preview = _build_preview_stage07(window, targets)
    if not targets:
        preview["errors"].append("Le dossier « {0} » ne contient aucun carnet publiable.".format(window._selected_folder.name))
    dialog = publication_preview_integration.PublicationPreviewWindow(preview, owner=window)
    dialog.ShowDialog()
    if not dialog.confirmed:
        return
    history = _history_service(window)
    batch = publication_preview_integration.PublicationBatchService(window.controller.publication_service)
    for target in targets:
        settings = window._resolve_settings(target)
        states = _current_states(window, target)
        candidates, classified = history.candidates(target, states, settings.modified_only)
        target._publication_items = candidates
        target._history_info = {"states": states}
    report_data = batch.publish(targets, lambda target: window._resolve_settings(target),
                                window._folder_for_set, history_service=history)
    report = {"success": report_data.get("success", False),
              "carnet": "Publication : dossier « {0} »".format(window._selected_folder.name),
              "results": report_data.get("results", []), "errors": report_data.get("errors", []),
              "warnings": report_data.get("warnings", []),
              "output_directory": "; ".join(report_data.get("output_directories", []))}
    publication_preview_integration.PublicationReportWindow(report, owner=window).ShowDialog()


def _install_stage07_hooks():
    """Branche Stage 07 sur les handlers déjà installés par l'intégration."""
    def modified_only_changed(self, sender, args):
        if getattr(self, "_loading_settings", False):
            return
        if self._selected_kind == "FOLDER":
            self._save_folder_settings("modified_only")
        else:
            self._save_selected_field("modified_only")
    ExportWindow.ModifiedOnlyChanged = modified_only_changed
    publication_preview_integration._build_preview = _build_preview_stage07
    publication_preview_integration._publish_targets = _publish_targets_stage07
    publication_preview_integration._preview_then_publish_folder = _preview_then_publish_folder_stage07


_install_stage07_hooks()


def main():
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit is not available.")
    export_service = ExportService(revit.doc, parameter_utils)
    carnet_service = CarnetService(export_service)
    parameter_service = ParameterService(parameter_utils)
    publication_service = PublicationService(revit.doc)
    repository = CarnetRepository(_get_storage_path(revit.doc))
    controller = CarnetController(export_service, carnet_service, parameter_service,
                                   repository, publication_service)
    window = ExportWindow(controller, repository)
    _install_modified_only_selection_sync(window)
    _install_modified_only_value_support(window)
    window._publication_tree_drag_drop = PublicationTreeDragDrop(window)
    window.ShowDialog()


if __name__ == "__main__":
    main()
