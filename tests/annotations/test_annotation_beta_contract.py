# -*- coding: utf-8 -*-
"""Tests statiques hors Revit ; ne remplacent pas la recette Revit 2025.4."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Annotations.panel"


def test_scripts_and_services_compile():
    paths = [
        PANEL / "Cotation.pushbutton" / "script.py",
        PANEL / "Etiquetage.pushbutton" / "script.py",
        PANEL / "services" / "launcher.py",
        PANEL / "services" / "annotations_service.py",
    ]
    for path in paths:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_both_buttons_use_one_launcher():
    cotation = (PANEL / "Cotation.pushbutton" / "script.py").read_text(encoding="utf-8")
    etiquetage = (PANEL / "Etiquetage.pushbutton" / "script.py").read_text(encoding="utf-8")
    assert 'run("dims")' in cotation
    assert 'run("tags")' in etiquetage
    assert "from launcher import run" in cotation
    assert "from launcher import run" in etiquetage


def test_shared_engines_and_atomic_group_rollback():
    source = (PANEL / "services" / "annotations_service.py").read_text(encoding="utf-8")
    assert "from dimension_service import DimensionService" in source
    assert "from room_tag_service import RoomTagService" in source
    assert "scope.RollBack()" in source
    assert "GetAvailableAttachedDetailGroupTypeIds" in source
    assert "NewDetailCurve" in source
    assert "ShowAttachedDetailGroups" in source
