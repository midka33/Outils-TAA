# -*- coding: utf-8 -*-
"""Barriere de securite temporaire apres crash natif Revit."""

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Annotations.panel" / "services"


def test_crash_trace_written_on_disk_and_flushed(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "taa_crash_trace_test", SERVICES / "crash_trace.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.TRACE_PATH = str(tmp_path / "trace.log")
    module.trace("BEFORE_DIMENSION_ENGINE", "Vue RDC", "2249", "geometry")
    content = Path(module.TRACE_PATH).read_text(encoding="utf-8")
    assert "BEFORE_DIMENSION_ENGINE" in content
    assert "2249" in content
    assert "geometry" in content


def test_no_ad_hoc_floor_solid_traversal_in_annotation_adapter():
    tree = ast.parse(
        (SERVICES / "annotations_service.py").read_text(encoding="utf-8"))
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef)
               and x.name == "GenericDimensions")
    methods = [x.name for x in cls.body if isinstance(x, ast.FunctionDef)]
    assert "_nearby_floor_edges" not in methods
    assert "_matching_floor_edge_reference" not in methods
    src = (SERVICES / "annotations_service.py").read_text(encoding="utf-8")
    assert "floor.get_Geometry" not in src
    assert "diagnostic_room_uid=None" in src


def test_launcher_enforces_one_view_one_room_before_running():
    source = (SERVICES / "launcher.py").read_text(encoding="utf-8")
    assert "diagnostic_room_uid=diagnostic_room_uid" in source
    assert "Diagnostic securise : choisir UNE piece hors groupe" in source
    assert "MODE DIAGNOSTIC APRES CRASH REVIT" in source
