# -*- coding: utf-8 -*-
"""Réglages normalisés d'une publication Export."""


from pdf_options import PDF_OPTION_FIELDS, defaults as pdf_defaults


class PublicationSettings(object):
    """Réglages d'un niveau de publication.

    Une valeur à None signifie « hériter ». Les réglages résolus sont des
    valeurs concrètes produits par SettingsResolver et ne sont jamais
    directement sérialisés comme hérités.
    """

    FIELDS = (
        "pdf_enabled", "pdf_mode", "pdf_quality", "dwg_enabled", "dwg_mode",
        "dwg_setup_name", "dwg_true_color", "output_directory",
        "filename_template", "separate_carnet_subfolder"
    ) + PDF_OPTION_FIELDS

    PDF_QUALITIES = (72, 144, 300, 600, 1200, 2400, 3600, 4000)

    def __init__(self, output_directory=None, pdf_enabled=None,
                 pdf_mode=None, dwg_enabled=None, dwg_mode=None,
                 dwg_setup_name=None, dwg_true_color=None,
                 filename_template=None, modified_only=None, pdf_quality=None,
                 separate_carnet_subfolder=None, **pdf_options):
        unknown = set(pdf_options) - set(PDF_OPTION_FIELDS)
        if unknown:
            raise TypeError("Réglage PDF inconnu : " + ", ".join(sorted(unknown)))
        for field in PDF_OPTION_FIELDS:
            setattr(self, field, pdf_options.get(field))
        self.separate_carnet_subfolder = separate_carnet_subfolder
        self.output_directory = output_directory
        self.pdf_enabled = pdf_enabled
        self.pdf_mode = pdf_mode
        self.pdf_quality = pdf_quality
        self.dwg_enabled = dwg_enabled
        self.dwg_mode = dwg_mode
        self.dwg_setup_name = dwg_setup_name
        self.dwg_true_color = dwg_true_color
        self.filename_template = filename_template
        # Le paramètre historique est accepté mais ignoré en V1.

    @property
    def modified_only(self):
        """Compatibilité Stage 07 : aucun filtrage historique en V1."""
        return False

    @classmethod
    def defaults(cls):
        return cls(output_directory=None, pdf_enabled=True,
                   pdf_mode="COMBINED", dwg_enabled=True,
                   dwg_mode="SEPARATE", dwg_setup_name=None,
                   dwg_true_color=True, filename_template="{carnet}",
                   modified_only=False, pdf_quality=300,
                   separate_carnet_subfolder=True, **pdf_defaults())

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
        if self.pdf_enabled and self.pdf_quality not in self.PDF_QUALITIES:
            errors.append("La qualité PDF est invalide.")
        return errors

    def to_dict(self):
        return dict((field, getattr(self, field)) for field in self.FIELDS)

    @classmethod
    def from_dict(cls, value):
        value = value or {}
        return cls(**dict((field, value.get(field)) for field in cls.FIELDS))
