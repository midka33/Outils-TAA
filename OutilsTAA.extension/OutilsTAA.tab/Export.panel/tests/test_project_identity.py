# -*- coding: utf-8 -*-
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
SERVICES_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "services"))
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from project_identity import get_project_identity, project_key


class FakeProjectInfo(object):
    def __init__(self, unique_id):
        self.UniqueId = unique_id


class FakeDocument(object):
    def __init__(self, title, path_name="", unique_id="uid"):
        self.Title = title
        self.PathName = path_name
        self.ProjectInformation = FakeProjectInfo(unique_id)

    def GetWorksharingCentralModelPath(self):
        return None


def test_unsaved_projects_with_same_title_have_distinct_identities():
    first = FakeDocument("Projet1", unique_id="project-a")
    second = FakeDocument("Projet1", unique_id="project-b")

    assert get_project_identity(first) != get_project_identity(second)
    assert project_key(first) != project_key(second)


def test_saved_projects_use_path_identity():
    document = FakeDocument("Projet1", path_name=r"C:\Projet\A.rvt", unique_id="project-a")

    assert get_project_identity(document) == "FILE:C:\\Projet\\A.rvt"


def test_document_title_is_not_used_as_unsaved_identity():
    document = FakeDocument("Projet1", unique_id="project-a")

    identity = get_project_identity(document)

    assert identity.startswith("UNSAVED_PROJECT_INFO:")
    assert "Projet1" not in identity
