# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Construction d'un contour de crop optimisé à partir des pièces du logement."""

from plans_vente.crop_bounds import CropBounds
from plans_vente.view_frame import ViewFrame
from plans_vente import local_crop_geometry as local_geometry


class OptimizedCropResult(object):
    """Résultat du calcul de crop avant application à la vue."""

    def __init__(
        self,
        curve_loop,
        mode,
        warning=None,
        fallback_curve_loop=None,
    ):
        self.curve_loop = curve_loop
        self.mode = mode or ""
        self.warning = warning or ""
        self.fallback_curve_loop = fallback_curve_loop


class CropGeometryStageError(Exception):
    """Erreur enrichie avec l'étape géométrique ayant échoué."""

    def __init__(self, stage, error):
        self.stage = stage or "étape inconnue"
        self.original_error = error
        Exception.__init__(
            self,
            "{} : {}".format(
                self.stage,
                error,
            ),
        )


class CropGeometryService(object):
    """Construit un contour logement réel, avec secours rectangulaire explicite."""

    BOOLEAN_EXTRUSION_HEIGHT = 1.0
    MIN_DETAIL_CLEANUP_MM = 300.0
    MAX_DETAIL_CLEANUP_MM = 600.0
    SHAFT_MAX_MOUTH_MM = 3500.0
    SHAFT_MAX_DEPTH_MM = 2000.0
    SHAFT_MAX_FILL_AREA_M2 = 5.0
    SHAFT_MAX_EXTENSION_MM = 3500.0

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document
        self._last_closed_recess_count = 0
        self._last_recess_counts = local_geometry.empty_diagnostics()

    def build_optimized_crop(
        self,
        room_unique_ids,
        view,
        margin_mm,
    ):
        """Construit un contour extérieur compatible avec les crops Revit.

        Important : ViewCropRegionShapeManager n'accepte que des segments
        droits pour une forme de crop. Les boucles issues des pièces ou d'une
        opération booléenne sont donc linéarisées avant validation.
        """
        if view is None:
            raise ValueError("Vue Revit manquante pour calculer le crop.")

        margin_internal = self._millimeters_to_internal(margin_mm)
        self._last_closed_recess_count = 0
        self._last_recess_counts = local_geometry.empty_diagnostics()
        fallback_loop = self._build_rectangular_fallback(
            room_unique_ids,
            view,
            margin_mm,
        )

        try:
            room_loops, reference_z = self._stage(
                "Lecture des contours de pièces",
                self._collect_room_outer_loops,
                room_unique_ids,
                view,
            )
            room_union_solid = self._stage(
                "Union géométrique des pièces",
                self._union_room_solids,
                room_loops,
                view,
            )
            room_outer_loop = self._stage(
                "Extraction du contour extérieur",
                self._extract_outer_union_loop,
                room_union_solid,
                view,
                reference_z,
            )
            straight_room_outer_loop = self._stage(
                "Linéarisation du contour extérieur",
                self._linearize_curve_loop,
                room_outer_loop,
                view,
            )

            clean_outer_loop = self._stage(
                "Fermeture des petites gaines et retraits",
                self._close_small_recesses,
                straight_room_outer_loop,
                view,
                self._millimeters_to_internal(self.SHAFT_MAX_MOUTH_MM),
                self._millimeters_to_internal(self.SHAFT_MAX_DEPTH_MM),
                self._square_meters_to_internal_area(self.SHAFT_MAX_FILL_AREA_M2),
            )

            final_loop = self._stage(
                "Construction de la marge robuste",
                self._buffer_outward,
                clean_outer_loop,
                margin_internal,
                view,
            )

            final_loop = self._stage(
                "Linéarisation finale",
                self._linearize_curve_loop,
                final_loop,
                view,
            )

            mode = "Contour optimisé — " + self._recess_diagnostic()

            return OptimizedCropResult(
                curve_loop=final_loop,
                mode=mode,
                fallback_curve_loop=fallback_loop,
            )

        except Exception as error:
            return OptimizedCropResult(
                curve_loop=fallback_loop,
                mode="Rectangle de secours",
                fallback_curve_loop=fallback_loop,
                warning=(
                    "Le contour optimisé n'a pas pu être construit. "
                    "Un rectangle aligné à la vue a été utilisé. "
                    "Nettoyage avant échec : {}. Étape en échec : {}"
                ).format(
                    self._recess_diagnostic(),
                    error,
                ),
            )

    def apply_to_view(self, view, crop_result):
        """Applique le crop sur la vue cible créée.

        La capacité à recevoir une forme non rectangulaire doit être testée sur
        la VUE CIBLE, pas sur la vue source utilisée pour le calcul géométrique.
        """
        if crop_result is None or crop_result.curve_loop is None:
            raise ValueError("Contour de crop manquant.")

        manager = view.GetCropRegionShapeManager()
        selected_loop = crop_result.curve_loop
        mode = crop_result.mode
        warning = crop_result.warning or ""

        if mode.startswith("Contour optimisé") and not bool(manager.CanHaveShape):
            released, detail = self._try_release_scope_box(view)
            if released:
                self.document.Regenerate()
                manager = view.GetCropRegionShapeManager()

            if not bool(manager.CanHaveShape):
                fallback = crop_result.fallback_curve_loop
                if fallback is None:
                    raise ValueError(
                        "La vue dépendante créée n'autorise pas un crop "
                        "non rectangulaire. {}".format(detail or "")
                    )

                selected_loop = fallback
                mode = "Rectangle de secours"
                warning = (
                    "La vue dépendante créée n'autorise pas un crop "
                    "non rectangulaire. {} Un rectangle aligné à la vue "
                    "a été appliqué."
                ).format(detail or "").strip()

        if not manager.IsCropRegionShapeValid(selected_loop):
            raise ValueError(
                "Le contour calculé n'est pas accepté par Revit comme crop."
            )

        view.CropBoxActive = True
        view.CropBoxVisible = True
        manager.SetCropShape(selected_loop)

        crop_result.curve_loop = selected_loop
        crop_result.mode = mode
        crop_result.warning = warning
        return crop_result

    @staticmethod
    def _stage(stage_name, function, *args):
        try:
            return function(*args)
        except CropGeometryStageError:
            raise
        except Exception as error:
            raise CropGeometryStageError(stage_name, error)

    def _collect_room_outer_loops(self, room_unique_ids, view):
        from Autodesk.Revit.DB import (
            CurveLoop,
            SpatialElementBoundaryLocation,
            SpatialElementBoundaryOptions,
        )

        options = SpatialElementBoundaryOptions()
        options.SpatialElementBoundaryLocation = (
            SpatialElementBoundaryLocation.Center
        )

        room_loops = []
        reference_z_values = []

        for unique_id in room_unique_ids or []:
            room = self.document.GetElement(unique_id)
            if room is None:
                continue

            try:
                boundary_loops = room.GetBoundarySegments(options)
            except Exception:
                boundary_loops = None

            candidates = []
            for segment_loop in boundary_loops or []:
                curve_loop = CurveLoop()
                for segment in segment_loop or []:
                    curve = segment.GetCurve()
                    if curve is not None:
                        curve_loop.Append(curve)

                if curve_loop.IsOpen():
                    continue

                area = abs(self._curve_loop_area(curve_loop, view))
                if area > 1e-9:
                    candidates.append((area, curve_loop))

            if not candidates:
                continue

            candidates.sort(key=lambda item: item[0], reverse=True)
            outer_loop = candidates[0][1]
            room_loops.append(outer_loop)

            for curve in outer_loop:
                point = curve.GetEndPoint(0)
                reference_z_values.append(point.Z)
                break

        if not room_loops:
            raise ValueError(
                "Aucun contour fermé exploitable n'a été trouvé pour les pièces."
            )

        reference_z = (
            sum(reference_z_values) / float(len(reference_z_values))
            if reference_z_values
            else 0.0
        )

        return room_loops, reference_z

    def _union_room_solids(
        self,
        room_loops,
        view,
    ):
        from Autodesk.Revit.DB import (
            BooleanOperationsType,
            BooleanOperationsUtils,
            CurveLoop,
            GeometryCreationUtilities,
        )
        from System.Collections.Generic import List

        direction = getattr(view, "ViewDirection", None)
        if direction is None:
            raise ValueError("La vue ne fournit pas de direction exploitable.")

        solids = []
        all_loops = list(room_loops or [])
        for curve_loop in all_loops:
            loops = List[CurveLoop]()
            loops.Add(curve_loop)
            solid = GeometryCreationUtilities.CreateExtrusionGeometry(
                loops,
                direction,
                self.BOOLEAN_EXTRUSION_HEIGHT,
            )
            if solid is not None and solid.Volume > 1e-9:
                solids.append(solid)

        if not solids:
            raise ValueError("Impossible de créer les solides temporaires des pièces.")

        union_solid = solids[0]
        for solid in solids[1:]:
            union_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                union_solid,
                solid,
                BooleanOperationsType.Union,
            )

        if union_solid is None or union_solid.Volume <= 1e-9:
            raise ValueError("L'union géométrique des pièces est vide.")

        return union_solid

    def _extract_outer_union_loop(self, solid, view, reference_z):
        from Autodesk.Revit.DB import PlanarFace

        view_direction = view.ViewDirection
        face_candidates = []

        for face in solid.Faces:
            if not isinstance(face, PlanarFace):
                continue

            normal = face.FaceNormal
            parallel = abs(abs(normal.DotProduct(view_direction)) - 1.0)
            if parallel > 1e-6:
                continue

            loops = list(face.GetEdgesAsCurveLoops() or [])
            if not loops:
                continue

            loop_data = []
            for curve_loop in loops:
                area = abs(self._curve_loop_area(curve_loop, view))
                if area > 1e-9:
                    loop_data.append((area, curve_loop))

            if not loop_data:
                continue

            loop_data.sort(key=lambda item: item[0], reverse=True)
            outer_area, outer_loop = loop_data[0]
            face_z = self._curve_loop_average_z(outer_loop)
            face_candidates.append(
                (
                    abs(face_z - reference_z),
                    -outer_area,
                    outer_loop,
                )
            )

        if not face_candidates:
            raise ValueError(
                "Aucune face plane de l'union n'est exploitable pour le crop."
            )

        face_candidates.sort(key=lambda item: (item[0], item[1]))
        return face_candidates[0][2]

    def _linearize_curve_loop(self, curve_loop, view):
        """Convertit arcs/splines en une boucle composée uniquement de Line."""
        from Autodesk.Revit.DB import CurveLoop, Line

        points = self._tessellated_loop_points(curve_loop)
        points = self._remove_near_duplicates(points)
        points = self._simplify_collinear_points(points, view)

        if len(points) < 3:
            raise ValueError(
                "Le contour linéarisé contient moins de trois sommets."
            )

        loop = CurveLoop()
        count = len(points)
        for index in range(count):
            start = points[index]
            end = points[(index + 1) % count]
            if start.DistanceTo(end) <= self._short_curve_tolerance():
                continue
            loop.Append(Line.CreateBound(start, end))

        if loop.IsOpen():
            raise ValueError(
                "Le contour linéarisé n'est pas fermé."
            )

        return loop

    def _tessellated_loop_points(self, curve_loop):
        points = []

        for curve in curve_loop:
            tessellated = list(curve.Tessellate() or [])
            if not tessellated:
                continue

            for point in tessellated:
                if not points or point.DistanceTo(points[-1]) > 1e-9:
                    points.append(point)

        if len(points) > 1 and points[0].DistanceTo(points[-1]) <= 1e-9:
            points = points[:-1]

        return points

    def _remove_near_duplicates(self, points):
        tolerance = max(self._short_curve_tolerance(), 1e-7)
        cleaned = []

        for point in points or []:
            if not cleaned or point.DistanceTo(cleaned[-1]) > tolerance:
                cleaned.append(point)

        if (
            len(cleaned) > 1
            and cleaned[0].DistanceTo(cleaned[-1]) <= tolerance
        ):
            cleaned = cleaned[:-1]

        return cleaned

    def _simplify_collinear_points(self, points, view):
        """Retire les sommets quasi colinéaires sans changer la forme visible."""
        values = list(points or [])
        if len(values) <= 3:
            return values

        frame = self._frame_from_view(view)
        changed = True

        while changed and len(values) > 3:
            changed = False
            simplified = []
            count = len(values)

            for index in range(count):
                previous = values[(index - 1) % count]
                current = values[index]
                following = values[(index + 1) % count]

                p = frame.project((previous.X, previous.Y, previous.Z))
                c = frame.project((current.X, current.Y, current.Z))
                n = frame.project((following.X, following.Y, following.Z))

                left = (c[0] - p[0], c[1] - p[1])
                right = (n[0] - c[0], n[1] - c[1])

                left_length = self._vector_length_2d(left)
                right_length = self._vector_length_2d(right)

                if left_length <= 1e-9 or right_length <= 1e-9:
                    changed = True
                    continue

                cross = abs(
                    (left[0] * right[1]) - (left[1] * right[0])
                )
                sin_angle = cross / (left_length * right_length)
                dot = (left[0] * right[0]) + (left[1] * right[1])

                if sin_angle <= 1e-6 and dot > 0:
                    changed = True
                    continue

                simplified.append(current)

            if len(simplified) < 3:
                break

            values = simplified

        return values

    def _recess_diagnostic(self):
        counts = self._last_recess_counts
        message = (
            "{} fermeture(s) colinéaire(s), {} raccord(s) Trim/Extend, "
            "{} raccord(s) perpendiculaire(s), "
            "{} segment(s) parasite(s) absorbé(s)"
        ).format(
            counts["collinear"],
            counts["trim"],
            counts["perpendicular"],
            counts.get("absorbed", 0),
        )
        if counts["budget_exhausted"]:
            message += " — limite de calcul atteinte, retraits restants conservés"
        return message

    def _close_small_recesses(
        self, curve_loop, view, max_mouth_internal,
        max_depth_internal, max_fill_area_internal,
    ):
        """Adaptateur Revit du moteur local pur ; conservation en cas de doute."""
        frame = self._frame_from_view(view)
        points = self._remove_near_duplicates(self._tessellated_loop_points(curve_loop))
        uv = [frame.project((p.X, p.Y, p.Z)) for p in points]
        cleaned, counts = local_geometry.close_pockets(
            uv, max_mouth_internal, max_depth_internal, max_fill_area_internal,
            self._millimeters_to_internal(self.SHAFT_MAX_EXTENSION_MM),
            tolerance=max(self._short_curve_tolerance(), 1e-7),
        )
        if not sum(counts[key] for key in ("collinear", "trim", "perpendicular")):
            self._last_recess_counts["budget_exhausted"] |= counts["budget_exhausted"]
            return curve_loop
        try:
            result = self._curve_loop_from_uv_points(cleaned, frame)
        except Exception:
            return curve_loop
        # Counters describe reconstructed geometry only.
        for key in (
            "collinear",
            "trim",
            "perpendicular",
            "absorbed",
            "candidates",
            "validations",
        ):
            self._last_recess_counts[key] += counts.get(key, 0)
        self._last_recess_counts["budget_exhausted"] |= counts["budget_exhausted"]
        self._last_closed_recess_count += sum(
            counts[key] for key in ("collinear", "trim", "perpendicular")
        )
        return result

    def _try_native_offset_outward(self, curve_loop, margin_internal, view):
        """Essaie d'abord l'offset natif sur le contour DEJA nettoyé.

        L'ancien échec de CreateViaOffset venait du contour brut avec ses
        micro-concavités. Après fermeture des petites gaines, la géométrie est
        plus simple et l'offset natif redevient une excellente solution :
        pas de booléens 3D, pas de faces coplanaires, angles propres.
        """
        from Autodesk.Revit.DB import CurveLoop

        if margin_internal <= 1e-9:
            return curve_loop

        base_area = abs(self._curve_loop_area(curve_loop, view))
        candidates = []

        for distance in (margin_internal, -margin_internal):
            try:
                candidate = CurveLoop.CreateViaOffset(
                    curve_loop,
                    distance,
                    view.ViewDirection,
                )
                candidate = self._linearize_curve_loop(
                    candidate,
                    view,
                )
                if not candidate.IsOpen():
                    area = abs(self._curve_loop_area(candidate, view))
                    if area > base_area + 1e-9:
                        candidates.append((area, candidate))
            except Exception:
                continue

        if not candidates:
            return None

        # Retenir l'expansion valide la plus compacte.
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _buffer_outward(self, curve_loop, margin_internal, view):
        """Construit la marge sans booléens 3D.

        Stratégie :
        1. essayer l'offset natif sur le contour nettoyé ;
        2. si Revit refuse encore, simplifier uniquement des concavités
           locales qui ajoutent peu de surface ;
        3. retenter l'offset après chaque simplification ;
        4. si aucun offset valide n'est obtenu, laisser le niveau supérieur
           appliquer le rectangle de secours.

        Cette approche évite les erreurs BooleanOperationsUtils liées aux
        solides quasi coplanaires observées dans Revit 2025.4.
        """
        if margin_internal <= 1e-9:
            return curve_loop

        straight_loop = self._linearize_curve_loop(
            curve_loop,
            view,
        )

        native_offset = self._try_native_offset_outward(
            straight_loop,
            margin_internal,
            view,
        )
        if native_offset is not None:
            return self._postprocess_offset(
                native_offset,
                view,
                margin_internal,
            )

        adaptive_offset = self._try_offset_after_concavity_cleanup(
            straight_loop,
            margin_internal,
            view,
        )
        if adaptive_offset is not None:
            return self._postprocess_offset(
                adaptive_offset,
                view,
                margin_internal,
            )

        raise ValueError(
            "Revit n'a pas réussi à créer une marge 2D valide, même après "
            "simplification contrôlée des petites concavités."
        )

    def _postprocess_offset(self, curve_loop, view, margin_internal):
        cleanup_internal = self._millimeters_to_internal(
            self._detail_cleanup_mm(
                self._internal_to_millimeters(margin_internal)
            )
        )
        return self._cleanup_small_notches(
            curve_loop,
            view,
            cleanup_internal,
        )

    def _try_offset_after_concavity_cleanup(
        self,
        curve_loop,
        margin_internal,
        view,
    ):
        """Retente une simplification locale sûre, jamais une corde diagonale."""
        cleaned = self._close_small_recesses(
            curve_loop, view,
            self._millimeters_to_internal(self.SHAFT_MAX_MOUTH_MM),
            self._millimeters_to_internal(self.SHAFT_MAX_DEPTH_MM),
            self._square_meters_to_internal_area(self.SHAFT_MAX_FILL_AREA_M2),
        )
        if cleaned is curve_loop:
            return None
        return self._try_native_offset_outward(cleaned, margin_internal, view)

    def _curve_loop_from_uv_points(self, uv_points, frame):
        from Autodesk.Revit.DB import XYZ

        world_points = [
            frame.to_world(point[0], point[1])
            for point in uv_points
        ]
        xyz_points = [
            XYZ(point[0], point[1], point[2])
            for point in world_points
        ]
        return self._curve_loop_from_points(
            xyz_points,
            max(self._short_curve_tolerance(), 1e-7),
        )

    def _cleanup_small_notches(self, curve_loop, view, tolerance_internal):
        """Même garde-fou de contenance après offset ; pas de corde de secours."""
        if tolerance_internal <= 1e-9:
            return curve_loop
        return self._close_small_recesses(
            curve_loop, view, tolerance_internal, tolerance_internal,
            tolerance_internal * tolerance_internal,
        )

    def _detail_cleanup_mm(self, margin_mm):
        """Tolérance graphique : petite, bornée et liée à la marge."""
        try:
            value = float(margin_mm)
        except Exception:
            value = 0.0

        return max(
            self.MIN_DETAIL_CLEANUP_MM,
            min(self.MAX_DETAIL_CLEANUP_MM, value),
        )

    @staticmethod
    def _curve_loop_from_points(points, tolerance):
        from Autodesk.Revit.DB import CurveLoop, Line

        values = list(points or [])
        if len(values) < 3:
            raise ValueError("Au moins trois points sont requis.")

        loop = CurveLoop()
        count = len(values)
        added = 0

        for index in range(count):
            start = values[index]
            end = values[(index + 1) % count]
            if start.DistanceTo(end) <= tolerance:
                continue
            loop.Append(Line.CreateBound(start, end))
            added += 1

        if added < 3 or loop.IsOpen():
            raise ValueError(
                "Impossible de construire une boucle fermée à partir des points."
            )

        return loop

    def _validate_crop_geometry(self, view, curve_loop):
        """Valide uniquement la géométrie, indépendamment de la capacité cible."""
        manager = view.GetCropRegionShapeManager()

        if not manager.IsCropRegionShapeValid(curve_loop):
            raise ValueError(
                "Le contour optimisé n'est pas géométriquement valide pour "
                "un crop Revit. Il doit être fermé, sans auto-intersection "
                "et composé uniquement de segments droits non nuls."
            )

    def _try_release_scope_box(self, view):
        """Retire le Scope Box uniquement sur la nouvelle vue si c'est possible."""
        try:
            from Autodesk.Revit.DB import BuiltInParameter, ElementId

            parameter = view.get_Parameter(
                BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP
            )
            if parameter is None:
                return False, "Aucun paramètre Scope Box n'est disponible."

            scope_box_id = parameter.AsElementId()
            if scope_box_id is None or scope_box_id == ElementId.InvalidElementId:
                return False, "Aucun Scope Box n'est affecté à la vue."

            if bool(parameter.IsReadOnly):
                return (
                    False,
                    "Le Scope Box hérité est en lecture seule sur cette vue.",
                )

            parameter.Set(ElementId.InvalidElementId)
            return True, "Le Scope Box de la vue créée a été retiré."
        except Exception as error:
            return False, "Impossible de retirer le Scope Box : {}.".format(error)

    def _build_rectangular_fallback(self, room_unique_ids, view, margin_mm):
        from Autodesk.Revit.DB import CurveLoop, Line, XYZ

        points = self._collect_boundary_points(room_unique_ids)
        frame = self._frame_from_view(view)

        projected = []
        for point in points:
            u, v = frame.project(point)
            projected.append((u, v, 0.0))

        bounds = CropBounds.from_points(projected)
        bounds = bounds.expanded(self._millimeters_to_internal(margin_mm))

        corners = [
            frame.to_world(bounds.min_x, bounds.min_y),
            frame.to_world(bounds.max_x, bounds.min_y),
            frame.to_world(bounds.max_x, bounds.max_y),
            frame.to_world(bounds.min_x, bounds.max_y),
        ]

        xyz_points = [
            XYZ(float(point[0]), float(point[1]), float(point[2]))
            for point in corners
        ]

        loop = CurveLoop()
        for start, end in (
            (xyz_points[0], xyz_points[1]),
            (xyz_points[1], xyz_points[2]),
            (xyz_points[2], xyz_points[3]),
            (xyz_points[3], xyz_points[0]),
        ):
            loop.Append(Line.CreateBound(start, end))

        return loop

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

    def _curve_loop_area(self, curve_loop, view):
        frame = self._frame_from_view(view)
        points = []

        for curve in curve_loop:
            tessellated = list(curve.Tessellate() or [])
            if not tessellated:
                continue

            for point in tessellated:
                uv = frame.project((point.X, point.Y, point.Z))
                if not points or self._distance_2d(points[-1], uv) > 1e-9:
                    points.append(uv)

        if len(points) < 3:
            return 0.0

        if self._distance_2d(points[0], points[-1]) <= 1e-9:
            points = points[:-1]

        area = 0.0
        count = len(points)
        for index in range(count):
            x1, y1 = points[index]
            x2, y2 = points[(index + 1) % count]
            area += (x1 * y2) - (x2 * y1)

        return area * 0.5

    @staticmethod
    def _curve_loop_average_z(curve_loop):
        values = []
        for curve in curve_loop:
            try:
                point = curve.GetEndPoint(0)
                values.append(point.Z)
            except Exception:
                continue
        return sum(values) / float(len(values)) if values else 0.0

    @staticmethod
    def _distance_2d(left, right):
        dx = float(left[0]) - float(right[0])
        dy = float(left[1]) - float(right[1])
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def _vector_length_2d(vector):
        return (
            (float(vector[0]) * float(vector[0]))
            + (float(vector[1]) * float(vector[1]))
        ) ** 0.5

    def _short_curve_tolerance(self):
        application = getattr(self.document, "Application", None)
        value = getattr(application, "ShortCurveTolerance", None)
        try:
            return float(value)
        except Exception:
            return 1e-7

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
    def _square_meters_to_internal_area(value):
        from Autodesk.Revit.DB import UnitTypeId, UnitUtils
        return UnitUtils.ConvertToInternalUnits(
            float(value),
            UnitTypeId.SquareMeters,
        )

    @staticmethod
    def _internal_to_millimeters(value):
        from Autodesk.Revit.DB import UnitTypeId, UnitUtils
        return UnitUtils.ConvertFromInternalUnits(
            float(value),
            UnitTypeId.Millimeters,
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
