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
    SHEET_TOKENS = ("numero", "nom", "nom_complet", "indice")

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

    def resolve_carnet(self, template, publication_set, folder_name=None):
        """Résout un nom de livrable global sans prendre la première feuille.

        Les variables propres à une feuille ne sont pas déterministes pour un
        PDF combiné. Si le modèle en contient, la première variable de feuille
        est remplacée par le nom du carnet et les suivantes sont supprimées.
        Les variables projet/date/dossier restent résolues normalement.
        """
        template = (template or "{carnet}").strip()
        already_has_carnet = "{carnet}" in template
        inserted_carnet = already_has_carnet

        def replace_sheet_token(match):
            token = match.group(1).strip()
            scope, separator, selector = token.partition(":")

            is_sheet_token = token in self.SHEET_TOKENS
            is_sheet_parameter = (
                scope in NamingParameters.SCOPES
                and not scope.startswith("info_projet")
            )
            if not is_sheet_token and not is_sheet_parameter:
                return match.group(0)

            if not inserted_state[0]:
                inserted_state[0] = True
                return "{carnet}"
            return ""

        # Listes utilisées au lieu de nonlocal pour compatibilité IronPython 2.
        inserted_state = [inserted_carnet]
        collection_template = self.TOKEN_PATTERN.sub(
            replace_sheet_token,
            template,
        )

        value, unknown = self.resolve(
            collection_template,
            publication_set,
            item=None,
            folder_name=folder_name,
        )

        # Une suppression de variable de feuille peut laisser un séparateur
        # final issu du modèle, par exemple "..._{numero}_{nom}".
        value = re.sub(r"[_\-\s]+$", "", value).strip()
        return self.sanitize(value), unknown

    def carnet_filename(self, template, publication_set,
                        folder_name=None, extension=".pdf"):
        """Nom d'un livrable de carnet (PDF combiné, préfixe global...)."""
        base, unknown = self.resolve_carnet(
            template,
            publication_set,
            folder_name=folder_name,
        )
        ext = extension if extension.startswith(".") else "." + extension
        return base + ext, unknown

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
