"""Service d'accès aux feuilles Revit pour le module Export."""

from publication_item import PublicationItem


class ExportService(object):
    """Prépare les éléments Revit destinés à la publication."""

    def __init__(self, document, parameter_utils):
        self.document = document
        self.parameter_utils = parameter_utils

    def get_sheets(self):
        """Retourne les feuilles du document actif."""
        if self.document is None:
            raise ValueError("Document Revit manquant.")

        try:
            from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet
        except ImportError:
            raise RuntimeError("L'API Revit n'est pas disponible.")

        return list(
            FilteredElementCollector(self.document)
            .OfClass(ViewSheet)
            .ToElements()
        )

    def build_publication_items(self, sheets, parameter_name=None,
                                parameter_value=None):
        """Transforme les feuilles sélectionnées en modèles de publication."""
        items = []

        for sheet in sheets or []:
            if sheet is None:
                continue

            value = None
            if parameter_name:
                value = self.parameter_utils.get_parameter_value(
                    sheet,
                    parameter_name,
                    None
                )

            if parameter_value is not None and value != parameter_value:
                continue

            items.append(
                PublicationItem(
                    sheet.UniqueId,
                    sheet.Id.IntegerValue,
                    "SHEET",
                    sheet.SheetNumber,
                    sheet.Name,
                    value
                )
            )

        return items

    def get_publication_items(self, parameter_name=None,
                              parameter_value=None):
        """Retourne les éléments publiables du document selon un filtre optionnel."""
        sheets = self.get_sheets()
        return self.build_publication_items(
            sheets,
            parameter_name,
            parameter_value
        )
