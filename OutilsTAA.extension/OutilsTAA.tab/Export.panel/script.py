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


def main():
    """Point d'entrée principal du module Export."""
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    export_service = ExportService(revit.doc, parameter_utils)
    carnet_service = CarnetService(export_service)

    # Le moteur est maintenant capable de créer les trois types de carnets.
    # L'interface utilisateur et l'export PDF/DWG seront branchés ensuite.
    return carnet_service


if __name__ == "__main__":
    main()
