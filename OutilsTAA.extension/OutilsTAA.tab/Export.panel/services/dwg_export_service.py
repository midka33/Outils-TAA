# -*- coding: utf-8 -*-
"""Service d'export DWG natif Revit pour l'outil Export."""

import os


class DwgExportService(object):
    """Exécute les exports DWG natifs à partir d'une configuration Revit."""

    def __init__(self, document):
        self.document = document

    def get_predefined_setups(self):
        """Retourne les configurations DWG natives disponibles dans Revit."""
        from Autodesk.Revit.DB import DWGExportOptions
        return list(DWGExportOptions.GetPredefinedSetupNames(self.document))

    def _get_options(self, setup_name=None, merged_views=False,
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

        # MergedViews demande à Revit de produire un fichier principal unique
        # en utilisant les vues exportées comme références externes.
        options.MergedViews = bool(merged_views)

        if true_color:
            # La configuration explicite ici le comportement attendu par TAA.
            # Une configuration prédéfinie peut toujours être utilisée sans
            # cette surcharge lorsque le profil doit respecter ses réglages.
            try:
                from Autodesk.Revit.DB import ExportColorMode
                options.Colors = ExportColorMode.TrueColor
            except Exception:
                # Compatibilité avec les environnements où l'énumération n'est
                # pas exposée de la même manière par le moteur Python.
                pass

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
                        setup_name=None, true_color=False):
        """Exporte plusieurs feuilles en DWG distincts.

        Revit utilise ``filename_prefix`` comme préfixe lorsque plusieurs vues
        sont exportées. Le choix exact du suffixe reste piloté par Revit et sa
        configuration de nommage.
        """
        self._validate(view_ids, output_directory, filename_prefix)
        options = self._get_options(
            setup_name,
            merged_views=False,
            true_color=true_color
        )
        return self.document.Export(
            output_directory,
            filename_prefix,
            list(view_ids),
            options
        )

    def export_combined(self, view_ids, output_directory, filename,
                        setup_name=None, true_color=False):
        """Exporte un carnet en fichier DWG principal unique via MergedViews.

        Revit documente MergedViews comme la fusion des vues dans un fichier
        par l'intermédiaire de références externes (XRefs). Cette solution est
        native Revit et constitue notre première implémentation du DWG combiné.
        """
        self._validate(view_ids, output_directory, filename)
        options = self._get_options(
            setup_name,
            merged_views=True,
            true_color=true_color
        )
        return self.document.Export(
            output_directory,
            filename,
            list(view_ids),
            options
        )

    def export(self, view_ids, output_directory, filename, setup_name=None,
               merged_views=False, true_color=False):
        """Point d'entrée compatible pour l'export DWG."""
        if merged_views:
            return self.export_combined(
                view_ids,
                output_directory,
                filename,
                setup_name,
                true_color
            )

        return self.export_separate(
            view_ids,
            output_directory,
            filename,
            setup_name,
            true_color
        )
