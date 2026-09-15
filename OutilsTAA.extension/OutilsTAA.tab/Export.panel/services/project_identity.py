# -*- coding: utf-8 -*-
"""Identité persistante des projets Revit pour le module Export."""

import hashlib


SCHEMA_GUID = "8cef85dd-7891-4715-942b-4667df6f17e4"
SCHEMA_NAME = "OutilsTAA.Export.ProjectIdentity"
FIELD_NAME = "ProjectId"


def _lookup_schema():
    from System import Guid
    from Autodesk.Revit.DB.ExtensibleStorage import Schema
    return Schema.Lookup(Guid(SCHEMA_GUID))


def _get_schema():
    from System import Guid, String
    from Autodesk.Revit.DB.ExtensibleStorage import SchemaBuilder

    schema = _lookup_schema()
    if schema is not None:
        return schema

    builder = SchemaBuilder(Guid(SCHEMA_GUID))
    builder.SetSchemaName(SCHEMA_NAME)
    builder.AddSimpleField(FIELD_NAME, String)
    return builder.Finish()


def _read_embedded_identity(document):
    """Lit uniquement une identité réellement embarquée dans le document."""
    if document is None:
        return None
    try:
        schema = _lookup_schema()
        if schema is None:
            return None
        field = schema.GetField(FIELD_NAME)
        from Autodesk.Revit.DB import DataStorage, FilteredElementCollector
        for storage in FilteredElementCollector(document).OfClass(DataStorage):
            entity = storage.GetEntity(schema)
            if entity is None or not entity.IsValid():
                continue
            value = entity.Get(field)
            if value:
                return str(value)
    except Exception:
        return None
    return None


def get_project_identity(document):
    """Retourne l'identité du projet pour calculer le stockage Export.

    Une identité embarquée est prioritaire et constitue la seule identité
    durable. Les chemins et le hash ne servent que de repli avant que le GUID
    Outils TAA ait été créé dans un document.
    """
    if document is None:
        return "UNKNOWN:DOCUMENT"

    embedded = _read_embedded_identity(document)
    if embedded:
        return "EMBEDDED:" + embedded

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
        return "UNSAVED_DOCUMENT:" + str(document.GetHashCode())
    except Exception:
        return "UNSAVED_INSTANCE:" + str(id(document))


def ensure_project_identity(document):
    """Crée et enregistre un GUID Outils TAA dans le document si nécessaire."""
    if document is None:
        raise ValueError("Le document Revit est obligatoire.")

    existing = _read_embedded_identity(document)
    if existing:
        return existing

    from System import Guid
    from Autodesk.Revit.DB import DataStorage, Transaction
    from Autodesk.Revit.DB.ExtensibleStorage import Entity

    project_id = str(Guid.NewGuid())
    schema = _get_schema()
    field = schema.GetField(FIELD_NAME)

    transaction = Transaction(document, "Outils TAA - Identité projet")
    transaction.Start()
    try:
        storage = DataStorage.Create(document)
        entity = Entity(schema)
        entity.Set(field, project_id)
        storage.SetEntity(entity)
        transaction.Commit()
    except Exception:
        try:
            transaction.RollBack()
        except Exception:
            pass
        raise

    return project_id


def project_key(document):
    return hashlib.sha1(get_project_identity(document).encode("utf-8")).hexdigest()
