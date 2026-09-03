"""Point d'entrée pyRevit du module Export."""

import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
EXTENSION_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
MODEL_DIR = os.path.join(CURRENT_DIR, "models")
SERVICE_DIR = os.path.join(CURRENT_DIR, "services")

for path in (EXTENSION_DIR, MODEL_DIR, SERVICE_DIR):
    if path not in sys.path:
        sys.path.append(path)

from lib.common import parameter_utils
from export_service import ExportService
from carnet_service import CarnetService
from parameter_service import ParameterService
from carnet_controller import CarnetController


def main():
    """Point d'entrée principal de la couche métier Export."""
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    export_service = ExportService(revit.doc, parameter_utils)
    carnet_service = CarnetService(export_service)
    parameter_service = ParameterService(parameter_utils)

    # La fenêtre WPF consommera cette façade sans accéder directement à Revit.
    return CarnetController(
        export_service,
        carnet_service,
        parameter_service
    )


if __name__ == "__main__":
    main()
