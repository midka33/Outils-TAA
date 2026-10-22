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
                          max_edges=120):
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
            best = (score, reference, element_id)
    if best is None:
        return None
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
