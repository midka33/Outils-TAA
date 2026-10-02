# -*- coding: utf-8 -*-
from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "crop_geometry_service.py"
PROTOTYPE = PANEL / "services" / "prototype_view_service.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"


def test_optimized_crop_python_files_parse():
    for path in (SERVICE, PROTOTYPE, WINDOW):
        text = path.read_text(encoding="utf-8")
        assert text.splitlines()[0] == "# -*- coding: utf-8 -*-"
        ast.parse(text)


def test_optimized_crop_uses_room_center_boundaries_and_boolean_union():
    text = SERVICE.read_text(encoding="utf-8")

    assert "SpatialElementBoundaryLocation.Center" in text
    assert "CreateExtrusionGeometry" in text
    assert "BooleanOperationsUtils.ExecuteBooleanOperation" in text
    assert "BooleanOperationsType.Union" in text


def test_optimized_crop_extracts_outer_loop_and_builds_margin_in_2d():
    text = SERVICE.read_text(encoding="utf-8")

    assert "GetEdgesAsCurveLoops" in text
    assert "_extract_outer_union_loop" in text
    assert "def _buffer_outward(" in text
    assert "def _try_native_offset_outward(" in text
    assert "CurveLoop.CreateViaOffset" in text
    assert "def _try_offset_after_concavity_cleanup(" in text


def test_fallback_is_explicit_and_reported():
    service_text = SERVICE.read_text(encoding="utf-8")
    prototype_text = PROTOTYPE.read_text(encoding="utf-8")
    window_text = WINDOW.read_text(encoding="utf-8")

    assert "Rectangle de secours" in service_text
    assert "crop_mode" in prototype_text
    assert "warning" in prototype_text
    assert "result.warning" in window_text
    assert "result.crop_mode" in window_text


