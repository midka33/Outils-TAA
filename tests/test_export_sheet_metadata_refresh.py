# -*- coding: utf-8 -*-
"""Anti-régression : les libellés persistants suivent les feuilles Revit."""
import sys
from pathlib import Path

PANEL = Path(__file__).resolve().parents[1] / (
    "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
)
for part in ("services", "models"):
    sys.path.insert(0, str(PANEL / part))

from carnet_controller import CarnetController
from publication_item import PublicationItem
from publication_set import PublicationSet


class FakeId(object):
    def __init__(self, value):
        self.IntegerValue = value


class FakeSheet(object):
    def __init__(self, uid, element_id, number, name):
        self.UniqueId = uid
        self.Id = FakeId(element_id)
        self.SheetNumber = number
        self.Name = name


class FakeExportService(object):
    def __init__(self, sheets):
        self.document = object()
        self._sheets = list(sheets)

    def get_sheets(self):
        return list(self._sheets)


class FakeRepository(object):
    def __init__(self, values):
        self.values = list(values)
        self.write_count = 0

    def list_all(self):
        return list(self.values)

    def save(self, value):
        self.write_count += 1
        return value


def controller(sheets, values):
    return CarnetController(
        export_service=FakeExportService(sheets),
        carnet_service=None,
        parameter_service=None,
        repository=FakeRepository(values),
        publication_service=None,
    )


def test_persistent_sheet_name_and_number_follow_current_revit_sheet():
    saved = PublicationSet(
        "DCE",
        [
            PublicationItem(
                "uid-a",
                1,
                "SHEET",
                "A101",
                "Ancien nom",
            )
        ],
        set_id="dce",
        persistent=True,
    )
    ctl = controller(
        [FakeSheet("uid-a", 42, "A201", "Nouveau nom")],
        [saved],
    )

    values = ctl.list_persistent()
    item = values[0].items[0]

    assert item.sheet_id == 42
    assert item.sheet_number == "A201"
    assert item.sheet_name == "Nouveau nom"
    assert ctl.repository.write_count == 0


def test_missing_revit_sheet_keeps_saved_snapshot_for_diagnostic():
    saved = PublicationSet(
        "DCE",
        [
            PublicationItem(
                "uid-missing",
                7,
                "SHEET",
                "A999",
                "Feuille supprimée",
            )
        ],
        set_id="dce",
        persistent=True,
    )
    ctl = controller([], [saved])

    item = ctl.list_persistent()[0].items[0]

    assert item.sheet_id == 7
    assert item.sheet_number == "A999"
    assert item.sheet_name == "Feuille supprimée"
    assert ctl.repository.write_count == 0
