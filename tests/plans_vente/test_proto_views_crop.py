# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"


def test_new_python_files_parse_and_keep_encoding_header():
    paths = [
        ROOT / "OutilsTAA.extension" / "lib" / "plans_vente" / "crop_bounds.py",
        ROOT / "OutilsTAA.extension" / "lib" / "plans_vente" / "view_frame.py",
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


def test_crop_uses_view_coordinate_system_and_true_room_union():
    geometry_text = (PANEL / "services" / "crop_geometry_service.py").read_text(
        encoding="utf-8"
    )
    prototype_text = (PANEL / "services" / "prototype_view_service.py").read_text(
        encoding="utf-8"
    )

    assert "RightDirection" in geometry_text
    assert "UpDirection" in geometry_text
    assert "ViewFrame" in geometry_text
    assert "SpatialElementBoundaryLocation.Center" in geometry_text
    assert "CreateExtrusionGeometry" in geometry_text
    assert "BooleanOperationsUtils.ExecuteBooleanOperation" in geometry_text
    assert "CurveLoop.CreateViaOffset" in geometry_text
    assert "build_optimized_crop" in prototype_text



def test_prototype_needs_only_housing_source_view_and_margin():
    for path in (PANEL / "ui" / "plans_vente.xaml",
                 PANEL / "ui" / "plans_vente_window.py",
                 PANEL / "services" / "plans_vente_controller.py",
                 PANEL / "services" / "prototype_view_service.py"):
        text = path.read_text(encoding="utf-8")
        for obsolete in ("PeripheralWallType", "peripheral_wall_type", "RevitLinkInstance"):
            assert obsolete not in text
    text = (PANEL / "ui" / "plans_vente.xaml").read_text(encoding="utf-8")
    assert 'x:Name="SourceViewCombo"' in text
    assert 'x:Name="CropMarginTextBox"' in text
    assert 'Content="Créer le contour optimisé"' in text
