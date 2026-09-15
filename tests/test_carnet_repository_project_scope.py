# -*- coding: utf-8 -*-
"""Tests de non-régression de l'isolation des stockages Export par projet."""

import json
import os
import sys


SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                            "OutilsTAA.extension",
                                            "OutilsTAA.tab",
                                            "Export.panel", "services"))
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                           "OutilsTAA.extension",
                                           "OutilsTAA.tab",
                                           "Export.panel", "models"))
for path in (SERVICES_DIR, MODELS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

from carnet_repository import CarnetRepository
from publication_folder import PublicationFolder


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


def test_repository_persists_current_project_identity(tmpdir):
    path = str(tmpdir.join("project.json"))
    repository = CarnetRepository(path, project_identity="EMBEDDED:project-c")
    folder = PublicationFolder("DCE", "folder-dce", None, True, None)

    repository.save_folder(folder)

    with open(path, "r") as handle:
        data = json.load(handle)

    assert data["project_identity"] == "EMBEDDED:project-c"
