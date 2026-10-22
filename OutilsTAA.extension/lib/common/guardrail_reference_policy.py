# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Appariement pur d'une limite de pièce et d'une arête de garde-corps.

Une arête n'est pas admissible du seul fait qu'elle appartient à un
garde-corps : elle doit être presque colinéaire à la limite privative.
Le calcul ne remplace pas la détermination réglementaire de la surface.
"""

from plans_vente.dimension_geometry import segment_match_metrics


def matches_guardrail_edge(boundary, edge, tolerance,
                           angle_degrees=3., minimum_overlap=.60):
    """Retourne les métriques de confiance du même moteur que les dalles."""
    return segment_match_metrics(
        boundary, edge,
        angle_tolerance_degrees=angle_degrees,
        distance_tolerance=tolerance,
        minimum_overlap_ratio=minimum_overlap)


def select_guardrail_edge(boundary, edges, tolerance,
                          angle_degrees=3., minimum_overlap=.60,
                          max_edges=120, include_metrics=False):
    """Choisir une référence d'arête valide, pas un axe théorique.

    edges: (segment_xy, reference, element_id, z) déjà présélectionnés
    sur au plus deux garde-corps visibles proches. En cas de surcharge,
    retourner None sans tenter de raccourci géométrique approximatif.
    """
    edges = list(edges or [])
    if len(edges) > int(max_edges):
        return None
    best = None
    for segment, reference, element_id, z in edges:
        if reference is None:
            continue
        metrics = matches_guardrail_edge(
            boundary, segment, tolerance, angle_degrees, minimum_overlap)
        if metrics is None:
            continue
        score = metrics["score"]
        if best is None or score < best[0]:
            best = (score, reference, element_id, metrics)
    if best is None:
        return None
    if include_metrics:
        return best[1], best[2], best[3]
    return best[1], best[2]


def select_guardrails_by_path(items, target_segments, tolerance,
                              max_railings=2, max_segments=80,
                              angle_degrees=12.0, minimum_overlap=.30):
    """Filtre léger AVANT extraction native des arêtes des garde-corps.

    items : (element, segments_xy_du_chemin_revit) ; le chemin ne sert
    qu'au filtrage spatial, JAMAIS comme Reference pour la cote.
    Un garde-corps est retenu si une portion de son chemin est
    sensiblement parallèle et proche d'une limite de pièce sélectionnée.
    Budget de chemins dépassé ou trop de garde-corps réellement pertinents
    => liste vide, puis le module garde son repli 2D.
    """
    targets = list(target_segments or [])
    if not targets:
        return []
    inspected = 0
    matches = []
    for element, segments in items:
        for segment in segments:
            inspected += 1
            if inspected > int(max_segments):
                return []
            best = None
            for target in targets:
                metrics = segment_match_metrics(
                    target, segment,
                    angle_tolerance_degrees=angle_degrees,
                    distance_tolerance=tolerance,
                    minimum_overlap_ratio=minimum_overlap)
                if metrics is not None and (best is None or
                                            metrics["score"] < best):
                    best = metrics["score"]
            if best is not None:
                matches.append((best, element))
                break
        if len(matches) > int(max_railings):
            # Pas de selection arbitraire lorsque plusieurs ouvrages sont
            # vraiment sur la meme limite de pièce.
            return []
    matches.sort(key=lambda item: item[0])
    return [element for _score, element in matches]


def diagnose_guardrail_candidates(boundary, edges, tolerance,
                                  angle_degrees=3., minimum_overlap=.60,
                                  max_edges=120):
    """Mesures brutes de correspondance, SANS relacher les seuils.

    Une entree par arete native candidate, meme si le test strict echoue.
    Le resultat informe sur la cause du rejet sans proposer une Reference
    trompeuse. Unites : pieds Revit ; angle en degres.
    """
    import math

    edges = list(edges or [])
    if len(edges) > int(max_edges):
        return []
    ax, ay, bx, by = [float(x) for x in boundary]
    vx, vy = bx-ax, by-ay
    length = math.sqrt(vx*vx + vy*vy)
    if length < 1.e-9:
        return []
    ux, uy = vx/length, vy/length
    nx, ny = -uy, ux
    result = []
    for segment, reference, element_id, z in edges:
        if reference is None:
            continue
        cx, cy, dx, dy = [float(x) for x in segment]
        wx, wy = dx-cx, dy-cy
        other_len = math.sqrt(wx*wx + wy*wy)
        if other_len < 1.e-9:
            continue
        dot = min(1., max(0., abs(ux*wx/other_len + uy*wy/other_len)))
        angle = math.degrees(math.acos(dot))
        midpoint_dx = (cx+dx-ax-bx)*.5
        midpoint_dy = (cy+dy-ay-by)*.5
        distance = abs(midpoint_dx*nx + midpoint_dy*ny)
        c0 = (cx-ax)*ux + (cy-ay)*uy
        c1 = (dx-ax)*ux + (dy-ay)*uy
        overlap = max(0., min(length, max(c0, c1)) -
                      max(0., min(c0, c1))) / length
        reasons = []
        if angle > angle_degrees + 1.e-8:
            reasons.append("angle")
        if distance > tolerance + 1.e-10:
            reasons.append("ecart")
        if overlap + 1.e-12 < minimum_overlap:
            reasons.append("recouvrement")
        result.append({
            "element_id": element_id,
            "z": z,
            "distance": distance,
            "angle": angle,
            "overlap": overlap,
            "reasons": reasons,
            "eligible": not reasons,
        })
    # Commencer par les segments dont la direction et la couverture
    # correspondent, meme s'ils sont decales lateralement. Les autres
    # sont conserves dans le retour pour le diagnostic complet.
    result.sort(key=lambda record: (
        "angle" in record["reasons"],
        "recouvrement" in record["reasons"],
        record["distance"], record["angle"]))
    return result


def is_exterior_annex(room_name, interior_exterior=""):
    """Loggia, terrasse, balcon ou jardin ; ou classification projet Ext.

    Le nom est issu du parametre ROOM_NAME (pas de Room.Name sous
    IronPython). La classification optionnelle est le parametre
    utilisateur 'Int/Ext'. Ne pas deduire 'exterieur' de la geometrie
    de la Room ou de la simple presence d'une separation de piece.
    """
    name = (room_name or "").lower().strip()
    flag = (interior_exterior or "").lower().strip()
    return (any(word in name for word in (
                "loggia", "balcon", "terrasse", "jardin"))
            or flag in ("ext", "exterieur", "extérieur", "externe"))


def guardrail_tolerance_mm(is_exterior, ordinary_mm=20., recovery_mm=50.):
    """Marge supplementaire UNIQUEMENT pour les annexes exterieures."""
    return float(recovery_mm if is_exterior else ordinary_mm)
