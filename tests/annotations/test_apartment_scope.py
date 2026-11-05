# -*- coding: utf-8 -*-
"""Selection en lecture seule du perimetre d'un appartement pour Cotation beta."""

import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "OutilsTAA.extension/OutilsTAA.tab/Annotations.panel/services"


def policy():
    spec = importlib.util.spec_from_file_location(
        "_taa_apartment_policy", SERVICES / "apartment_scope.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Param(object):
    def __init__(self, name, value, storage="String"):
        self.Definition = SimpleNamespace(Name=name)
        self.value = value
        self.StorageType = storage

    def AsString(self):
        return self.value if self.StorageType == "String" else None

    def AsInteger(self):
        return int(self.value)

    def AsValueString(self):
        return str(self.value)


class Room(object):
    def __init__(self, uid, apartment, building, name="Chambre"):
        self.UniqueId = uid
        self.Number = uid
        self.Parameters = [
            Param("N° appartement", apartment),
            Param("Bâtiment", building),
            Param("Nom", name),
            Param("Numéro", uid),
        ]


def sample():
    return [
        Room("A01", "101", "A", "Séjour"),
        Room("A02", "101", "A", "Cuisine"),
        Room("A03", "101", "A", "Chambre"),
        Room("B01", "101", "B", "Séjour"),
        Room("B02", "101", "B", "Salle de bains"),
        Room("A04", "102", "A", "Séjour"),
        Room("A05", "102", "A", "Cuisine"),
        Room("A06", "102", "A", "Chambre"),
    ]


def test_parametre_logement_propose_en_priorite():
    names = policy().parameter_candidates(sample())
    assert names[0] == "N° appartement"
    assert "Bâtiment" in names
    assert "Numéro" not in names


def test_choix_exact_et_batiment_evite_appartements_homonymes():
    module = policy()
    assert [(key, len(items)) for key, items in
            module.apartment_values(sample(), "N° appartement")] == [
                ("101", 5), ("102", 3)]
    selected = module.filter_apartment(
        sample(), "N° appartement", "101",
        building_parameter="Bâtiment", building_value="A")
    assert [x.UniqueId for x in selected] == ["A01", "A02", "A03"]


def test_sans_batiment_choix_explicitement_de_cinq_pieces():
    selected = policy().filter_apartment(
        sample(), "N° appartement", "101")
    assert len(selected) == 5
    # C'est la confirmation UI qui refuse de valider deux appartements
    # homonymes. Sans identifiant batiment, ne pas inventer la separation.


def test_refuse_une_seule_piece_et_selection_vide():
    module = policy()
    with pytest.raises(ValueError, match="au moins 2"):
        module.filter_apartment(sample(), "Numéro", "A01")
    with pytest.raises(ValueError, match="vide"):
        module.filter_apartment(sample(), "N° appartement", "")


def test_limite_stricte_douze_pieces():
    module = policy()
    rooms = [Room("R{}".format(i), "777", "A") for i in range(13)]
    with pytest.raises(ValueError, match="13 pieces"):
        module.filter_apartment(rooms, "N° appartement", "777")
    assert len(module.filter_apartment(
        rooms[:12], "N° appartement", "777")) == 12


def test_refuse_filtre_batiment_incoherent():
    module = policy()
    with pytest.raises(ValueError, match="distinct"):
        module.filter_apartment(
            sample(), "Bâtiment", "A",
            building_parameter="Bâtiment", building_value="A")
    with pytest.raises(ValueError, match="sans parametre"):
        module.filter_apartment(sample(), "N° appartement", "101",
                                building_value="A")


def test_parametre_ambigu_et_non_renseigne_ne_fuit_pas():
    module = policy()
    room = Room("X", "101", "A")
    room.Parameters += [
        Param("N° appartement", "999"),
        Param("Champ vide", ""),
    ]
    data = module.room_parameters(room)
    assert "N° appartement" not in data
    assert "Champ vide" not in data
    assert data["Bâtiment"] == "A"


def test_numero_d_appartement_entier_zero_non_ignore():
    module = policy()
    rooms = [Room("X", "0", "A"), Room("Y", "0", "A")]
    for room in rooms:
        room.Parameters[0] = Param("Appartement", 0, storage="Integer")
    assert [r.UniqueId for r in module.filter_apartment(
        rooms, "Appartement", "0")] == ["X", "Y"]


def test_pas_de_dependance_api_revit_et_syntaxe_ironpython():
    text = (SERVICES / "apartment_scope.py").read_text(encoding="utf-8")
    assert "Autodesk" not in text
    assert "pyrevit" not in text
    ast.parse(text)


def test_lanceur_conserve_mode_piece_et_previsualise_l_appartement():
    source = (SERVICES / "launcher.py").read_text(encoding="utf-8")
    assert '"room", "Une piece' in source
    assert '"apartment", "Un appartement' in source
    assert "filter_apartment(" in source
    assert "VERIFIER LE PERIMETRE DE L'APPARTEMENT" in source
    assert "MAX_APARTMENT_ROOMS" in source
    assert "GroupId != DB.ElementId.InvalidElementId" in source
    assert "diagnostic_room_uids=diagnostic_room_uids" in source


def test_service_borne_perimetre_transactions_et_arret():
    text = (SERVICES / "annotations_service.py").read_text(encoding="utf-8")
    assert "diagnostic_room_uid=None, diagnostic_room_uids=None" in text
    assert 'len(expected_ids) > 12' in text
    assert "Perimetre appartement modifie depuis l'apercu" in text
    assert "ARRET PREVENTIF" in text
    assert "trace(\"BATCH_STOP\"" in text
    assert "self._run_unit(" in text
