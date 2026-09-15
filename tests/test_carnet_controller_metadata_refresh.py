# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
SERVICE_DIR = os.path.join(ROOT, "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel", "services")
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)

from carnet_controller import CarnetController


class FakeSheet(object):
    def __init__(self, unique_id, number, name):
        self.UniqueId = unique_id
        self.SheetNumber = number
        self.Name = name


class FakeItem(object):
    def __init__(self, unique_id, number, name):
        self.unique_id = unique_id
        self.sheet_number = number
        self.sheet_name = name


class FakeCarnet(object):
    def __init__(self, items):
        self.items = items


class FakeExportService(object):
    def __init__(self, sheets):
        self._sheets = sheets

    def get_sheets(self):
        return self._sheets


class FakeRepository(object):
    def __init__(self, carnets):
        self.carnets = carnets
        self.saved = []

    def list_all(self):
        return list(self.carnets)

    def save(self, carnet):
        self.saved.append(carnet)
        return carnet


def _controller(repo, sheets):
    return CarnetController(
        FakeExportService(sheets),
        carnet_service=None,
        parameter_service=None,
        repository=repo,
        publication_service=None,
    )


def test_refresh_persistent_metadata_updates_names_without_reordering():
    items = [
        FakeItem("uid-2", "A102", "Ancien R+1"),
        FakeItem("uid-1", "A101", "RDC"),
    ]
    carnet = FakeCarnet(items)
    repo = FakeRepository([carnet])
    sheets = [
        FakeSheet("uid-1", "A101", "RDC"),
        FakeSheet("uid-2", "A202", "Nouveau R+1"),
    ]

    assert _controller(repo, sheets).refresh_persistent_metadata() is True
    assert [item.unique_id for item in carnet.items] == ["uid-2", "uid-1"]
    assert carnet.items[0].sheet_number == "A202"
    assert carnet.items[0].sheet_name == "Nouveau R+1"
    assert len(repo.saved) == 1


def test_refresh_persistent_metadata_ignores_missing_sheet():
    item = FakeItem("uid-missing", "A999", "Ancienne")
    carnet = FakeCarnet([item])
    repo = FakeRepository([carnet])

    assert _controller(repo, []).refresh_persistent_metadata() is False
    assert item.sheet_number == "A999"
    assert item.sheet_name == "Ancienne"
    assert repo.saved == []
