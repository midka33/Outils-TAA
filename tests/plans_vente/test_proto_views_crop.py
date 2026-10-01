# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"


def test_new_python_files_parse_and_keep_encoding_header():
    paths = [
        ROOT / "OutilsTAA.extension" / "lib" / "plans_vente" / "crop_bounds.py",
        PANEL / "services" / "plan_view_service.py",
        PANEL / "services" / "crop_geometry_service.py",
        PANEL / "services" / "prototype_view_service.py",
        PANEL / "services" / "plans_vente_controller.py",
        PANEL / "ui" / "plans_vente_window.py",
        PANEL / "PlansDeVente.pushbutton" / "script.py",
    ]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.splitlines()[0] == "# -*- coding: utf-8 -*-"
        ast.parse(text)


def test_xaml_handlers_for_prototype_exist():
    xaml_path = PANEL / "ui" / "plans_vente.xaml"
    py_path = PANEL / "ui" / "plans_vente_window.py"

    ET.parse(str(xaml_path))
    python_text = py_path.read_text(encoding="utf-8")

    for handler in (
        "HousingSelectionChanged",
        "SourceViewChanged",
        "CreatePrototype_Click",
    ):
        assert "def {}(".format(handler) in python_text


def test_prototype_service_uses_dependent_view_and_unique_ids():
    service_text = (PANEL / "services" / "prototype_view_service.py").read_text(
        encoding="utf-8"
    )
    geometry_text = (PANEL / "services" / "crop_geometry_service.py").read_text(
        encoding="utf-8"
    )

    assert "ViewDuplicateOption.AsDependent" in service_text
    assert "room_unique_ids" in service_text
    assert "GetCropRegionShapeManager" in geometry_text
    assert "SetCropShape" in geometry_text
