# -*- coding: utf-8 -*-
"""Réglages normalisés d'une publication Export."""


class PublicationSettings(object):
    """Contient les réglages d'exécution d'un carnet."""

    def __init__(self, output_directory=None, pdf_enabled=True,
                 pdf_mode="COMBINED", dwg_enabled=True,
                 dwg_mode="SEPARATE", dwg_setup_name=None):
        self.output_directory = output_directory
        self.pdf_enabled = pdf_enabled
        self.pdf_mode = pdf_mode
        self.dwg_enabled = dwg_enabled
        self.dwg_mode = dwg_mode
        self.dwg_setup_name = dwg_setup_name

    def validate(self):
        errors = []
        if not self.output_directory:
            errors.append("Le dossier de destination est manquant.")
        if self.pdf_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode PDF est invalide.")
        if self.dwg_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode DWG est invalide.")
        return errors
