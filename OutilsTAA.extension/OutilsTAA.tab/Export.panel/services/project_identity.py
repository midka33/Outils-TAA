# -*- coding: utf-8 -*-
"""Identité persistante des projets Revit pour le module Export."""

import hashlib


SCHEMA_GUID = "8cef85dd-7891-4715-942b-4667df6f17e4"
# Revit 2025 rejects dotted schema names for Extensible Storage.
# Keep this as a simple identifier; the GUID remains the schema identity.
SCHEMA_NAME = "OutilsTAA_Export_ProjectIdentity"
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


def _get_document_path(document):
    try:
        return document.PathName or ""
    except Exception:
        return ""


def _get_document_hash(document):
    try:
        return str(document.GetHashCode())
    except Exception:
        return None


def _read_embedded_storage(document):
    """Retourne le DataStorage portant l'identité Outils TAA, s'il existe."""
    if document is None:
        return None
    try:
        schema = _lookup_schema()
        if schema is None:
            return None
        from Autodesk.Revit.DB.ExtensibleStorage import DataStorage
        from Autodesk.Revit.DB import FilteredElementCollector
        for storage in FilteredElementCollector(document).OfClass(DataStorage):
            entity = storage.GetEntity(schema)
            if entity is not None and entity.IsValid():
                return storage
    except Exception:
        return None
    return None


def _read_embedded_identity(document):
    """Lit uniquement une identité réellement embarquée dans le document."""
    try:
        storage = _read_embedded_storage(document)
        if storage is None:
            return None
        schema = _lookup_schema()
        field = schema.GetField(FIELD_NAME)
        entity = storage.GetEntity(schema)
        value = entity.Get(field)
        return str(value) if value else None
    except Exception:
        return None


def _is_embedded_identity_valid_for_document(document, embedded):
    """Évite qu'une identité héritée d'un gabarit soit réutilisée par un nouveau document non enregistré.

    Les documents non enregistrés sont identifiés pendant la session par leur
    hash Document. L'identité embarquée contient alors ``GUID|hash``. Une
    identité héritée d'un gabarit possède soit un autre hash, soit l'ancien
    format GUID seul : elle doit être remplacée.
    """
    if not embedded:
        return False
    if _get_document_path(document):
        return True
    document_hash = _get_document_hash(document)
    if document_hash is None:
        return False
    parts = embedded.split("|", 1)
    return len(parts) == 2 and parts[1] == document_hash


def _embedded_identity_value(project_id, document):
    document_hash = _get_document_hash(document)
    if not _get_document_path(document) and document_hash is not None:
        return project_id + "|" + document_hash
    return project_id


def get_project_identity(document):
    """Retourne l'identité du projet pour calculer le stockage Export."""
    if document is None:
        return "UNKNOWN:DOCUMENT"

    embedded = _read_embedded_identity(document)
    if embedded and _is_embedded_identity_valid_for_document(document, embedded):
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

    path_name = _get_document_path(document)
    if path_name:
        return "FILE:" + path_name

    document_hash = _get_document_hash(document)
    if document_hash is not None:
        return "UNSAVED_DOCUMENT:" + document_hash
    return "UNSAVED_INSTANCE:" + str(id(document))


def ensure_project_identity(document):
    """Crée ou corrige l'identité Outils TAA embarquée dans le document."""
    if document is None:
        raise ValueError("Le document Revit est obligatoire.")

    existing = _read_embedded_identity(document)
    if existing and _is_embedded_identity_valid_for_document(document, existing):
        return existing

    from System import Guid
    from Autodesk.Revit.DB import Transaction
    from Autodesk.Revit.DB.ExtensibleStorage import DataStorage, Entity

    project_id = _embedded_identity_value(str(Guid.NewGuid()), document)
    schema = _get_schema()
    field = schema.GetField(FIELD_NAME)

    transaction = Transaction(document, "Outils TAA - Identité projet")
    transaction.Start()
    try:
        storage = _read_embedded_storage(document)
        if storage is None:
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
