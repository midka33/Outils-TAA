# -*- coding: utf-8 -*-
"""Résolution et sécurisation des noms de fichiers de publication."""
from __future__ import unicode_literals

import os
import re
from datetime import datetime
from naming_parameters import NamingParameters, NamingVariable, text_type


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
        self.parameters = NamingParameters(document)

    def available_tokens(self):
        """Retourne les variables intégrées affichables dans l'interface."""
        return list(self.BUILTIN_TOKENS)

    def variable_catalogue(self, sheets):
        """Variables intégrées et paramètres du document pour le sélecteur."""
        return [NamingVariable("Variable — {0}".format(token), "{{{0}}}".format(token))
                for token in self.BUILTIN_TOKENS] + self.parameters.catalogue(sheets)

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
            scope, separator, selector = token.partition(":")
            if scope in NamingParameters.SCOPES and separator and selector.strip():
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
                return text_type(context[token] or "")
            scope, separator, selector = token.partition(":")
            if scope in NamingParameters.SCOPES and separator:
                items = getattr(publication_set, "items", None) or [None]
                value = self.parameters.read(scope, selector.strip(), item or items[0])
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
