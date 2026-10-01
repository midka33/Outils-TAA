# -*- coding: utf-8 -*-
"""Chemins partagés par l'aperçu et les moteurs PDF/DWG."""
import os
import re
from filename_service import FilenameService


def safe_directory_name(name):
    """Sécurise un composant Windows, y compris les périphériques avec suffixe."""
    value = FilenameService().sanitize(name)
    value = re.sub(r"[\x00-\x1f]", "_", value)
    stem = value.split(".")[0].upper()
    if stem in ("CON", "PRN", "AUX", "NUL") or re.match(r"^(COM[1-9]|LPT[1-9])$", stem):
        value = "_" + value
    return value


def publication_directory(target, destination, combined, settings=None):
    """Décline la destination effective sans créer de dossier pendant l'aperçu.

    Les cibles de dossier portent leur chemin relatif. Le mode séparé ajoute
    le nom du carnet par défaut, sauf désactivation explicite de cette option.
    """
    parts = getattr(target, "publication_folder_parts", ())
    names = [safe_directory_name(part) for part in parts]
    settings = settings or getattr(target, "publication_settings", None)
    create_subfolder = getattr(settings, "separate_carnet_subfolder", None) is not False
    if not combined and create_subfolder:
        names.append(safe_directory_name(target.name))
    return os.path.join(destination, *names) if names else destination
