# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Adaptateurs du moteur Plans de vente pour les vues Revit ordinaires.

Aucun code de Plans de vente n'est modifie : les controles PDV sont remplaces
uniquement dans ces sous-classes. Revit 2025.4 / pyRevit 5.x.
"""

from Autodesk.Revit import DB
from System.Collections.Generic import List
import traceback

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
        if getattr(getattr(view, "GenLevel", None), "Name", None) != level_name:
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
    """Conserve les references et les regles de cotation de Plans de vente."""

    def __init__(self, document):
        super(GenericDimensions, self).__init__(document)
        self.proxy_candidates = {}

    def _room_boundary_candidates(self, room):
        cached = self.proxy_candidates.get(str(room.UniqueId))
        if cached is not None:
            return cached
        return super(GenericDimensions, self)._room_boundary_candidates(room)

    def _plan_graphics(self, room, view, lines, anchors, tags, dimensions,
                       equipment, warnings, placement_regions=None):
        result = super(GenericDimensions, self)._plan_graphics(
            room, view, lines, anchors, tags, dimensions, equipment, warnings,
            placement_regions=placement_regions)
        if any((placement.outside_count or placement.tag_hits or
                placement.dimension_hits or any(
                    "collision" in message.lower() or
                    "croisement" in message.lower()
                    for message in placement.warnings)) for placement in result):
            raise ValueError("Aucune position de cote sans collision.")
        return result


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
        # Choix conservateur : ne pas ajouter un jeu de cotes dans une piece
        # ayant deja une cote dont l'emprise intersecte la piece.
        existing = self._elements(view, "dims")
        filtered = []
        for room in rooms:
            bounds = room.get_BoundingBox(view)
            if bounds is None:
                continue
            used = False
            for dim in existing:
                try:
                    bbox = dim.get_BoundingBox(view)
                    if (bbox and bbox.Max.X > bounds.Min.X and
                            bbox.Min.X < bounds.Max.X and
                            bbox.Max.Y > bounds.Min.Y and
                            bbox.Min.Y < bounds.Max.Y):
                        used = True
                        break
                except Exception:
                    pass
            if not used:
                filtered.append(room)
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
                    ref = DB.Reference(detail)
                    if ref is None:
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
        scope = DB.TransactionGroup(self.doc, "TAA {} - {}".format(kind, name))
        scope.Start()
        self.dims.proxy_candidates = {}
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
                dims = self.dims._view_obstacles(view, [])[1]
                result = self.tags.create_tags(
                    housing, str(view.UniqueId), annotation_type_id,
                    exclusion_boxes=dims)
            else:
                result = self.dims.create_dimensions(
                    housing, str(view.UniqueId), annotation_type_id)
            new_ids = self._ids(view, kind) - before
            if group and new_ids:
                self._attach(group, view,
                             [e.Id for e in self._elements(view, kind)
                              if id_value(e.Id) in new_ids],
                             proxy_ids, kind, existing_attached)
            elif group and proxy_ids:
                raise RuntimeError("Aucune cote native produite : references annulees.")
            scope.Assimilate()
            return len(new_ids), list(result.warnings)
        except Exception as exc:
            scope.RollBack()
            return 0, ["{} / {} : annule sans annotation isolee ({}: {}).\n{}".format(
                safe_name(view, "Vue"), name, type(exc).__name__, exc,
                traceback.format_exc())]
        finally:
            self.dims.proxy_candidates = {}

    def run(self, kind, views, annotation_type_id, line_style=None):
        report, total = [], 0
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
        return total, report
