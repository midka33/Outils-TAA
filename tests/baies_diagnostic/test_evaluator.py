# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"OutilsTAA.extension"/"lib"))
from baies_diagnostic.evaluator import evaluate,aggregate_by_type,normalize_name,csv_content

def p(name,value,origin="type"):
    return dict(name=name,value_m=value,origin=origin)

def test_priority_tableau():
    r=evaluate([p("Largeur",1.4),p("Hauteur",2.15),p("Largeur tableau",1.44),p("Hauteur tableau",2.18)])
    assert r["status"]=="CANDIDAT_TABLEAU"
    assert abs(r["selected"]["area_m2"]-1.44*2.18)<1e-8
    assert "non démontrée" in r["reason"]

def test_rough_width_height():
    r=evaluate([p("Rough Width",1.41),p("Rough Height",2.16),p("Width",1.4),p("Height",2.15)])
    assert r["selected"]["method"]=="OUVERTURE_BRUTE"

def test_nominal_not_validated():
    r=evaluate([p("Largeur",1.4),p("Hauteur",2.15)])
    assert r["status"]=="NOMINAL_A_CONFIRMER"

def test_incomplete_is_unknown():
    assert evaluate([p("Largeur tableau",1.4)])["selected"] is None

def test_duplicate_conflict():
    r=evaluate([p("Largeur tableau",1.4),p("Largeur en tableau",1.6),p("Hauteur tableau",2.15)])
    assert r["status"]=="A_VERIFIER" and r["selected"] is None

def test_occurrence_preferred():
    r=evaluate([p("Largeur tableau",1.4),p("Largeur tableau",1.5,"occurrence"),p("Hauteur tableau",2.15)])
    assert r["selected"]["width_origin"]=="occurrence"

def test_accents():
    assert normalize_name("Largeur-TABLEAU")=="largeur tableau"

def test_distinct_link_instances():
    rows=[dict(source="Host",source_id="HOST",family="F",type="T",status="NOMINAL_A_CONFIRMER",method="NOMINALE",area_m2=3,element_id="1"),
          dict(source="Lien",source_id="L1",family="F",type="T",status="NOMINAL_A_CONFIRMER",method="NOMINALE",area_m2=3,element_id="2"),
          dict(source="Host",source_id="HOST",family="F",type="T",status="A_VERIFIER",method="NOMINALE",area_m2=3,element_id="3")]
    groups=aggregate_by_type(rows)
    assert len(groups)==2
    assert next(x for x in groups if x["source_id"]=="HOST")["status"]=="VARIABLE_SELON_OCCURRENCE"

def test_csv_quotes():
    csv=csv_content([dict(nom='Porte; "baie"',etat="À examiner\nEncore")],["nom","etat"])
    assert '"Porte; ""baie"""' in csv
    assert "À examiner Encore" in csv

def test_glazing_dimensions_not_tableau():
    assert evaluate([p("Largeur vitrage",1),p("Hauteur vitrage",2)])["selected"] is None


def test_taa_prefers_nominal_over_rough():
    r=evaluate([p("Largeur",2.7),p("Hauteur",2.0),
                p("Largeur brute",2.74),p("Hauteur brute",2.30)],
               prefer_nominal=True)
    assert r["selected"]["method"]=="NOMINALE"
    assert r["status"]=="NOMINAL_A_CONFIRMER"
    assert abs(r["selected"]["area_m2"]-5.4)<1e-10
    assert len(r["candidates"])==2
    assert "Convention TAA" in r["reason"]


def test_taa_prioritizes_named_tableau_if_defined():
    r=evaluate([p("Largeur",2.7),p("Hauteur",2.0),
                p("Largeur tableau",2.65),p("Hauteur tableau",1.98),
                p("Largeur brute",2.74),p("Hauteur brute",2.30)],
               prefer_nominal=True)
    assert r["selected"]["method"]=="TABLEAU"


def test_taa_rejects_only_brute_dimensions():
    r=evaluate([p("Largeur brute",2.74),p("Hauteur brute",2.30)],
               prefer_nominal=True)
    assert r["selected"] is None
    assert r["status"]=="A_VERIFIER"
    assert len(r["candidates"])==1


def test_regular_diagnostic_keeps_rough_default():
    r=evaluate([p("Largeur brute",2.74),p("Hauteur brute",2.30),
                p("Largeur",2.7),p("Hauteur",2.0)])
    assert r["selected"]["method"]=="OUVERTURE_BRUTE"


def test_taa_window_with_no_volet_has_height_nominale():
    r=evaluate([p("Largeur",1.10),p("Hauteur",1.40)], prefer_nominal=True)
    assert r["selected"]["method"]=="NOMINALE"
    assert abs(r["selected"]["area_m2"]-1.54)<1e-10
