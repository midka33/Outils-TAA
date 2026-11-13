# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Adaptateurs du moteur Plans de vente pour les vues Revit ordinaires.

Aucun code de Plans de vente n'est modifie : les controles PDV sont remplaces
uniquement dans ces sous-classes. Revit 2025.4 / pyRevit 5.x.
"""

from Autodesk.Revit import DB
from System.Collections.Generic import List
import traceback
from crash_trace import trace

from plans_vente.housing import Housing, RoomSnapshot
from dimension_service import DimensionService
from room_tag_service import RoomTagService

# Marqueur lisible dans le rapport : permet de detecter une autre copie
# de l'extension ou un cache pyRevit/IronPython encore charge.
ANNOTATIONS_BETA_REVISION = "2026-11-05-apartment-room-dedup-04"
GROUP_DIMENSIONS_BETA_REVISION = "2026-11-13-group-dimensions-01"


def id_value(element_id):
    value = getattr(element_id, "Value", None)
    return int(value if value is not None else element_id.IntegerValue)


def safe_name(element, fallback=""):
    """Element.Name est souvent inaccessible avec IronPython (Room/GroupType)."""
    if element is None:
        return fallback
    try:
        return str(DB.Element.Name.GetValue(element))
    except Exception:
        try:
            return str(element.Name)
        except Exception:
            return fallback


def room_value(room, parameter_id, fallback=""):
    """Les noms et numeros des pieces viennent des parametres Revit natifs."""
    try:
        parameter = room.get_Parameter(parameter_id)
        if parameter is not None:
            value = parameter.AsString()
            if value is not None:
                return str(value)
    except Exception:
        pass
    return fallback


def plan_compatible(view):
    return (view is not None and not view.IsTemplate and
            view.ViewType == DB.ViewType.FloorPlan)


def room_housing(rooms, key):
    snapshots = []
    for room in rooms:
        level = getattr(room, "Level", None)
        snapshots.append(RoomSnapshot(
            str(room.UniqueId),
            name=room_value(room, DB.BuiltInParameter.ROOM_NAME, ""),
            number=room_value(room, DB.BuiltInParameter.ROOM_NUMBER, ""),
            level_name=safe_name(level, ""),
        ))
    return Housing(key, snapshots)


class _GenericViewMixin(object):
    def _validate_target_view(self, view, housing_key, level_name):
        if not plan_compatible(view):
            raise ValueError("Seuls les plans d'etage non gabarits sont acceptes.")
        if safe_name(getattr(view, "GenLevel", None), "") != level_name:
            raise ValueError("Niveau de la vue different du niveau des pieces.")


class GenericRoomTags(_GenericViewMixin, RoomTagService):
    """Place la meilleure etiquette possible, avec ancrage interieur.

    Les collisions et debordements ne bloquent plus l'etiquetage dans les
    vues ordinaires : l'utilisateur ajuste ensuite la lisibilite.
    La verification du point d'ancrage interieur reste dans le moteur PDV.
    """

    def _place_one_tag(self, room, view, tag_type, candidates, probe_z,
                       occupied_boxes, padding):
        return super(GenericRoomTags, self)._place_one_tag(
            room, view, tag_type, candidates, probe_z, occupied_boxes, padding)


class GenericDimensions(_GenericViewMixin, DimensionService):
    """Adapte le placement 06F sans modifier le moteur Plans de vente."""

    def __init__(self, document):
        super(GenericDimensions, self).__init__(document)
        self.proxy_candidates = {}
        self.target_view = None
        self._guardrail_cache = {}
        self._guardrail_warnings = []
        self._guardrail_paths = {}
        self._guardrail_native_parents = {}
        self._length_fallback_room_allow = False
        self._length_fallback_reference_keys = set()

    def _stable_reference(self, reference):
        if reference is None:
            return None
        try:
            return str(reference.ConvertToStableRepresentation(self.document))
        except Exception:
            return None

    def _dimension_ownership_in_room(self, dimension, room):
        """Situer UNE cote dans une piece pour l'anti-doublon.

        Dimension.Curve est NON BORNEE dans l'API Revit : GetEndPoint
        echoue sur les dimensions lineaires. Pour une cote a un segment,
        Dimension.Origin est le milieu REEL de sa ligne de cote.
        Pour une cote non localisable, renvoyer None (verrou conservateur).
        """
        if room is None:
            return None
        # Le moteur TAA ne cree que des cotes lineaires a deux refs.
        # NumberOfSegments est 0 pour une cote a un seul segment dans
        # l'API Revit. Ne pas acceder a Segments sur une cote simple :
        # cet acces peut lever une exception .NET selon le type.
        try:
            segments_count = getattr(dimension, "NumberOfSegments", None)
            if segments_count is not None:
                if int(segments_count) > 1:
                    return None
            else:
                # Compatibilite des doubles de tests / objets externes.
                segments = getattr(dimension, "Segments", None)
                if segments is not None and int(segments.Size) > 1:
                    return None
        except Exception:
            # Sans preuve d'une dimension multi-segments, essayer Origin
            # (qui demeure le mecanisme Revit standard a un segment).
            pass
        try:
            origin = dimension.Origin
            if origin is not None:
                z = self._probe_z(room)
                return bool(room.IsPointInRoom(
                    self._xyz(float(origin.X), float(origin.Y), z)))
        except Exception:
            pass
        # Cas des doubles de test ou de courbes BORNEES seulement.
        # Revit renvoie une dimension.Curve NON BORNEE : NE PAS appeler
        # GetEndPoint dans ce cas.
        try:
            curve = dimension.Curve
            if curve is None or not curve.IsBound:
                return None
            p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
            z = self._probe_z(room)
            for fraction in (.2, .5, .8):
                point = self._xyz(
                    float(p0.X) + (float(p1.X)-float(p0.X))*fraction,
                    float(p0.Y) + (float(p1.Y)-float(p0.Y))*fraction,
                    z)
                if room.IsPointInRoom(point):
                    return True
            return False
        except Exception:
            return None

    def _existing_dimension_reference_pairs(self, room=None):
        """Identifier les cotes deja presentes par leurs references Revit.

        Une bbox partagee avec une autre piece n'est jamais une preuve
        que cette piece est deja cotee.
        """
        view = self.target_view
        if view is None:
            return set()
        result = set()
        scope_stats = {"inside": 0, "outside": 0, "unknown": 0}
        self._dimension_scope_stats = scope_stats
        try:
            dimensions = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfCategory(DB.BuiltInCategory.OST_Dimensions)
                          .WhereElementIsNotElementType().ToElements())
            for dimension in dimensions:
                try:
                    if dimension.IsHidden(view):
                        continue
                    # Le meme couple de faces peut etre cote dans une
                    # chambre VOISINE. La Reference seule ne suffit pas
                    # a deduire qu'une piece possede deja sa cote.
                    if room is not None:
                        ownership = self._dimension_ownership_in_room(
                            dimension, room)
                        if ownership is False:
                            scope_stats["outside"] += 1
                            continue
                        elif ownership is True:
                            scope_stats["inside"] += 1
                        else:
                            # Cote sans courbe lisible : ne pas inventer
                            # l'appartenance a la piece ni risquer un doublon.
                            scope_stats["unknown"] += 1
                    keys = [self._stable_reference(reference)
                            for reference in dimension.References]
                    if len(keys) == 2 and all(keys) and keys[0] != keys[1]:
                        result.add(frozenset(keys))
                except Exception:
                    continue
        except Exception:
            pass
        return result

    def _existing_proxy_dimensions(self, room=None):
        """Cotes 2D TAA identifiables par repere de 5 mm dans la vue.

        Les references natives des cotes de details ne correspondent pas
        aux references des separations de piece. Le test historique par
        paires de references ne suffit donc pas au second lancement.
        Rechercher seulement les petites DetailCurve deja referencees
        par les cotes, sans parcourir la geometrie des planchers.
        """
        view = self.target_view
        if view is None:
            return []
        found = []
        try:
            dimensions = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfCategory(DB.BuiltInCategory.OST_Dimensions)
                          .WhereElementIsNotElementType().ToElements())
        except Exception:
            return found
        maximum = self._millimeters_to_internal(10.0)
        for dim in dimensions:
            try:
                if dim.IsHidden(view):
                    continue
                if (room is not None
                        and self._dimension_ownership_in_room(
                            dim, room) is False):
                    continue
                references = list(dim.References)
                if len(references) != 2:
                    continue
                value = float(dim.Value)
                points = []
                for reference in references:
                    element = self.document.GetElement(reference.ElementId)
                    if not isinstance(element, DB.DetailCurve):
                        continue
                    curve = element.GeometryCurve
                    if not isinstance(curve, DB.Line):
                        continue
                    if curve.Length > maximum:
                        continue
                    p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
                    points.append(((float(p0.X)+float(p1.X))*.5,
                                   (float(p0.Y)+float(p1.Y))*.5))
                if points:
                    found.append((value, points))
            except Exception:
                continue
        return found

    def _pair_already_proxied(self, pair, candidates, records):
        """Sauter la portee deja cotée via une DetailLine de substitution."""
        tolerance = self._millimeters_to_internal(3.0)
        separator_centers = []
        for index in (pair.first_index, pair.second_index):
            candidate = candidates[index]
            if getattr(candidate, "source_kind", None) != "separator":
                continue
            x0, y0, x1, y1 = candidate.segment
            separator_centers.append(((x0+x1)*.5, (y0+y1)*.5))
        for measured, reference_points in records:
            if abs(measured-pair.distance) > tolerance:
                continue
            for cx, cy in separator_centers:
                if any((px-cx)**2 + (py-cy)**2 <= tolerance**2
                       for px, py in reference_points):
                    return True
        return False

    def _native_rail_solids(self, geometry, max_objects=64, max_depth=2):
        """Solides natifs, y compris les SymbolGeometry non copiees.

        Les objets sous GeometryInstance sont dans le repere du symbole :
        on applique les transforms seulement aux POINTS pour l'appariement.
        La Reference vient exclusivement de GetSymbolGeometry() SANS
        argument, jamais de GetInstanceGeometry() (copies non cotables).
        Les limites d'objets/profondeur bloquent tout parcours anormal.
        """
        counters = {"objects": 0, "instances": 0, "symbols": 0,
                    "direct_solids": 0, "symbol_solids": 0}
        def visit(items, transforms, depth):
            for obj in items:
                counters["objects"] += 1
                if counters["objects"] > max_objects:
                    raise ValueError("Budget des objets de rail depasse.")
                if isinstance(obj, DB.Solid):
                    try:
                        if obj.Volume <= 1e-12:
                            continue
                    except Exception:
                        pass
                    if transforms:
                        counters["symbol_solids"] += 1
                    else:
                        counters["direct_solids"] += 1
                    yield obj, transforms
                elif isinstance(obj, DB.GeometryInstance):
                    counters["instances"] += 1
                    if depth >= max_depth:
                        continue
                    # Récupération de la véritable géométrie symbolique ;
                    # GetSymbolGeometry(Transform) fournit une COPIE.
                    symbol = obj.GetSymbolGeometry()
                    if symbol is None:
                        continue
                    counters["symbols"] += 1
                    next_transforms = (obj.Transform,) + transforms
                    for nested in visit(symbol, next_transforms, depth+1):
                        yield nested
        return visit(geometry, (), 0), counters

    @staticmethod
    def _rail_model_point(point, transforms):
        for transform in transforms:
            point = transform.OfPoint(point)
        return point

    def _noncontinuous_rail_count(self, railing):
        """RailStructure du type Revit, sans inspection des solides."""
        try:
            rail_type = self.document.GetElement(railing.GetTypeId())
            structure = rail_type.RailStructure
            if structure is None:
                return 0
            return max(0, int(structure.GetNonContinuousRailCount()))
        except Exception:
            # Une structure non accessible ne justifie PAS de sonder
            # aveuglément les solides du garde-corps parent.
            return None

    def _bounded_noncontinuous_edges(self, room, railing,
                                     boundary_segments, max_edges=48,
                                     max_objects=16):
        """Une seule lisse non continue, seulement solides DIRECTS du GC.

        Cette lecture ne s'effectue que sur un Railing sans TopRail ni
        HandRail exploitable, et dont le type déclare au moins une lisse
        non continue. Pas de GetInstanceGeometry, pas de symboles de
        balustres, budgets distincts des 120 arêtes globales.
        """
        number = room_value(
            room, DB.BuiltInParameter.ROOM_NUMBER, str(room.UniqueId))
        ident = id_value(railing.Id)
        from common.guardrail_reference_policy import matches_guardrail_edge
        tolerance = self._millimeters_to_internal(50.)
        minimum = self._millimeters_to_internal(100.)
        options = DB.Options()
        options.ComputeReferences = True
        options.IncludeNonVisibleObjects = False
        try:
            options.DetailLevel = DB.ViewDetailLevel.Coarse
        except Exception:
            pass
        found = []
        scanned = 0
        objects = 0
        skipped_instances = 0
        trace("GUARDRAIL_NONCONTINUOUS_BEFORE",
              safe_name(self.target_view), number, "id={}".format(ident))
        try:
            geom = railing.get_Geometry(options)
            trace("GUARDRAIL_NONCONTINUOUS_AFTER",
                  safe_name(self.target_view), number, "id={}".format(ident))
            if geom is None:
                self._guardrail_warnings.append(
                    "{} : GC {} sans geometrie non continue exploitable."
                    .format(number, ident))
                return []
            for obj in geom:
                objects += 1
                if objects > max_objects:
                    raise ValueError(
                        "budget {} objets directs depasse".format(max_objects))
                if not isinstance(obj, DB.Solid):
                    skipped_instances += 1
                    continue
                try:
                    if obj.Volume <= 1.e-12:
                        continue
                except Exception:
                    pass
                for edge in obj.Edges:
                    scanned += 1
                    if scanned > max_edges:
                        raise ValueError(
                            "budget {} aretes non continues depasse"
                            .format(max_edges))
                    try:
                        reference = edge.Reference
                        if reference is None:
                            continue
                        curve = edge.AsCurve()
                        if not isinstance(curve, DB.Line):
                            continue
                        if curve.Length < minimum:
                            continue
                        p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
                        if abs(p1.Z-p0.Z) > minimum*.1:
                            continue
                        segment = (float(p0.X), float(p0.Y),
                                   float(p1.X), float(p1.Y))
                        if not any(matches_guardrail_edge(
                                boundary, segment, tolerance,
                                angle_degrees=3., minimum_overlap=.25)
                                   for boundary in boundary_segments):
                            continue
                        reference.ConvertToStableRepresentation(self.document)
                        found.append((
                            segment, reference, railing.Id,
                            (float(p0.Z)+float(p1.Z))*.5))
                        if len(found) > 12:
                            raise ValueError(
                                "budget 12 references non continues depasse")
                    except ValueError:
                        raise
                    except Exception:
                        continue
        except Exception as error:
            self._guardrail_warnings.append(
                "{} : GC {} non continu non exploitable ({}) ; "
                "repli 2D conserve.".format(number, ident, error))
            return []
        self._guardrail_warnings.append(
            "{} : GC {} non continu : {} objet(s), {} arete(s), "
            "{} reference(s) candidate(s), {} instance(s) ignoree(s)."
            .format(number, ident, objects, scanned, len(found),
                    skipped_instances))
        return found

    def _nearby_guardrail_edges(self, room, boundary_segments):
        """Références NATIVES de trois GC au plus, sans parcours global.

        Les lisses non continues du type ne sont sondées que sur
        un seul GC sans composant TopRail ou HandRail exploitable.
        Sinon, le repère 2D reste le secours.
        """
        if self.target_view is None:
            return []
        key = str(room.UniqueId)
        if key in self._guardrail_cache:
            return self._guardrail_cache[key]
        # En cas de refus ou d'ambiguite, garder le cache vide plutôt
        # que de parcourir la geometrie une deuxieme fois.
        self._guardrail_cache[key] = []
        self._guardrail_paths[key] = []
        self._guardrail_native_parents = {}
        try:
            from Autodesk.Revit.DB.Architecture import Railing
            from common.floor_reference_policy import intersects_xy
            from common.guardrail_reference_policy import (
                select_guardrails_by_path)
        except Exception:
            return []

        view = self.target_view
        try:
            box = self._bbox_xy(room.get_BoundingBox(None))
            if box is None:
                return []
            candidates = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfClass(Railing)
                          .WhereElementIsNotElementType().ToElements())
        except Exception:
            return []

        # La bbox de tout le local peut contenir plusieurs garde-corps
        # de logements voisins ; elle n'est qu'un premier filtre peu couteux.
        # GetPath donne leur trajet en plan, pas une Reference de cotation.
        # On n'extrait les solides que des chemins longeant réellement
        # les separations selectionnees pour les deux cotes principales.
        nearby = []
        margin = self._millimeters_to_internal(150.)
        for railing in candidates:
            try:
                bbox = self._bbox_xy(railing.get_BoundingBox(view))
                if intersects_xy(box, bbox, padding=margin):
                    nearby.append(railing)
                    if len(nearby) > 24:
                        self._guardrail_warnings.append(
                            "{} : trop de garde-corps dans la vue "
                            "(plus de 24) ; reperes 2D conserves.".format(
                                room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key)))
                        return []
            except Exception:
                continue
        if not nearby:
            return []

        paths = []
        count_path_segments = 0
        for railing in nearby:
            try:
                segments = []
                for curve in list(railing.GetPath() or []):
                    count_path_segments += 1
                    if count_path_segments > 80:
                        self._guardrail_warnings.append(
                            "{} : plus de 80 segments de chemin de garde-corps "
                            "; reperes 2D conserves.".format(
                                room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key)))
                        return []
                    if not isinstance(curve, DB.Line):
                        continue
                    p0, p1 = curve.GetEndPoint(0), curve.GetEndPoint(1)
                    segments.append((float(p0.X), float(p0.Y),
                                     float(p1.X), float(p1.Y)))
                paths.append((railing, segments))
            except Exception:
                # GetPath peut etre inapplicable pour un garde-corps
                # atypique. Ne surtout pas extraire sa geometrie a
                # l'aveugle apres le crash Revit deja rencontre.
                continue

        railings, selection = select_guardrails_by_path(
            paths, boundary_segments,
            tolerance=self._millimeters_to_internal(500.),
            max_railings=3, max_segments=80,
            angle_degrees=12., minimum_overlap=.30,
            ambiguity_gap=self._millimeters_to_internal(1.),
            # Un second rail n'est retenu sur une meme limite que si
            # la continuite est prouvee avant extraction native.
            allow_contiguous_companion=True,
            companion_gap=self._millimeters_to_internal(100.),
            companion_lateral=self._millimeters_to_internal(20.),
            with_diagnostics=True)
        label = room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key)
        reason = selection["reason"]
        closest = selection["closest_distance"]
        distance_text = (
            "{:.0f} mm".format(
                closest / self._millimeters_to_internal(1.0))
            if closest is not None else "aucune")
        self._guardrail_warnings.append(
            "{} : filtrage GC : {} chemin(s) dans la piece, "
            "{} limite(s), {} correspondance(s), {} egalite(s) "
            "departagee(s) par longueur, {} second(s) troncon(s) "
            "a verifier sur les aretes, plus proche {}, statut {}.".format(
                label, len(paths), selection["target_count"],
                selection["path_matches"], selection["ties_by_length"],
                selection["companions"], distance_text, reason))
        if not railings:
            self._guardrail_warnings.append(
                "{} : aucune reference GC selectionnable sur les limites "
                "(statut {}) ; reperes 2D conserves.".format(
                    label, reason))
            return []
        self._guardrail_warnings.append(
            "{} : {} garde-corps retenu(s) par leur chemin "
            "pour examen des aretes natives.".format(
                label, len(railings)))
        # La verification de couverture se fera APRES extraction.
        # Une Reference native de TopRail peut ne couvrir que 52 %
        # alors que deux chemins de garde-corps couvrent toute la limite.
        selected_ids = set(id_value(item.Id) for item in railings)
        self._guardrail_paths[key] = [
            (id_value(item.Id), list(segments))
            for item, segments in paths
            if id_value(item.Id) in selected_ids]
        options = DB.Options()
        options.ComputeReferences = True
        options.IncludeNonVisibleObjects = False
        try:
            options.DetailLevel = DB.ViewDetailLevel.Medium
        except Exception:
            pass
        # Ne pas confondre trois GC selectionnes avec trois rails
        # accessibles. Leur type peut contenir des lisses non continues,
        # non exposes par TopRail / GetHandRails.
        continuous = []
        missing = []
        seen_rail_ids = set()
        for railing in railings:
            parent_id = id_value(railing.Id)
            ids = []
            top_status = "absent"
            try:
                top_id = railing.TopRail
                if (top_id is not None and
                        top_id != DB.ElementId.InvalidElementId):
                    ids.append(top_id)
                    top_status = str(id_value(top_id))
            except Exception:
                top_status = "indisponible"
            hand_count = 0
            try:
                for hand_id in railing.GetHandRails() or []:
                    if (hand_id is not None and
                            hand_id != DB.ElementId.InvalidElementId):
                        ids.append(hand_id)
                        hand_count += 1
            except Exception:
                pass

            resolved = 0
            for rail_id in ids[:5]:
                key_id = id_value(rail_id)
                if key_id in seen_rail_ids:
                    resolved += 1
                    continue
                try:
                    element = self.document.GetElement(rail_id)
                    if element is not None:
                        continuous.append((rail_id, element))
                        self._guardrail_native_parents[key_id] = parent_id
                        seen_rail_ids.add(key_id)
                        resolved += 1
                except Exception:
                    continue

            if resolved:
                self._guardrail_warnings.append(
                    "{} : GC {} : TopRail {}, {} HandRail(s), "
                    "{} composant(s) filant(s) accessible(s).".format(
                        label, parent_id, top_status, hand_count, resolved))
            else:
                count = self._noncontinuous_rail_count(railing)
                count_text = ("indetermine" if count is None
                              else str(count))
                self._guardrail_warnings.append(
                    "{} : GC {} : TopRail {}, {} HandRail(s), "
                    "0 filant accessible, type : {} lisse(s) non "
                    "continue(s).".format(
                        label, parent_id, top_status,
                        hand_count, count_text))
                if count is not None and count > 0:
                    missing.append(railing)

        if not continuous and not missing:
            self._guardrail_warnings.append(
                "{} : aucun rail filant ni lisse non continue sondable ; "
                "reperes 2D conserves.".format(label))
            return []

        min_length = self._millimeters_to_internal(100.)
        edges = []
        inspected = 0
        max_edges = 120
        # Conserver exclusivement les References provenant de la geometrie
        # originale de l'element natif. GetInstanceGeometry() renvoie des
        # copies dont les References ne sont pas cotables dans Revit.
        for rail_id, element in continuous:
            trace("GUARDRAIL_COMPONENT_BEFORE", safe_name(view),
                  room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key),
                  "id={}".format(id_value(rail_id)))
            try:
                geometry = element.get_Geometry(options)
                trace("GUARDRAIL_COMPONENT_AFTER", safe_name(view),
                      room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key),
                      "id={}".format(id_value(rail_id)))
                if geometry is None:
                    continue
                native_solids, shape_stats = self._native_rail_solids(
                    geometry, max_objects=64, max_depth=2)
                try:
                    for solid, transforms in native_solids:
                        for edge in solid.Edges:
                            inspected += 1
                            if inspected > max_edges:
                                self._guardrail_warnings.append(
                                    "{} : plus de {} aretes des rails filants ; "
                                    "repli 2D par securite.".format(
                                        room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key),
                                        max_edges))
                                return []
                            try:
                                reference = edge.Reference
                                if reference is None:
                                    continue
                                curve = edge.AsCurve()
                                if not isinstance(curve, DB.Line):
                                    continue
                                if float(curve.Length) < min_length:
                                    continue
                                p0 = self._rail_model_point(
                                    curve.GetEndPoint(0), transforms)
                                p1 = self._rail_model_point(
                                    curve.GetEndPoint(1), transforms)
                                if abs(p1.Z-p0.Z) > min_length*.1:
                                    continue
                                reference.ConvertToStableRepresentation(self.document)
                                edges.append((
                                    (float(p0.X), float(p0.Y),
                                     float(p1.X), float(p1.Y)),
                                    reference, rail_id,
                                    (float(p0.Z)+float(p1.Z))*.5))
                            except Exception:
                                continue
                finally:
                    self._guardrail_warnings.append(
                        "{} : rail filant {} : {} instance(s), "
                        "{} symbole(s), {} solide(s) direct(s), "
                        "{} solide(s) symbolique(s).".format(
                            room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key),
                            id_value(rail_id), shape_stats["instances"],
                            shape_stats["symbols"], shape_stats["direct_solids"],
                            shape_stats["symbol_solids"]))
            except Exception as error:
                self._guardrail_warnings.append(
                    "{} : composant filant non exploitable : {}".format(
                        room_value(room, DB.BuiltInParameter.ROOM_NUMBER, key),
                        error))
                continue
        # Le rail non continu ne possède pas d'ElementId de TopRail
        # à interroger isolément. La nouvelle preuve par DEUX chemins
        # épargne cette lecture du parent pour les annexes extérieures.
        # Pour les pièces intérieures, l'ancien repli reste inchangé.
        # au plus 16 objets directs, 48 arêtes, sans GeometryInstance
        # (risque de parcourir tous les balustres) ni copie de référence.
        if len(missing) == 1 and self._is_exterior_annex(room):
            self._guardrail_warnings.append(
                "{} : GC {} sans rail filant : controle de couverture "
                "par chemins, aucun solide parent explore.".format(
                    label, id_value(missing[0].Id)))
        elif len(missing) == 1:
            if inspected >= max_edges:
                self._guardrail_warnings.append(
                    "{} : budget natif atteint, GC non continu non sonde."
                    .format(label))
            else:
                extra = self._bounded_noncontinuous_edges(
                    room, missing[0], boundary_segments,
                    max_edges=min(48, max_edges-inspected),
                    max_objects=16)
                edges.extend(extra)
        elif len(missing) > 1:
            self._guardrail_warnings.append(
                "{} : {} GC sans rail filant avec lisses non continues ; "
                "recherche parent ignoree (plus d'un GC a sonder), "
                "repli 2D conserve.".format(label, len(missing)))

        self._guardrail_warnings.append(
            "{} : {} rail(s) filant(s), {} aretes inspectees, "
            "{} reference(s) candidate(s) au total.".format(
                label, len(continuous), inspected, len(edges)))
        self._guardrail_cache[key] = edges
        return edges

    def _upgrade_separator_guardrail(self, room, candidates):
        """Pour les separations : arete de garde-corps, sinon repere 2D.

        Les faces finies de murs sont conservees ; les annexes exterieures
        ne remplacent pas une separation par une arête de dalle.
        """
        # Les murs ont deja une vraie Reference de face finie issue du
        # moteur Plans de vente. Ne JAMAIS rechercher un garde-corps
        # si les deux directions retenues sont bornees uniquement par
        # des murs. La recherche couteuse n'est autorisee que pour
        # une limite non murale encore sans Reference native de face.
        non_wall_limits = [
            item for item in candidates
            if getattr(item, "source_kind", "wall") != "wall"]
        if not non_wall_limits:
            return candidates
        remaining = [item for item in non_wall_limits
                     if getattr(item, "source_kind", "") == "separator"]
        if not remaining:
            return candidates
        from common.guardrail_reference_policy import (
            select_guardrail_edge, guardrail_tolerance_mm,
            guardrail_minimum_overlap, diagnose_guardrail_candidates,
            select_contiguous_guardrail_pair,
            select_native_edge_with_path_continuity,
            diagnose_guardrail_path_continuity,
            select_native_edge_with_path_axis_offset_recovery)
        edges = self._nearby_guardrail_edges(
            room, [item.segment for item in remaining])
        if not edges:
            return candidates
        exterior = self._is_exterior_annex(room)
        tolerance_mm = guardrail_tolerance_mm(
            exterior, ordinary_mm=self.FLOOR_EDGE_TOLERANCE_MM,
            recovery_mm=50.)
        tolerance = self._millimeters_to_internal(tolerance_mm)
        minimum_overlap = guardrail_minimum_overlap(
            exterior, ordinary=self.FLOOR_EDGE_MIN_OVERLAP_RATIO,
            exterior=self.FLOOR_EDGE_MIN_OVERLAP_RATIO)
        unit_mm = self._millimeters_to_internal(1.0)
        room_num = room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?")
        for candidate in remaining:
            path_diagnostic = None
            match = select_guardrail_edge(
                candidate.segment, edges,
                tolerance=tolerance,
                angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                minimum_overlap=minimum_overlap,
                include_metrics=True,
                distance_equality=self._millimeters_to_internal(1.))
            if match is None and exterior:
                # Deux garde-corps distincts peuvent former une seule
                # limite, chacun couvrant moins de 60%. Ne valider que
                # leur continuite, et conserver une Reference Revit native.
                match = select_contiguous_guardrail_pair(
                    candidate.segment, edges, tolerance,
                    angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                    min_combined_overlap=.90,
                    min_part_overlap=.25,
                    max_gap=self._millimeters_to_internal(100.),
                    max_lateral_mismatch=self._millimeters_to_internal(20.),
                    max_elevation_difference=self._millimeters_to_internal(150.),
                    distance_equality=self._millimeters_to_internal(1.))
            if match is None and exterior:
                # Deux chemins de garde-corps peuvent couvrir la limite
                # meme si un seul TopRail fournit une reference native.
                # La preuve reste geometrique : union projetee >=90 %,
                # 2 ouvrages distincts, peu de jour et peu de decalage.
                match = select_native_edge_with_path_continuity(
                    candidate.segment, edges,
                    self._guardrail_paths.get(str(room.UniqueId), []),
                    self._guardrail_native_parents,
                    native_tolerance=tolerance,
                    path_tolerance=self._millimeters_to_internal(500.),
                    angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                    minimum_path_coverage=.90,
                    minimum_part_coverage=.25,
                    maximum_gap=self._millimeters_to_internal(100.),
                    maximum_lateral_mismatch=self._millimeters_to_internal(20.),
                    distance_equality=self._millimeters_to_internal(1.),
                    max_railings=3, max_paths=80, max_edges=120)
                if match is None:
                    # Cas beta : deux chemins parfaitement successifs,
                    # axes decales de 20 a 40 mm par des types/placements
                    # differents, MAIS arête native a 5 mm maximum du nu.
                    # Ne PAS activer si les axes sont de part et d'autre,
                    # se superposent, presentent du jeu ou s'eloignent.
                    # La cote ne reste associee qu'a un seul garde-corps.
                    match = select_native_edge_with_path_axis_offset_recovery(
                        candidate.segment, edges,
                        self._guardrail_paths.get(str(room.UniqueId), []),
                        self._guardrail_native_parents,
                        native_tolerance=tolerance,
                        path_tolerance=self._millimeters_to_internal(500.),
                        angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                        max_relaxed_lateral=self._millimeters_to_internal(40.),
                        max_boundary_axis_offset=self._millimeters_to_internal(60.),
                        max_native_offset=self._millimeters_to_internal(5.),
                        minimum_coverage=.98,
                        maximum_overlap=.02,
                        maximum_gap=self._millimeters_to_internal(10.),
                        distance_equality=self._millimeters_to_internal(1.),
                        max_railings=3, max_paths=80, max_edges=120)
                if match is None:
                    # Les raisons du refus des chemins etaient invisibles
                    # dans l'ancien rapport, qui ne donnait que la meilleure
                    # arete native a 52 %. Aucun nouvel acces a l'API Revit :
                    # nous reutilisons strictement GetPath deja filtre.
                    path_diagnostic = diagnose_guardrail_path_continuity(
                        candidate.segment,
                        self._guardrail_paths.get(str(room.UniqueId), []),
                        path_tolerance=self._millimeters_to_internal(500.),
                        angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                        minimum_path_coverage=.90,
                        minimum_part_coverage=.25,
                        maximum_gap=self._millimeters_to_internal(100.),
                        maximum_lateral_mismatch=self._millimeters_to_internal(20.),
                        max_railings=3, max_paths=80)
            if match is None:
                if path_diagnostic is not None:
                    summary = path_diagnostic.get("best")
                    if summary is not None and unit_mm > 0:
                        parents = summary["parent_ids"]
                        spans = summary["start_end"]
                        self._guardrail_warnings.append(
                            "{} : diagnostic continuité GC {} + {} : "
                            "chemins {:.0f}-{:.0f}% / {:.0f}-{:.0f}%, "
                            "union {:.0f}%, superposition {:.0f}%, "
                            "jeu {:.0f} mm, decalage {:.0f} mm, "
                            "decalage absolu max {:.0f} mm ; "
                            "REFUS : {}. {} paire(s) evaluee(s)."
                            .format(
                                room_num, parents[0], parents[1],
                                spans[0][0]*100., spans[0][1]*100.,
                                spans[1][0]*100., spans[1][1]*100.,
                                summary["coverage"]*100.,
                                summary["overlap"]*100.,
                                summary["gap"]/unit_mm,
                                summary["lateral"]/unit_mm,
                                summary["max_boundary_offset"]/unit_mm,
                                ("chemins compatibles mais aucune arete "
                                 "native associable"
                                 if path_diagnostic["supported"]
                                 else ",".join(summary["reasons"])),
                                path_diagnostic["pair_count"]))
                    else:
                        self._guardrail_warnings.append(
                            "{} : diagnostic continuité GC : aucune paire "
                            "admissible ; statut {} ({} chemin(s), {} "
                            "segment(s), {} paire(s))."
                            .format(
                                room_num, path_diagnostic["reason"],
                                path_diagnostic["path_count"],
                                path_diagnostic["segment_count"],
                                path_diagnostic["pair_count"]))
                # Diagnostiquer les distances reelles, sans decaler les
                # references ni abaisser arbitrairement le recouvrement.
                records = diagnose_guardrail_candidates(
                    candidate.segment, edges, tolerance,
                    angle_degrees=self.FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES,
                    minimum_overlap=minimum_overlap)
                if records and unit_mm > 0:
                    near = records[0]
                    self._guardrail_warnings.append(
                        "{} : aucune arete admissible ; meilleure arete "
                        "ecart {:.1f} mm, angle {:.1f} deg, "
                        "recouvrement {:.0f}% (motifs {}).".format(
                            room_num, near["distance"]/unit_mm,
                            near["angle"], near["overlap"]*100.,
                            ",".join(near["reasons"]) or "aucun"))
                continue
            reference, railing_id, metrics = match
            candidate.reference = reference
            candidate.element_id_value = id_value(railing_id)
            candidate.length_references = None
            candidate.source_kind = "guardrail_edge"
            distance_mm = (metrics["distance"] / unit_mm
                           if unit_mm > 0 else 0.)
            self._guardrail_warnings.append(
                "{} : arete native de garde-corps utilisee, "
                "ecart de modelisation {:.1f} mm, "
                "recouvrement {:.0f}%. Cote mesuree sur l'ouvrage reel ; "
                "verifier son nu interieur et sa visibilite.".format(
                    room_num, distance_mm,
                    metrics["overlap_ratio"]*100.))
            if metrics.get("axis_offset_recovery"):
                self._guardrail_warnings.append(
                    "{} : RECUPERATION BETA du GC malgre axes decales "
                    "de {:.0f} mm (decalage max {:.0f} mm) : couverture "
                    "des deux chemins {:.0f}%, superposition {:.0f}%, "
                    "arete native a {:.1f} mm. ATTENTION : axes de "
                    "GetPath differents ; verifier EN PLAN le nu reel, "
                    "la valeur de cote et les deux ouvrages. "
                    "Association Revit a UNE arête seulement."
                    .format(
                        room_num,
                        metrics["axis_offset_gap"]/unit_mm,
                        metrics["axis_offset_max"]/unit_mm,
                        metrics["path_combined_overlap_ratio"]*100.,
                        metrics["axis_offset_overlap"]*100.,
                        distance_mm))
            if metrics.get("path_support_count") == 2:
                self._guardrail_warnings.append(
                    "{} : DEUX chemins de garde-corps alignes couvrent "
                    "{:.0f}% de la limite (jeu {:.0f} mm). "
                    "Cote associee UNIQUEMENT a l'arete native du GC {} "
                    "(couverture propre {:.0f}%). Le second GC ne pilote "
                    "pas la cote ; controle apres modification obligatoire."
                    .format(room_num,
                            metrics["path_combined_overlap_ratio"]*100.,
                            metrics["path_gap"]/unit_mm,
                            metrics["reference_parent_id"],
                            metrics["overlap_ratio"]*100.))
            if metrics.get("support_count") == 2:
                self._guardrail_warnings.append(
                    "{} : DEUX garde-corps contigus identifies : "
                    "couverture commune {:.0f}%, jeu {:.0f} mm, "
                    "decalage entre rails {:.0f} mm. Une seule "
                    "Reference Revit est utilisee pour la cote ; "
                    "surveiller les deux ouvrages apres modification."
                    .format(room_num,
                            metrics["combined_overlap_ratio"]*100.,
                            metrics["gap"]/unit_mm,
                            metrics["lateral_mismatch"]/unit_mm))
            if exterior and distance_mm > self.FLOOR_EDGE_TOLERANCE_MM:
                self._guardrail_warnings.append(
                    "{} : ecart superieur a {:.0f} mm : "
                    "rattrapage exterieur (50 mm maximum), "
                    "controle manuel de la valeur de cote obligatoire."
                    .format(room_num, self.FLOOR_EDGE_TOLERANCE_MM))
        return candidates

    def _room_boundary_candidates(self, room):
        cached = self.proxy_candidates.get(str(room.UniqueId))
        if cached is not None:
            # La preparation groupe calcule toutes les pieces avant le
            # moteur PDV. Restaurer les parametres de secours propres a
            # chacune : ne pas heriter ceux de la derniere piece preparee.
            state = getattr(self, "_group_length_fallback_state", {}).get(
                str(room.UniqueId))
            if state is not None:
                self._length_fallback_room_allow = state[0]
                self._length_fallback_reference_keys = set(state[1])
            return cached

        # Reutiliser les references de faces finies du moteur PDV.
        # Choisir les deux plus grandes portees de directions distinctes,
        # puis exclure les seules portees deja cotees dans cette vue.
        candidates = super(GenericDimensions, self)._room_boundary_candidates(room)
        from annotations.principal_dimension_axes import principal_pairs
        pairs = principal_pairs(
            [item.segment for item in candidates],
            angle_tolerance_degrees=self.ANGLE_TOLERANCE_DEGREES,
            minimum_relative_length=self.MINIMUM_RELATIVE_LENGTH,
            placement_fraction=self.PLACEMENT_FRACTION,
        )
        self._length_fallback_room_allow = len(pairs) < 2
        self._length_fallback_reference_keys = set()
        if len(pairs) < 2:
            count_native = sum(bool(
                getattr(c, "source_kind", None) == "wall" and
                getattr(c, "length_references", None))
                for c in candidates)
            self._guardrail_warnings.append(
                "{} : {} axe(s) entre faces opposees detecte(s). "
                "Recherche d'une longueur complementaire de mur "
                "avec DEUX references d'extremites natives "
                "({} mur(s) possible(s)), selon le repli Plans de vente."
                .format(
                    room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                    len(pairs), count_native))
        # Ne sonder le garde-corps que lorsque la direction retenue
        # pour une vraie dimension comporte une séparation non résolue.
        selected_indexes = set(
            index for pair in pairs
            for index in (pair.first_index, pair.second_index))
        self._upgrade_separator_guardrail(
            room, [candidates[index] for index in sorted(selected_indexes)])
        # Calculer les références DEJA cotées après substitution :
        # une cote fondée sur une vraie arête de garde-corps doit être
        # reconnue à la relance plutôt que dupliquée.
        # IMPORTANT : lire UNIQUEMENT les cotes localisees dans la
        # piece en cours. La detection historique sur la VUE ENTIERE
        # supprimait la deuxieme orientation de 2247 lorsque les
        # chambres voisines avaient deja ete cotees en mode appartement.
        # Sans geometrie de cote exploitable : protection conservative.
        existing = self._existing_dimension_reference_pairs(room)
        existing_proxy = self._existing_proxy_dimensions(room)
        indexes = set()
        # Un seul couple de murs opposes ne suffit pas pour deux
        # directions. Reprendre le SEC0URS Plans de vente : la longueur
        # d'un mur (deux references d'extremites natives), et non
        # l'invention d'une distance entre deux faces non opposees.
        # Retenir les candidats de mur, jamais les balustres, dalles ou
        # lignes de separation de piece.
        fallback_indices = []
        if len(pairs) < 2:
            for index, candidate in enumerate(candidates):
                if (getattr(candidate, "source_kind", None) != "wall"
                        or not getattr(candidate, "length_references", None)):
                    continue
                refs = [self._stable_reference(ref)
                        for ref in candidate.length_references]
                if (len(refs) != 2 or not all(refs)
                        or refs[0] == refs[1]):
                    continue
                keys = frozenset(refs)
                if keys in existing:
                    continue
                fallback_indices.append(index)
                self._length_fallback_reference_keys.add(keys)
            # Donner la RAISON observable de la seconde cote manquante :
            # un mur present dans les limites n'a pas necessairement deux
            # references d'extremites Revit utilisables. Cette ligne ne
            # declenche aucune nouvelle lecture geometrie/API.
            by_source = {}
            native_candidates = 0
            for item in candidates:
                category = getattr(item, "source_kind", "inconnu")
                by_source[category] = by_source.get(category, 0) + 1
                if (category == "wall"
                        and getattr(item, "length_references", None)):
                    native_candidates += 1
            source_summary = ", ".join(
                "{}={}".format(name, by_source[name])
                for name in sorted(by_source))
            self._guardrail_warnings.append(
                "{} : DIAGNOSTIC 2247 : {} limite(s) candidates "
                "({}), {} mur(s) avec deux references "
                "d'extremites presentes, {} secours de longueur "
                "mur autorise(s) apres filtrage anti-doublon."
                .format(
                    room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                    len(candidates), source_summary,
                    native_candidates, len(fallback_indices)))
            if not fallback_indices:
                self._guardrail_warnings.append(
                    "{} : aucune longueur de mur native complementaire "
                    "disponible : seconde cote non creee pour eviter "
                    "une fausse mesure.".format(
                        room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?")))
        ignored_existing, ignored_proxies = 0, 0
        for pair in pairs:
            refs = [self._stable_reference(candidates[index].reference)
                    for index in (pair.first_index, pair.second_index)]
            if len(refs) == 2 and all(refs) and frozenset(refs) in existing:
                ignored_existing += 1
                continue
            if self._pair_already_proxied(pair, candidates, existing_proxy):
                ignored_proxies += 1
                continue
            indexes.add(pair.first_index)
            indexes.add(pair.second_index)
        if len(pairs) >= 2:
            scope_stats = getattr(self, "_dimension_scope_stats", {})
            if scope_stats.get("outside", 0) or scope_stats.get("unknown", 0):
                self._guardrail_warnings.append(
                    "{} : COTES DEJA PRESENTES : {} dans cette piece, "
                    "{} d'autres pieces ignorees, {} a position "
                    "indeterminee conservees par securite."
                    .format(
                        room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                        scope_stats.get("inside", 0),
                        scope_stats.get("outside", 0),
                        scope_stats.get("unknown", 0)))
            self._guardrail_warnings.append(
                "{} : CONTROLE DOUBLONS PAR PIECE : {} axe(s) geometriques, "
                "{} deja cote(s) dans CETTE piece, {} deja cote(s) "
                "par reperes 2D, {} axe(s) retenu(s)."
                .format(
                    room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
                    len(pairs), ignored_existing, ignored_proxies,
                    len(pairs)-ignored_existing-ignored_proxies))
        # La re-evaluation PDV des paires n'efface pas l'identite
        # des References ; les candidats complementaires apportent
        # seulement leurs references D'EXTREMITES de mur.
        indexes.update(fallback_indices)
        selected = [candidate for index, candidate in enumerate(candidates)
                    if index in indexes]
        # Une piece ayant deux couples de faces fiables ne peut jamais
        # recevoir une cote supplementaire de longueur en relance.
        # Les longueurs deja mesurees sont elles aussi neutralisees ;
        # les References de face sont conservees.
        for candidate in selected:
            pair = getattr(candidate, "length_references", None)
            if not pair:
                continue
            refs = [self._stable_reference(ref) for ref in pair]
            if (len(pairs) >= 2 or len(refs) != 2
                    or not all(refs) or frozenset(refs) in existing):
                candidate.length_references = None
        return selected

    # Le secours par longueur conserve DESORMAIS l'implementation validee
    # de DimensionService (Plans de vente), sans override ici. Les seules
    # longueurs admises sont bornees par _room_boundary_candidates : les
    # murs avec deux References natives et sans cote deja existante.

    def _is_exterior_annex(self, room):
        """Selection du mode murs / garde-corps / 2D pour les annexes."""
        from common.guardrail_reference_policy import is_exterior_annex
        name = room_value(room, DB.BuiltInParameter.ROOM_NAME, "")
        flag = ""
        try:
            parameter = room.LookupParameter("Int/Ext")
            if parameter is not None:
                flag = parameter.AsString() or ""
        except Exception:
            pass
        return is_exterior_annex(name, flag)

    def _floor_cache_key(self, room, room_level_key):
        """Les planchers sont recherches localement PAR piece, pas par niveau."""
        return (room_level_key, str(room.UniqueId))

    @staticmethod
    def _bbox_xy(bbox):
        if bbox is None:
            return None
        try:
            return (float(bbox.Min.X), float(bbox.Min.Y),
                    float(bbox.Max.X), float(bbox.Max.Y))
        except Exception:
            return None

    def _floor_candidates(self, room, same_level, nearby_level):
        """Recherche locale bornee ; extraction geometrique reste dans PDV.

        Les deux classes appellent la meme politique de selection et le
        meme moteur natif d'arêtes. Ici seules les boites englobantes sont
        lues avant la recherche ; jamais de second passage des solides.
        """
        from common.floor_reference_policy import select_floor_candidates
        try:
            room_xy = self._bbox_xy(room.get_BoundingBox(None))
        except Exception:
            room_xy = None

        def floor_xy(floor):
            return self._bbox_xy(floor.get_BoundingBox(None))

        # Pour les annexes exterieures, la limite constructive cherchee
        # est d'abord le mur, ensuite le garde-corps ; jamais l'arete de
        # dalle en substitution silencieuse de cette limite.
        if self._is_exterior_annex(room):
            return []

        result = select_floor_candidates(
            same_level, nearby_level, mode="local",
            room_xy=room_xy, get_floor_xy=floor_xy,
            padding=self._millimeters_to_internal(300.0),
            max_floors=6)
        trace("FLOOR_CANDIDATES", "",
              room_value(room, DB.BuiltInParameter.ROOM_NUMBER, "?"),
              "local={} same={} nearby={} max=6".format(
                  len(result), len(same_level), len(nearby_level)))
        return result

    def _alignment_rails(self, view):
        """Segments des cotes Revit deja creees dans la vue.

        Chaque cote precedente peut servir de guide aux pieces voisines.
        Aucune modification de ces cotes n'est effectuee.
        """
        rails = []
        try:
            dimensions = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfCategory(DB.BuiltInCategory.OST_Dimensions)
                          .WhereElementIsNotElementType().ToElements())
            for dim in dimensions:
                try:
                    if dim.IsHidden(view):
                        continue
                    curve = dim.Curve
                    if not isinstance(curve, DB.Line):
                        continue
                    p0 = curve.GetEndPoint(0)
                    p1 = curve.GetEndPoint(1)
                    rails.append(((float(p0.X), float(p0.Y)),
                                  (float(p1.X), float(p1.Y))))
                except Exception:
                    continue
        except Exception:
            pass
        return rails

    def _view_obstacles(self, view, warnings):
        """Pour les cotes, bloquer les textes, pas tout le trait graphique.

        Une cote entre deux faces opposees doit pouvoir croiser la ligne
        d'une autre dimension. Les lignes superposees sont testees a part.
        Si la position du texte est inconnue, garder la bbox native Revit.
        """
        tags, original_dimensions, equipment = super(
            GenericDimensions, self)._view_obstacles(view, warnings)
        dimension_texts = []
        try:
            dimensions = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfCategory(DB.BuiltInCategory.OST_Dimensions)
                          .WhereElementIsNotElementType().ToElements())
        except Exception:
            return tags, original_dimensions, equipment
        paper = lambda mm: self._millimeters_to_internal(
            mm * max(1, int(view.Scale)))
        width = paper(self.PAPER_TEXT_WIDTH_MM * 1.5)
        height = paper(self.PAPER_TEXT_HEIGHT_MM * 1.5)
        for dim in dimensions:
            try:
                if dim.IsHidden(view):
                    continue
                position = dim.TextPosition
                if position is None:
                    raise ValueError("Texte inaccessible")
                # La cote peut afficher un texte horizontal ou parallele
                # a la ligne : reserver l'enveloppe des deux orientations.
                axis = (float(view.RightDirection.X),
                        float(view.RightDirection.Y))
                curve = dim.Curve
                if isinstance(curve, DB.Line):
                    direction = curve.Direction
                    other = (float(direction.X), float(direction.Y))
                else:
                    other = axis
                for dx, dy in (axis, other):
                    length = (dx * dx + dy * dy) ** .5
                    if length < 1e-9:
                        continue
                    dx, dy = dx / length, dy / length
                    nx, ny = -dy, dx
                    corners = [
                        (position.X + dx * sx * width * .5 + nx * sy * height,
                         position.Y + dy * sx * width * .5 + ny * sy * height)
                        for sx in (-1., 1.) for sy in (-1., 1.)]
                    dimension_texts.append((
                        min(p[0] for p in corners),
                        min(p[1] for p in corners),
                        max(p[0] for p in corners),
                        max(p[1] for p in corners)))
            except Exception:
                fallback = self._graphic_box(dim, view)
                if fallback is not None:
                    dimension_texts.append(fallback)
        return tags, dimension_texts, equipment

    def _plan_graphics(self, room, view, lines, anchors, tags, dimensions,
                       equipment, warnings, placement_regions=None):
        # Reprendre les memes generateurs de positions que Plans de vente.
        # Le seul changement est la selection partielle sans collision.
        from plans_vente.dimension_positioning import placement_candidates
        from annotations.dimension_alignment import (
            aligned_candidates, collinear_line_overlap)
        from annotations.strict_dimension_positioning import (
            SkippedPlacement, select_collision_free_placements)
        from annotations.inside_dimension_positioning import (
            select_inside_placements, line_inside_room,
            text_anchor_inside_room)

        if not lines:
            return []
        scale = max(1, int(view.Scale))
        paper = lambda mm: self._millimeters_to_internal(mm * scale)
        settings = dict(
            clearance=paper(self.PAPER_CLEARANCE_MM),
            text_width=paper(self.PAPER_TEXT_WIDTH_MM),
            text_height=paper(self.PAPER_TEXT_HEIGHT_MM),
            padding=paper(self.PAPER_PADDING_MM),
            witness_length=paper(self.PAPER_WITNESS_MM),
        )
        try:
            points = self._placement_room_points(room)
            probe_z = self._probe_z(room)
            cache = {}

            def contains(xy):
                xy = (float(xy[0]), float(xy[1]))
                if xy not in cache:
                    cache[xy] = bool(room.IsPointInRoom(
                        self._xyz(xy[0], xy[1], probe_z)))
                return cache[xy]

            text_axis = (float(view.RightDirection.X),
                         float(view.RightDirection.Y))
            rails = self._alignment_rails(view)
            # Un voisin au-dela de 25 mm papier n'est pas un rail de
            # cotation local ; tol. de coincidence 0,25 mm papier.
            near_gap = paper(25.)
            snap_tolerance = paper(.25)
            regions = placement_regions or [None] * len(lines)
            groups = []
            for line, anchor, region in zip(lines, anchors, regions):
                group = placement_candidates(
                    line, region or points, contains,
                    tag_boxes=tags, dimension_boxes=dimensions,
                    equipment_boxes=equipment, witness_anchors=anchor,
                    text_axis=text_axis, **settings)
                for candidate in group:
                    candidate.text_inside = all(
                        contains(point) for polygon in candidate.text_polygons
                        for point in polygon)
                group.extend(aligned_candidates(
                    line, region or points, rails, contains, settings,
                    tag_boxes=tags, dimension_boxes=dimensions,
                    equipment_boxes=equipment, witness_anchors=anchor,
                    text_axis=text_axis, max_neighbor_gap=near_gap))
                # Bloquer un vrai recouvrement colineaire avec une cote
                # deja presente, mais autoriser le croisement ponctuel.
                for candidate in group:
                    if collinear_line_overlap(
                            (candidate.line_start, candidate.line_end),
                            rails, offset_tolerance=paper(.5)):
                        candidate.dimension_hits += 1
                groups.append(group)

            chosen = select_collision_free_placements(
                groups, rails=rails, max_neighbor_gap=near_gap,
                snap_tolerance=snap_tolerance)
            # Exigence agence : DEUX cotes INTERIEURES par piece
            # des que les deux orientations possedent des References
            # Revit reelles. En espace exigu, le texte et les temoins
            # peuvent se superposer, mais la ligne de cote et son
            # point d'ancrage restent toujours dans la piece.
            #
            # Le mode classique n'est conserve que s'il remplit deja
            # ces criteres : sinon effectuer un second choix parmi les
            # memes candidats de Plans de vente, SANS repli exterieur.
            classic_usable = (
                len(chosen) == len(lines)
                and all(
                    not isinstance(item, SkippedPlacement)
                    and line_inside_room(item, contains)
                    and text_anchor_inside_room(item, contains)
                    for item in chosen)
            )
            if not classic_usable:
                try:
                    inner = select_inside_placements(groups, contains)
                    before = sum(not isinstance(item, SkippedPlacement)
                                 for item in chosen)
                    after = sum(not isinstance(item, SkippedPlacement)
                                for item in inner)
                    # Une cote retenue doit etre INTERIEURE, meme quand
                    # le calcul strict contenait deja 2 cotes exterieures.
                    chosen = inner
                    warnings.append(
                        "{} : COTATION INTERIEURE : {} / {} axe(s) "
                        "place(s) a l'interieur (ancien choix : {}). "
                        "Superposition autorisee si manque de place ; "
                        "valeurs et textes a verifier visuellement."
                        .format(self._room_label(room), after,
                                len(lines), before))
                except Exception as error:
                    # Le choix precedent peut comporter des cotes a
                    # l'exterieur : ne pas les accepter silencieusement.
                    warnings.append(
                        "{} : choix interieur impossible ({}), "
                        "cotes exterieures refusees."
                        .format(self._room_label(room), error))
                    chosen = [SkippedPlacement(
                        "placement interieur indisponible")
                        for _ in lines]
            for i, choice in enumerate(chosen):
                if isinstance(choice, SkippedPlacement):
                    group = groups[i]
                    if group:
                        min_tags = min(c.tag_hits for c in group)
                        min_dims = min(c.dimension_hits for c in group)
                        inside = sum(int(c.text_inside) for c in group)
                        eligible = sum(not c.tag_hits and not c.dimension_hits
                                       for c in group)
                        interior = sum(int(line_inside_room(c, contains)
                                           and text_anchor_inside_room(c, contains))
                                       for c in group)
                        detail = ("{} position(s) (dont {} ligne(s) interieures), "
                                  "{} texte(s) dans piece, {} candidate(s) "
                                  "sans obstacle preexistant, minimum "
                                  "{} collision(s) etiquette, {} cote(s). "
                                  "Conflit possible entre les textes des "
                                  "deux orientations ou traits paralleles"
                                  ).format(
                                      len(group), interior, inside, eligible,
                                      min_tags, min_dims)
                    else:
                        detail = "aucun candidat de placement"
                    warnings.append(
                        "{} : orientation {} ignoree : {} ({})".format(
                            self._room_label(room), i + 1, choice.reason,
                            detail))
            return chosen
        except Exception as error:
            # Ne jamais utiliser silencieusement la position 06E non verifiee
            # pour ces commandes ayant promis l'absence de collision.
            warnings.append(
                "{} : cotations ignorees, calcul des positions impossible : {}".
                format(self._room_label(room), error))
            return [SkippedPlacement("calcul graphique indisponible")
                    for _ in lines]

    def _create_dimension(self, view, dimension_type, first_reference,
                          second_reference, line_start, line_end, room):
        if line_start is None or line_end is None:
            raise ValueError("Orientation ignoree : aucun placement sans collision.")
        return super(GenericDimensions, self)._create_dimension(
            view, dimension_type, first_reference, second_reference,
            line_start, line_end, room)


class AnnotationService(object):
    """Cotation / etiquetage independants sur vues existantes.

    Les groupes sont traites de facon atomique. Si l'API refuse le detail
    attache, l'ensemble des elements ajoutes au groupe est annule.
    """

    def __init__(self, document):
        self.doc = document
        self.tags = GenericRoomTags(document)
        self.dims = GenericDimensions(document)

    def list_views(self):
        return sorted([
            v for v in DB.FilteredElementCollector(self.doc).OfClass(
                DB.ViewPlan).WhereElementIsNotElementType().ToElements()
            if plan_compatible(v)
        ], key=lambda v: safe_name(v).lower())

    def list_types(self, kind):
        return (self.tags.list_tag_types() if kind == "tags"
                else self.dims.list_dimension_types())

    def line_styles(self):
        result = []
        for style in DB.FilteredElementCollector(self.doc).OfClass(
                DB.GraphicsStyle).ToElements():
            try:
                if (style.GraphicsStyleType == DB.GraphicsStyleType.Projection
                        and style.GraphicsStyleCategory.Parent.Id ==
                        DB.ElementId(DB.BuiltInCategory.OST_Lines)):
                    result.append(style)
            except Exception:
                continue
        return sorted(result, key=lambda x: safe_name(x).lower())

    def _rooms(self, view):
        collector = (DB.FilteredElementCollector(self.doc, view.Id)
                     .OfCategory(DB.BuiltInCategory.OST_Rooms)
                     .WhereElementIsNotElementType())
        result = []
        for room in collector.ToElements():
            try:
                if room.Area > 0 and room.Level.Id == view.GenLevel.Id:
                    result.append(room)
            except Exception:
                continue
        return sorted(result, key=lambda x: (x.Number or "", id_value(x.Id)))

    def _elements(self, view, kind):
        category = (DB.BuiltInCategory.OST_RoomTags if kind == "tags"
                    else DB.BuiltInCategory.OST_Dimensions)
        return list(DB.FilteredElementCollector(self.doc, view.Id)
                    .OfCategory(category)
                    .WhereElementIsNotElementType().ToElements())

    def _ids(self, view, kind):
        return set(id_value(e.Id) for e in self._elements(view, kind))

    def _not_yet_tagged(self, view, rooms):
        ids = self.tags._already_tagged_room_ids(
            self.tags._existing_room_tags(view))
        return [room for room in rooms if self.tags._room_tag_identity(room) not in ids]

    def _not_yet_dimensioned(self, view, rooms):
        # Ne PAS exclure toute une piece des qu'une cote touche sa bbox.
        # Cela empechait d'ajouter l'axe manquant lors d'un second lancement.
        # GenericDimensions._room_boundary_candidates compare les references
        # des deux portees principales avec celles des cotes deja posees.
        filtered = []
        for room in rooms:
            try:
                if room.get_BoundingBox(view) is not None:
                    filtered.append(room)
            except Exception:
                continue
        return filtered

    def _create_proxies(self, view, rooms, group, line_style):
        """5 mm sur la face finie des parois exterieures au groupe.

        Les references sont volontairement non associatives avec ces parois.
        """
        if line_style is None:
            raise ValueError("Choisir le style des lignes 2D de reference.")
        member_ids = set(id_value(x) for x in group.GetMemberIds())
        created = []
        tx = DB.Transaction(self.doc, "TAA - References 2D")
        tx.Start()
        try:
            for room in rooms:
                candidates = self.dims._room_boundary_candidates(room)
                from plans_vente.dimension_geometry import dominant_dimension_pairs
                segments = [c.segment for c in candidates]
                pairs = dominant_dimension_pairs(
                    segments,
                    angle_tolerance_degrees=self.dims.ANGLE_TOLERANCE_DEGREES,
                    minimum_relative_length=self.dims.MINIMUM_RELATIVE_LENGTH,
                    placement_fraction=self.dims.PLACEMENT_FRACTION,
                    max_results=2)
                required = set()
                for pair in pairs:
                    required.add(pair.first_index)
                    required.add(pair.second_index)
                # Interdire les references de longueur de murs hors groupe.
                for index, c in enumerate(candidates):
                    if c.element_id_value not in member_ids:
                        c.length_references = None
                for index, c in enumerate(candidates):
                    if index not in required or c.element_id_value in member_ids:
                        continue
                    x0, y0, x1, y1 = c.segment
                    dx, dy = x1-x0, y1-y0
                    length = (dx*dx + dy*dy)**0.5
                    if length < 1e-7:
                        continue
                    half = min(length * 0.25, DB.UnitUtils.ConvertToInternalUnits(
                        2.5, DB.UnitTypeId.Millimeters))
                    mx, my = (x0+x1)*0.5, (y0+y1)*0.5
                    ux, uy = dx/length, dy/length
                    z = room.Level.Elevation
                    line = DB.Line.CreateBound(
                        DB.XYZ(mx-ux*half, my-uy*half, z),
                        DB.XYZ(mx+ux*half, my+uy*half, z))
                    detail = self.doc.Create.NewDetailCurve(view, line)
                    detail.LineStyle = line_style
                    self.doc.Regenerate()
                    # Une cote native doit pointer vers la geometrie de la ligne.
                    ref = detail.GeometryCurve.Reference
                    if ref is None:
                        raise ValueError("Reference de ligne 2D indisponible.")
                    c.reference = ref
                    c.element_id_value = id_value(detail.Id)
                    c.length_references = None
                    c.source_kind = "proxy"
                    created.append(detail.Id)
                key = str(room.UniqueId)
                self.dims.proxy_candidates[key] = candidates
                self.dims._group_length_fallback_state[key] = (
                    bool(self.dims._length_fallback_room_allow),
                    set(self.dims._length_fallback_reference_keys))
            tx.Commit()
            return created
        except Exception:
            tx.RollBack()
            raise

    def _create_separator_proxies(self, view, rooms, line_style):
        """References 2D uniquement si la limite de piece est une separation.

        On conserve la geometrie des faces opposees choisies par PDV.
        Une petite DetailLine est creee sur chaque separation necessaire ;
        la cote pointe sur sa Reference native, jamais sur la separation.
        Ces lignes ne sont pas liees au mur ou a la dalle : en cas de
        modification architecturale, les cotes doivent etre revues.
        """
        if line_style is None:
            raise ValueError("Choisir un style visible pour les reperes 2D.")

        created = []
        tx = DB.Transaction(self.doc, "TAA - Reperes 2D separations")
        tx.Start()
        try:
            for room in rooms:
                candidates = list(self.dims._room_boundary_candidates(room))
                pending = []
                for candidate in candidates:
                    if getattr(candidate, "source_kind", None) != "separator":
                        continue
                    x0, y0, x1, y1 = candidate.segment
                    dx, dy = x1-x0, y1-y0
                    length = (dx*dx + dy*dy)**.5
                    if length < 1e-7:
                        raise ValueError("Separation de longueur nulle.")
                    # Segment court de 5 mm, centre sur la limite finie.
                    half = min(length * .25,
                               DB.UnitUtils.ConvertToInternalUnits(
                                   2.5, DB.UnitTypeId.Millimeters))
                    mx, my = (x0+x1)*.5, (y0+y1)*.5
                    ux, uy = dx/length, dy/length
                    z = float(room.Level.Elevation)
                    curve = DB.Line.CreateBound(
                        DB.XYZ(mx-ux*half, my-uy*half, z),
                        DB.XYZ(mx+ux*half, my+uy*half, z))
                    detail = self.doc.Create.NewDetailCurve(view, curve)
                    if detail is None:
                        raise ValueError("Creation du repere 2D impossible.")
                    detail.LineStyle = line_style
                    pending.append((candidate, detail))
                    created.append(detail.Id)

                if pending:
                    self.doc.Regenerate()
                    for candidate, detail in pending:
                        reference = detail.GeometryCurve.Reference
                        if reference is None:
                            raise ValueError(
                                "Reference native de repere 2D indisponible.")
                        candidate.reference = reference
                        candidate.element_id_value = id_value(detail.Id)
                        candidate.length_references = None
                        candidate.source_kind = "proxy"
                # Memoriser AUSSI les references toutes natives.
                # Sinon create_dimensions relance _room_boundary_candidates
                # une seconde fois et duplique les diagnostics GC.
                # Cache limite a cette seule piece / TransactionGroup,
                # nettoye dans _run_unit.finally (pas de persistance).
                self.dims.proxy_candidates[str(room.UniqueId)] = candidates

            tx.Commit()
            return created
        except Exception:
            tx.RollBack()
            raise

    def _cleanup_unused_group_proxies(self, view, proxy_ids, dimension_ids):
        """Ne rattacher au groupe que les reperes effectivement cotes.

        Une reference Revit incertaine interdit de supprimer les lignes :
        annuler le TransactionGroup au lieu de laisser un repere orphelin.
        """
        if not proxy_ids:
            return []
        if not dimension_ids:
            raise RuntimeError(
                "Aucune cote creee : annulation des reperes du groupe.")
        used = set()
        for dimension in self._elements(view, "dims"):
            if id_value(dimension.Id) not in dimension_ids:
                continue
            references = getattr(dimension, "References", None)
            if references is None:
                raise RuntimeError(
                    "References de cote groupe non verifiables.")
            for reference in references:
                used.add(id_value(reference.ElementId))
        kept = [element_id for element_id in proxy_ids
                if id_value(element_id) in used]
        unused = [element_id for element_id in proxy_ids
                  if id_value(element_id) not in used]
        if unused:
            tx = DB.Transaction(self.doc, "TAA - Nettoyer reperes groupe")
            tx.Start()
            try:
                for element_id in unused:
                    self.doc.Delete(element_id)
                tx.Commit()
            except Exception:
                tx.RollBack()
                raise
        return kept

    def _cleanup_unused_separator_proxies(self, view, proxy_ids, dimension_ids):
        """Ne pas laisser de lignes 2D non utilisees apres cotation partielle.

        Si les references de cotes ne peuvent pas etre relues, lever une
        erreur : la TransactionGroup appelante annule tout sans residu.
        """
        if not proxy_ids:
            return
        used = set()
        for dimension in self._elements(view, "dims"):
            if id_value(dimension.Id) not in dimension_ids:
                continue
            references = dimension.References
            if references is None:
                raise RuntimeError("References de cote non verifiables.")
            for reference in references:
                used.add(id_value(reference.ElementId))

        unused = [element_id for element_id in proxy_ids
                  if id_value(element_id) not in used]
        if not dimension_ids:
            raise RuntimeError(
                "Aucune cote creee : annulation des reperes 2D.")
        if len(unused) == len(proxy_ids):
            raise RuntimeError(
                "Aucune cote n'utilise les reperes 2D : annulation de securite.")
        if unused:
            tx = DB.Transaction(self.doc, "TAA - Nettoyer reperes 2D inutilises")
            tx.Start()
            try:
                for element_id in unused:
                    self.doc.Delete(element_id)
                tx.Commit()
            except Exception:
                tx.RollBack()
                raise

    def _available_type(self, group, kind):
        prefix = "TAA - Etiquettes" if kind == "tags" else "TAA - Cotations"
        for tid in group.GetAvailableAttachedDetailGroupTypeIds():
            typ = self.doc.GetElement(tid)
            if typ and safe_name(typ).startswith(prefix):
                return tid
        return None

    def _attach(self, group, view, annotation_ids, proxy_ids, kind, previous):
        ids = List[DB.ElementId]()
        ids.Add(group.Id)
        for item in annotation_ids:
            ids.Add(item)
        for item in proxy_ids:
            ids.Add(item)
        tx = DB.Transaction(self.doc, "TAA - Groupe de details attaches")
        tx.Start()
        try:
            original_members = set(id_value(x) for x in group.GetMemberIds())
            original_type = id_value(group.GetTypeId())
            created = self.doc.Create.NewGroup(ids)
            self.doc.Regenerate()
            # Le NewGroup mixte peut creer une nouvelle structure de groupe
            # de modele au lieu d'attacher des details au groupe existant.
            # Ne jamais valider une telle transformation silencieusement.
            if created is None or not created.IsValidObject:
                raise RuntimeError(
                    "Revit n'a pas cree de groupe valide : annulation.")
            # NewGroup renvoie un groupe de modele lorsque des elements
            # de modele et des annotations sont fournis. Son identite
            # peut donc correspondre a celle du groupe existant.
            # Ne pas conclure a un echec a partir de l'Id retourne :
            # verifier les nouveaux details attaches et leurs membres.
            returned_group_id = id_value(created.Id)
            parent_group_id = id_value(group.Id)
            # Comparer les valeurs numeriques uniquement, mais conserver
            # les vrais ElementId fournis par l'API Revit pour GetElement.
            # Revit 2025 / IronPython n'accepte pas un int a sa place.
            available_type_ids = {
                id_value(element_id): element_id
                for element_id in group.GetAvailableAttachedDetailGroupTypeIds()
            }
            available = set(available_type_ids)
            new_ids = available - previous
            if (not group.IsValidObject or
                    id_value(group.GetTypeId()) != original_type or
                    set(id_value(x) for x in group.GetMemberIds()) != original_members):
                raise RuntimeError(
                    "Le groupe initial serait modifie : annulation de securite.")
            if not new_ids:
                raise RuntimeError(
                    "Aucun nouveau type de details attaches apres NewGroup "
                    "(retour {}, parent {}, types avant {}, apres {})."
                    .format(returned_group_id, parent_group_id,
                            len(previous), len(available)))
            if len(new_ids) != 1:
                raise RuntimeError(
                    "Plusieurs types de details attaches crees : annulation.")
            group_type_id = available_type_ids[next(iter(new_ids))]
            if self.doc.GetElement(group_type_id) is None:
                raise RuntimeError(
                    "Type de details attaches introuvable : annulation.")
            # La creation d'un type attache est insuffisante : une instance
            # effectivement rattachee au groupe initial doit etre retrouvee.
            # Chercher aussi les groupes attaches non encore affiches
            # dans la vue. Le collector limite a view.Id peut exclure
            # une instance masquee juste apres sa creation.
            attached_instances = [
                item for item in DB.FilteredElementCollector(self.doc)
                .OfClass(DB.Group).WhereElementIsNotElementType().ToElements()
                if bool(getattr(item, "IsAttached", False))
                and id_value(item.GetTypeId()) == id_value(group_type_id)
                and id_value(item.AttachedParentId) == parent_group_id
            ]
            if not attached_instances:
                raise RuntimeError(
                    "Nouveau type trouve, mais aucun groupe de details "
                    "n'est attache au parent {} : annulation."
                    .format(parent_group_id))
            # Le nouveau groupe doit contenir les annotations produites.
            # Un type disponible sans ses etiquettes ne suffit pas.
            grouped_members = set()
            for attached in attached_instances:
                grouped_members.update(id_value(member)
                                       for member in attached.GetMemberIds())
            expected_members = set(
                id_value(item) for item in list(annotation_ids) + list(proxy_ids))
            missing = expected_members - grouped_members
            if missing:
                raise RuntimeError(
                    "{} element(s) de details (cotes ou reperes) "
                    "non rattache(s) au groupe parent {} : annulation."
                    .format(len(missing), parent_group_id))
            name = ("TAA - Etiquettes" if kind == "tags" else "TAA - Cotations")
            name += " - {}".format(safe_name(group.GroupType, "Groupe"))
            self.doc.GetElement(group_type_id).Name = name
            tx.Commit()
            return group_type_id
        except Exception:
            tx.RollBack()
            raise

    def _show(self, group, view, type_id):
        tx = DB.Transaction(self.doc, "TAA - Afficher details attaches")
        tx.Start()
        try:
            group.ShowAttachedDetailGroups(view, type_id)
            tx.Commit()
        except Exception:
            tx.RollBack()
            raise

    def _run_unit(self, view, rooms, kind, annotation_type_id, group, line_style):
        room_set = (self._not_yet_tagged(view, rooms) if kind == "tags"
                    else self._not_yet_dimensioned(view, rooms))
        if not room_set:
            return 0, ["{} : annotations deja presentes ou vues non cotables.".format(
                safe_name(group.GroupType, "Groupe") if group else safe_name(view))]
        name = safe_name(group.GroupType, "Groupe") if group else "hors groupe"
        room_id = room_value(room_set[0], DB.BuiltInParameter.ROOM_NUMBER, "?")
        trace("ROOM_START", safe_name(view), room_id, kind)
        scope = DB.TransactionGroup(self.doc, "TAA {} - {}".format(kind, name))
        scope.Start()
        self.dims.proxy_candidates = {}
        self.dims._group_length_fallback_state = {}
        self.dims._guardrail_cache = {}
        self.dims._guardrail_warnings = []
        self.dims._guardrail_paths = {}
        self.dims._guardrail_native_parents = {}
        self.dims._length_fallback_room_allow = False
        self.dims._length_fallback_reference_keys = set()
        self.dims.target_view = view
        try:
            before = self._ids(view, kind)
            existing_attached = (
                set(id_value(x) for x in group.GetAvailableAttachedDetailGroupTypeIds())
                if group else set())
            proxy_ids = []
            separator_proxy_ids = []
            if kind == "dims" and group:
                proxy_ids = self._create_proxies(view, room_set, group, line_style)
            elif kind == "dims":
                trace("BEFORE_SEPARATOR_PROXY", safe_name(view), room_id)
                separator_proxy_ids = self._create_separator_proxies(
                    view, room_set, line_style)
                trace("AFTER_SEPARATOR_PROXY", safe_name(view), room_id,
                      "count={}".format(len(separator_proxy_ids)))
            housing = room_housing(room_set, name)
            if kind == "tags":
                # Les etiquettes evitent toute l'emprise des cotes ;
                # seule la cotation autorise les croisements de traits.
                dims = DimensionService._view_obstacles(self.dims, view, [])[1]
                result = self.tags.create_tags(
                    housing, str(view.UniqueId), annotation_type_id,
                    exclusion_boxes=dims)
            else:
                trace("BEFORE_DIMENSION_ENGINE", safe_name(view), room_id,
                      "references/geometry/transactions")
                result = self.dims.create_dimensions(
                    housing, str(view.UniqueId), annotation_type_id)
                trace("AFTER_DIMENSION_ENGINE", safe_name(view), room_id,
                      "created={}".format(result.created_count))
            new_ids = self._ids(view, kind) - before
            if group and kind == "dims":
                proxy_ids = self._cleanup_unused_group_proxies(
                    view, proxy_ids, new_ids)
            if group and new_ids:
                self._attach(group, view,
                             [e.Id for e in self._elements(view, kind)
                              if id_value(e.Id) in new_ids],
                             proxy_ids, kind, existing_attached)
            elif group and proxy_ids:
                raise RuntimeError("Aucune cote native produite : references annulees.")
            if separator_proxy_ids:
                self._cleanup_unused_separator_proxies(
                    view, separator_proxy_ids, new_ids)
            scope.Assimilate()
            trace("ROOM_COMMITTED", safe_name(view), room_id,
                  "created={}".format(len(new_ids)))
            messages = list(result.warnings) + list(self.dims._guardrail_warnings)
            if separator_proxy_ids:
                messages.append(
                    "{} : reperes 2D utilises a la place des separations "
                    "de piece ; garder leur style visible dans la vue. "
                    "Cotes non associatives : verification apres "
                    "modification de la loggia.".format(room_id))
            return len(new_ids), messages
        except Exception as exc:
            trace("ROOM_EXCEPTION", safe_name(view), room_id,
                  "{}: {}".format(type(exc).__name__, exc))
            scope.RollBack()
            return 0, ["{} / {} : annule sans annotation isolee ({}: {}).\n{}".format(
                safe_name(view, "Vue"), name, type(exc).__name__, exc,
                traceback.format_exc())]
        finally:
            self.dims.proxy_candidates = {}
            self.dims._group_length_fallback_state = {}
            self.dims._guardrail_cache = {}
            self.dims._guardrail_warnings = []
            self.dims._guardrail_paths = {}
            self.dims._guardrail_native_parents = {}
            self.dims._length_fallback_room_allow = False
            self.dims._length_fallback_reference_keys = set()
            self.dims.target_view = None

    def run(self, kind, views, annotation_type_id, line_style=None,
            diagnostic_room_uid=None, diagnostic_room_uids=None,
            diagnostic_group_uid=None):
        """Cotation beta : une piece, un appartement ou un groupe confirme.

        Une seule vue par lancement, jamais toute la vue en mode cotation.
        Un groupe : un seul groupe de modele (1 a 12 pieces) dans
        un TransactionGroup atomique, avec details attaches verifies.
        """
        report, total = [], 0
        if kind == "dims":
            report.append("REVISION COTATION BETA : {}".format(
                ANNOTATIONS_BETA_REVISION))
        apartment_mode = kind == "dims" and diagnostic_room_uids is not None
        group_mode = kind == "dims" and diagnostic_group_uid is not None
        expected_ids = None
        if kind == "dims":
            # Crash historique : le mode multi-vues et les groupes de
            # masse restent interdits. Groupe individuel teste uniquement
            # par choix explicite ; l'appartement reste hors groupes.
            if len(views) != 1:
                raise ValueError(
                    "Mode beta cotation : une seule vue par lancement.")
            if apartment_mode:
                if diagnostic_room_uid is not None or group_mode:
                    raise ValueError(
                        "Choisir UNE piece, UN appartement OU UN groupe.")
                expected_ids = [str(x) for x in diagnostic_room_uids]
                if (len(expected_ids) < 2 or len(expected_ids) > 12
                        or any(not x for x in expected_ids)
                        or len(set(expected_ids)) != len(expected_ids)):
                    raise ValueError(
                        "Appartement invalide : 2 a 12 pieces distinctes requises.")
                report.append(
                    "MODE BETA APPARTEMENT : {} pieces dans une seule vue ; "
                    "une transaction et un journal par piece ; "
                    "aucun groupe Revit.".format(len(expected_ids)))
            elif group_mode:
                if diagnostic_room_uid is not None:
                    raise ValueError(
                        "Choisir UN groupe OU UNE piece, jamais les deux.")
                if not str(diagnostic_group_uid or ""):
                    raise ValueError("Identifiant de groupe manquant.")
                report.append(
                    "MODE BETA GROUPE : {} ; UNE seule occurrence, "
                    "UNE vue, 12 pieces maximum ; aucun traitement "
                    "des autres groupes.".format(GROUP_DIMENSIONS_BETA_REVISION))
            elif not diagnostic_room_uid:
                raise ValueError(
                    "Mode diagnostic obligatoire : une vue et une piece."
                )
        trace("RUN_START", "", "", kind)
        for view in views:
            if not plan_compatible(view):
                report.append("{} : vue incompatible.".format(safe_name(view, "Vue")))
                continue
            try:
                rooms = self._rooms(view)
            except Exception as exc:
                report.append("{} : lecture pieces impossible : {}: {}\n{}".format(
                    safe_name(view, "Vue"), type(exc).__name__, exc, traceback.format_exc()))
                continue
            if kind == "dims":
                if apartment_mode:
                    selected = set(expected_ids)
                    rooms = [room for room in rooms
                             if str(room.UniqueId) in selected]
                    if len(rooms) != len(expected_ids):
                        raise ValueError(
                            "Perimetre appartement modifie depuis l'apercu : "
                            "{} pieces trouvees sur {}. Aucune cote creee."
                            .format(len(rooms), len(expected_ids)))
                    if any(room.GroupId != DB.ElementId.InvalidElementId
                           for room in rooms):
                        raise ValueError(
                            "Appartement contenant une piece en groupe : "
                            "aucune cote creee. Les groupes attaches "
                            "restent suspendus apres crash.")
                elif group_mode:
                    # Selection explicite : ne jamais coter les autres groupes
                    # de la meme vue au cours d'un essai beta.
                    candidates = []
                    for room in rooms:
                        if room.GroupId == DB.ElementId.InvalidElementId:
                            continue
                        group = self.doc.GetElement(room.GroupId)
                        if group is not None and (
                                str(group.UniqueId) == str(diagnostic_group_uid)):
                            candidates.append(room)
                    if not candidates or len(candidates) > 12:
                        raise ValueError(
                            "Perimetre groupe modifie ou introuvable "
                            "(1 a 12 pieces) : aucune cote creee.")
                    rooms = candidates
                else:
                    rooms = [room for room in rooms
                             if str(room.UniqueId) == diagnostic_room_uid]
                    if len(rooms) != 1:
                        raise ValueError("Piece choisie introuvable dans la vue.")
                    if rooms[0].GroupId != DB.ElementId.InvalidElementId:
                        raise ValueError(
                            "Groupe interdit en mode piece hors groupe ; "
                            "choisir le mode beta groupe.")
            grouped, singles = {}, []
            for room in rooms:
                gid = room.GroupId
                if gid == DB.ElementId.InvalidElementId:
                    singles.append(room)
                else:
                    grp = self.doc.GetElement(gid)
                    if grp is not None:
                        grouped.setdefault(id_value(grp.Id), (grp, []))[1].append(room)
                    else:
                        report.append("{} : groupe introuvable.".format(room.Number))
            report.append("{} : {} piece(s) dans la vue, {} dans un groupe, {} hors groupe.".format(
                safe_name(view, "Vue"), len(rooms), len(rooms)-len(singles), len(singles)))
            # Isoler toutes les pieces de l'appartement. Si une transaction
            # echoue techniquement, les precedentes restent valides,
            # les nouvelles de la piece echouee sont annulees et la boucle
            # s'arrete pour ne pas reproduire le meme crash.
            for index, room in enumerate(singles):
                count, warnings = self._run_unit(
                    view, [room], kind, annotation_type_id, None, line_style)
                total += count
                report.extend(warnings)
                if apartment_mode:
                    label = room_value(
                        room, DB.BuiltInParameter.ROOM_NUMBER,
                        str(room.UniqueId))
                    report.append(
                        "APPARTEMENT : piece {} ({}/{}) : "
                        "{} annotation(s) creee(s).".format(
                            label, index+1, len(singles), count))
                    if any("annule sans annotation isolee" in str(w)
                           for w in warnings):
                        remaining = len(singles) - index - 1
                        report.append(
                            "ARRET PREVENTIF : echec technique sur {}. "
                            "{} piece(s) restante(s) non traitee(s). "
                            "Verifier le journal avant reprise."
                            .format(label, remaining))
                        trace("BATCH_STOP", safe_name(view), label,
                              "remaining={}".format(remaining))
                        break
            # Etiquetage : traitements groupes valides dans Revit.
            # Cotation : UN SEUL groupe explicitement confirme en beta,
            # aucun autre groupe de la vue ne peut etre touche.
            for key in sorted(grouped):
                group, room_set = grouped[key]
                existing = self._available_type(group, kind)
                if existing is not None:
                    try:
                        self._show(group, view, existing)
                        report.append("{} : details attaches reutilises.".format(
                            safe_name(group.GroupType, "Groupe")))
                    except Exception as exc:
                        report.append("{} : impossible d'afficher : {}".format(
                            safe_name(group.GroupType, "Groupe"), exc))
                    continue
                count, warnings = self._run_unit(
                    view, room_set, kind, annotation_type_id, group, line_style)
                total += count
                report.extend(warnings)
                if group_mode:
                    report.append(
                        "GROUPE BETA : {} piece(s), {} cote(s) creee(s), "
                        "groupe {}.".format(
                            len(room_set), count,
                            safe_name(group.GroupType, "Groupe")))
        trace("RUN_END", "", "", "created={}".format(total))
        return total, report
