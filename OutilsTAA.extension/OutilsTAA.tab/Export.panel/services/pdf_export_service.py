# -*- coding: utf-8 -*-
"""Service d'export PDF natif Revit pour l'outil Export."""

import os


class PdfExportService(object):
    """Prépare et exécute les exports PDF via l'API native Revit."""

    def __init__(self, document):
        self.document = document

    def _validate(self, sheet_ids, output_directory):
        """Valide les entrées communes aux exports PDF."""
        if not output_directory:
            raise ValueError("Le dossier de destination PDF est manquant.")
        if not os.path.isdir(output_directory):
            raise ValueError(
                "Le dossier de destination PDF n'existe pas : {}"
                .format(output_directory)
            )
        if not sheet_ids:
            raise ValueError("Aucune feuille à exporter en PDF.")

    def export_combined(self, sheet_ids, output_directory, filename,
                        export_quality=300):
        """Exporte toutes les feuilles dans un PDF unique."""
        from Autodesk.Revit.DB import PDFExportOptions

        self._validate(sheet_ids, output_directory)
        if not filename:
            raise ValueError("Le nom du fichier PDF est manquant.")

        options = PDFExportOptions()
        options.Combine = True
        options.FileName = filename
        options.ExportQuality = export_quality

        return self.document.Export(
            output_directory,
            list(sheet_ids),
            options
        )

    def export_separate(self, sheet_ids, output_directory,
                        export_quality=300):
        """Exporte chaque feuille dans son propre PDF.

        Le nom de chaque fichier est alors généré par Revit selon sa règle de
        nommage PDF active. ``FileName`` est volontairement laissé vide :
        l'API l'ignore lorsque Combine est faux.
        """
        from Autodesk.Revit.DB import PDFExportOptions

        self._validate(sheet_ids, output_directory)

        options = PDFExportOptions()
        options.Combine = False
        options.ExportQuality = export_quality

        return self.document.Export(
            output_directory,
            list(sheet_ids),
            options
        )

    def export(self, sheet_ids, output_directory, filename=None,
               combined=True, export_quality=300):
        """Point d'entrée compatible pour les deux modes PDF."""
        if combined:
            return self.export_combined(
                sheet_ids,
                output_directory,
                filename,
                export_quality
            )

        return self.export_separate(
            sheet_ids,
            output_directory,
            export_quality
        )
