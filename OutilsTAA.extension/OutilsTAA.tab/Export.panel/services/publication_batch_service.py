# -*- coding: utf-8 -*-
"""Orchestrateur de publication de plusieurs carnets pour Export."""


class PublicationBatchService(object):
    """Exécute plusieurs carnets avec une résolution indépendante des réglages."""

    def __init__(self, publication_service):
        self.publication_service = publication_service

    def publish(self, targets, settings_resolver, folder_resolver):
        """Publie une liste de carnets et agrège le rapport final."""
        results = []
        errors = []
        warnings = []
        all_success = True
        output_directories = []

        for target in targets or []:
            folder = folder_resolver(target)
            settings = settings_resolver(target, folder=folder)
            validation_errors = settings.validate()
            if validation_errors:
                errors.extend([
                    "{0} : {1}".format(target.name, error)
                    for error in validation_errors
                ])
                all_success = False
                continue

            if settings.output_directory and settings.output_directory not in output_directories:
                output_directories.append(settings.output_directory)

            try:
                result = self.publication_service.publish(
                    target,
                    settings.output_directory,
                    export_pdf=settings.pdf_enabled,
                    export_dwg=settings.dwg_enabled,
                    pdf_combined=settings.pdf_mode == "COMBINED",
                    dwg_combined=settings.dwg_mode == "COMBINED",
                    dwg_setup_name=settings.dwg_setup_name,
                    dwg_true_color=settings.dwg_true_color
                )
            except Exception as exc:
                result = {
                    "success": False,
                    "results": [],
                    "errors": [str(exc)],
                    "warnings": []
                }

            for item_result in result.get("results", []):
                row = dict(item_result)
                row["carnet"] = target.name
                results.append(row)

            errors.extend([
                "{0} : {1}".format(target.name, error)
                for error in result.get("errors", [])
            ])
            warnings.extend([
                "{0} : {1}".format(target.name, warning)
                for warning in result.get("warnings", [])
            ])
            all_success = all_success and bool(result.get("success"))

        return {
            "success": bool(targets) and all_success and not errors,
            "results": results,
            "errors": errors,
            "warnings": warnings,
            "output_directories": output_directories
        }
