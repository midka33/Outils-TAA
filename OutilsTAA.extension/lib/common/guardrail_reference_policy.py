# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Appariement pur d'une limite de pièce et d'une arête de garde-corps.

Une arête n'est pas admissible du seul fait qu'elle appartient à un
garde-corps : elle doit être presque colinéaire à la limite privative.
Le calcul ne remplace pas la détermination réglementaire de la surface.
"""

from plans_vente.dimension_geometry import segment_match_metrics



def _closest_then_longest(candidates, distance_equality=0.):
    """Trier selon distance absolue puis longueur si meme distance.

    Le seuil d'egalite est applique par rapport au MINIMUM GLOBAL,
    sans chainage de tolerances sur plusieurs candidats.
    Les autres controles geometriques sont effectues en amont.
    Entrees : tuples (distance, longueur, ...).
    """
    rows = list(candidates or [])
    if not rows:
        return None
    shortest_distance = min(item[0] for item in rows)
    equality = max(0., float(distance_equality))
    near = [item for item in rows
            if item[0] <= shortest_distance + equality + 1.e-10]
    # Conserver le premier en cas d'egalite complete (ordre stable).
    return max(near, key=lambda item: item[1])


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
                          max_edges=120, include_metrics=False,
                          distance_equality=0.):
    """Choisir une référence d'arête valide, pas un axe théorique.

    edges: (segment_xy, reference, element_id, z) déjà présélectionnés
    sur au plus deux garde-corps visibles proches. En cas de surcharge,
    retourner None sans tenter de raccourci géométrique approximatif.
    """
    edges = list(edges or [])
    if len(edges) > int(max_edges):
        return None
    import math

    eligible = []
    for segment, reference, element_id, z in edges:
        if reference is None:
            continue
        metrics = matches_guardrail_edge(
            boundary, segment, tolerance, angle_degrees, minimum_overlap)
        if metrics is None:
            continue
        distance = float(metrics["distance"])
        length = math.hypot(float(segment[2])-float(segment[0]),
                            float(segment[3])-float(segment[1]))
        eligible.append((distance, length, reference, element_id, metrics))
    best = _closest_then_longest(eligible, distance_equality)
    if best is None:
        return None
    if include_metrics:
        return best[2], best[3], best[4]
    return best[2], best[3]


def select_guardrails_by_path(items, target_segments, tolerance,
                              max_railings=2, max_segments=80,
                              angle_degrees=12.0, minimum_overlap=.30,
                              ambiguity_gap=0.0, with_diagnostics=False,
                              allow_contiguous_companion=False,
                              companion_gap=.32808399,
                              companion_lateral=.0656168):
    """Choisir les garde-corps les plus proches, puis les plus longs.

    Le chemin Railing.GetPath sert a filtrer les ouvrages, JAMAIS
    comme reference de cote. Les contraintes d'angle/recouvrement
    restent obligatoires. ambiguity_gap est conserve pour compatibilite,
    et represente desormais le seuil de distance dite egale (en pieds).
    """
    import math

    targets = list(target_segments or [])
    info = {"reason": "no_targets", "inspected": 0, "path_matches": 0,
            "ambiguous": 0, "selected": 0, "closest_distance": None,
            "target_count": len(targets), "ties_by_length": 0,
            "companions": 0}
    if not targets:
        return ([], info) if with_diagnostics else []
    equality = max(0., float(ambiguity_gap))
    rows = [[] for _ in targets]
    for element, segments in items:
        for segment in segments:
            info["inspected"] += 1
            if info["inspected"] > int(max_segments):
                info["reason"] = "path_budget"
                return ([], info) if with_diagnostics else []
            length = math.hypot(float(segment[2])-float(segment[0]),
                                float(segment[3])-float(segment[1]))
            for i, target in enumerate(targets):
                metrics = segment_match_metrics(
                    target, segment,
                    angle_tolerance_degrees=angle_degrees,
                    distance_tolerance=tolerance,
                    minimum_overlap_ratio=minimum_overlap)
                if metrics is None:
                    continue
                distance = float(metrics["distance"])
                rows[i].append((distance, length, element,
                                segment, metrics["overlap_ratio"]))
                info["path_matches"] += 1
                if (info["closest_distance"] is None or
                        distance < info["closest_distance"]):
                    info["closest_distance"] = distance

    selected = []
    second_choices = []
    for target, matches in zip(targets, rows):
        if not matches:
            continue
        # Un même garde-corps peut exposer plusieurs troncons de chemin :
        # garder sa meilleure correspondance, sans confondre ses troncons
        # avec des ouvrages distincts.
        unique = []
        for distance, length, element, segment, overlap in matches:
            if any(entry[2] is element for entry in unique):
                continue
            same_element = [x for x in matches if x[2] is element]
            unique.append(_closest_then_longest(
                same_element, distance_equality=equality))

        primary = _closest_then_longest(unique, distance_equality=equality)
        equivalents = [candidate for candidate in unique
                       if abs(candidate[0]-primary[0]) <= equality]
        if len(equivalents) > 1:
            info["ties_by_length"] += 1
        if all(existing is not primary[2] for existing in selected):
            selected.append(primary[2])

        if allow_contiguous_companion:
            # Ne pas conclure sur la continuité d'après GetPath :
            # un chemin peut couvrir 100% tandis que les arêtes natives
            # du TopRail ne couvrent que 52%. Conserver le candidat
            # suivant uniquement pour CONTRÔLE natif si un budget reste.
            # Le moteur select_contiguous_guardrail_pair validera ensuite
            # l'adjacence et la couverture des véritables Edge.Reference.
            others = [candidate for candidate in unique
                      if candidate[2] is not primary[2]]
            while others:
                extra = _closest_then_longest(
                    others, distance_equality=equality)
                others = [o for o in others if o is not extra]
                if any(existing is extra[2] for existing in selected):
                    continue
                if any(entry[2] is extra[2] for entry in second_choices):
                    continue
                second_choices.append(extra)
                break

    if allow_contiguous_companion and second_choices:
        # Les références candidates n'ont PAS encore été validées.
        # Limiter le nombre d'ouvrages inspectés, sans inventer
        # une ligne continue depuis leur simple chemin Revit.
        available_slots = max(0, int(max_railings)-len(selected))
        remaining = list(second_choices)
        while remaining and available_slots:
            extra = _closest_then_longest(
                remaining, distance_equality=equality)
            remaining = [r for r in remaining if r is not extra]
            if all(existing is not extra[2] for existing in selected):
                selected.append(extra[2])
                info["companions"] += 1
                available_slots -= 1
        if remaining:
            info["reason"] = "rail_budget"

    if len(selected) > int(max_railings):
        info["reason"] = "rail_budget"
        selected = []
    elif not selected:
        info["reason"] = "no_match"
    elif info["reason"] != "rail_budget":
        info["reason"] = "selected"
    info["selected"] = len(selected)
    return (selected, info) if with_diagnostics else selected


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



def select_contiguous_guardrail_pair(boundary, edges, tolerance,
                                     angle_degrees=3.,
                                     min_combined_overlap=.90,
                                     min_part_overlap=.25,
                                     max_gap=.32808399,
                                     max_lateral_mismatch=.0656168,
                                     max_elevation_difference=.492126,
                                     max_edges=120,
                                     distance_equality=0.):
    """Deux rails successifs peuvent constituer UNE limite exterieure.

    Toutes les distances sont en unites des segments (pieds Revit dans
    l'adaptateur). Un rail seul inferieur a 60% ne suffit PAS. Les deux
    ouvrages doivent avoir des references natives, des ElementId distincts,
    être alignes, proches, adjacents et recouvrir au moins 90% de la limite.
    La Reference retenue est celle de l'un des rails natifs ; le second
    confirme la geometrie et n'est PAS associe a la cote Revit.
    """
    import math

    available = list(edges or [])
    if len(available) > int(max_edges):
        return None
    x0, y0, x1, y1 = [float(a) for a in boundary]
    dx, dy = x1-x0, y1-y0
    length = math.sqrt(dx*dx+dy*dy)
    if length <= 1e-9:
        return None
    ux, uy = dx/length, dy/length
    nx, ny = -uy, ux

    def element_key(eid):
        for attr in ("Value", "IntegerValue"):
            try:
                return int(getattr(eid, attr))
            except Exception:
                continue
        return str(eid)

    segments = []
    for segment, reference, element_id, z in available:
        if reference is None:
            continue
        ax, ay, bx, by = [float(v) for v in segment]
        vx, vy = bx-ax, by-ay
        slen = math.sqrt(vx*vx+vy*vy)
        if slen <= 1e-9:
            continue
        angle = math.degrees(math.acos(
            min(1., max(0., abs((ux*vx+uy*vy)/slen)))))
        if angle > float(angle_degrees):
            continue
        lateral = ((ax+bx)*.5-x0)*nx + ((ay+by)*.5-y0)*ny
        if abs(lateral) > float(tolerance):
            continue
        a = max(0., min(length, (ax-x0)*ux+(ay-y0)*uy))
        b = max(0., min(length, (bx-x0)*ux+(by-y0)*uy))
        left, right = min(a,b), max(a,b)
        fraction = (right-left)/length
        if fraction < float(min_part_overlap):
            continue
        segments.append((left, right, lateral, float(z),
                         reference, element_id, angle, fraction))

    valid_pairs = []
    for i, a in enumerate(segments):
        for b in segments[i+1:]:
            if element_key(a[5]) == element_key(b[5]):
                continue
            if abs(a[2]-b[2]) > float(max_lateral_mismatch):
                continue
            if abs(a[3]-b[3]) > float(max_elevation_difference):
                continue
            first, second = sorted((a,b), key=lambda v: v[0])
            gap = max(0., second[0]-first[1])
            if gap > float(max_gap):
                continue
            overlap = max(0., min(first[1],second[1])-second[0])
            # Eviter d'interpreter deux rails presque superposes comme
            # deux portions successives distinctes.
            if overlap > .1*length:
                continue
            coverage = (a[1]-a[0]+b[1]-b[0]-overlap)/length
            if coverage + 1e-9 < float(min_combined_overlap):
                continue
            if min(a[0],b[0]) > float(max_gap):
                continue
            if length-max(a[1],b[1]) > float(max_gap):
                continue
            # La reference native est celle du rail le plus proche
            # de la limite, non automatiquement celui de la plus
            # grande portion. Egalite de distance => rail le plus long.
            keeper = _closest_then_longest([
                (abs(a[2]), a[7], a),
                (abs(b[2]), b[7], b)],
                distance_equality=distance_equality)[2]
            companion = b if keeper is a else a
            metrics = {
                "distance": abs(keeper[2]),
                "overlap_ratio": keeper[7],
                "support_count": 2,
                "combined_overlap_ratio": coverage,
                "gap": gap,
                "lateral_mismatch": abs(a[2]-b[2]),
                "companion_element_id": companion[5],
            }
            valid_pairs.append((abs(keeper[2]), keeper[7],
                                keeper[4], keeper[5], metrics))
    best = _closest_then_longest(
        valid_pairs, distance_equality=distance_equality)
    if best is None:
        return None
    return best[2], best[3], best[4]


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


def guardrail_minimum_overlap(is_exterior, ordinary=.60, exterior=.60):
    """Meme seuil pour une arête seule ; les ouvrages adjacents sont
    verifies par select_contiguous_guardrail_pair, jamais par un seuil
    individuel affaibli sans preuve de continuite.
    """
    return float(exterior if is_exterior else ordinary)
