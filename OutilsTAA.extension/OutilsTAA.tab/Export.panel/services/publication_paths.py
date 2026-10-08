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

    combined est conservé uniquement pour compatibilité avec les appels
    historiques. Il n'influence plus la création du dossier du carnet.

    Si separate_carnet_subfolder est actif, la structure est toujours :

        <destination>/<dossiers publication>/<carnet>/<PDF|DWG>/

    Le comportement est identique pour PDF combiné/séparé et pour la stratégie
    DWG interne. Lorsque l'option est désactivée, les fichiers restent directement
    dans la destination issue de l'arborescence de publication.
    """
    parts = getattr(target, "publication_folder_parts", ())
    names = [safe_directory_name(part) for part in parts]
    settings = settings or getattr(target, "publication_settings", None)
    create_subfolder = (
        getattr(settings, "separate_carnet_subfolder", None) is not False
    )

    if create_subfolder:
        names.append(safe_directory_name(target.name))
        if format_name:
            names.append(safe_directory_name(str(format_name).upper()))

    return os.path.join(destination, *names) if names else destination
