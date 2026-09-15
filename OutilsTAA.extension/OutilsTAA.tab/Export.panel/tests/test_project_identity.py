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
    def __init__(self, title, path_name="", unique_id="uid", document_hash=None):
        self.Title = title
        self.PathName = path_name
        self.ProjectInformation = FakeProjectInfo(unique_id)
        self.document_hash = document_hash

    def GetWorksharingCentralModelPath(self):
        return None

    def GetHashCode(self):
        return self.document_hash


def test_unsaved_projects_with_same_title_have_distinct_identities():
    first = FakeDocument("Projet1", unique_id="same-project-info", document_hash=101)
    second = FakeDocument("Projet1", unique_id="same-project-info", document_hash=202)

    assert get_project_identity(first) != get_project_identity(second)
    assert project_key(first) != project_key(second)


def test_unsaved_identity_does_not_use_project_information_unique_id():
    first = FakeDocument("Projet1", unique_id="same-project-info", document_hash=101)
    second = FakeDocument("Projet2", unique_id="same-project-info", document_hash=202)

    assert get_project_identity(first) == "UNSAVED_DOCUMENT:101"
    assert get_project_identity(second) == "UNSAVED_DOCUMENT:202"


def test_saved_projects_use_path_identity():
    document = FakeDocument("Projet1", path_name=r"C:\Projet\A.rvt", unique_id="project-a", document_hash=101)

    assert get_project_identity(document) == "FILE:C:\\Projet\\A.rvt"


def test_document_title_is_not_used_as_unsaved_identity():
    document = FakeDocument("Projet1", unique_id="project-a", document_hash=101)

    identity = get_project_identity(document)

    assert identity == "UNSAVED_DOCUMENT:101"
    assert "Projet1" not in identity
