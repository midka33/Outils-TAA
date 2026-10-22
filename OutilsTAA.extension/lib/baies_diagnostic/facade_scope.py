# -*- coding: utf-8 -*-
from __future__ import unicode_literals
"""Périmètre TAA pour le diagnostic, sans validation des surfaces RE2020."""
import re

FACADE_PREFIXES = ("FEN-EXT", "PORFEN-EXT")
ROOF_HOSTS = ("toit", "toits", "toiture", "toitures", "roof", "roofs")
MRX_PATTERN = re.compile(r"(^|[^a-z0-9])mrx($|[^a-z0-9])", re.IGNORECASE)


def is_facade_family(name):
    return (name or "").strip().upper().startswith(FACADE_PREFIXES)


def exclusion_reason(family_name, type_name="", host_category=""):
    """Exclusions métier, prioritaires et indépendantes des cases de visibilité.

    MRX = famille / type de mur-rideau selon le nommage TAA. Un lanterneau
    hébergé par une toiture est aussi exclu, même si son nom n'est pas explicite.
    """
    title = u"{} {}".format(family_name or u"", type_name or u"").lower()
    if ((host_category or "").strip().lower() in ROOF_HOSTS
            or "lanterneau" in title or "désenfumage" in title
            or "desenfumage" in title):
        return "LANTERNEAU"
    if (MRX_PATTERN.search(title) or "mur rideau" in title
            or "mur-rideau" in title or "murs rideaux" in title
            or "métal perforé" in title or "metal perfore" in title):
        return "MRX"
    return ""


def facade_status(name, host_category="", wall_function="", type_name=""):
    if not is_facade_family(name):
        return "HORS_PREFIXES"
    reason = exclusion_reason(name, type_name, host_category)
    if reason == "LANTERNEAU":
        return "CAS_SPECIAL_LANTERNEAU"
    if reason == "MRX":
        return "CAS_SPECIAL_MRX_A_EXCLURE"
    if (host_category or "").strip().lower() not in ("mur", "murs", "wall", "walls"):
        return "HOTE_NON_MUR_A_VERIFIER"
    if (wall_function or "").strip().lower() != "exterior":
        return "EXTERIORITE_A_VERIFIER"
    return "FACADE_PRESUMEE_A_VALIDER"


def coffre_tunnel_alert(family_name, type_name=""):
    """Alerte métier : la réservation brute inclut le coffre tunnel du volet.

    Le nom ne suffit pas à mesurer le tableau : aucun seuil réglementaire
    n'est déduit, même si les cotes brutes et nominales sont disponibles.
    """
    name = u"{} {}".format(family_name or u"", type_name or u"").lower()
    if ("tunnel" in name and (
            "vr" in name or "volet" in name or "coffre" in name)):
        return "RESERVATION_COFFRE_TUNNEL_A_VERIFIER"
    return ""


def rule_16_status(family_name, type_name="", host_category="", wall_function=""):
    """Un statut de présélection, jamais une attestation réglementaire."""
    reason = exclusion_reason(family_name, type_name, host_category)
    if reason:
        return "EXCLU_" + reason
    if coffre_tunnel_alert(family_name, type_name):
        return "A_VERIFIER_COFFRE_TUNNEL"
    if facade_status(family_name, host_category, wall_function, type_name) == "FACADE_PRESUMEE_A_VALIDER":
        return "CANDIDAT_A_CONTROLER"
    return "HORS_PERIMETRE_OU_A_VERIFIER"
