"""Point d'entrée pyRevit du module Export."""

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
from carnet_controller import CarnetController
from carnet_repository import CarnetRepository
from export_window import ExportWindow


def _get_storage_path():
    """Retourne le fichier local de carnets persistants de l'utilisateur."""
    app_data = os.environ.get("APPDATA") or os.path.expanduser("~")
    directory = os.path.join(app_data, "Outils-TAA", "Export")
    return os.path.join(directory, "carnets.json")


def main():
    """Lance l'interface WPF du module Export."""
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    export_service = ExportService(revit.doc, parameter_utils)
    carnet_service = CarnetService(export_service)
    parameter_service = ParameterService(parameter_utils)
    repository = CarnetRepository(_get_storage_path())

    controller = CarnetController(
        export_service,
        carnet_service,
        parameter_service,
        repository
    )

    window = ExportWindow(controller, repository)
    window.ShowDialog()


if __name__ == "__main__":
    main()
