# -*- coding: utf-8 -*-
"""Version centrale de la suite Outils TAA, lisible depuis tout module pyRevit.

La copie de développement se distingue de la dernière release publiée :
le manifeste sera mis à jour explicitement lors de chaque release stable.
"""
import codecs
import json
import os

try:
    _string_type = basestring  # IronPython 2.7
except NameError:
    _string_type = str  # CPython 3


def manifest_path():
    """L'extension peut être installée dans tout répertoire (y compris réseau)."""
    extension_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", ".."))
    return os.path.join(extension_dir, "version.json")


def read_version(path=None):
    """Retourne un manifeste valide, ou un état 'indisponible' explicite.

    Ne dépend ni de Git ni d'un accès réseau, et ne modifie aucun fichier.
    """
    source = path or manifest_path()
    try:
        with codecs.open(source, "r", "utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError("Le manifeste doit être un objet JSON.")
        number = data.get("version")
        channel = data.get("channel")
        last_published = data.get("last_published")
        if (not isinstance(number, _string_type) or not number.strip()
                or channel not in ("stable", "development")
                or not isinstance(last_published, _string_type)
                or not last_published.strip()):
            raise ValueError("Métadonnées de version invalides.")
        return {
            "version": number.strip(),
            "channel": channel,
            "last_published": last_published.strip(),
            "available": True,
        }
    except (IOError, OSError, ValueError, TypeError):
        return {
            "version": "indisponible",
            "channel": "unknown",
            "last_published": "indisponible",
            "available": False,
        }


def display_version(info):
    number = info.get("version", "indisponible")
    if info.get("channel") == "development":
        return "{} (développement)".format(number)
    return number


def display_release(info):
    return "Dernière version publiée : v{}".format(
        info.get("last_published", "indisponible"))


def display_status(info):
    if not info.get("available"):
        return "Informations de version introuvables ou illisibles."
    if info.get("channel") == "development":
        return ("Cette copie inclut des modifications non publiées "
                "depuis la version stable.")
    return "Version stable publiée."
