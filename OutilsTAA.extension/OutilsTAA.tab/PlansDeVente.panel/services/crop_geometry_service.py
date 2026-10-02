# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Construction d'un contour de crop optimisé à partir des pièces du logement."""

from plans_vente.crop_bounds import CropBounds
from plans_vente.view_frame import ViewFrame


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
    SHAFT_MAX_MOUTH_MM = 2000.0
    SHAFT_MAX_DEPTH_MM = 2000.0
    SHAFT_MAX_FILL_AREA_M2 = 3.0

    def __init__(self, document):
        if document is None:
            raise ValueError("Document Revit manquant.")
        self.document = document

    def build_optimized_crop(self, room_unique_ids, view, margin_mm):
        """Construit un contour extérieur compatible avec les crops Revit.

        Important : ViewCropRegionShapeManager n'accepte que des segments
        droits pour une forme de crop. Les boucles issues des pièces ou d'une
        opération booléenne sont donc linéarisées avant validation.
        """
        if view is None:
            raise ValueError("Vue Revit manquante pour calculer le crop.")

        margin_internal = self._millimeters_to_internal(margin_mm)
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
            union_solid = self._stage(
                "Union géométrique des pièces",
                self._union_room_solids,
                room_loops,
                view,
            )
            outer_loop = self._stage(
                "Extraction du contour extérieur",
                self._extract_outer_union_loop,
                union_solid,
                view,
                reference_z,
            )

            straight_outer_loop = self._stage(
                "Linéarisation du contour extérieur",
                self._linearize_curve_loop,
                outer_loop,
                view,
            )

            clean_outer_loop = self._stage(
                "Fermeture des petites gaines et retraits",
                self._close_small_recesses,
                straight_outer_loop,
                view,
                self._millimeters_to_internal(self.SHAFT_MAX_MOUTH_MM),
                self._millimeters_to_internal(self.SHAFT_MAX_DEPTH_MM),
                self._square_meters_to_internal_area(
                    self.SHAFT_MAX_FILL_AREA_M2
                ),
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

            return OptimizedCropResult(
                curve_loop=final_loop,
                mode="Contour optimisé",
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
                    "Étape en échec : {}"
                ).format(error),
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

        if mode == "Contour optimisé" and not bool(manager.CanHaveShape):
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

    def _union_room_solids(self, room_loops, view):
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
        for curve_loop in room_loops:
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

    def _close_small_recesses(
        self,
        curve_loop,
        view,
        max_mouth_internal,
        max_depth_internal,
        max_fill_area_internal,
    ):
        """Ferme uniquement des poches orthogonales clairement identifiées.

        La version précédente testait toutes les paires de sommets et pouvait
        fabriquer un contour invalide. Cette version est volontairement plus
        conservatrice : elle cherche une séquence locale en forme de poche
        (entrée -> fond -> sortie) et ne remplace la chaîne que si le pont
        direct est sûr et le polygone résultant reste simple.
        """
        frame = self._frame_from_view(view)
        xyz_points = self._tessellated_loop_points(curve_loop)
        xyz_points = self._remove_near_duplicates(xyz_points)
        if len(xyz_points) < 5:
            return curve_loop

        uv_points = [
            frame.project((point.X, point.Y, point.Z))
            for point in xyz_points
        ]

        changed = True
        safety = 0

        while changed and len(uv_points) >= 5 and safety < 50:
            changed = False
            safety += 1
            count = len(uv_points)
            original_area = abs(self._polygon_signed_area(uv_points))
            orientation = self._polygon_signed_area(uv_points)
            if abs(orientation) <= 1e-12:
                break

            best = None

            # Une gaine / poche typique est délimitée localement par deux
            # sommets concaves séparés de quelques sommets seulement.
            concave = self._concave_vertex_indices(
                uv_points,
                orientation,
            )

            for left_pos in range(len(concave)):
                for right_pos in range(left_pos + 1, len(concave)):
                    i = concave[left_pos]
                    j = concave[right_pos]

                    if self._vertices_are_adjacent(i, j, count):
                        continue

                    chain = self._forward_chain_indices(i, j, count)
                    if len(chain) > 7:
                        continue

                    mouth = self._distance_2d(
                        uv_points[i],
                        uv_points[j],
                    )
                    if mouth <= 1e-9 or mouth > max_mouth_internal:
                        continue

                    if self._bridge_intersects_polygon(
                        uv_points,
                        i,
                        j,
                    ):
                        continue

                    midpoint = (
                        (uv_points[i][0] + uv_points[j][0]) * 0.5,
                        (uv_points[i][1] + uv_points[j][1]) * 0.5,
                    )
                    if self._point_in_polygon(midpoint, uv_points):
                        continue

                    removed_chain = [
                        uv_points[index]
                        for index in chain
                    ]
                    depth = self._max_chain_distance_to_bridge(
                        removed_chain,
                        uv_points[i],
                        uv_points[j],
                    )
                    if depth > max_depth_internal:
                        continue

                    candidate = self._replace_chain_with_bridge(
                        uv_points,
                        i,
                        j,
                    )
                    if len(candidate) < 3:
                        continue

                    if not self._is_simple_polygon(candidate):
                        continue

                    candidate_area = abs(
                        self._polygon_signed_area(candidate)
                    )
                    fill_area = candidate_area - original_area
                    if (
                        fill_area <= 1e-9
                        or fill_area > max_fill_area_internal
                    ):
                        continue

                    score = (fill_area, mouth, depth)
                    if best is None or score < best[0]:
                        best = (score, candidate)

            if best is not None:
                uv_points = best[1]
                changed = True

        from Autodesk.Revit.DB import XYZ

        world_points = [
            frame.to_world(point[0], point[1])
            for point in uv_points
        ]
        xyz_result = [
            XYZ(point[0], point[1], point[2])
            for point in world_points
        ]

        result = self._curve_loop_from_points(
            xyz_result,
            max(self._short_curve_tolerance(), 1e-7),
        )

        # Sécurité finale : si le nettoyage produit malgré tout une boucle
        # géométriquement douteuse, on revient au contour d'origine plutôt que
        # de faire échouer tout le crop optimisé.
        if not self._is_simple_polygon(uv_points):
            return curve_loop

        return result

    @staticmethod
    def _forward_chain_indices(i, j, count):
        values = [i]
        index = i
        while index != j:
            index = (index + 1) % count
            values.append(index)
            if len(values) > count + 1:
                break
        return values

    @staticmethod
    def _replace_chain_with_bridge(points, i, j):
        values = list(points or [])
        count = len(values)
        if i > j:
            i, j = j, i
        return values[:i + 1] + values[j:]

    @classmethod
    def _is_simple_polygon(cls, points):
        values = list(points or [])
        count = len(values)
        if count < 3:
            return False

        for i in range(count):
            a = values[i]
            b = values[(i + 1) % count]

            for j in range(i + 1, count):
                c_index = j
                d_index = (j + 1) % count

                if i == c_index or i == d_index:
                    continue
                if (i + 1) % count == c_index or (i + 1) % count == d_index:
                    continue

                c = values[c_index]
                d = values[d_index]
                if cls._segments_intersect_2d(a, b, c, d):
                    return False

        return True

    def _polygon_signed_area(points):
        values = list(points or [])
        if len(values) < 3:
            return 0.0

        area = 0.0
        count = len(values)
        for index in range(count):
            x1, y1 = values[index]
            x2, y2 = values[(index + 1) % count]
            area += (x1 * y2) - (x2 * y1)
        return area * 0.5

    @staticmethod
    def _concave_vertex_indices(points, signed_area):
        values = list(points or [])
        count = len(values)
        if count < 4:
            return []

        orientation_sign = 1.0 if signed_area > 0.0 else -1.0
        result = []

        for index in range(count):
            previous = values[(index - 1) % count]
            current = values[index]
            following = values[(index + 1) % count]

            left = (
                current[0] - previous[0],
                current[1] - previous[1],
            )
            right = (
                following[0] - current[0],
                following[1] - current[1],
            )

            cross = (
                (left[0] * right[1])
                - (left[1] * right[0])
            )
            if (cross * orientation_sign) < -1e-9:
                result.append(index)

        return result

    def _bridge_intersects_polygon(self, points, i, j):
        count = len(points)
        a = points[i]
        b = points[j]

        for edge_index in range(count):
            next_index = (edge_index + 1) % count

            if edge_index in (i, j) or next_index in (i, j):
                continue

            c = points[edge_index]
            d = points[next_index]

            if self._segments_intersect_2d(a, b, c, d):
                return True

        return False

    @staticmethod
    def _bridge_candidate_polygons(points, i, j):
        if i > j:
            i, j = j, i

        first_chain = list(points[i:j + 1])
        second_chain = list(points[j:]) + list(points[:i + 1])

        # Chaque candidate garde une chaîne et remplace l'autre par le pont.
        # removed_chain est utilisée pour mesurer la profondeur de la poche.
        return [
            (first_chain, second_chain),
            (second_chain, first_chain),
        ]

    @staticmethod
    def _segments_intersect_2d(a, b, c, d):
        def orient(p, q, r):
            return (
                (q[0] - p[0]) * (r[1] - p[1])
                - (q[1] - p[1]) * (r[0] - p[0])
            )

        o1 = orient(a, b, c)
        o2 = orient(a, b, d)
        o3 = orient(c, d, a)
        o4 = orient(c, d, b)

        epsilon = 1e-9
        return (
            (o1 * o2) < -epsilon
            and (o3 * o4) < -epsilon
        )

    @staticmethod
    def _max_chain_distance_to_bridge(chain, bridge_start, bridge_end):
        values = list(chain or [])
        if not values:
            return 0.0

        ax, ay = bridge_start
        bx, by = bridge_end
        dx = bx - ax
        dy = by - ay
        denominator = (dx * dx) + (dy * dy)

        if denominator <= 1e-12:
            return float("inf")

        maximum = 0.0
        for point in values:
            px, py = point
            t = (
                ((px - ax) * dx)
                + ((py - ay) * dy)
            ) / denominator
            projection = (
                ax + (t * dx),
                ay + (t * dy),
            )
            distance = CropGeometryService._distance_2d(
                point,
                projection,
            )
            if distance > maximum:
                maximum = distance

        return maximum

    def _buffer_outward(self, curve_loop, margin_internal, view):
        """Dilate le contour sans dépendre de CurveLoop.CreateViaOffset.

        CreateViaOffset peut échouer brutalement quand une concavité ou un
        petit décrochement devient plus petit que la marge. Le buffer robuste
        construit à la place l'union de :
        - la surface du logement ;
        - une bande rectangulaire de largeur 2 x marge autour de chaque arête ;
        - un carré de raccord, aligné sur la vue, autour de chaque sommet.

        Les carrés évitent les artefacts "arrondis / crénelés" visibles avec
        les anciens raccords octogonaux lorsque la marge devient importante.
        """
        if margin_internal <= 1e-9:
            return curve_loop

        from Autodesk.Revit.DB import (
            BooleanOperationsType,
            BooleanOperationsUtils,
            CurveLoop,
            GeometryCreationUtilities,
            Line,
        )
        from System.Collections.Generic import List
        straight_loop = self._linearize_curve_loop(curve_loop, view)
        base_solid = self._solid_from_loop(straight_loop, view)
        result_solid = base_solid

        curves = list(straight_loop)
        if len(curves) < 3:
            raise ValueError(
                "Le contour ne contient pas assez de segments pour construire la marge."
            )

        tolerance = max(self._short_curve_tolerance(), 1e-7)

        # 1. Bandes autour de chaque arête.
        vertices = []
        for curve in curves:
            start = curve.GetEndPoint(0)
            end = curve.GetEndPoint(1)
            if start.DistanceTo(end) <= tolerance:
                continue

            if not vertices or start.DistanceTo(vertices[-1]) > tolerance:
                vertices.append(start)

            tangent = end.Subtract(start).Normalize()
            perpendicular = view.ViewDirection.CrossProduct(tangent).Normalize()
            delta = perpendicular.Multiply(margin_internal)

            p1 = start.Add(delta)
            p2 = end.Add(delta)
            p3 = end.Subtract(delta)
            p4 = start.Subtract(delta)

            strip_loop = self._curve_loop_from_points(
                (p1, p2, p3, p4),
                tolerance,
            )
            strip_solid = self._solid_from_loop(strip_loop, view)
            result_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                result_solid,
                strip_solid,
                BooleanOperationsType.Union,
            )

        if not vertices:
            raise ValueError(
                "Aucun sommet exploitable n'a été trouvé pour construire la marge."
            )

        # 2. Raccords carrés, alignés sur le repère de la vue.
        #
        # Le crop de plan de vente doit rester graphique et propre. Des caps
        # octogonaux créaient des facettes visibles à 200/500 mm. Le carré
        # produit des angles francs et reste volontairement un peu plus large
        # en diagonale que la marge saisie, jamais plus étroit.
        right = view.RightDirection.Normalize()
        up = view.UpDirection.Normalize()
        right_delta = right.Multiply(margin_internal)
        up_delta = up.Multiply(margin_internal)

        for vertex in vertices:
            cap_points = [
                vertex.Add(right_delta).Add(up_delta),
                vertex.Subtract(right_delta).Add(up_delta),
                vertex.Subtract(right_delta).Subtract(up_delta),
                vertex.Add(right_delta).Subtract(up_delta),
            ]

            cap_loop = self._curve_loop_from_points(
                cap_points,
                tolerance,
            )
            cap_solid = self._solid_from_loop(cap_loop, view)
            result_solid = BooleanOperationsUtils.ExecuteBooleanOperation(
                result_solid,
                cap_solid,
                BooleanOperationsType.Union,
            )

        reference_z = self._curve_loop_average_z(straight_loop)
        buffered_loop = self._extract_outer_union_loop(
            result_solid,
            view,
            reference_z,
        )

        buffered_loop = self._linearize_curve_loop(
            buffered_loop,
            view,
        )

        cleanup_internal = self._millimeters_to_internal(
            self._detail_cleanup_mm(
                self._internal_to_millimeters(margin_internal)
            )
        )
        return self._cleanup_small_notches(
            buffered_loop,
            view,
            cleanup_internal,
        )

    def _cleanup_small_notches(self, curve_loop, view, tolerance_internal):
        """Supprime les petits détours en U qui n'améliorent pas le cadrage.

        Le crop représente l'enveloppe graphique du logement, pas chaque
        décrochement créé par une gaine ou une pièce non modélisée. Cette
        passe ne touche qu'aux motifs rectangulaires courts.
        """
        if tolerance_internal <= 1e-9:
            return curve_loop

        frame = self._frame_from_view(view)
        points_xyz = self._tessellated_loop_points(curve_loop)
        points_xyz = self._remove_near_duplicates(points_xyz)

        if len(points_xyz) < 4:
            return curve_loop

        points_uv = [
            frame.project((point.X, point.Y, point.Z))
            for point in points_xyz
        ]

        changed = True
        safety = 0
        while changed and len(points_uv) >= 4 and safety < 100:
            changed = False
            safety += 1
            count = len(points_uv)

            for index in range(count):
                p0 = points_uv[index % count]
                p1 = points_uv[(index + 1) % count]
                p2 = points_uv[(index + 2) % count]
                p3 = points_uv[(index + 3) % count]

                if not self._is_u_turn_notch(
                    p0,
                    p1,
                    p2,
                    p3,
                    tolerance_internal,
                ):
                    continue

                remove_indices = sorted(
                    [
                        (index + 1) % count,
                        (index + 2) % count,
                    ],
                    reverse=True,
                )
                for remove_index in remove_indices:
                    points_uv.pop(remove_index)

                changed = True
                break

        if len(points_uv) < 3:
            return curve_loop

        world_points = [
            frame.to_world(point[0], point[1])
            for point in points_uv
        ]

        from Autodesk.Revit.DB import XYZ
        xyz_points = [
            XYZ(point[0], point[1], point[2])
            for point in world_points
        ]
        return self._curve_loop_from_points(
            xyz_points,
            max(self._short_curve_tolerance(), 1e-7),
        )

    @staticmethod
    def _is_u_turn_notch(p0, p1, p2, p3, tolerance):
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        v3 = (p3[0] - p2[0], p3[1] - p2[1])
        bridge = (p3[0] - p0[0], p3[1] - p0[1])

        l1 = CropGeometryService._vector_length_2d(v1)
        l2 = CropGeometryService._vector_length_2d(v2)
        l3 = CropGeometryService._vector_length_2d(v3)
        lb = CropGeometryService._vector_length_2d(bridge)

        if min(l1, l2, l3, lb) <= 1e-9:
            return False

        parallel_13 = abs(
            (v1[0] * v3[1]) - (v1[1] * v3[0])
        ) / (l1 * l3)
        opposite_13 = (
            (v1[0] * v3[0]) + (v1[1] * v3[1])
        ) < 0.0

        perpendicular_12 = abs(
            (v1[0] * v2[0]) + (v1[1] * v2[1])
        ) / (l1 * l2)

        bridge_parallel_2 = abs(
            (bridge[0] * v2[1]) - (bridge[1] * v2[0])
        ) / (lb * l2)

        if (
            parallel_13 > 1e-3
            or not opposite_13
            or perpendicular_12 > 1e-3
            or bridge_parallel_2 > 1e-3
        ):
            return False

        depth = min(l1, l3)
        width = l2

        return depth <= tolerance or width <= tolerance

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

    def _solid_from_loop(self, curve_loop, view):
        from Autodesk.Revit.DB import CurveLoop, GeometryCreationUtilities
        from System.Collections.Generic import List

        loops = List[CurveLoop]()
        loops.Add(curve_loop)

        solid = GeometryCreationUtilities.CreateExtrusionGeometry(
            loops,
            view.ViewDirection,
            self.BOOLEAN_EXTRUSION_HEIGHT,
        )
        if solid is None or solid.Volume <= 1e-9:
            raise ValueError(
                "Impossible de créer le solide temporaire utilisé pour la marge."
            )
        return solid

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
