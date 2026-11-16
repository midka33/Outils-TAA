# -*- coding: utf-8 -*-
from pathlib import Path
import sys
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel"
LIB = ROOT / "OutilsTAA.extension/lib"
sys.path.insert(0, str(LIB))
sys.path.insert(0, str(PANEL / "services"))

from plans_vente_settings_service import PlansVenteSettingsService


class Descriptor(object):
    def __init__(self, name, key):
        self.name = name
        self.identity_key = key

    def to_dict(self):
        kind, value = self.identity_key.split(":", 1)
        return {
            "name": self.name,
            "identity_kind": kind,
            "identity_value": value,
            "storage_type": "String",
        }


def test_project_settings_round_trip(tmp_path):
    path = tmp_path / "pdv.json"
    svc = PlansVenteSettingsService(
        storage_path=str(path),
        project_identity="FILE:C:\\projet\\a.rvt",
    )
    desc = Descriptor("N° Appartement", "NAME:N° Appartement")
    svc.save({
        "crop_margin_mm": 100.0,
        "allowed_scales": [50, 75],
        "main_view_template_unique_id": "uid-template",
        "room_tag_type_unique_id": "uid-tag",
    }, desc)

    data = svc.load()
    assert data["settings"]["crop_margin_mm"] == 100.0
    assert data["settings"]["allowed_scales"] == [50, 75]
    assert data["settings"]["main_view_template_unique_id"] == "uid-template"
    assert data["active_parameter"]["name"] == "N° Appartement"


def test_project_settings_are_isolated_by_identity(tmp_path):
    path = tmp_path / "pdv.json"
    first = PlansVenteSettingsService(
        storage_path=str(path),
        project_identity="FILE:C:\\projet\\a.rvt",
    )
    first.save({"crop_margin_mm": 100.0}, None)

    second = PlansVenteSettingsService(
        storage_path=str(path),
        project_identity="FILE:C:\\projet\\b.rvt",
    )
    assert second.load() == {}


def test_match_descriptor_prefers_durable_identity_then_unique_name():
    saved = {
        "name": "Appartement",
        "identity_kind": "SHARED_GUID",
        "identity_value": "abc",
        "storage_type": "String",
    }
    exact = Descriptor("Appartement", "SHARED_GUID:abc")
    same_name = Descriptor("Appartement", "NAME:Appartement")
    assert PlansVenteSettingsService.match_descriptor(
        saved, [same_name, exact]
    ) is exact

    saved["identity_value"] = "missing"
    assert PlansVenteSettingsService.match_descriptor(
        saved, [same_name]
    ) is same_name
