# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SERVICE_DIR = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel", "services")
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from filename_service import FilenameService


class Item(object):
    def __init__(self, unique_id="uid", sheet_number="A101", sheet_name="RDC"):
        self.unique_id = unique_id
        self.sheet_number = sheet_number
        self.sheet_name = sheet_name
        self.parameter_value = "DCE"


class PublicationSet(object):
    def __init__(self, name="Plans", items=None):
        self.name = name
        self.items = items or [Item()]


def test_preview_returns_resolved_filename_instead_of_placeholder():
    service = FilenameService()
    settings = type("Settings", (), {"filename_template": "{carnet}_{numero}_{nom}"})()
    assert service.preview(PublicationSet(), settings) == "Plans_A101_RDC"


def test_preview_resolves_revit_parameter_token():
    service = FilenameService()
    publication_set = PublicationSet(items=[Item()])
    settings = type("Settings", (), {"filename_template": "{parametre:Sous-titre}"})()
    service._parameter_value = lambda current_item, name: "DCE" if name == "Sous-titre" else ""
    assert service.preview(publication_set, settings) == "DCE"
