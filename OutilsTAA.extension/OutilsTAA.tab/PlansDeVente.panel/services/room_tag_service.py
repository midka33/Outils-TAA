# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Placement contrôlé des étiquettes de pièces du plan de vente."""

ROOM_TAG_SERVICE_BUILD = "stage05-room-tags-category-only-v3"

from common.transaction import RevitTransaction
from plans_vente.tag_positioning import (
    boxes_overlap,
    ordered_candidate_points,
    polygon_area,
)


class RoomTagTypeCandidate(object):
    def __init__(self, unique_id, name, family_name="", element_id_value=None):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.family_name = family_name or ""
        self.element_id_value = element_id_value

    @property
    def label(self):
        family_name = str(self.family_name or "").strip()
        type_name = str(self.name or "").strip()

        if family_name and type_name and family_name != type_name:
            return "{} — {}".format(family_name, type_name)
        if type_name:
            return type_name
        if family_name:
            return family_name

        if self.element_id_value is not None:
            return "Type d'étiquette #{}".format(self.element_id_value)
        return "Type d'étiquette"


class RoomTagViewCandidate(object):
    def __init__(self, unique_id, name, level_name, scale=0):
        self.unique_id = unique_id or ""
        self.name = name or ""
        self.level_name = level_name or ""
        self.scale = int(scale or 0)

    @property
    def label(self):
        scale = "1:{}".format(self.scale) if self.scale else "échelle inconnue"
        return "{} — {}".format(self.name, scale)


class RoomTagCreationResult(object):
    def __init__(
        self,
        housing_key,
        view_name,
        tag_type_name,
        created_count,
        adjusted_count=0,
        warnings=None,
    ):
        self.housing_key = housing_key or ""
        self.view_name = view_name or ""
        self.tag_type_name = tag_type_name or ""
        self.created_count = int(created_count or 0)
        self.adjusted_count = int(adjusted_count or 0)
        self.warnings = list(warnings or [])

    @property
    def warning_count(self):
        return len(self.warnings)


