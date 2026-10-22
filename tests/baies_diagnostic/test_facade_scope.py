# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"))
from baies_diagnostic.facade_scope import is_facade_family, facade_status
from baies_diagnostic.evaluator import aggregate_by_type


def test_prefixes():
    assert is_facade_family("FEN-EXT-GEN-1V_ITI")
    assert is_facade_family("PORFEN-EXT-GEN-2V_ITI")
    assert is_facade_family(" fen-ext-abc ")
    assert not is_facade_family("POR-EXT-MET-1V")
    assert not is_facade_family("POR-INT-GEN-1V")


def test_exterior_wall_presumed_not_certified():
    assert facade_status("PORFEN-EXT-GEN-1V_ITI", "Murs", "Exterior") == "FACADE_PRESUMEE_A_VALIDER"
    assert facade_status("FEN-EXT-GEN-1V_ITI", "Walls", "Interior") == "EXTERIORITE_A_VERIFIER"


def test_perforated_metal_flagged():
    assert facade_status("FEN-EXT-GEN-1V_MRX", "Murs", "Exterior") == "CAS_SPECIAL_MRX_A_EXCLURE"


def test_skylight_flagged():
    assert facade_status("FEN-EXT-GEN-1V_LanterneauDesenfumage", "Toits", "") == "CAS_SPECIAL_LANTERNEAU"


def test_other_host_flagged():
    assert facade_status("FEN-EXT-GEN-1V_ITI", "Toits", "") == "HOTE_NON_MUR_A_VERIFIER"


def test_type_summary_has_facade_status():
    rows=[dict(source="HOST",source_id="HOST",family="FEN-EXT",type="A",status="NOMINAL_A_CONFIRMER",
               method="NOMINALE",area_m2=1,element_id="1",facade_status="FACADE_PRESUMEE_A_VALIDER")]
    x=aggregate_by_type(rows)
    assert x[0]["facade_status"]=="FACADE_PRESUMEE_A_VALIDER"