def test_crop_is_linearized_to_straight_segments_before_revit_validation():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _linearize_curve_loop(" in text
    assert "Tessellate()" in text
    assert "Line.CreateBound" in text
    assert "ShortCurveTolerance" in text
    assert "Linéarisation du contour extérieur" in text
    assert "Linéarisation finale" in text
    assert text.index("Linéarisation du contour extérieur") < text.index(
        "Construction de la marge robuste"
    )
    assert "Linéarisation finale" in text
    assert "def apply_to_view(" in text
    assert "manager.IsCropRegionShapeValid(selected_loop)" in text


def test_crop_fallback_reports_exact_failed_stage():
    text = SERVICE.read_text(encoding="utf-8")

    assert "class CropGeometryStageError" in text
    assert "Étape en échec" in text
    assert '"Union géométrique des pièces"' in text
    assert '"Extraction du contour extérieur"' in text
    assert "Étape en échec" in text


def test_crop_capability_is_checked_on_created_target_view():
    text = SERVICE.read_text(encoding="utf-8")

    build_start = text.index("def build_optimized_crop(")
    apply_start = text.index("def apply_to_view(")
    build_block = text[build_start:apply_start]
    apply_block = text[apply_start:]

    assert "CanHaveShape" not in build_block
    assert "CanHaveShape" in apply_block
    assert "_try_release_scope_box" in apply_block
    assert "VIEWER_VOLUME_OF_INTEREST_CROP" in text
    assert "fallback_curve_loop" in text


def test_margin_no_longer_uses_boolean_buffer():
    text = SERVICE.read_text(encoding="utf-8")

    buffer_start = text.index("def _buffer_outward(")
    cleanup_start = text.index("def _cleanup_small_notches(", buffer_start)
    buffer_block = text[buffer_start:cleanup_start]

    assert "BooleanOperationsUtils." not in buffer_block
    assert "ExecuteBooleanOperation" not in buffer_block
    assert "strip_loop" not in buffer_block
    assert "cap_points" not in buffer_block
    assert "_try_native_offset_outward" in buffer_block
    assert "_try_offset_after_concavity_cleanup" in buffer_block


def test_large_margin_uses_adaptive_concavity_cleanup():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _try_offset_after_concavity_cleanup(" in text
    assert "def _point_distance_to_segment(" in text
    assert "def _cleanup_small_notches(" in text
    assert "MIN_DETAIL_CLEANUP_MM = 300.0" in text
    assert "MAX_DETAIL_CLEANUP_MM = 600.0" in text


def test_small_shaft_recesses_are_closed_before_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert '"Fermeture des petites gaines et retraits"' in text
    assert "def _close_small_recesses(" in text
    assert "def _concave_vertex_indices(" in text
    assert "def _bridge_candidate_polygons(" in text
    assert "def _max_chain_distance_to_bridge(" in text
    assert "SHAFT_MAX_MOUTH_MM = 3500.0" in text
    assert "SHAFT_MAX_DEPTH_MM = 2000.0" in text
    assert "SHAFT_MAX_FILL_AREA_M2 = 5.0" in text
    assert text.index("Fermeture des petites gaines et retraits") < text.index(
        "Construction de la marge robuste"
    )


def test_shaft_detection_is_independent_from_crop_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _point_in_polygon(" in text
    assert "def _vertices_are_adjacent(" in text
    assert "SHAFT_MAX_MOUTH_MM = 3500.0" in text
    assert "SHAFT_MAX_DEPTH_MM = 2000.0" in text
    assert "SHAFT_MAX_FILL_AREA_M2 = 5.0" in text
    assert "for i in range(count):" in text
    assert "for j in range(i + 1, count):" in text
    assert "def _wall_aligned_bridge_paths(" in text
    assert "if not self._point_in_polygon(" in text
    assert text.index("Fermeture des petites gaines et retraits") < text.index(
        "Construction de la marge robuste"
    )


def test_shaft_cleanup_is_conservative_and_reversible():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _is_simple_polygon(" in text
    assert "def _forward_chain_indices(" in text
    assert "def _replace_chain_with_bridge(" in text
    assert "if not self._is_simple_polygon(candidate):" in text
    assert "return curve_loop" in text


def test_polygon_area_helper_is_static():
    text = SERVICE.read_text(encoding="utf-8")
    assert "@staticmethod\n    def _polygon_signed_area(points):" in text


def test_shaft_cleanup_helpers_are_defined():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _vertices_are_adjacent(" in text
    assert "def _point_in_polygon(" in text


def test_private_self_calls_have_matching_methods():
    import re

    text = SERVICE.read_text(encoding="utf-8")
    definitions = set(
        re.findall(r"^\s+def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", text, re.M)
    )
    calls = set(
        re.findall(r"self\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", text)
    )

    missing = sorted(
        name for name in calls
        if name.startswith("_") and name not in definitions
    )
    assert missing == []


def test_shaft_cleaner_tests_all_non_adjacent_vertices_safely():
    text = SERVICE.read_text(encoding="utf-8")

    assert "for i in range(count):" in text
    assert "for j in range(i + 1, count):" in text
    assert "if self._vertices_are_adjacent(i, j, count):" in text
    assert "def _wall_aligned_bridge_paths(" in text
    assert "if not self._point_in_polygon(" in text
    assert "if not self._is_simple_polygon(candidate):" in text
    assert "fill_area = candidate_area - original_area" in text


def test_shaft_cleanup_reports_how_many_pockets_were_closed():
    text = SERVICE.read_text(encoding="utf-8")

    assert "_last_closed_recess_count" in text
    assert "gaine(s)/retrait(s) comblé(s)" in text


def test_native_offset_is_attempted_before_adaptive_cleanup():
    text = SERVICE.read_text(encoding="utf-8")

    buffer_start = text.index("def _buffer_outward(")
    cleanup_start = text.index("def _cleanup_small_notches(", buffer_start)
    block = text[buffer_start:cleanup_start]

    native_call = block.index("native_offset = self._try_native_offset_outward")
    adaptive_call = block.index("adaptive_offset = self._try_offset_after_concavity_cleanup")
    assert native_call < adaptive_call


def test_shaft_closure_prefers_opposite_wall_faces_over_diagonal_chords():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _collect_opposite_wall_face_guides(" in text
    assert "wall.Orientation" in text
    assert "wall.Width" in text
    assert "def _wall_aligned_bridge_paths(" in text
    assert "WALL_GUIDE_EXTENSION_MM = 600.0" in text
    assert "def _bridge_matches_local_direction(" in text
    assert "def _bridge_candidate_polygons_with_path(" in text
    assert "_last_wall_aligned_recess_count" in text
    assert "fermeture(s) alignée(s) sur mur" in text

    close_start = text.index("def _close_small_recesses(")
    close_end = text.index("def _vertices_are_adjacent(", close_start)
    close_block = text[close_start:close_end]

    assert "bridge_options.append((0, bridge_path))" in close_block
    assert "if self._bridge_matches_local_direction(" in close_block

    wall_start = text.index("def _wall_aligned_bridge_paths(")
    wall_end = text.index("def _bridge_matches_local_direction(", wall_start)
    wall_block = text[wall_start:wall_end]

    # Une bouche diagonale ne doit plus exclure le mur guide : c'était
    # précisément la cause du fallback observé dans Revit.
    assert "mouth_vector" not in wall_block
    assert "parallel_sin" not in wall_block
    assert "_project_point_to_line(" in wall_block


def test_fallback_reports_wall_guided_cleanup_counts():
    text = SERVICE.read_text(encoding="utf-8")

    assert "Nettoyage avant échec" in text
    assert "_last_closed_recess_count" in text
    assert "_last_wall_aligned_recess_count" in text


def test_selected_peripheral_wall_type_uses_fast_wall_strip_union():
    text = SERVICE.read_text(encoding="utf-8")

    assert "peripheral_wall_type_unique_id=None" in text
    assert "def _collect_peripheral_wall_strip_loops(" in text
    assert "wall_type_unique_id != selected_unique_id" in text
    assert "supplemental_loops=None" in text
    assert "list(room_loops or []) + list(supplemental_loops or [])" in text
    assert "if peripheral_wall_type_unique_id:" in text
    assert "clean_outer_loop = straight_outer_loop" in text
    assert "_last_peripheral_wall_count" in text
    assert "Murs périphériques utilisés" in text

    # Le type choisi est recherché près du contour extérieur des Rooms :
    # il n'a plus besoin d'être directement BoundarySegment.ElementId.
    collector_start = text.index("def _collect_peripheral_wall_strip_loops(")
    collector_end = text.index(
        "def _collect_opposite_wall_face_guides(",
        collector_start,
    )
    collector = text[collector_start:collector_end]

    assert "FilteredElementCollector(source_document)" in collector
    assert "PERIPHERAL_WALL_SEARCH_MM = 1000.0" in text
    assert "PERIPHERAL_WALL_PARALLEL_SIN" in text
    assert "def _segment_distance_2d(" in text
    assert "segment.ElementId" not in collector
    assert "room_outer_loop" in collector


def test_peripheral_wall_search_supports_linked_revit_sources():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _resolve_peripheral_wall_source(" in text
    assert 'if value.startswith("LINK|"):' in text
    assert "GetLinkDocument()" in text
    assert "GetTotalTransform()" in text
    assert "source_transform.OfPoint(wall_start)" in text
    assert "source_transform.OfVector(" in text
    assert "def _bounding_box_host_z_range(" in text
    assert "_last_peripheral_wall_source" in text
    assert "Source murs : {}." in text
