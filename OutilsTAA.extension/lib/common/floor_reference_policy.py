# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Politique commune de recherche des planchers pour les cotes natives.

Aucune dependance Revit : les appelants fournissent leurs planchers et les
emprises XY, en unites internes. Le service Plans de vente garde son
comportement historique ; le mode local est opt-in et borne.
"""


def _valid_box(box):
    if box is None or len(box) != 4:
        return False
    try:
        return (float(box[2]) >= float(box[0])
                and float(box[3]) >= float(box[1]))
    except (TypeError, ValueError):
        return False


def intersects_xy(a, b, padding=0.0):
    """Intersections de bboxes en XY avec une marge metrique explicite."""
    if not _valid_box(a) or not _valid_box(b):
        return False
    pad = max(0.0, float(padding))
    return not (b[2] < a[0] - pad or b[0] > a[2] + pad
                or b[3] < a[1] - pad or b[1] > a[3] + pad)


def _distance_box_centers(a, b):
    ax, ay = (a[0]+a[2])*.5, (a[1]+a[3])*.5
    bx, by = (b[0]+b[2])*.5, (b[1]+b[3])*.5
    return (ax-bx)**2 + (ay-by)**2


def select_floor_candidates(same_level, nearby_level, mode="legacy",
                            room_xy=None, get_floor_xy=None, padding=0.0,
                            max_floors=12):
    """Renvoie une liste de planchers a inspecter, sans extraction de solides.

    legacy : comportement PDV historique strictement conserve.
    local  : uniquement les planchers proches XY, sur meme niveau ET sur
             niveau voisin deja filtre en altitude par l'appelant.
             Depassement de budget ou bbox inconnue : aucun plancher
             analyse. Le fallback 2D du module Annotations est alors utilise.

    Cette fonction NE manipule PAS de geometrie Revit, ni de transactions.
    """
    current = list(same_level or [])
    nearby = list(nearby_level or [])
    if mode == "legacy":
        return current if current else nearby
    if mode != "local":
        raise ValueError("Politique de plancher inconnue : {}".format(mode))
    if not _valid_box(room_xy) or not callable(get_floor_xy):
        return []
    if int(max_floors) < 1:
        return []

    selected = []
    for floor in current + nearby:
        try:
            bbox = get_floor_xy(floor)
        except Exception:
            continue
        if not intersects_xy(room_xy, bbox, padding):
            continue
        priority = 0 if floor in current else 1
        selected.append((priority, _distance_box_centers(room_xy, bbox), floor))

    # En cas de selection trop importante, ne pas parcourir les solides :
    # tenter le fallback 2D. Aucune troncature arbitraire n'est autorisee.
    if len(selected) > int(max_floors):
        return []
    selected.sort(key=lambda entry: (entry[0], entry[1]))
    return [entry[2] for entry in selected]
