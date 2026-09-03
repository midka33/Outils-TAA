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


def _get_project_identity(document):
    """Retourne une identité stable du projet Revit courant."""
    if document is None:
        return "unknown-project"

    # Pour un modèle collaboratif, utiliser le chemin du modèle central.
    # Cela garantit que tous les utilisateurs d'un même projet partagent
    # les mêmes carnets, tout en séparant les projets différents.
    try:
        from Autodesk.Revit.DB import ModelPathUtils
        central_path = document.GetWorksharingCentralModelPath()
        if central_path:
            return ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
    except Exception:
        pass

    # Modèle non collaboratif : le chemin du fichier est suffisamment stable.
    try:
        if document.PathName:
            return document.PathName
    except Exception:
        pass

    # Dernier recours pour un document non enregistré.
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
    window.ShowDialog()


if __name__ == "__main__":
    main()
