# -*- coding: utf-8 -*-
"""Service d'export DWG natif Revit pour l'outil Export."""

import os


class DwgExportService(object):
    """Exécute les exports DWG natifs à partir d'une configuration Revit."""

    def __init__(self, document):
        self.document = document

    @staticmethod
    def _to_element_ids(view_ids):
        """Construit l'ICollection[ElementId] attendue par l'API DWG."""
        from Autodesk.Revit.DB import ElementId
        from System.Collections.Generic import List
        result = List[ElementId]()
        for view_id in view_ids:
            result.Add(view_id)
        return result

    def get_predefined_setups(self):
        """Retourne les configurations DWG natives disponibles dans Revit."""
        from Autodesk.Revit.DB import DWGExportOptions
        return list(DWGExportOptions.GetPredefinedSetupNames(self.document))

    def _get_options(self, setup_name=None, merged_views=True,
                     true_color=False):
        """Construit les options DWG à partir d'une configuration Revit."""
        from Autodesk.Revit.DB import DWGExportOptions

        if setup_name:
            options = DWGExportOptions.GetPredefinedOptions(
                self.document,
                setup_name
            )
            if options is None:
                raise ValueError(
                    "La configuration DWG Revit '{}' est introuvable."
                    .format(setup_name)
                )
        else:
            options = DWGExportOptions()

        # Fusion des vues/liens d'une feuille, jamais de plusieurs feuilles.
        options.MergedViews = bool(merged_views)
        if true_color:
            # Surcharge explicite historique. Décoché : conserver le preset.
            # Une incompatibilité doit remonter dans le rapport, pas être ignorée.
            from Autodesk.Revit.DB import ExportColorMode
            options.Colors = ExportColorMode.TrueColor

        return options

    def _validate(self, view_ids, output_directory, filename):
        """Valide les entrées communes aux exports DWG."""
        if not output_directory:
            raise ValueError("Le dossier de destination DWG est manquant.")
        if not os.path.isdir(output_directory):
            raise ValueError(
                "Le dossier de destination DWG n'existe pas : {}"
                .format(output_directory)
            )
        if not filename:
            raise ValueError("Le nom de fichier/préfixe DWG est manquant.")
        if not view_ids:
            raise ValueError("Aucune feuille à exporter en DWG.")

    def export_separate(self, view_ids, output_directory, filename_prefix,
                        setup_name=None, true_color=False, merged_views=True):
        """Compatibilité : les références sont indépendantes du lot de feuilles."""
        return self.export(view_ids, output_directory, filename_prefix,
                           setup_name, merged_views, true_color)

    def export_combined(self, view_ids, output_directory, filename,
                        setup_name=None, true_color=False, merged_views=True):
        """Lot natif Revit ; plusieurs feuilles restent plusieurs DWG."""
        return self.export(view_ids, output_directory, filename,
                           setup_name, merged_views, true_color)

    def export(self, view_ids, output_directory, filename, setup_name=None,
               merged_views=True, true_color=False):
        """Exporte la collection typée, avec le preset et deux surcharges au plus."""
        self._validate(view_ids, output_directory, filename)
        options = self._get_options(setup_name, merged_views, true_color)
        return self.document.Export(output_directory, filename,
                                    self._to_element_ids(view_ids), options)
