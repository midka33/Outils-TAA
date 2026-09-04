# -*- coding: utf-8 -*-
"""Réglages normalisés d'une publication Export."""


class PublicationSettings(object):
    """Réglages d'un niveau de publication.

    Une valeur à None signifie « hériter ». Les réglages résolus sont des
    valeurs concrètes produits par SettingsResolver et ne sont jamais
    directement sérialisés comme hérités.
    """

    FIELDS = (
        "pdf_enabled", "pdf_mode", "dwg_enabled", "dwg_mode",
        "dwg_setup_name", "dwg_true_color", "output_directory",
        "filename_template", "modified_only"
    )

    def __init__(self, output_directory=None, pdf_enabled=None,
                 pdf_mode=None, dwg_enabled=None, dwg_mode=None,
                 dwg_setup_name=None, dwg_true_color=None,
                 filename_template=None, modified_only=None):
        self.output_directory = output_directory
        self.pdf_enabled = pdf_enabled
        self.pdf_mode = pdf_mode
        self.dwg_enabled = dwg_enabled
        self.dwg_mode = dwg_mode
        self.dwg_setup_name = dwg_setup_name
        self.dwg_true_color = dwg_true_color
        self.filename_template = filename_template
        self.modified_only = modified_only

    @classmethod
    def defaults(cls):
        return cls(output_directory=None, pdf_enabled=True,
                   pdf_mode="COMBINED", dwg_enabled=True,
                   dwg_mode="SEPARATE", dwg_setup_name=None,
                   dwg_true_color=True, filename_template="{carnet}",
                   modified_only=False)

    def copy(self):
        return self.__class__(**dict((field, getattr(self, field))
                                     for field in self.FIELDS))

    def validate(self):
        errors = []
        if self.output_directory is None or not self.output_directory:
            errors.append("Le dossier de destination est manquant.")
        if self.pdf_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode PDF est invalide.")
        if self.dwg_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode DWG est invalide.")
        if self.pdf_enabled is None or self.dwg_enabled is None:
            errors.append("Les réglages PDF/DWG n'ont pas été résolus.")
        if self.modified_only is None:
            errors.append("Le réglage des mises en page modifiées n'a pas été résolu.")
        return errors

    def to_dict(self):
        return dict((field, getattr(self, field)) for field in self.FIELDS)

    @classmethod
    def from_dict(cls, value):
        value = value or {}
        # Compatibilité avec les anciens carnets où les valeurs étaient
        # toujours explicites.
        return cls(
            output_directory=value.get("output_directory"),
            pdf_enabled=value.get("pdf_enabled", None),
            pdf_mode=value.get("pdf_mode", None),
            dwg_enabled=value.get("dwg_enabled", None),
            dwg_mode=value.get("dwg_mode", None),
            dwg_setup_name=value.get("dwg_setup_name", None),
            dwg_true_color=value.get("dwg_true_color", None),
            filename_template=value.get("filename_template", None),
            modified_only=value.get("modified_only", None)
        )
