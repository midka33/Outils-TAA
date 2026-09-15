# -*- coding: utf-8 -*-
"""Tests de non-régression de l'identité de stockage Export."""

import os
import sys


SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..",
                                            "OutilsTAA.extension",
                                            "OutilsTAA.tab",
                                            "Export.panel", "services"))
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from project_identity import get_project_identity, project_key


class FakeUnsavedDocument(object):
    def __init__(self, document_hash):
        self._document_hash = document_hash
        self.PathName = ""

    def GetWorksharingCentralModelPath(self):
        return None

    def GetHashCode(self):
        return self._document_hash


class FakeSavedDocument(FakeUnsavedDocument):
    def __init__(self, path, document_hash=1):
        FakeUnsavedDocument.__init__(self, document_hash)
        self.PathName = path


def test_two_unsaved_documents_have_distinct_project_keys():
    first = FakeUnsavedDocument(101)
    second = FakeUnsavedDocument(202)

    assert get_project_identity(first) != get_project_identity(second)
    assert project_key(first) != project_key(second)


def test_unsaved_identity_does_not_use_project_title():
    document = FakeUnsavedDocument(303)

    identity = get_project_identity(document)

    assert "Projet1" not in identity
    assert identity.startswith("UNSAVED_DOCUMENT:")


def test_saved_document_uses_file_path_identity():
    document = FakeSavedDocument(r"C:\Projets\MonProjet.rvt", document_hash=999)

    identity = get_project_identity(document)

    assert identity == r"FILE:C:\Projets\MonProjet.rvt"
    assert project_key(document) != project_key(FakeUnsavedDocument(999))
