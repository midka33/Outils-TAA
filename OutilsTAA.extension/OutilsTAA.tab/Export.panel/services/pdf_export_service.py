# -*- coding: utf-8 -*-
"""Service d'export PDF natif Revit pour l'outil Export."""

import os
from pdf_file_delivery import (deliver_named_pdfs, validate_names,
                               validate_native_keys, reconcile_native_pdfs)
from filename_service import FilenameService
from pdf_options import apply_options
from publication_progress import operation, progress_kwargs


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

    def _to_export_quality(self, export_quality):
        """Convertit une résolution numérique en enum Revit.

        Revit 2025 expose ExportQuality comme PDFExportQualityType et non
        comme une propriété numérique. On conserve toutefois l'argument
        numérique pour la compatibilité avec les appels existants du service.
        """
        from Autodesk.Revit.DB import PDFExportQualityType

        if export_quality is None:
            return PDFExportQualityType.DPI300

        # Si l'appelant fournit déjà l'enum .NET, on le conserve tel quel.
        try:
            if isinstance(export_quality, PDFExportQualityType):
                return export_quality
        except TypeError:
            pass

        quality_map = {
            72: PDFExportQualityType.DPI72,
            144: PDFExportQualityType.DPI144,
            300: PDFExportQualityType.DPI300,
            600: PDFExportQualityType.DPI600,
            1200: PDFExportQualityType.DPI1200,
            2400: PDFExportQualityType.DPI2400,
            3600: PDFExportQualityType.DPI3600,
            4000: PDFExportQualityType.DPI4000,
        }

        try:
            numeric_quality = int(export_quality)
        except (TypeError, ValueError):
            raise ValueError(
                "La qualité PDF doit être une résolution supportée "
                "(72, 144, 300, 600, 1200, 2400, 3600 ou 4000 DPI)."
            )

        if numeric_quality not in quality_map:
            raise ValueError(
                "Résolution PDF non supportée : {} DPI. "
                "Valeurs acceptées : 72, 144, 300, 600, 1200, 2400, "
                "3600 ou 4000 DPI.".format(numeric_quality)
            )

        return quality_map[numeric_quality]

    def export_combined(self, sheet_ids, output_directory, filename,
                        export_quality=300, settings=None, progress=None):
        """Exporte toutes les feuilles dans un PDF unique."""
        from Autodesk.Revit.DB import PDFExportOptions

        self._validate(sheet_ids, output_directory)
        if not filename:
            raise ValueError("Le nom du fichier PDF est manquant.")

        options = PDFExportOptions()
        options.Combine = True
        options.FileName = filename
        options.ExportQuality = self._to_export_quality(export_quality)
        apply_options(options, settings)

        with operation(progress, "pdf", "Export PDF Revit"):
            return self.document.Export(
                output_directory,
                list(sheet_ids),
                options
            )

    def export_named_separate(self, sheet_ids, output_directory, filenames,
                              export_quality=300, settings=None, progress=None):
        """Associe chaque PDF à son numéro de feuille, puis applique le modèle TAA."""
        self._validate(sheet_ids, output_directory)
        sheet_ids = list(sheet_ids)
        source_names = []
        for sheet_id in sheet_ids:
            sheet = self.document.GetElement(sheet_id)
            number = getattr(sheet, "SheetNumber", None)
            if not number:
                raise ValueError("PDF séparé : numéro de feuille indisponible.")
            source_names.append(FilenameService().sanitize("taa_" + number) + ".pdf")
        # Un numéro contenant * est autorisé dans Revit. La comparaison des
        # sorties natives doit rester unique même après nettoyage Windows.
        validate_names(source_names)
        validate_native_keys(source_names)

        def export_and_match(directory):
            success = self.export_separate(
                sheet_ids, directory, export_quality, use_sheet_numbers=True, settings=settings,
                **progress_kwargs(progress))
            if success:
                if progress is not None:
                    progress.begin("delivery", "Rapprochement et livraison des PDF")
                reconcile_native_pdfs(directory, source_names)
            return success

        try:
            paths = deliver_named_pdfs(
                output_directory, source_names, filenames, export_and_match)
        except Exception:
            if progress is not None:
                progress.end_if_started("delivery", "Échec de livraison — voir le rapport")
            raise
        if progress is not None:
            progress.end_if_started("delivery")
        return paths

    def export_separate(self, sheet_ids, output_directory,
                        export_quality=300, use_sheet_numbers=False, settings=None, progress=None):
        """Exporte chaque feuille dans son propre PDF.

        Le nom de chaque fichier est alors généré par Revit selon sa règle de
        nommage PDF active. ``FileName`` est volontairement laissé vide :
        l'API l'ignore lorsque Combine est faux.
        """
        from Autodesk.Revit.DB import PDFExportOptions

        self._validate(sheet_ids, output_directory)

        options = PDFExportOptions()
        options.Combine = False
        if use_sheet_numbers:
            from Autodesk.Revit.DB import (TableCellCombinedParameterData,
                                           BuiltInParameter, BuiltInCategory, ElementId)
            from System.Collections.Generic import List
            field = TableCellCombinedParameterData.Create()
            field.CategoryId = ElementId(BuiltInCategory.OST_Sheets)
            field.ParamId = ElementId(BuiltInParameter.SHEET_NUMBER)
            field.Prefix = "taa_"
            field.Suffix = ""
            field.Separator = ""
            rule = List[TableCellCombinedParameterData]()
            rule.Add(field)
            options.SetNamingRule(rule)
        options.ExportQuality = self._to_export_quality(export_quality)
        apply_options(options, settings)

        with operation(progress, "pdf", "Export PDF Revit"):
            return self.document.Export(
                output_directory,
                list(sheet_ids),
                options
            )

    def export(self, sheet_ids, output_directory, filename=None,
               combined=True, export_quality=300, settings=None, progress=None):
        """Point d'entrée compatible pour les deux modes PDF."""
        if combined:
            return self.export_combined(
                sheet_ids,
                output_directory,
                filename,
                export_quality, settings=settings, **progress_kwargs(progress)
            )

        return self.export_separate(
            sheet_ids,
            output_directory,
            export_quality, settings=settings, **progress_kwargs(progress)
        )
