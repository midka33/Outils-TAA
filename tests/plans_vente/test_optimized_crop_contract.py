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


def test_optimized_crop_extracts_outer_loop_and_offsets_it():
    text = SERVICE.read_text(encoding="utf-8")

    assert "GetEdgesAsCurveLoops" in text
    assert "CurveLoop.CreateViaOffset" in text
    assert "_extract_outer_union_loop" in text
    assert "_offset_outward" in text


def test_fallback_is_explicit_and_reported():
    service_text = SERVICE.read_text(encoding="utf-8")
    prototype_text = PROTOTYPE.read_text(encoding="utf-8")
    window_text = WINDOW.read_text(encoding="utf-8")

    assert "Rectangle de secours" in service_text
    assert "crop_mode" in prototype_text
    assert "warning" in prototype_text
    assert "result.warning" in window_text
    assert "result.crop_mode" in window_text
