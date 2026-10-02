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


def test_optimized_crop_extracts_outer_loop_and_builds_robust_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert "GetEdgesAsCurveLoops" in text
    assert "_extract_outer_union_loop" in text
    assert "def _buffer_outward(" in text
    assert "CreateViaOffset" not in text
    assert "cap_radius" in text
    assert "BooleanOperationsType.Union" in text


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
        "Application de la marge"
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


def test_robust_margin_uses_edge_strips_and_vertex_caps():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _buffer_outward(" in text
    assert "strip_loop" in text
    assert "cap_points" in text
    assert "sides = 8" in text
    assert "math.cos(math.pi / float(sides))" in text
    assert "BooleanOperationsUtils.ExecuteBooleanOperation" in text
    assert "CurveLoop.CreateViaOffset" not in text


def test_large_margin_uses_square_caps_and_notch_cleanup():
    text = SERVICE.read_text(encoding="utf-8")

    assert "Raccords carrés" in text
    assert "right_delta" in text
    assert "up_delta" in text
    assert "def _cleanup_small_notches(" in text
    assert "def _is_u_turn_notch(" in text
    assert "MIN_DETAIL_CLEANUP_MM = 300.0" in text
    assert "MAX_DETAIL_CLEANUP_MM = 600.0" in text


def test_small_shaft_recesses_are_closed_before_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert '"Fermeture des petites gaines et retraits"' in text
    assert "def _close_small_recesses(" in text
    assert "def _concave_vertex_indices(" in text
    assert "def _bridge_candidate_polygons(" in text
    assert "def _max_chain_distance_to_bridge(" in text
    assert "SHAFT_MAX_MOUTH_MM = 1500.0" in text
    assert "SHAFT_MAX_DEPTH_MM = 1500.0" in text
    assert "SHAFT_MAX_FILL_AREA_M2 = 2.0" in text
    assert text.index("Fermeture des petites gaines et retraits") < text.index(
        "Construction de la marge robuste"
    )


def test_shaft_detection_is_independent_from_crop_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _point_in_polygon(" in text
    assert "def _vertices_are_adjacent(" in text
    assert "SHAFT_MAX_MOUTH_MM = 2000.0" in text
    assert "SHAFT_MAX_DEPTH_MM = 2000.0" in text
    assert "SHAFT_MAX_FILL_AREA_M2 = 3.0" in text
    assert "for i in range(count):" in text
    assert "for j in range(i + 1, count):" in text
    assert "if self._point_in_polygon(midpoint, uv_points):" in text
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
