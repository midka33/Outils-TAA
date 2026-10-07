# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Étape 06 — cotations principales des pièces."""

DIMENSION_SERVICE_BUILD = "stage06e-dimensions-floor-edge-substitution-v5"

import math

from common.transaction import RevitTransaction
from plans_vente.dimension_geometry import (
    dominant_dimension_pairs,
    representative_length_indexes,
    segment_match_metrics,
)
from plans_vente.tag_positioning import polygon_area


class DimensionTypeCandidate(object):
    def __init__(self, unique_id, name, element_id_value=None):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.element_id_value = element_id_value

    @property
    def label(self):
        if self.name:
            return self.name
        if self.element_id_value is not None:
            return "Type de cote #{}".format(self.element_id_value)
        return "Type de cote"


class DimensionViewCandidate(object):
    def __init__(self, unique_id, name, level_name, scale=0):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.level_name = level_name or ""
        self.scale = int(scale or 0)

    @property
    def label(self):
        scale = "1:{}".format(self.scale) if self.scale else "échelle inconnue"
        return "{} — {}".format(self.name, scale)


class DimensionCreationResult(object):
    def __init__(
        self,
        housing_key,
        view_name,
        dimension_type_name,
        created_count,
        room_count,
        full_room_count=0,
        partial_room_count=0,
        skipped_room_count=0,
        warnings=None,
    ):
        self.housing_key = housing_key or ""
        self.view_name = view_name or ""
        self.dimension_type_name = dimension_type_name or ""
        self.created_count = int(created_count or 0)
        self.room_count = int(room_count or 0)
        self.full_room_count = int(full_room_count or 0)
        self.partial_room_count = int(partial_room_count or 0)
        self.skipped_room_count = int(skipped_room_count or 0)
        self.warnings = list(warnings or [])

    @property
    def warning_count(self):
        return len(self.warnings)


class _BoundaryReferenceCandidate(object):
    def __init__(
        self,
        segment,
        reference,
        element_id_value,
        length_references=None,
        source_kind="wall",
    ):
        self.segment = segment
        self.reference = reference
        self.element_id_value = element_id_value
        self.length_references = length_references
        self.source_kind = source_kind


