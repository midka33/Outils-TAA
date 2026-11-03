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


def publication_directory(target, destination, combined=None, settings=None,
                          format_name=None):
    """Retourne la destination effective sans créer de dossier pendant l'aperçu.

    Deux réglages indépendants :
    - separate_carnet_subfolder : ajoute le nom du dossier publié ;
    - separate_format_subfolders : ajoute PDF ou DWG.

    Un ancien profil/une ancienne publication ne contient pas le second champ.
    Dans ce cas (None), les chemins historiques sont strictement conservés :
    les sous-dossiers PDF/DWG n'existaient que si le dossier publié était créé.

    combined est un argument historique ignoré : la fusion PDF ne modifie
    jamais la structure des répertoires.
    """
    parts = getattr(target, "publication_folder_parts", ())
    names = [safe_directory_name(part) for part in parts]
    settings = settings or getattr(target, "publication_settings", None)
    create_subfolder = (
        getattr(settings, "separate_carnet_subfolder", None) is not False
    )

    if create_subfolder:
        names.append(safe_directory_name(target.name))

    create_format_subfolder = getattr(
        settings, "separate_format_subfolders", None)
    if create_format_subfolder is None:
        # Profil/dossier avant la séparation des deux options.
        create_format_subfolder = create_subfolder
    if create_format_subfolder and format_name:
        names.append(safe_directory_name(str(format_name).upper()))

    return os.path.join(destination, *names) if names else destination
