# -*- coding: utf-8 -*-
"""Réglages normalisés d'une publication Export."""


class PublicationSettings(object):
    """Contient les réglages persistants d'exécution d'un carnet."""

    def __init__(self, output_directory=None, pdf_enabled=True,
                 pdf_mode="COMBINED", dwg_enabled=True,
                 dwg_mode="SEPARATE", dwg_setup_name=None,
                 dwg_true_color=True, filename_template="{carnet}"):
        self.output_directory = output_directory
        self.pdf_enabled = pdf_enabled
        self.pdf_mode = pdf_mode
        self.dwg_enabled = dwg_enabled
        self.dwg_mode = dwg_mode
        self.dwg_setup_name = dwg_setup_name
        self.dwg_true_color = dwg_true_color
        self.filename_template = filename_template

    def validate(self):
        errors = []
        if not self.output_directory:
            errors.append("Le dossier de destination est manquant.")
        if self.pdf_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode PDF est invalide.")
        if self.dwg_mode not in ("COMBINED", "SEPARATE"):
            errors.append("Le mode DWG est invalide.")
        return errors

    def to_dict(self):
        """Convertit les réglages en données JSON simples."""
        return {
            "output_directory": self.output_directory,
            "pdf_enabled": bool(self.pdf_enabled),
            "pdf_mode": self.pdf_mode,
            "dwg_enabled": bool(self.dwg_enabled),
            "dwg_mode": self.dwg_mode,
            "dwg_setup_name": self.dwg_setup_name,
            "dwg_true_color": bool(self.dwg_true_color),
            "filename_template": self.filename_template
        }

    @classmethod
    def from_dict(cls, value):
        value = value or {}
        return cls(
            output_directory=value.get("output_directory"),
            pdf_enabled=value.get("pdf_enabled", True),
            pdf_mode=value.get("pdf_mode", "COMBINED"),
            dwg_enabled=value.get("dwg_enabled", True),
            dwg_mode=value.get("dwg_mode", "SEPARATE"),
            dwg_setup_name=value.get("dwg_setup_name"),
            dwg_true_color=value.get("dwg_true_color", True),
            filename_template=value.get("filename_template", "{carnet}")
        )
