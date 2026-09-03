# -*- coding: utf-8 -*-
"""Service d'export PDF natif Revit pour l'outil Export."""


class PdfExportService(object):
    """Prépare et exécute les exports PDF via l'API native Revit."""

    def __init__(self, document):
        self.document = document

    def export(self, sheet_ids, output_directory, filename):
        """Exporte une ou plusieurs feuilles en PDF.

        L'implémentation utilise Document.Export avec PDFExportOptions.
        Elle est volontairement isolée afin de centraliser les réglages Revit.
        """
        from Autodesk.Revit.DB import PDFExportOptions

        options = PDFExportOptions()
        options.Combine = True
        options.FileName = filename
        options.ExportQuality = 300

        if not output_directory:
            raise ValueError("Le dossier de destination PDF est manquant.")

        if not filename:
            raise ValueError("Le nom du fichier PDF est manquant.")

        return self.document.Export(output_directory, list(sheet_ids), options)
