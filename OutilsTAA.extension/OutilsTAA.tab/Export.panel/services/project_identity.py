# -*- coding: utf-8 -*-
"""Identité et stockage isolé des projets Revit pour Export."""

import hashlib
import os


def get_project_identity(document):
    """Retourne une identité de stockage adaptée à l'état du document.

    Un document enregistré utilise son chemin (ou le chemin du central), donc
    son identité peut être conservée entre les sessions Revit.

    Un document non enregistré ne possède pas de chemin persistant fiable.
    Revit fournit cependant un hash propre à l'instance du Document ouverte ou
    créée dans la session courante. Ce hash est volontairement utilisé comme
    identité de session : il évite que deux nouveaux projets « Projet1 »
    partagent la même persistance. Il n'est pas supposé survivre à une
    fermeture/réouverture de Revit.
    """
    if document is None:
        return "UNKNOWN:DOCUMENT"

    try:
        from Autodesk.Revit.DB import ModelPathUtils
        central_path = document.GetWorksharingCentralModelPath()
        if central_path:
            visible_path = ModelPathUtils.ConvertModelPathToUserVisiblePath(central_path)
            if visible_path:
                return "CENTRAL:" + visible_path
    except Exception:
        pass

    try:
        path_name = document.PathName
        if path_name:
            return "FILE:" + path_name
    except Exception:
        pass

    # Pour un document non enregistré, Document.GetHashCode() est généré
    # pour l'instance ouverte/créée dans la session Revit. Autodesk précise
    # qu'il n'est pas identique lorsque le même fichier est rouvert dans une
    # autre session ; c'est exactement le comportement recherché ici.
    try:
        document_hash = document.GetHashCode()
        return "UNSAVED_DOCUMENT:" + str(document_hash)
    except Exception:
        pass

    # Dernier recours : ne jamais retomber sur une valeur commune comme
    # « Projet1 », afin d'éviter toute collision de persistance.
    return "UNSAVED_INSTANCE:" + str(id(document))


def project_key(document):
    return hashlib.sha1(get_project_identity(document).encode("utf-8")).hexdigest()
