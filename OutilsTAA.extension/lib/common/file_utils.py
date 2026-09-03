# -*- coding: utf-8 -*-
"""Utilitaires de fichiers sans logique métier."""

import os


def ensure_directory(path):
    """Crée le dossier si nécessaire et retourne son chemin."""
    if not path:
        raise ValueError("Le chemin de destination est vide.")
    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def sanitize_filename(name):
    """Supprime les caractères interdits dans un nom de fichier Windows."""
    invalid = '<>:"/\\|?*'
    return "".join("_" if char in invalid else char for char in name).strip()
