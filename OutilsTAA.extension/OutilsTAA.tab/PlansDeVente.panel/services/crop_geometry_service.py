# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Extraction des contours de pièces et application d'un crop rectangulaire."""

from plans_vente.crop_bounds import CropBounds


class CropGeometryService(object):
    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document

    def build_bounds(self, room_unique_ids, margin_mm):
        points = self._collect_boundary_points(room_unique_ids)
        bounds = CropBounds.from_points(points)
        return bounds.expanded(self._millimeters_to_internal(margin_mm))

    def apply_to_view(self, view, bounds):
        from Autodesk.Revit.DB import CurveLoop, Line, XYZ

        loop = CurveLoop()
        p1 = XYZ(bounds.min_x, bounds.min_y, bounds.z)
        p2 = XYZ(bounds.max_x, bounds.min_y, bounds.z)
        p3 = XYZ(bounds.max_x, bounds.max_y, bounds.z)
        p4 = XYZ(bounds.min_x, bounds.max_y, bounds.z)

        for start, end in ((p1, p2), (p2, p3), (p3, p4), (p4, p1)):
            loop.Append(Line.CreateBound(start, end))

        manager = view.GetCropRegionShapeManager()
        if not manager.IsCropRegionShapeValid(loop):
            raise ValueError("Le contour calculé n'est pas accepté par Revit comme crop.")

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
