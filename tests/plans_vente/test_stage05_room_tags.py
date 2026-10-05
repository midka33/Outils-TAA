# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

from plans_vente.tag_positioning import (
    boxes_overlap,
    ordered_candidate_points,
    polygon_centroid,
)


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "room_tag_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"


def test_polygon_centroid_for_rectangle():
    value = polygon_centroid([(0, 0), (4, 0), (4, 2), (0, 2)])
    assert abs(value[0] - 2.0) < 1e-9
    assert abs(value[1] - 1.0) < 1e-9


def test_candidate_points_start_near_room_center_and_keep_location_fallback():
    points = ordered_candidate_points(
        [(0, 0), (10, 0), (10, 6), (0, 6)],
        location_point=(2, 2),
    )
    assert points[0] == (5.0, 3.0)
    assert (2.0, 2.0) in points
    assert len(points) == len(set(points))


def test_boxes_overlap_contract():
    assert boxes_overlap((0, 0, 2, 2), (1, 1, 3, 3))
    assert not boxes_overlap((0, 0, 1, 1), (2, 2, 3, 3))
    assert boxes_overlap((0, 0, 1, 1), (1.05, 0, 2, 1), padding=0.1)


def test_room_tag_service_uses_verified_revit_api_contract():
    text = SERVICE.read_text(encoding="utf-8")
    ast.parse(text)
    for token in (
        "RoomTagType",
        "NewRoomTag",
        "LinkElementId",
        "UV(",
        "IsPointInRoom",
        "TagHeadPosition",
        "RoomTagType = tag_type",
        "TaggedLocalRoomId",
        "get_BoundingBox",
        "RevitTransaction",
    ):
        assert token in text


def test_room_tag_target_is_dependent_pdv_view_for_selected_housing():
    text = SERVICE.read_text(encoding="utf-8")
    assert "GetPrimaryViewId()" in text
    assert 'prefix = "PDV PROTO - {} - "' in text
    assert "ElementId.InvalidElementId" in text


def test_room_tag_ui_exposes_view_type_and_creation_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    for name in (
        "RoomTagViewCombo",
        "RoomTagTypeCombo",
        "RoomTagInfoText",
        "CreateRoomTagsButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'Click="CreateRoomTags_Click"' in xaml
    assert 'SelectionChanged="RoomTagChoiceChanged"' in xaml
    assert "def CreateRoomTags_Click(" in window
    assert "def _load_room_tag_views(" in window


def test_controller_keeps_room_tag_api_outside_ui_and_business_layer():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "self.room_tag_service = room_tag_service" in text
    assert "def room_tag_types(" in text
    assert "def room_tag_target_views(" in text
    assert "def create_room_tags(" in text
    assert "NewRoomTag" not in text


def test_base_collision_logic_is_ready_for_future_dimension_exclusion_boxes():
    text = SERVICE.read_text(encoding="utf-8")
    assert "exclusion_boxes=None" in text
    assert "occupied_boxes = list(exclusion_boxes or [])" in text
    assert "boxes_overlap" in text
    assert "COLLISION_PADDING_MM" in text


def test_tag_type_names_use_ironpython_safe_element_type_name():
    text = SERVICE.read_text(encoding="utf-8")
    assert "Element.Name.GetValue(element_type)" in text
    assert "BuiltInParameter.SYMBOL_NAME_PARAM" in text
    assert "BuiltInParameter.SYMBOL_FAMILY_NAME_PARAM" in text
    assert "FamilyName" in text
    assert "_room_tag_type_name(tag_type)" in text
    assert "_room_tag_family_name(tag_type)" in text


def test_room_tag_type_label_never_becomes_visually_empty():
    text = SERVICE.read_text(encoding="utf-8")
    assert "<Type d'étiquette sans nom>" in text
