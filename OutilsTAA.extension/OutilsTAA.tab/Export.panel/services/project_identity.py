# -*- coding: utf-8 -*-
"""Identité et stockage isolé des projets Revit pour Export."""

import hashlib
import os


def get_project_identity(document):
    """Retourne une identité stable sans utiliser Document.Title pour un projet non enregistré."""
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
    try:
        project_info = document.ProjectInformation
        project_uid = getattr(project_info, "UniqueId", None)
        if project_uid:
            return "UNSAVED_PROJECT_INFO:" + str(project_uid)
    except Exception:
        pass
    return "UNSAVED:DOCUMENT"


def project_key(document):
    return hashlib.sha1(get_project_identity(document).encode("utf-8")).hexdigest()
