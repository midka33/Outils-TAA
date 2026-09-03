"""Façade métier préparant les données consommées par l'interface WPF."""


class CarnetController(object):
    """Orchestre découverte, création, résolution et persistance des carnets."""

    def __init__(self, export_service, carnet_service, parameter_service,
                 repository=None):
        self.export_service = export_service
        self.carnet_service = carnet_service
        self.parameter_service = parameter_service
        self.repository = repository

    def get_context(self):
        """Retourne le contexte initial nécessaire à l'écran WPF."""
        sheets = self.export_service.get_sheets()
        return {
            "sheets": sheets,
            "sheet_count": len(sheets),
            "parameters": self.parameter_service.get_sheet_parameter_names(sheets)
        }

    def get_parameter_preview(self, parameter_name):
        """Retourne les valeurs et effectifs pour l'aperçu WPF."""
        sheets = self.export_service.get_sheets()
        summary = self.parameter_service.get_parameter_summary(
            sheets,
            parameter_name
        )
        return {
            "parameter_name": parameter_name,
            "sheet_count": len(sheets),
            "values": summary,
            "carnet_count": len(summary),
            "assigned_sheet_count": sum(item["count"] for item in summary)
        }

    def create_from_parameter(self, parameter_name, name_template=None):
        """Crée les carnets automatiques à partir d'un paramètre."""
        return self.carnet_service.create_from_parameter(
            parameter_name,
            name_template
        )

    def create_manual_persistent(self, name, items, output_directory=None,
                                 filename_template_id=None):
        """Crée puis enregistre un carnet manuel persistant."""
        publication_set = self.carnet_service.create_manual_persistent(
            name,
            items,
            output_directory,
            filename_template_id
        )
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        return self.repository.save(publication_set)

    def create_manual_temporary(self, name, items):
        """Crée un carnet manuel temporaire pour la session courante."""
        return self.carnet_service.create_manual_temporary(name, items)

    def list_persistent(self):
        """Retourne les carnets enregistrés."""
        if self.repository is None:
            return []
        return self.repository.list_all()

    def resolve_persistent(self, publication_set):
        """Résout un carnet enregistré dans le document Revit courant."""
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")

        sheets = self.export_service.get_sheets()
        return self.carnet_service.resolve_persistent_carnet(
            publication_set,
            sheets
        )
