# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Prototype Étape 06 — deux cotations principales par pièce."""

DIMENSION_SERVICE_BUILD = "stage06-dimensions-finish-faces-v1"

from common.transaction import RevitTransaction
from plans_vente.dimension_geometry import dominant_dimension_pairs
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
        warnings=None,
    ):
        self.housing_key = housing_key or ""
        self.view_name = view_name or ""
        self.dimension_type_name = dimension_type_name or ""
        self.created_count = int(created_count or 0)
        self.room_count = int(room_count or 0)
        self.warnings = list(warnings or [])

    @property
    def warning_count(self):
        return len(self.warnings)


class _BoundaryReferenceCandidate(object):
    def __init__(self, segment, reference, element_id_value):
        self.segment = segment
        self.reference = reference
        self.element_id_value = element_id_value


class DimensionService(object):
    """Service Revit du premier prototype de l'Étape 06."""

    ANGLE_TOLERANCE_DEGREES = 5.0
    MINIMUM_RELATIVE_LENGTH = 0.25
    PLACEMENT_FRACTION = 0.25

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.build_id = DIMENSION_SERVICE_BUILD

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
                raise ValueError(
                    "Une pièce du logement n'existe plus : {}.".format(unique_id)
                )

            boundary_candidates = self._room_boundary_candidates(room)
            segments = [candidate.segment for candidate in boundary_candidates]
            pairs = dominant_dimension_pairs(
                segments,
                angle_tolerance_degrees=self.ANGLE_TOLERANCE_DEGREES,
                minimum_relative_length=self.MINIMUM_RELATIVE_LENGTH,
                placement_fraction=self.PLACEMENT_FRACTION,
                max_results=2,
            )

            room_label = (
                getattr(room, "Number", "")
                or getattr(room, "Name", "")
                or str(getattr(room, "UniqueId", ""))
            )

            if len(pairs) < 2:
                raise ValueError(
                    "La pièce « {} » ne fournit pas encore deux paires de "
                    "faces finies opposées fiables. Le prototype 06A gère "
                    "pour l'instant les limites droites portées par des murs.".format(
                        room_label
                    )
                )

            room_plans.append((room, boundary_candidates, pairs))

        created_count = 0
        with RevitTransaction(
            self.document,
            "Plans de vente - Cotations {}".format(housing.key),
        ):
            for room, boundary_candidates, pairs in room_plans:
                for pair in pairs:
                    first = boundary_candidates[pair.first_index]
                    second = boundary_candidates[pair.second_index]
                    dimension = self._create_dimension(
                        view,
                        dimension_type,
                        first.reference,
                        second.reference,
                        pair.line_start,
                        pair.line_end,
                        room,
                    )
                    if dimension is None:
                        raise RuntimeError(
                            "Revit n'a pas créé une des cotations attendues."
                        )
                    created_count += 1

        expected = len(room_plans) * 2
        if created_count != expected:
            warnings.append(
                "{} cote(s) créée(s) au lieu de {}.".format(
                    created_count,
                    expected,
                )
            )

        return DimensionCreationResult(
            housing_key=housing.key,
            view_name=str(getattr(view, "Name", "") or ""),
            dimension_type_name=self._element_type_name(dimension_type),
            created_count=created_count,
            room_count=len(room_plans),
            warnings=warnings,
        )

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
            if host is None or not isinstance(host, Wall):
                continue

            midpoint = curve.Evaluate(0.5, True)
            direction = curve.Direction
            reference = self._nearest_finish_face_reference(
                host,
                midpoint,
                direction,
            )
            if reference is None:
                continue

            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            result.append(
                _BoundaryReferenceCandidate(
                    segment=(
                        float(start.X),
                        float(start.Y),
                        float(end.X),
                        float(end.Y),
                    ),
                    reference=reference,
                    element_id_value=self._element_id_value(host.Id),
                )
            )

        return result

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
                vector = midpoint - face.Origin
                distance = abs(float(vector.DotProduct(normal)))
            except Exception:
                continue

            if best is None or distance < best[0]:
                best = (distance, reference)

        return best[1] if best is not None else None

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
