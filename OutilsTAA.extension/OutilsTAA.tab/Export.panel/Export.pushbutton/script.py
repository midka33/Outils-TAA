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
from publication_preview_integration import install_preview_on_export_window
from publication_tree_drag_drop import PublicationTreeDragDrop


# L'aperçu est installé avant la création de la fenêtre afin que le bouton
# de publication passe systématiquement par la phase de confirmation.
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
    """Retourne le fichier de carnets propre au projet Revit courant."""
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    directory = os.path.join(app_data, "Outils-TAA", "Export", "Projects")

    project_identity = _get_project_identity(document)
    project_key = hashlib.sha1(project_identity.encode("utf-8")).hexdigest()
    return os.path.join(directory, project_key + "_carnets.json")


def _install_modified_only_selection_sync(window):
    """Synchronise la case Modifiés uniquement avec la sélection courante."""
    def on_selection_changed(sender, args):
        try:
            if window._selected_kind == "FOLDER" and window._selected_folder is not None:
                settings = window._selected_folder.publication_settings
                value = bool(getattr(settings, "modified_only", False)) if settings is not None else False
            elif window._selected_set is not None:
                settings = window._resolve_settings(window._selected_set)
                value = bool(getattr(settings, "modified_only", False))
            else:
                value = False
            window._loading_settings = True
            try:
                window.ModifiedOnlyCheckBox.IsChecked = value
            finally:
                window._loading_settings = False
        except Exception:
            # La synchronisation visuelle ne doit jamais empêcher l'outil de
            # poursuivre son flux normal de sélection.
            pass

    window.PublicationTree.SelectedItemChanged += on_selection_changed
    window._modified_only_selection_sync = on_selection_changed


def main():
    """Launch the Export WPF window."""
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit is not available.")

    export_service = ExportService(revit.doc, parameter_utils)
    carnet_service = CarnetService(export_service)
    parameter_service = ParameterService(parameter_utils)
    publication_service = PublicationService(revit.doc)
    repository = CarnetRepository(_get_storage_path(revit.doc))

    controller = CarnetController(
        export_service,
        carnet_service,
        parameter_service,
        repository,
        publication_service
    )

    window = ExportWindow(controller, repository)
    _install_modified_only_selection_sync(window)

    # Important : le gestionnaire de glisser-déposer doit être conservé en
    # vie pendant toute la durée de la fenêtre. Sans cette instance, les
    # événements WPF ne sont jamais abonnés à PublicationTree.
    window._publication_tree_drag_drop = PublicationTreeDragDrop(window)

    window.ShowDialog()


if __name__ == "__main__":
    main()
