# -*- coding: utf-8 -*-
"""Gestion des dossiers et noms de fichiers de publication."""

import os
import re


class OutputService(object):
    """Centralise la préparation des destinations de publication."""

    INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')

    def ensure_directory(self, path):
        if not path:
            raise ValueError("Le dossier de destination est manquant.")
        if not os.path.isdir(path):
            os.makedirs(path)
        return path

    def sanitize_name(self, name):
        value = (name or "").strip()
        value = self.INVALID_CHARS.sub("_", value)
        value = value.rstrip(". ")
        return value or "Sans_nom"

    def carnet_directory(self, root, carnet_name):
        return self.ensure_directory(
            os.path.join(root, self.sanitize_name(carnet_name))
        )

    def file_path(self, directory, filename, extension):
        base = self.sanitize_name(filename)
        ext = extension if extension.startswith(".") else "." + extension
        return os.path.join(directory, base + ext)
