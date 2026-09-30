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


def publication_directory(target, destination, combined):
    """Décline la destination effective sans créer de dossier pendant l'aperçu.

    Seules les copies préparées pour une publication de dossier portent le chemin
    relatif. La publication directe d'une feuille ou d'un carnet reste inchangée.
    """
    parts = getattr(target, "publication_folder_parts", None)
    if parts is None:
        return destination
    names = [safe_directory_name(part) for part in parts]
    if not combined:
        names.append(safe_directory_name(target.name))
    return os.path.join(destination, *names)