class RoomTagService(object):
    """Service Revit de l'Étape 05."""

    COLLISION_PADDING_MM = 10.0

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self.build_id = ROOM_TAG_SERVICE_BUILD

    def list_tag_types(self):
        from Autodesk.Revit.DB import (
            BuiltInCategory,
            FamilySymbol,
            FilteredElementCollector,
        )

        # RoomTagType ne peut pas être utilisé avec ElementClassFilter / OfClass.
        # On collecte sa classe native parente FamilySymbol puis la catégorie
        # OST_RoomTags, qui identifie les vrais types d'étiquettes de pièces.
        result = []
        for tag_type in (
            FilteredElementCollector(self.document)
            .OfClass(FamilySymbol)
            .OfCategory(BuiltInCategory.OST_RoomTags)
            .WhereElementIsElementType()
            .ToElements()
        ):
            name = self._room_tag_type_name(tag_type)
            family_name = self._room_tag_family_name(tag_type)
            result.append(
                RoomTagTypeCandidate(
                    unique_id=str(getattr(tag_type, "UniqueId", "") or ""),
                    name=name,
                    family_name=family_name,
                    element_id_value=self._element_id_value(tag_type.Id),
                )
            )

        return sorted(
            result,
            key=lambda item: (item.family_name.lower(), item.name.lower()),
        )

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
                RoomTagViewCandidate(
                    unique_id=str(getattr(view, "UniqueId", "") or ""),
                    name=name,
                    level_name=level_name,
                    scale=int(getattr(view, "Scale", 0) or 0),
                )
            )

        return sorted(result, key=lambda item: item.name.lower())

    def create_tags(
        self,
        housing,
        target_view_unique_id,
        room_tag_type_unique_id,
        exclusion_boxes=None,
    ):
        if housing is None:
            raise ValueError("Sélectionnez un logement.")

        level_name = self._single_level_name(housing)
        view = self._get_element(
            target_view_unique_id,
            "Sélectionnez une vue logement.",
        )
        tag_type = self._get_element(
            room_tag_type_unique_id,
            "Sélectionnez un type d'étiquette de pièce.",
        )

        self._validate_target_view(view, housing.key, level_name)

        if not self._is_room_tag_type(tag_type):
            raise ValueError(
                "Le type d'étiquette sélectionné n'est plus un type "
                "d'étiquette de pièce du document hôte."
            )

        rooms = []
        for unique_id in housing.room_unique_ids:
            room = self.document.GetElement(unique_id)
            if room is None:
                raise ValueError(
                    "Une pièce du logement n'existe plus : {}.".format(unique_id)
                )
            rooms.append(room)

        existing_tags = self._existing_room_tags(view)
        duplicate_rooms = self._already_tagged_room_ids(existing_tags)
        duplicated = [
            room for room in rooms
            if self._element_id_value(room.Id) in duplicate_rooms
        ]
        if duplicated:
            labels = [
                getattr(room, "Number", "") or getattr(room, "Name", "")
                for room in duplicated
            ]
            raise ValueError(
                "Des étiquettes existent déjà dans cette vue pour : {}. "
                "La mise à jour sera traitée à l'Étape 08.".format(
                    ", ".join(label for label in labels if label)
                    or "{} pièce(s)".format(len(duplicated))
                )
            )

        occupied_boxes = list(exclusion_boxes or [])
        for existing in existing_tags:
            bbox = self._bounding_box_2d(existing, view)
            if bbox is not None:
                occupied_boxes.append(bbox)

        created_count = 0
        adjusted_count = 0
        warnings = []
        padding = self._millimeters_to_internal(self.COLLISION_PADDING_MM)

        with RevitTransaction(
            self.document,
            "Plans de vente - Étiquettes {}".format(housing.key),
        ):
            for room in rooms:
                candidates, probe_z = self._valid_candidate_points(room)
                if not candidates:
                    raise ValueError(
                        "Aucun point intérieur fiable n'a été trouvé pour la pièce « {} ».".format(
                            getattr(room, "Number", "")
                            or getattr(room, "Name", "")
                            or str(getattr(room, "UniqueId", ""))
                        )
                    )

                tag, candidate_index, fully_inside, collision = self._place_one_tag(
                    room,
                    view,
                    tag_type,
                    candidates,
                    probe_z,
                    occupied_boxes,
                    padding,
                )
                created_count += 1
                if candidate_index > 0:
                    adjusted_count += 1

                bbox = self._bounding_box_2d(tag, view)
                if bbox is not None:
                    occupied_boxes.append(bbox)

                room_label = (
                    getattr(room, "Number", "")
                    or getattr(room, "Name", "")
                    or str(getattr(room, "UniqueId", ""))
                )
                if not fully_inside:
                    warnings.append(
                        "{} : l'étiquette reste centrée dans la pièce, mais son "
                        "emprise graphique dépasse partiellement la pièce.".format(
                            room_label
                        )
                    )
                if collision:
                    warnings.append(
                        "{} : aucune position sans collision n'a été trouvée ; "
                        "la meilleure position intérieure a été conservée.".format(
                            room_label
                        )
                    )

        return RoomTagCreationResult(
            housing_key=housing.key,
            view_name=str(getattr(view, "Name", "") or ""),
            tag_type_name=self._room_tag_type_name(tag_type),
            created_count=created_count,
            adjusted_count=adjusted_count,
            warnings=warnings,
        )

    def _place_one_tag(
        self,
        room,
        view,
        tag_type,
        candidates,
        probe_z,
        occupied_boxes,
        padding,
    ):
        from Autodesk.Revit.DB import LinkElementId, UV, XYZ

        first = candidates[0]
        tag = self.document.Create.NewRoomTag(
            LinkElementId(room.Id),
            UV(first[0], first[1]),
            view.Id,
        )
        if tag is None:
            raise RuntimeError("Revit n'a pas créé l'étiquette de pièce.")

        tag.RoomTagType = tag_type
        try:
            tag.HasLeader = False
        except Exception:
            pass

        best = None
        for index, point in enumerate(candidates):
            if index > 0:
                head = tag.TagHeadPosition
                tag.TagHeadPosition = XYZ(point[0], point[1], head.Z)

            self.document.Regenerate()
            bbox = self._bounding_box_2d(tag, view)
            fully_inside = self._tag_box_inside_room(
                room,
                bbox,
                probe_z,
            )
            collision = any(
                boxes_overlap(bbox, occupied, padding)
                for occupied in occupied_boxes
            ) if bbox is not None else False

            rank = (
                1 if collision else 0,
                1 if not fully_inside else 0,
                index,
            )
            if best is None or rank < best[0]:
                best = (rank, index, point, fully_inside, collision)

            if fully_inside and not collision:
                break

        if best is None:
            raise RuntimeError("Aucune position d'étiquette n'a pu être évaluée.")

        _, chosen_index, chosen_point, fully_inside, collision = best
        head = tag.TagHeadPosition
        tag.TagHeadPosition = XYZ(
            chosen_point[0],
            chosen_point[1],
            head.Z,
        )
        self.document.Regenerate()

        if not bool(getattr(tag, "IsInRoom", True)):
            raise RuntimeError(
                "Revit indique que l'étiquette créée n'est pas dans la pièce."
            )

        return tag, chosen_index, fully_inside, collision

    def _valid_candidate_points(self, room):
        from Autodesk.Revit.DB import XYZ

        boundary = self._outer_boundary_points(room)
        if len(boundary) < 3:
            return [], self._probe_z(room)

        location = getattr(room, "Location", None)
        location_point = getattr(location, "Point", None)
        location_xy = (
            (location_point.X, location_point.Y)
            if location_point is not None
            else None
        )

        probe_z = self._probe_z(room)
        result = []
        for x_value, y_value in ordered_candidate_points(
            boundary,
            location_xy,
        ):
            point = XYZ(x_value, y_value, probe_z)
            try:
                inside = bool(room.IsPointInRoom(point))
            except Exception:
                inside = False
            if inside:
                result.append((x_value, y_value))

        return result, probe_z

    def _outer_boundary_points(self, room):
        from Autodesk.Revit.DB import (
            SpatialElementBoundaryLocation,
            SpatialElementBoundaryOptions,
        )

        options = SpatialElementBoundaryOptions()
        options.SpatialElementBoundaryLocation = (
            SpatialElementBoundaryLocation.Finish
        )

        loops = []
        for segment_loop in room.GetBoundarySegments(options) or []:
            points = []
            for segment in segment_loop or []:
                curve = segment.GetCurve()
                if curve is None:
                    continue
                for point in list(curve.Tessellate() or []):
                    xy = (point.X, point.Y)
                    if not points or (
                        abs(xy[0] - points[-1][0]) > 1e-9
                        or abs(xy[1] - points[-1][1]) > 1e-9
                    ):
                        points.append(xy)

            if (
                len(points) > 1
                and abs(points[0][0] - points[-1][0]) <= 1e-9
                and abs(points[0][1] - points[-1][1]) <= 1e-9
            ):
                points = points[:-1]

            if len(points) >= 3:
                loops.append((abs(polygon_area(points)), points))

        if not loops:
            return []

        loops.sort(key=lambda item: item[0], reverse=True)
        return loops[0][1]

    def _probe_z(self, room):
        try:
            bbox = room.get_BoundingBox(None)
        except Exception:
            bbox = None

        if bbox is not None and bbox.Max.Z > bbox.Min.Z:
            return (bbox.Min.Z + bbox.Max.Z) * 0.5

        location = getattr(room, "Location", None)
        point = getattr(location, "Point", None)
        if point is not None:
            return point.Z + 1.0

        level = getattr(room, "Level", None)
        elevation = float(getattr(level, "Elevation", 0.0) or 0.0)
        return elevation + 1.0

    def _tag_box_inside_room(self, room, bbox, probe_z):
        if bbox is None:
            return False

        from Autodesk.Revit.DB import XYZ

        corners = (
            (bbox[0], bbox[1]),
            (bbox[0], bbox[3]),
            (bbox[2], bbox[1]),
            (bbox[2], bbox[3]),
        )
        for x_value, y_value in corners:
            try:
                if not bool(room.IsPointInRoom(XYZ(x_value, y_value, probe_z))):
                    return False
            except Exception:
                return False
        return True

    def _existing_room_tags(self, view):
        from Autodesk.Revit.DB import (
            BuiltInCategory,
            FilteredElementCollector,
        )

        # Filtrage volontairement uniquement par catégorie.
        # Cela évite complètement ElementClassFilter sur les classes spécialisées
        # d'étiquettes spatiales, qui est la source des erreurs RoomTag/RoomTagType.
        return list(
            FilteredElementCollector(self.document, view.Id)
            .OfCategory(BuiltInCategory.OST_RoomTags)
            .WhereElementIsNotElementType()
            .ToElements()
        )

    def _already_tagged_room_ids(self, tags):
        values = set()
        for tag in tags or []:
            room_id = getattr(tag, "TaggedLocalRoomId", None)
            if room_id is None:
                continue
            try:
                value = self._element_id_value(room_id)
            except Exception:
                continue
            if value >= 0:
                values.add(value)
        return values

    def _validate_target_view(self, view, housing_key, level_name):
        from Autodesk.Revit.DB import ElementId, ViewType

        if bool(getattr(view, "IsTemplate", False)):
            raise ValueError("La vue logement sélectionnée est un gabarit.")
        if getattr(view, "ViewType", None) != ViewType.FloorPlan:
            raise ValueError("Les étiquettes V1 attendent une vue en plan.")

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

    def _bounding_box_2d(self, element, view):
        try:
            bbox = element.get_BoundingBox(view)
        except Exception:
            bbox = None
        if bbox is None:
            return None
        return (
            float(bbox.Min.X),
            float(bbox.Min.Y),
            float(bbox.Max.X),
            float(bbox.Max.Y),
        )

    def _get_element(self, unique_id, error_message):
        if not unique_id:
            raise ValueError(error_message)
        element = self.document.GetElement(unique_id)
        if element is None:
            raise ValueError(error_message)
        return element

    @classmethod
    def _is_room_tag_type(cls, tag_type):
        if tag_type is None:
            return False

        try:
            from Autodesk.Revit.DB import (
                BuiltInCategory,
                ElementId,
                FamilySymbol,
            )
            if not isinstance(tag_type, FamilySymbol):
                return False

            category = getattr(tag_type, "Category", None)
            if category is None:
                return False

            return category.Id == ElementId(BuiltInCategory.OST_RoomTags)
        except Exception:
            return False

    @classmethod
    def _room_tag_type_name(cls, tag_type):
        """Nom de type robuste pour RoomTagType sous IronPython/pyRevit."""
        if tag_type is None:
            return ""

        value = cls._element_type_name(tag_type)
        if value:
            return value

        try:
            from Autodesk.Revit.DB import BuiltInParameter
            for built_in in (
                BuiltInParameter.ALL_MODEL_TYPE_NAME,
                BuiltInParameter.SYMBOL_NAME_PARAM,
            ):
                value = cls._parameter_text(tag_type, built_in)
                if value:
                    return value
        except Exception:
            pass

        try:
            return "Type d'étiquette #{}".format(
                cls._element_id_value(tag_type.Id)
            )
        except Exception:
            return "Type d'étiquette"

    @classmethod
    def _room_tag_family_name(cls, tag_type):
        """Nom de famille robuste sans dépendre de Family.Name."""
        if tag_type is None:
            return ""

        try:
            value = cls._clean_text(getattr(tag_type, "FamilyName", None))
            if value:
                return value
        except Exception:
            pass

        try:
            from Autodesk.Revit.DB import BuiltInParameter
            for built_in in (
                BuiltInParameter.ALL_MODEL_FAMILY_NAME,
                BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM,
            ):
                value = cls._parameter_text(tag_type, built_in)
                if value:
                    return value
        except Exception:
            pass

        try:
            family = getattr(tag_type, "Family", None)
            if family is not None:
                from Autodesk.Revit.DB import Element
                value = cls._clean_text(Element.Name.GetValue(family))
                if value:
                    return value
        except Exception:
            pass

        return ""

    @staticmethod
    def _clean_text(value):
        if value is None:
            return ""
        try:
            return str(value).strip()
        except Exception:
            return ""

    @classmethod
    def _parameter_text(cls, element, built_in_parameter):
        try:
            parameter = element.get_Parameter(built_in_parameter)
        except Exception:
            parameter = None
        if parameter is None:
            return ""

        for getter_name in ("AsString", "AsValueString"):
            getter = getattr(parameter, getter_name, None)
            if getter is None:
                continue
            try:
                value = getter()
            except Exception:
                value = None
            value = cls._clean_text(value)
            if value:
                return value
        return ""

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

        return ""

    @staticmethod
    def _single_level_name(housing):
        levels = list(getattr(housing, "level_names", []) or [])
        if len(levels) != 1:
            raise ValueError(
                "Les étiquettes V1 attendent un logement sur un seul niveau. "
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
        return UnitUtils.ConvertToInternalUnits(float(value), UnitTypeId.Millimeters)
