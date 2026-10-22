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
    """Meme moteur geometrique; echec plutot qu'etiquette en collision."""

    def _place_one_tag(self, room, view, tag_type, candidates, probe_z,
                       occupied_boxes, padding):
        result = super(GenericRoomTags, self)._place_one_tag(
            room, view, tag_type, candidates, probe_z, occupied_boxes, padding)
        if not result[2] or result[3]:
            raise ValueError("Aucune position interieure sans chevauchement.")
        return result


class GenericDimensions(_GenericViewMixin, DimensionService):
    """Adapte le placement 06F sans modifier le moteur Plans de vente."""

    def __init__(self, document):
        super(GenericDimensions, self).__init__(document)
        self.proxy_candidates = {}
        self.target_view = None

    def _stable_reference(self, reference):
        if reference is None:
            return None
        try:
            return str(reference.ConvertToStableRepresentation(self.document))
        except Exception:
            return None

    def _existing_dimension_reference_pairs(self):
        """Identifier les cotes deja presentes par leurs references Revit.

        Une bbox partagee avec une autre piece n'est jamais une preuve
        que cette piece est deja cotee.
        """
        view = self.target_view
        if view is None:
            return set()
        result = set()
        try:
            dimensions = (DB.FilteredElementCollector(self.document, view.Id)
                          .OfCategory(DB.BuiltInCategory.OST_Dimensions)
                          .WhereElementIsNotElementType().ToElements())
            for dimension in dimensions:
                try:
                    if dimension.IsHidden(view):
                        continue
                    keys = [self._stable_reference(reference)
                            for reference in dimension.References]
                    if len(keys) == 2 and all(keys) and keys[0] != keys[1]:
                        result.add(frozenset(keys))
                except Exception:
                    continue
        except Exception:
            pass
        return result

    def _room_boundary_candidates(self, room):
        cached = self.proxy_candidates.get(str(room.UniqueId))
        if cached is not None:
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
        existing = self._existing_dimension_reference_pairs()
        indexes = set()
        for pair in pairs:
            refs = [self._stable_reference(candidates[index].reference)
                    for index in (pair.first_index, pair.second_index)]
            if len(refs) == 2 and all(refs) and frozenset(refs) in existing:
                continue
            indexes.add(pair.first_index)
            indexes.add(pair.second_index)
        return [candidate for index, candidate in enumerate(candidates)
                if index in indexes]

    def _fallback_length_indexes(self, boundary_candidates, pairs):
        # Aucune longueur de mur en remplacement des portees opposees.
        return []

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
            for i, choice in enumerate(chosen):
                if isinstance(choice, SkippedPlacement):
                    group = groups[i]
                    if group:
                        min_tags = min(c.tag_hits for c in group)
                        min_dims = min(c.dimension_hits for c in group)
                        inside = sum(int(c.text_inside) for c in group)
                        detail = ("{} position(s), {} texte(s) dans piece,"
                                  " minimum {} collision(s) etiquette,"
                                  " {} cote(s)").format(
                                      len(group), inside, min_tags, min_dims)
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
                    c.length_references = None
                    c.source_kind = "proxy"
                    created.append(detail.Id)
                self.dims.proxy_candidates[str(room.UniqueId)] = candidates
            tx.Commit()
            return created
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
            available = set(id_value(x) for x in
                            group.GetAvailableAttachedDetailGroupTypeIds())
            new_ids = available - previous
            if (not group.IsValidObject or
                    id_value(group.GetTypeId()) != original_type or
                    set(id_value(x) for x in group.GetMemberIds()) != original_members):
                raise RuntimeError(
                    "Le groupe initial serait modifie : annulation de securite.")
            if not new_ids:
                raise RuntimeError(
                    "L'API n'a pas cree de groupe de details attache au groupe initial.")
            group_type_id = self.doc.GetElement(next(iter(new_ids))).Id
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
        self.dims.target_view = view
        try:
            before = self._ids(view, kind)
            existing_attached = (
                set(id_value(x) for x in group.GetAvailableAttachedDetailGroupTypeIds())
                if group else set())
            proxy_ids = []
            if kind == "dims" and group:
                proxy_ids = self._create_proxies(view, room_set, group, line_style)
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
            if group and new_ids:
                self._attach(group, view,
                             [e.Id for e in self._elements(view, kind)
                              if id_value(e.Id) in new_ids],
                             proxy_ids, kind, existing_attached)
            elif group and proxy_ids:
                raise RuntimeError("Aucune cote native produite : references annulees.")
            scope.Assimilate()
            trace("ROOM_COMMITTED", safe_name(view), room_id,
                  "created={}".format(len(new_ids)))
            return len(new_ids), list(result.warnings)
        except Exception as exc:
            trace("ROOM_EXCEPTION", safe_name(view), room_id,
                  "{}: {}".format(type(exc).__name__, exc))
            scope.RollBack()
            return 0, ["{} / {} : annule sans annotation isolee ({}: {}).\n{}".format(
                safe_name(view, "Vue"), name, type(exc).__name__, exc,
                traceback.format_exc())]
        finally:
            self.dims.proxy_candidates = {}
            self.dims.target_view = None

    def run(self, kind, views, annotation_type_id, line_style=None,
            diagnostic_room_uid=None):
        report, total = [], 0
        if kind == "dims":
            # Crash 2026-10-22 : le traitement de masse est suspendu.
            if not diagnostic_room_uid or len(views) != 1:
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
                rooms = [room for room in rooms
                         if str(room.UniqueId) == diagnostic_room_uid]
                if len(rooms) != 1:
                    raise ValueError("Piece choisie introuvable dans la vue.")
                if rooms[0].GroupId != DB.ElementId.InvalidElementId:
                    raise ValueError(
                        "Groupes attaches suspendus en diagnostic apres crash.")
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
            # Une piece impossible n'annule pas toutes les autres pieces du plan.
            for room in singles:
                count, warnings = self._run_unit(
                    view, [room], kind, annotation_type_id, None, line_style)
                total += count
                report.extend(warnings)
            # Reutiliser le type de detail deja cree pour les autres occurrences.
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
        trace("RUN_END", "", "", "created={}".format(total))
        return total, report