class DimensionService(object):
    """Service Revit de l'Étape 06."""

    ANGLE_TOLERANCE_DEGREES = 5.0
    MINIMUM_RELATIVE_LENGTH = 0.25
    PLACEMENT_FRACTION = 0.25
    LENGTH_DIRECTION_TOLERANCE_DEGREES = 12.0
    LENGTH_OFFSET_MM = 180.0

    FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES = 3.0
    FLOOR_EDGE_TOLERANCE_MM = 20.0
    FLOOR_EDGE_MIN_OVERLAP_RATIO = 0.60
    FLOOR_LEVEL_TOLERANCE_MM = 500.0
    FLOOR_EDGE_MIN_LENGTH_MM = 100.0

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.build_id = DIMENSION_SERVICE_BUILD
        self._floor_edge_cache = {}

    def list_dimension_types(self):
        from Autodesk.Revit.DB import (
            DimensionStyleType,
            DimensionType,
            FilteredElementCollector,
        )

        result = []
        for dimension_type in (
            FilteredElementCollector(self.document)
            .OfClass(DimensionType)
            .WhereElementIsElementType()
            .ToElements()
        ):
            try:
                style_type = dimension_type.StyleType
            except Exception:
                continue

            allowed = [DimensionStyleType.Linear]
            linear_fixed = getattr(DimensionStyleType, "LinearFixed", None)
            if linear_fixed is not None:
                allowed.append(linear_fixed)
            if style_type not in allowed:
                continue

            result.append(
                DimensionTypeCandidate(
                    unique_id=str(
                        getattr(dimension_type, "UniqueId", "") or ""
                    ),
                    name=self._element_type_name(dimension_type),
                    element_id_value=self._element_id_value(dimension_type.Id),
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def target_views_for_housing(self, housing):
        level_name = self._single_level_name(housing)

        from Autodesk.Revit.DB import (
            ElementId,
            FilteredElementCollector,
            ViewPlan,
            ViewType,
        )

        prefix = "PDV PROTO - {} - ".format(housing.key)
        result = []

        for view in (
            FilteredElementCollector(self.document)
            .OfClass(ViewPlan)
            .WhereElementIsNotElementType()
            .ToElements()
        ):
            if bool(getattr(view, "IsTemplate", False)):
                continue
            if getattr(view, "ViewType", None) != ViewType.FloorPlan:
                continue

            level = getattr(view, "GenLevel", None)
            if getattr(level, "Name", None) != level_name:
                continue

            try:
                if view.GetPrimaryViewId() == ElementId.InvalidElementId:
                    continue
            except Exception:
                continue

            name = str(getattr(view, "Name", "") or "")
            if not name.startswith(prefix):
                continue

            result.append(
                DimensionViewCandidate(
                    unique_id=str(getattr(view, "UniqueId", "") or ""),
                    name=name,
                    level_name=level_name,
                    scale=int(getattr(view, "Scale", 0) or 0),
                )
            )

        return sorted(result, key=lambda item: item.name.lower())

    def create_dimensions(
        self,
        housing,
        target_view_unique_id,
        dimension_type_unique_id,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        level_name = self._single_level_name(housing)
        view = self._get_element(
            target_view_unique_id,
            "Sélectionnez une vue logement.",
        )
        dimension_type = self._get_element(
            dimension_type_unique_id,
            "Sélectionnez un type de cote.",
        )

        self._validate_target_view(view, housing.key, level_name)
        if not self._is_linear_dimension_type(dimension_type):
            raise ValueError(
                "Le type sélectionné n'est pas un type de cote linéaire."
            )

        room_plans = []
        warnings = []

        for unique_id in housing.room_unique_ids:
            room = self.document.GetElement(unique_id)
            if room is None:
                warnings.append(
                    "Une pièce du logement n'existe plus : {}.".format(unique_id)
                )
                continue

            boundary_candidates = self._room_boundary_candidates(room)
            segments = [candidate.segment for candidate in boundary_candidates]
            pairs = dominant_dimension_pairs(
                segments,
                angle_tolerance_degrees=self.ANGLE_TOLERANCE_DEGREES,
                minimum_relative_length=self.MINIMUM_RELATIVE_LENGTH,
                placement_fraction=self.PLACEMENT_FRACTION,
                max_results=2,
            )

            fallback_indexes = self._fallback_length_indexes(
                boundary_candidates,
                pairs,
            )
            room_plans.append(
                (room, boundary_candidates, pairs, fallback_indexes)
            )

        created_count = 0
        full_room_count = 0
        partial_room_count = 0
        skipped_room_count = 0

        for room, boundary_candidates, pairs, fallback_indexes in room_plans:
            room_label = self._room_label(room)
            room_created = 0
            used_length_indexes = set()

            try:
                with RevitTransaction(
                    self.document,
                    "Plans de vente - Cotations {} - {}".format(
                        housing.key,
                        room_label,
                    ),
                ):
                    for pair in pairs:
                        if room_created >= 2:
                            break
                        first = boundary_candidates[pair.first_index]
                        second = boundary_candidates[pair.second_index]
                        try:
                            dimension = self._create_dimension(
                                view,
                                dimension_type,
                                first.reference,
                                second.reference,
                                pair.line_start,
                                pair.line_end,
                                room,
                            )
                            if dimension is not None:
                                room_created += 1
                        except Exception as error:
                            warnings.append(
                                "{} : cote entre faces opposées non créée ({})".format(
                                    room_label,
                                    str(error) or repr(error),
                                )
                            )

                    for index in fallback_indexes:
                        if room_created >= 2:
                            break
                        if index in used_length_indexes:
                            continue

                        candidate = boundary_candidates[index]
                        if not candidate.length_references:
                            continue

                        used_length_indexes.add(index)
                        try:
                            line_start, line_end = self._length_dimension_line(
                                candidate,
                                room,
                            )
                            dimension = self._create_dimension(
                                view,
                                dimension_type,
                                candidate.length_references[0],
                                candidate.length_references[1],
                                line_start,
                                line_end,
                                room,
                            )
                            if dimension is not None:
                                room_created += 1
                        except Exception as error:
                            warnings.append(
                                "{} : cote de longueur de secours non créée ({})".format(
                                    room_label,
                                    str(error) or repr(error),
                                )
                            )
            except Exception as error:
                warnings.append(
                    "{} : transaction de cotation annulée ({})".format(
                        room_label,
                        str(error) or repr(error),
                    )
                )
                room_created = 0

            created_count += room_created
            if room_created >= 2:
                full_room_count += 1
            elif room_created == 1:
                partial_room_count += 1
                warnings.append(
                    "{} : une seule dimension principale fiable a pu être créée.".format(
                        room_label
                    )
                )
            else:
                skipped_room_count += 1
                warnings.append(
                    "{} : aucune dimension principale fiable n'a pu être créée.".format(
                        room_label
                    )
                )

        return DimensionCreationResult(
            housing_key=housing.key,
            view_name=str(getattr(view, "Name", "") or ""),
            dimension_type_name=self._element_type_name(dimension_type),
            created_count=created_count,
            room_count=len(room_plans),
            full_room_count=full_room_count,
            partial_room_count=partial_room_count,
            skipped_room_count=skipped_room_count,
            warnings=warnings,
        )

    def _fallback_length_indexes(self, boundary_candidates, pairs):
        segments = [candidate.segment for candidate in boundary_candidates]
        result = []

        # Avec une seule paire parallèle, sa plus longue limite fournit une
        # longueur complémentaire naturelle à la distance entre les deux faces.
        if len(pairs) == 1:
            pair = pairs[0]
            pair_indexes = [pair.first_index, pair.second_index]
            pair_indexes.sort(
                key=lambda index: self._segment_length(
                    boundary_candidates[index].segment
                ),
                reverse=True,
            )
            for index in pair_indexes:
                if boundary_candidates[index].length_references:
                    result.append(index)

        # Sans deux familles parallèles, on complète par les longueurs de murs
        # dominantes, en évitant deux directions quasi parallèles.
        for index in representative_length_indexes(
            segments,
            angle_tolerance_degrees=self.LENGTH_DIRECTION_TOLERANCE_DEGREES,
            max_results=max(4, len(segments)),
        ):
            if index not in result:
                result.append(index)

        # Dernier filet de sécurité : garder aussi les autres limites longues
        # munies de références d'extrémité.
        remaining = list(range(len(boundary_candidates)))
        remaining.sort(
            key=lambda index: self._segment_length(
                boundary_candidates[index].segment
            ),
            reverse=True,
        )
        for index in remaining:
            if (
                index not in result
                and boundary_candidates[index].length_references
            ):
                result.append(index)

        return result

    def _room_boundary_candidates(self, room):
        from Autodesk.Revit.DB import (
            Line,
            SpatialElementBoundaryLocation,
            SpatialElementBoundaryOptions,
            Wall,
        )

        options = SpatialElementBoundaryOptions()
        options.SpatialElementBoundaryLocation = (
            SpatialElementBoundaryLocation.Finish
        )

        loops = []
        for segment_loop in room.GetBoundarySegments(options) or []:
            area_points = []
            raw_segments = []

            for boundary_segment in segment_loop or []:
                curve = boundary_segment.GetCurve()
                if curve is None:
                    continue

                for point in list(curve.Tessellate() or []):
                    xy = (float(point.X), float(point.Y))
                    if not area_points or (
                        abs(xy[0] - area_points[-1][0]) > 1e-9
                        or abs(xy[1] - area_points[-1][1]) > 1e-9
                    ):
                        area_points.append(xy)

                if isinstance(curve, Line):
                    raw_segments.append((boundary_segment, curve))

            if (
                len(area_points) > 1
                and abs(area_points[0][0] - area_points[-1][0]) <= 1e-9
                and abs(area_points[0][1] - area_points[-1][1]) <= 1e-9
            ):
                area_points = area_points[:-1]

            if len(area_points) >= 3:
                loops.append(
                    (
                        abs(polygon_area(area_points)),
                        raw_segments,
                    )
                )

        if not loops:
            return []

        loops.sort(key=lambda item: item[0], reverse=True)
        raw_segments = loops[0][1]
        result = []

        for boundary_segment, curve in raw_segments:
            try:
                host = self.document.GetElement(boundary_segment.ElementId)
            except Exception:
                host = None
            if host is None:
                continue

            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            segment = (
                float(start.X),
                float(start.Y),
                float(end.X),
                float(end.Y),
            )

            if isinstance(host, Wall):
                midpoint = curve.Evaluate(0.5, True)
                direction = curve.Direction
                reference = self._nearest_finish_face_reference(
                    host,
                    midpoint,
                    direction,
                )
                if reference is None:
                    continue

                length_references = self._length_endpoint_references(
                    host,
                    reference,
                    curve,
                )

                result.append(
                    _BoundaryReferenceCandidate(
                        segment=segment,
                        reference=reference,
                        element_id_value=self._element_id_value(host.Id),
                        length_references=length_references,
                    )
                )
                continue

            # Une ligne de séparation de pièce est une vraie limite de pièce.
            # Elle doit participer à la recherche des deux dimensions
            # principales, même si elle n'est pas portée par un mur.
            reference = self._room_separator_reference(host)
            if reference is None:
                continue

            # On utilise la séparation comme référence de distance, mais pas
            # comme longueur de secours : la courbe de séparation peut dépasser
            # la portion réellement utilisée par la pièce.
            result.append(
                _BoundaryReferenceCandidate(
                    segment=segment,
                    reference=reference,
                    element_id_value=self._element_id_value(host.Id),
                    length_references=None,
                )
            )

        return result

    def _room_separator_reference(self, element):
        from Autodesk.Revit.DB import BuiltInCategory, ElementId

        category = getattr(element, "Category", None)
        if category is None:
            return None

        try:
            expected = ElementId(BuiltInCategory.OST_RoomSeparationLines)
            if category.Id != expected:
                return None
        except Exception:
            return None

        # Les séparations de pièces sont des CurveElement / ModelCurve.
        # GeometryCurve.Reference fournit la référence géométrique utilisable
        # par une cote linéaire.
        try:
            geometry_curve = element.GeometryCurve
            reference = geometry_curve.Reference
            if reference is not None:
                return reference
        except Exception:
            pass

        return None

    def _nearest_finish_face_reference(self, wall, midpoint, tangent):
        from Autodesk.Revit.DB import (
            HostObjectUtils,
            PlanarFace,
            ShellLayerType,
        )

        references = []
        for side in (ShellLayerType.Interior, ShellLayerType.Exterior):
            try:
                references.extend(
                    list(HostObjectUtils.GetSideFaces(wall, side) or [])
                )
            except Exception:
                continue

        best = None
        for reference in references:
            try:
                face = wall.GetGeometryObjectFromReference(reference)
            except Exception:
                face = None
            if face is None or not isinstance(face, PlanarFace):
                continue

            try:
                normal = face.FaceNormal.Normalize()
                direction = tangent.Normalize()
            except Exception:
                continue

            if abs(float(normal.Z)) > 0.2:
                continue
            if abs(float(normal.DotProduct(direction))) > 0.1:
                continue

            try:
                vector = midpoint.Subtract(face.Origin)
                distance = abs(float(vector.DotProduct(normal)))
            except Exception:
                continue

            if best is None or distance < best[0]:
                best = (distance, reference)

        return best[1] if best is not None else None

    def _length_endpoint_references(self, wall, finish_reference, boundary_curve):
        # Certains Curve issus de Revit exposent directement des références
        # d'extrémité utilisables. On les privilégie.
        try:
            first = boundary_curve.GetEndPointReference(0)
            second = boundary_curve.GetEndPointReference(1)
            if first is not None and second is not None:
                return (first, second)
        except Exception:
            pass

        # Les BoundarySegment de pièce ne portent généralement pas de
        # références d'extrémité exploitables. On recharge donc la géométrie
        # réelle du mur avec ComputeReferences=True, puis on retrouve la face
        # latérale la plus proche de la limite finie de la pièce.
        face = self._computed_side_face_with_references(
            wall,
            boundary_curve,
        )
        if face is None:
            return None

        start = boundary_curve.GetEndPoint(0)
        end = boundary_curve.GetEndPoint(1)

        try:
            bbox = wall.get_BoundingBox(None)
            wall_height = max(
                0.0,
                float(bbox.Max.Z - bbox.Min.Z),
            ) if bbox is not None else 0.0
        except Exception:
            wall_height = 0.0

        edge_candidates = []
        try:
            edge_loops = list(face.EdgeLoops or [])
        except Exception:
            edge_loops = []

        for edge_loop in edge_loops:
            for edge in edge_loop:
                try:
                    edge_curve = edge.AsCurve()
                    p0 = edge_curve.GetEndPoint(0)
                    p1 = edge_curve.GetEndPoint(1)
                    reference = edge.Reference
                except Exception:
                    continue

                if reference is None:
                    continue

                dx = float(p1.X - p0.X)
                dy = float(p1.Y - p0.Y)
                dz = abs(float(p1.Z - p0.Z))
                xy = math.sqrt((dx * dx) + (dy * dy))

                # Les références recherchées sont les arêtes verticales qui
                # matérialisent les extrémités de la face de finition en plan.
                if dz <= 1e-9:
                    continue
                if xy > max(1e-6, dz * 0.05):
                    continue
                if wall_height > 1e-9 and dz < (wall_height * 0.35):
                    continue

                x = (float(p0.X) + float(p1.X)) * 0.5
                y = (float(p0.Y) + float(p1.Y)) * 0.5
                edge_candidates.append((x, y, reference))

        if len(edge_candidates) < 2:
            return None

        first = self._nearest_xy_reference(edge_candidates, start)
        second = self._nearest_xy_reference(
            edge_candidates,
            end,
            excluded_reference=first,
        )
        if first is None or second is None:
            return None
        return (first, second)

    def _computed_side_face_with_references(self, wall, boundary_curve):
        from Autodesk.Revit.DB import (
            GeometryInstance,
            Options,
            PlanarFace,
            Solid,
            ViewDetailLevel,
        )

        options = Options()
        options.ComputeReferences = True
        options.IncludeNonVisibleObjects = False
        try:
            options.DetailLevel = ViewDetailLevel.Fine
        except Exception:
            pass

        try:
            geometry = wall.get_Geometry(options)
        except Exception:
            geometry = None
        if geometry is None:
            return None

        try:
            midpoint = boundary_curve.Evaluate(0.5, True)
            direction = boundary_curve.Direction.Normalize()
        except Exception:
            return None

        best = None
        for solid in self._geometry_solids(
            geometry,
            Solid,
            GeometryInstance,
        ):
            try:
                faces = list(solid.Faces or [])
            except Exception:
                faces = []

            for face in faces:
                if not isinstance(face, PlanarFace):
                    continue

                try:
                    reference = face.Reference
                    normal = face.FaceNormal.Normalize()
                except Exception:
                    continue
                if reference is None:
                    continue

                # Face latérale verticale et parallèle à la limite de pièce.
                if abs(float(normal.Z)) > 0.2:
                    continue
                if abs(float(normal.DotProduct(direction))) > 0.1:
                    continue

                try:
                    vector = midpoint.Subtract(face.Origin)
                    distance = abs(float(vector.DotProduct(normal)))
                except Exception:
                    continue

                if best is None or distance < best[0]:
                    best = (distance, face)

        return best[1] if best is not None else None

    def _geometry_solids(self, geometry, solid_type, instance_type):
        for geometry_object in geometry:
            if isinstance(geometry_object, solid_type):
                try:
                    if geometry_object.Volume > 1e-12:
                        yield geometry_object
                except Exception:
                    yield geometry_object
                continue

            if isinstance(geometry_object, instance_type):
                try:
                    nested = geometry_object.GetInstanceGeometry()
                except Exception:
                    nested = None
                if nested is None:
                    continue

                for solid in self._geometry_solids(
                    nested,
                    solid_type,
                    instance_type,
                ):
                    yield solid

    @staticmethod
    def _nearest_xy_reference(
        candidates,
        point,
        excluded_reference=None,
    ):
        best = None
        for x_value, y_value, reference in candidates:
            if (
                excluded_reference is not None
                and reference == excluded_reference
            ):
                continue
            dx = x_value - float(point.X)
            dy = y_value - float(point.Y)
            distance = (dx * dx) + (dy * dy)
            if best is None or distance < best[0]:
                best = (distance, reference)
        return best[1] if best is not None else None

    def _length_dimension_line(self, candidate, room):
        segment = candidate.segment
        dx = float(segment[2]) - float(segment[0])
        dy = float(segment[3]) - float(segment[1])
        length = math.sqrt((dx * dx) + (dy * dy))
        if length <= 1e-12:
            raise RuntimeError("Segment de longueur nulle.")

        tangent = (dx / length, dy / length)
        normal = (-tangent[1], tangent[0])
        offset = self._millimeters_to_internal(self.LENGTH_OFFSET_MM)

        midpoint = (
            (float(segment[0]) + float(segment[2])) * 0.5,
            (float(segment[1]) + float(segment[3])) * 0.5,
        )
        probe_z = self._probe_z(room)

        sign = 0.0
        for candidate_sign in (1.0, -1.0):
            point = self._xyz(
                midpoint[0] + (normal[0] * offset * candidate_sign),
                midpoint[1] + (normal[1] * offset * candidate_sign),
                probe_z,
            )
            try:
                if bool(room.IsPointInRoom(point)):
                    sign = candidate_sign
                    break
            except Exception:
                continue

        shift_x = normal[0] * offset * sign
        shift_y = normal[1] * offset * sign

        return (
            (
                float(segment[0]) + shift_x,
                float(segment[1]) + shift_y,
            ),
            (
                float(segment[2]) + shift_x,
                float(segment[3]) + shift_y,
            ),
        )

    def _create_dimension(
        self,
        view,
        dimension_type,
        first_reference,
        second_reference,
        line_start,
        line_end,
        room,
    ):
        from Autodesk.Revit.DB import Line, ReferenceArray, XYZ

        level = getattr(room, "Level", None)
        z_value = float(getattr(level, "Elevation", 0.0) or 0.0)

        start = XYZ(
            float(line_start[0]),
            float(line_start[1]),
            z_value,
        )
        end = XYZ(
            float(line_end[0]),
            float(line_end[1]),
            z_value,
        )

        dimension_line = Line.CreateBound(start, end)
        references = ReferenceArray()
        references.Append(first_reference)
        references.Append(second_reference)

        return self.document.Create.NewDimension(
            view,
            dimension_line,
            references,
            dimension_type,
        )

    def _validate_target_view(self, view, housing_key, level_name):
        from Autodesk.Revit.DB import ElementId, ViewType

        if bool(getattr(view, "IsTemplate", False)):
            raise ValueError("La vue logement sélectionnée est un gabarit.")
        if getattr(view, "ViewType", None) != ViewType.FloorPlan:
            raise ValueError("Les cotations V1 attendent une vue en plan.")

        level = getattr(view, "GenLevel", None)
        if getattr(level, "Name", None) != level_name:
            raise ValueError(
                "La vue logement doit appartenir au niveau « {} ».".format(
                    level_name
                )
            )

        try:
            primary_id = view.GetPrimaryViewId()
        except Exception:
            primary_id = ElementId.InvalidElementId
        if primary_id == ElementId.InvalidElementId:
            raise ValueError(
                "Sélectionnez une vue logement dépendante générée par Plans de vente."
            )

        prefix = "PDV PROTO - {} - ".format(housing_key)
        if not str(getattr(view, "Name", "") or "").startswith(prefix):
            raise ValueError(
                "La vue sélectionnée n'est pas une vue logement du logement « {} ».".format(
                    housing_key
                )
            )

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    @classmethod
    def _is_linear_dimension_type(cls, dimension_type):
        try:
            from Autodesk.Revit.DB import DimensionStyleType, DimensionType
            if not isinstance(dimension_type, DimensionType):
                return False

            allowed = [DimensionStyleType.Linear]
            linear_fixed = getattr(DimensionStyleType, "LinearFixed", None)
            if linear_fixed is not None:
                allowed.append(linear_fixed)
            return dimension_type.StyleType in allowed
        except Exception:
            return False

    @classmethod
    def _element_type_name(cls, element_type):
        if element_type is None:
            return ""

        try:
            from Autodesk.Revit.DB import Element
            value = cls._clean_text(Element.Name.GetValue(element_type))
            if value:
                return value
        except Exception:
            pass

        try:
            value = cls._clean_text(getattr(element_type, "Name", None))
            if value:
                return value
        except Exception:
            pass

        try:
            return "Type de cote #{}".format(
                cls._element_id_value(element_type.Id)
            )
        except Exception:
            return "Type de cote"

    @staticmethod
    def _clean_text(value):
        if value is None:
            return ""
        try:
            return str(value).strip()
        except Exception:
            return ""

    @staticmethod
    def _room_label(room):
        return (
            getattr(room, "Number", "")
            or getattr(room, "Name", "")
            or str(getattr(room, "UniqueId", ""))
        )

    @staticmethod
    def _segment_length(segment):
        dx = float(segment[2]) - float(segment[0])
        dy = float(segment[3]) - float(segment[1])
        return math.sqrt((dx * dx) + (dy * dy))

    @staticmethod
    def _single_level_name(housing):
        levels = list(getattr(housing, "level_names", []) or [])
        if len(levels) != 1:
            raise ValueError(
                "Les cotations V1 attendent un logement sur un seul niveau. "
                "Niveaux détectés : {}.".format(
                    ", ".join(levels) if levels else "aucun"
                )
            )
        return levels[0]

    @staticmethod
    def _element_id_value(element_id):
        value = getattr(element_id, "Value", None)
        if value is not None:
            return int(value)
        return int(element_id.IntegerValue)

    @staticmethod
    def _millimeters_to_internal(value):
        from Autodesk.Revit.DB import UnitTypeId, UnitUtils
        return UnitUtils.ConvertToInternalUnits(
            float(value),
            UnitTypeId.Millimeters,
        )

    @staticmethod
    def _xyz(x_value, y_value, z_value):
        from Autodesk.Revit.DB import XYZ
        return XYZ(float(x_value), float(y_value), float(z_value))

    @staticmethod
    def _probe_z(room):
        try:
            bbox = room.get_BoundingBox(None)
        except Exception:
            bbox = None

        if bbox is not None and bbox.Max.Z > bbox.Min.Z:
            return (bbox.Min.Z + bbox.Max.Z) * 0.5

        location = getattr(room, "Location", None)
        point = getattr(location, "Point", None)
        if point is not None:
            return float(point.Z) + 1.0

        level = getattr(room, "Level", None)
        elevation = float(getattr(level, "Elevation", 0.0) or 0.0)
        return elevation + 1.0
