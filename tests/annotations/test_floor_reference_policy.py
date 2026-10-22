# -*- coding: utf-8 -*-
"""Reference de dalle partagee : priorite historique et recherche locale bornee."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "OutilsTAA.extension" / "lib"
if str(LIB) not in sys.path:
    sys.path.insert(0, str(LIB))

from common.floor_reference_policy import (
    intersects_xy, select_floor_candidates)


class Floor(object):
    def __init__(self, label, bbox):
        self.label, self.bbox = label, bbox

    def __repr__(self):
        return self.label


def bounds(floor):
    return floor.bbox


def test_pdv_legacy_keeps_same_level_even_if_far_away():
    far = Floor("dalle RDC hors loggia", (300, 300, 500, 500))
    close_nearby = Floor("balcon niveau voisin", (-1, -1, 4, 5))
    assert select_floor_candidates(
        [far], [close_nearby], mode="legacy") == [far]
    assert select_floor_candidates([], [close_nearby],
                                   mode="legacy") == [close_nearby]


def test_loggia_retrouve_dalle_niveau_voisin_quand_meme_niveau_hors_piece():
    far = Floor("dalle meme niveau loin", (20, 20, 30, 30))
    close = Floor("balcon niveau voisin", (-.05, -.05, 3.2, 3.6))
    result = select_floor_candidates(
        [far], [close], mode="local",
        room_xy=(0, 0, 3.12, 3.62), get_floor_xy=bounds,
        padding=.3, max_floors=6)
    assert result == [close]


def test_loggia_peut_examiner_dalle_proche_sur_chacun_des_deux_niveaux():
    local = Floor("dalle même niveau", (0, 0, 3.12, 3.62))
    lower = Floor("dalle voisin", (-.1, -.1, 3.22, 3.7))
    result = select_floor_candidates(
        [local], [lower], mode="local",
        room_xy=(0, 0, 3.12, 3.62),
        get_floor_xy=bounds, padding=.3)
    assert result == [local, lower]


def test_recherche_locale_ignore_planchers_sans_boite_englobante_exploitable():
    unknown = Floor("inconnu", None)
    close = Floor("bon", (0, 0, 3, 4))
    assert select_floor_candidates(
        [unknown, close], [], mode="local",
        room_xy=(0, 0, 3, 4), get_floor_xy=bounds) == [close]
    assert select_floor_candidates(
        [close], [], mode="local",
        room_xy=None, get_floor_xy=bounds) == []


def test_recherche_locale_annule_le_parcours_si_budget_de_six_est_depasse():
    floors = [Floor("s%d" % i, (0, 0, 4, 4)) for i in range(7)]
    assert select_floor_candidates(
        floors, [], mode="local", room_xy=(0, 0, 3, 3),
        get_floor_xy=bounds, max_floors=6) == []


def test_recherche_ne_prend_pas_le_solide_dune_dalle_tres_eloignee():
    a, b = (0, 0, 3, 4), (40, 30, 50, 60)
    assert not intersects_xy(a, b, padding=.3)
    assert intersects_xy(a, (-.2, -.2, -.01, 4), padding=.3)
    assert not intersects_xy(a, (-.4, -.4, -.31, 4), padding=.3)


def test_mode_inconnu_refuse_plutot_que_fallback_silencieux():
    try:
        select_floor_candidates([], [], mode="unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("Le mode inconnu doit être refusé.")


def test_plan_vente_delegue_a_la_politique_partagee_sans_changer_mode():
    path = (ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" /
            "PlansDeVente.panel" / "services" / "dimension_service.py")
    src = path.read_text(encoding="utf-8")
    assert "def _floor_candidates(self, room, same_level, nearby_level)" in src
    assert "select_floor_candidates(same_level, nearby_level, mode=\"legacy\")" in src
    assert "self._floor_candidates(room, same_level, nearby_level)" in src
    assert "cache_key = self._floor_cache_key(room, room_level_key)" in src


def test_annotations_reutilise_le_meme_collecteur_natif_sans_parcours_additionnel():
    path = (ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" /
            "Annotations.panel" / "services" / "annotations_service.py")
    src = path.read_text(encoding="utf-8")
    assert "def _floor_candidates(self, room, same_level, nearby_level)" in src
    assert "mode=\"local\"" in src
    assert "max_floors=6" in src
    assert "def _nearby_floor_edges(self, room)" not in src
    assert "floor.get_Geometry" not in src
