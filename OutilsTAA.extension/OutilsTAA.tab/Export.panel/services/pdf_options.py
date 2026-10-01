# -*- coding: utf-8 -*-
"""Contrat des options PDF natives ; aucune dépendance WPF."""

# champ persistant, propriété API, valeur par défaut TAA, libellé utilisateur
PDF_OPTIONS = (
    ("pdf_links_blue", "ViewLinksInBlue", False, "Afficher les liens en bleu (impression couleur)"),
    ("pdf_hide_reference_planes", "HideReferencePlane", True, "Masquer les plans de réf/construction"),
    ("pdf_hide_unreferenced_tags", "HideUnreferencedViewTags", False, "Masquer les étiquettes de vues non référencées"),
    ("pdf_mask_coincident_lines", "MaskCoincidentLines", False, "Les bords de la zone masquent les lignes coïncidentes"),
    ("pdf_hide_scope_boxes", "HideScopeBoxes", True, "Masquer les zones de définition"),
    ("pdf_hide_crop_boundaries", "HideCropBoundaries", True, "Masquer les limites de cadrage"),
    ("pdf_halftone_thin", "ReplaceHalftoneWithThinLines", False, "Remplacer la demi-teinte par des lignes fines"),
    ("pdf_raster", "AlwaysUseRaster", False, "Traitement raster"),
)
PDF_OPTION_FIELDS = tuple(row[0] for row in PDF_OPTIONS)


def defaults():
    return dict((field, value) for field, prop, value, label in PDF_OPTIONS)


def capabilities():
    """Vérifie les membres sur la véritable API chargée par Revit 2025.4."""
    from Autodesk.Revit.DB import PDFExportOptions
    options = PDFExportOptions()
    try:
        return dict((field, hasattr(options, prop)) for field, prop, value, label in PDF_OPTIONS)
    finally:
        options.Dispose()


def apply_options(options, settings):
    """Applique uniquement des propriétés publiques ; export synchrone en V1."""
    if settings is not None:
        for field, prop, default, label in PDF_OPTIONS:
            value = getattr(settings, field, None)
            if value is None:
                continue
            if not hasattr(options, prop):
                if value == default:
                    continue
                raise ValueError("Option PDF indisponible dans cette API : " + label)
            setattr(options, prop, bool(value))
    # La livraison sécurisée doit attendre la fin effective de Document.Export.
    if hasattr(options, "SetExportInBackground"):
        options.SetExportInBackground(False)


def changed_options(initial, current):
    """N'enregistre pas les valeurs héritées restées inchangées dans le dialogue."""
    return dict((field, current[field]) for field in PDF_OPTION_FIELDS
                if field in current and current[field] != initial[field])
