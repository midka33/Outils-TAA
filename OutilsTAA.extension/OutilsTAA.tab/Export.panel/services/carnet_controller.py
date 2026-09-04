# -*- coding: utf-8 -*-
"""Façade métier préparant les données consommées par l'interface WPF."""


class CarnetController(object):
    """Orchestre découverte, création, résolution et publication des carnets."""

    def __init__(self, export_service, carnet_service, parameter_service,
                 repository=None, publication_service=None):
        self.export_service = export_service
        self.carnet_service = carnet_service
        self.parameter_service = parameter_service
        self.repository = repository
        self.publication_service = publication_service
        self.document = getattr(export_service, "document", None)

    def get_context(self):
        sheets = self.export_service.get_sheets()
        return {"sheets": sheets, "sheet_count": len(sheets),
                "parameters": self.parameter_service.get_sheet_parameter_names(sheets)}

    def get_parameter_preview(self, parameter_name):
        sheets = self.export_service.get_sheets()
        summary = self.parameter_service.get_parameter_summary(sheets, parameter_name)
        return {"parameter_name": parameter_name, "sheet_count": len(sheets),
                "values": summary, "carnet_count": len(summary),
                "assigned_sheet_count": sum(item["count"] for item in summary)}

    def create_from_parameter(self, parameter_name, name_template=None):
        return self.carnet_service.create_from_parameter(parameter_name, name_template)

    def create_manual_persistent(self, name, items, output_directory=None,
                                 filename_template_id=None):
        publication_set = self.carnet_service.create_manual_persistent(
            name, items, output_directory, filename_template_id)
        return self.save_persistent(publication_set)

    def save_persistent(self, publication_set):
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        return self.repository.save(publication_set)

    def create_manual_temporary(self, name, items):
        return self.carnet_service.create_manual_temporary(name, items)

    def list_persistent(self):
        return self.repository.list_all() if self.repository else []

    def list_folders(self):
        return self.repository.list_folders() if self.repository else []

    def save_folder(self, folder):
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        return self.repository.save_folder(folder)

    def delete_folder(self, folder_id):
        if self.repository is None:
            return False
        return self.repository.delete_folder(folder_id)

    def move_persistent(self, set_id, folder_id, before_set_id=None):
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        return self.repository.move_set(set_id, folder_id, before_set_id)

    def move_persistent_many(self, set_ids, folder_id, before_set_id=None):
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        return self.repository.move_sets(set_ids, folder_id, before_set_id)

    def resolve_persistent(self, publication_set):
        if self.repository is None:
            raise RuntimeError("Le dépôt des carnets n'est pas configuré.")
        sheets = self.export_service.get_sheets()
        return self.carnet_service.resolve_persistent_carnet(publication_set, sheets)

    def publish(self, publication_set, output_directory, export_pdf=True,
                export_dwg=False, pdf_combined=True, dwg_combined=False,
                dwg_setup_name=None, dwg_true_color=True, items=None):
        """Publie un carnet, éventuellement limité aux mises en page candidates."""
        if self.publication_service is None:
            raise RuntimeError("Le service de publication n'est pas configuré.")
        return self.publication_service.publish(
            publication_set, output_directory, export_pdf=export_pdf,
            export_dwg=export_dwg, pdf_combined=pdf_combined,
            dwg_combined=dwg_combined, dwg_setup_name=dwg_setup_name,
            dwg_true_color=dwg_true_color, items=items)
