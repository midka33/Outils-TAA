# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Extraction des contours de pièces et crop rectangulaire aligné à la vue."""

from plans_vente.crop_bounds import CropBounds
from plans_vente.view_frame import ViewFrame


class CropGeometryService(object):
    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document

    def build_view_aligned_corners(self, room_unique_ids, view, margin_mm):
        """Retourne quatre coins monde alignés sur les axes écran de la vue."""
        if view is None:
            raise ValueError("Vue Revit manquante pour calculer le crop.")

        points = self._collect_boundary_points(room_unique_ids)
        frame = self._frame_from_view(view)

        projected = []
        for point in points:
            u, v = frame.project(point)
            projected.append((u, v, 0.0))

        bounds = CropBounds.from_points(projected)
        bounds = bounds.expanded(self._millimeters_to_internal(margin_mm))

        return [
            frame.to_world(bounds.min_x, bounds.min_y),
            frame.to_world(bounds.max_x, bounds.min_y),
            frame.to_world(bounds.max_x, bounds.max_y),
            frame.to_world(bounds.min_x, bounds.max_y),
        ]

    def apply_to_view(self, view, world_corners):
        from Autodesk.Revit.DB import CurveLoop, Line, XYZ

        corners = list(world_corners or [])
        if len(corners) != 4:
            raise ValueError("Quatre coins sont requis pour le crop rectangulaire.")

        xyz_points = [
            XYZ(float(point[0]), float(point[1]), float(point[2]))
            for point in corners
        ]

        loop = CurveLoop()
        pairs = (
            (xyz_points[0], xyz_points[1]),
            (xyz_points[1], xyz_points[2]),
            (xyz_points[2], xyz_points[3]),
            (xyz_points[3], xyz_points[0]),
        )
        for start, end in pairs:
            loop.Append(Line.CreateBound(start, end))

        manager = view.GetCropRegionShapeManager()
        if not manager.IsCropRegionShapeValid(loop):
            raise ValueError(
                "Le contour aligné à la vue n'est pas accepté par Revit comme crop."
            )

        view.CropBoxActive = True
        view.CropBoxVisible = True
        manager.SetCropShape(loop)

    def _collect_boundary_points(self, room_unique_ids):
        from Autodesk.Revit.DB import SpatialElementBoundaryOptions

        options = SpatialElementBoundaryOptions()
        points = []

        for unique_id in room_unique_ids or []:
            room = self.document.GetElement(unique_id)
            if room is None:
                continue

            try:
                loops = room.GetBoundarySegments(options)
            except Exception:
                loops = None

            for segment_loop in loops or []:
                for segment in segment_loop or []:
                    curve = segment.GetCurve()
                    if curve is None:
                        continue
                    for index in (0, 1):
                        point = curve.GetEndPoint(index)
                        points.append((point.X, point.Y, point.Z))

        if not points:
            raise ValueError(
                "Aucun contour exploitable n'a été trouvé pour les pièces du logement."
            )

        return points

    @staticmethod
    def _frame_from_view(view):
        origin = getattr(view, "Origin", None)
        right = getattr(view, "RightDirection", None)
        up = getattr(view, "UpDirection", None)

        if origin is None or right is None or up is None:
            raise ValueError(
                "La vue ne fournit pas de repère exploitable pour aligner le crop."
            )

        return ViewFrame(
            origin=(origin.X, origin.Y, origin.Z),
            right=(right.X, right.Y, right.Z),
            up=(up.X, up.Y, up.Z),
        )

    @staticmethod
    def _millimeters_to_internal(value):
        from Autodesk.Revit.DB import UnitTypeId, UnitUtils

        try:
            margin_mm = float(value)
        except Exception:
            raise ValueError("La marge de crop doit être un nombre.")

        if margin_mm < 0:
            raise ValueError("La marge de crop ne peut pas être négative.")

        return UnitUtils.ConvertToInternalUnits(
            margin_mm,
            UnitTypeId.Millimeters,
        )
