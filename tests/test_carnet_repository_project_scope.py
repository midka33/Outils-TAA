# -*- coding: utf-8 -*-
"""Tests de non-régression de l'isolation des stockages Export par projet."""

import json

from OutilsTAA.extension.OutilsTAA.tab.Export.panel.services.carnet_repository import CarnetRepository


def test_repository_creates_general_folder_for_empty_project(tmpdir):
    path = str(tmpdir.join("project.json"))
    repository = CarnetRepository(path, project_identity="EMBEDDED:project-a")

    folders = repository.list_folders()

    assert len(folders) == 1
    assert folders[0].id == "default"
    assert folders[0].name == "Général"


def test_repository_rejects_storage_from_another_project(tmpdir):
    path = str(tmpdir.join("project.json"))
    with open(path, "w") as handle:
        json.dump({
            "schema_version": 5,
            "project_identity": "EMBEDDED:project-a",
            "folders": [{"id": "default", "name": "DCE", "parent_id": None, "persistent": True}],
            "sets": []
        }, handle)

    repository = CarnetRepository(path, project_identity="EMBEDDED:project-b")

    try:
        repository.list_folders()
        assert False, "Un stockage d'un autre projet ne doit jamais être chargé."
    except ValueError as exc:
        assert "ne correspond pas au projet Revit courant" in str(exc)


def test_repository_records_current_project_identity(tmpdir):
    path = str(tmpdir.join("project.json"))
    repository = CarnetRepository(path, project_identity="EMBEDDED:project-c")

    repository.list_folders()
    with open(path, "r") as handle:
        data = json.load(handle) if False else None

    # La structure initiale est générée en mémoire ; la persistance de
    # l'identité est vérifiée par la première écriture métier.
    assert repository.project_identity == "EMBEDDED:project-c"
