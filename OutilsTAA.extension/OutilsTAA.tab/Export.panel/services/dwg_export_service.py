# -*- coding: utf-8 -*-
"""Service d'export DWG natif Revit pour l'outil Export."""


class DwgExportService(object):
    """Exécute les exports DWG à partir d'une configuration Revit existante."""

    def __init__(self, document):
        self.document = document

    def get_predefined_setups(self):
        """Retourne les configurations DWG natives disponibles dans Revit."""
        from Autodesk.Revit.DB import DWGExportOptions
        return list(DWGExportOptions.GetPredefinedSetupNames(self.document))

    def export(self, view_ids, output_directory, filename, setup_name=None):
        """Exporte les vues/feuilles en DWG avec une configuration native Revit."""
        from Autodesk.Revit.DB import DWGExportOptions

        if not output_directory:
            raise ValueError("Le dossier de destination DWG est manquant.")
        if not filename:
            raise ValueError("Le nom du fichier DWG est manquant.")
        if not view_ids:
            raise ValueError("Aucune feuille à exporter en DWG.")

        if setup_name:
            options = DWGExportOptions.GetPredefinedOptions(
                self.document,
                setup_name
            )
        else:
            options = DWGExportOptions()

        return self.document.Export(
            output_directory,
            filename,
            list(view_ids),
            options
        )
