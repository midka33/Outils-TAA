# -*- coding: utf-8 -*-
"""Résolution et sécurisation des noms de fichiers de publication."""

import os
import re
from datetime import datetime


class FilenameService(object):
    """Construit les noms de fichiers à partir d'un modèle Publisher TAA."""

    TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")
    INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')
    BUILTIN_TOKENS = (
        "carnet", "numero", "nom", "nom_complet", "projet",
        "date", "indice", "dossier"
    )

    def __init__(self, document=None, output_service=None):
        self.document = document
        self.output_service = output_service

    def available_tokens(self):
        """Retourne les variables intégrées affichables dans l'interface."""
        return list(self.BUILTIN_TOKENS)

    def validate_template(self, template):
        """Retourne les erreurs de syntaxe d'un modèle de nommage."""
        template = (template or "").strip()
        errors = []
        if not template:
            return ["Le modèle de nommage est vide."]
        if template.count("{") != template.count("}"):
            errors.append("Le modèle de nommage contient des accolades déséquilibrées.")
        for match in self.TOKEN_PATTERN.finditer(template):
            token = match.group(1).strip()
            if token in self.BUILTIN_TOKENS:
                continue
            if token.startswith("parametre:") and token[len("parametre:"):].strip():
                continue
            errors.append("Variable inconnue : {{{}}}.".format(token))
        return errors

    def _project_name(self):
        try:
            title = self.document.Title
            if title:
                return os.path.splitext(title)[0]
        except Exception:
            pass
        return "Projet"

    def _parameter_value(self, item, parameter_name):
        """Lit un paramètre de la feuille courante si possible."""
        if item is None or not parameter_name:
            return ""
        element = None
        try:
            if getattr(item, "unique_id", None) and self.document is not None:
                element = self.document.GetElement(item.unique_id)
        except Exception:
            element = None
        if element is None:
            return ""
        try:
            parameter = element.LookupParameter(parameter_name)
            if parameter is None:
                return ""
            if parameter.StorageType.ToString() == "String":
                return parameter.AsString() or ""
            value = parameter.AsValueString()
            return value or ""
        except Exception:
            return ""

    def build_context(self, publication_set, item=None, folder_name=None):
        """Construit le contexte de résolution d'un nom."""
        if item is None and publication_set is not None:
            items = publication_set.items or []
            item = items[0] if items else None
        carnet = getattr(publication_set, "name", "") or "Carnet"
        numero = getattr(item, "sheet_number", "") or ""
        nom = getattr(item, "sheet_name", "") or ""
        return {
            "carnet": carnet,
            "numero": numero,
            "nom": nom,
            "nom_complet": ("{0} — {1}".format(numero, nom)).strip(" —"),
            "projet": self._project_name(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "indice": "",
            "dossier": folder_name or ""
        }

    def resolve(self, template, publication_set, item=None, folder_name=None):
        """Résout les variables intégrées et les paramètres Revit."""
        template = (template or "{carnet}").strip()
        context = self.build_context(publication_set, item, folder_name)
        unknown = []

        def replace(match):
            token = match.group(1).strip()
            if token in context:
                return str(context[token] or "")
            if token.startswith("parametre:"):
                parameter_name = token[len("parametre:"):].strip()
                value = self._parameter_value(item or ((publication_set.items or [None])[0]),
                                              parameter_name)
                if not value:
                    unknown.append(token)
                return value
            unknown.append(token)
            return ""

        value = self.TOKEN_PATTERN.sub(replace, template)
        return self.sanitize(value), unknown

    def sanitize(self, name):
        """Sécurise un nom selon les contraintes de fichiers Windows."""
        value = (name or "").strip()
        value = self.INVALID_CHARS.sub("_", value)
        value = value.rstrip(". ")
        if value.upper() in ("CON", "PRN", "AUX", "NUL"):
            value = "_" + value
        if re.match(r"^(COM[1-9]|LPT[1-9])$", value.upper()):
            value = "_" + value
        return value or "Sans_nom"

    def filename(self, template, publication_set, item=None,
                 folder_name=None, extension=".pdf"):
        """Retourne le nom complet sécurisé avec extension."""
        base, unknown = self.resolve(template, publication_set, item, folder_name)
        ext = extension if extension.startswith(".") else "." + extension
        return base + ext, unknown
