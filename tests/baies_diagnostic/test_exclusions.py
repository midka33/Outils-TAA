# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "OutilsTAA.extension" / "lib"))
from baies_diagnostic.facade_scope import exclusion_reason, facade_status, rule_16_status


def test_mrx_family_excluded():
    assert exclusion_reason("FEN-EXT-GEN-1V_MRX") == "MRX"
    assert rule_16_status("FEN-EXT-GEN-1V_MRX", host_category="Murs", wall_function="Exterior") == "EXCLU_MRX"


def test_mrx_not_a_substring():
    assert exclusion_reason("FEN-EXT-GEN-1V_MRXY") == ""
    assert exclusion_reason("PORFEN-EXT-GEN-2V_ITI_VR tunnel") == ""


def test_mrx_from_type():
    assert exclusion_reason("FEN-EXT-GEN-1V_ITI", type_name="MRX Métal perforé") == "MRX"


def test_lantern_name_detected():
    assert exclusion_reason("FEN-EXT-GEN-1V_Lanterneau") == "LANTERNEAU"
    assert rule_16_status("FEN-EXT-GEN-1V_Lanterneau", host_category="Murs") == "EXCLU_LANTERNEAU"


def test_roof_host_without_lantern_name():
    assert exclusion_reason("FEN-EXT-GEN-1V_ITI", host_category="Toits") == "LANTERNEAU"
    assert exclusion_reason("FEN-EXT-GEN-1V_ITI", host_category="Roofs") == "LANTERNEAU"


def test_ordinary_window_not_excluded():
    assert exclusion_reason("FEN-EXT-GEN-1V_ITI", host_category="Murs") == ""
    assert rule_16_status("FEN-EXT-GEN-1V_ITI", host_category="Murs", wall_function="Exterior") == "CANDIDAT_A_CONTROLER"


def test_aggregated_candidate_flags_remain_excluded():
    from baies_diagnostic.evaluator import aggregate_by_type
    rows=[dict(source="HOST",source_id="HOST",family="FEN-EXT-GEN-1V_MRX",
               type="Mur-rideau",method="NOMINALE",area_m2=2.0,
               status="NOMINAL_A_CONFIRMER",facade_status="CAS_SPECIAL_MRX_A_EXCLURE",
               rule_16_status="EXCLU_MRX",element_id="101")]
    summary=aggregate_by_type(rows)
    assert summary[0]["rule_16_status"] == "EXCLU_MRX"


def test_original_classification_compatibility():
    assert facade_status("FEN-EXT-GEN-1V_MRX", "Murs", "Exterior") == "CAS_SPECIAL_MRX_A_EXCLURE"
    assert facade_status("FEN-EXT-GEN-1V_Lanterneau", "Toits", "") == "CAS_SPECIAL_LANTERNEAU"


def test_candidates_eligible_only_as_qualified_not_certified():
    assert rule_16_status("FEN-EXT-GEN-1V_ITI", host_category="Murs", wall_function="Interior") == "HORS_PERIMETRE_OU_A_VERIFIER"
