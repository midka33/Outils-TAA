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
    assert "def _cleanup_small_notches(" in text
    assert "MIN_DETAIL_CLEANUP_MM = 300.0" in text
    assert "MAX_DETAIL_CLEANUP_MM = 600.0" in text


def test_small_shaft_recesses_are_closed_before_margin():
    text = SERVICE.read_text(encoding="utf-8")

    assert '"Fermeture des petites gaines et retraits"' in text
    assert "def _close_small_recesses(" in text
    assert "SHAFT_MAX_MOUTH_MM = 3500.0" in text
    assert "SHAFT_MAX_DEPTH_MM = 2000.0" in text
    assert "SHAFT_MAX_FILL_AREA_M2 = 5.0" in text
    assert text.index("Fermeture des petites gaines et retraits") < text.index(
        "Construction de la marge robuste"
    )










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






def test_native_offset_is_attempted_before_adaptive_cleanup():
    text = SERVICE.read_text(encoding="utf-8")

    buffer_start = text.index("def _buffer_outward(")
    cleanup_start = text.index("def _cleanup_small_notches(", buffer_start)
    block = text[buffer_start:cleanup_start]

    native_call = block.index("native_offset = self._try_native_offset_outward")
    adaptive_call = block.index("adaptive_offset = self._try_offset_after_concavity_cleanup")
    assert native_call < adaptive_call












def test_revit_adapter_uses_local_engine_without_wall_or_chord_fallback():
    text = SERVICE.read_text(encoding="utf-8")
    assert "local_geometry.close_pockets(" in text
    for obsolete in ("RevitLinkInstance", "peripheral_wall", "wall_guides",
                     "_bridge_candidate_polygons", "_collect_opposite_wall"):
        assert obsolete not in text
    assert "SHAFT_MAX_EXTENSION_MM = 3500.0" in text
    # Both cleanup paths after/before native offset delegate to the safe engine.
    for name in ("_try_offset_after_concavity_cleanup", "_cleanup_small_notches"):
        node = next(n for n in ast.walk(ast.parse(text))
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        block = "\n".join(text.splitlines()[node.lineno-1:node.end_lineno])
        assert "self._close_small_recesses(" in block


def test_diagnostics_distinguish_all_three_repair_types():
    text = SERVICE.read_text(encoding="utf-8")
    for word in ("colinéaire", "Trim/Extend", "perpendiculaire", "Nettoyage avant échec"):
        assert word in text
    assert 'mode.startswith("Contour optimisé")' in text
