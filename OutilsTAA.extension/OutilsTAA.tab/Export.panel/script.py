"""Point d'entrée pyRevit du module Export."""

import os
import sys


CURRENT_DIR = os.path.dirname(__file__)
EXTENSION_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))

if EXTENSION_DIR not in sys.path:
    sys.path.append(EXTENSION_DIR)

SERVICE_DIR = os.path.join(CURRENT_DIR, "services")
if SERVICE_DIR not in sys.path:
    sys.path.append(SERVICE_DIR)

from lib.common import parameter_utils
from export_service import ExportService


def main():
    """Point d'entrée principal du module Export."""
    try:
        from pyrevit import revit
    except ImportError:
        raise RuntimeError("pyRevit n'est pas disponible.")

    service = ExportService(revit.doc, parameter_utils)
    sheets = service.get_sheets()

    # Cette première version prépare uniquement le jeu de feuilles.
    # L'interface et les moteurs PDF/DWG seront ajoutés par étapes.
    return service.build_publication_items(sheets)


if __name__ == "__main__":
    main()
