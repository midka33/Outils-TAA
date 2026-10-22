# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Convention TAA : préfixes de familles de façade, sans validation des 1/6."""
FACADE_PREFIXES=("FEN-EXT","PORFEN-EXT")


def is_facade_family(name):
    return (name or "").strip().upper().startswith(FACADE_PREFIXES)


def facade_status(name, host_category="", wall_function=""):
    if not is_facade_family(name):
        return "HORS_PREFIXES"
    family=(name or "").lower()
    if "lanterneau" in family or "desenfumage" in family or "désenfumage" in family:
        return "CAS_SPECIAL_LANTERNEAU"
    if "_mrx" in family or "métal perforé" in family or "metal perfore" in family:
        return "CAS_SPECIAL_NON_VITRE_A_VERIFIER"
    if (host_category or "").strip().lower() not in ("mur","murs","wall","walls"):
        return "HOTE_NON_MUR_A_VERIFIER"
    if (wall_function or "").strip().lower()!="exterior":
        return "EXTERIORITE_A_VERIFIER"
    return "FACADE_PRESUMEE_A_VALIDER"
