# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

from plans_vente.dimension_geometry import (
    dominant_dimension_pairs,
    representative_length_indexes,
    segment_match_metrics,
)


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "dimension_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"
SCRIPT = PANEL / "PlansDeVente.pushbutton" / "script.py"
DOC = ROOT / "docs" / "20_Plans_de_Vente.md"


def test_rectangle_produces_two_principal_dimension_pairs():
    segments = [
        (0.0, 0.0, 6.0, 0.0),
        (6.0, 0.0, 6.0, 3.0),
        (6.0, 3.0, 0.0, 3.0),
        (0.0, 3.0, 0.0, 0.0),
    ]
    pairs = dominant_dimension_pairs(segments)

    assert len(pairs) == 2
    distances = sorted(round(pair.distance, 6) for pair in pairs)
    assert distances == [3.0, 6.0]


def test_small_recess_segment_is_not_selected_as_general_dimension():
    segments = [
        (0.0, 0.0, 8.0, 0.0),
        (8.0, 0.0, 8.0, 5.0),
        (8.0, 5.0, 0.0, 5.0),
        (0.0, 5.0, 0.0, 0.0),
        # Micro-segment horizontal simulant un petit décrochement.
        (2.0, 1.0, 2.6, 1.0),
    ]
    pairs = dominant_dimension_pairs(
        segments,
        minimum_relative_length=0.25,
    )

    assert len(pairs) == 2
    selected = {
        index
        for pair in pairs
        for index in (pair.first_index, pair.second_index)
    }
    assert 4 not in selected


def test_long_corridor_keeps_short_direction_pair():
    segments = [
        (0.0, 0.0, 10.0, 0.0),
        (10.0, 0.0, 10.0, 1.2),
        (10.0, 1.2, 0.0, 1.2),
        (0.0, 1.2, 0.0, 0.0),
    ]

    pairs = dominant_dimension_pairs(
        segments,
        minimum_relative_length=0.25,
    )

    assert len(pairs) == 2
    distances = sorted(round(pair.distance, 6) for pair in pairs)
    assert distances == [1.2, 10.0]


def test_dimension_service_uses_finish_faces_and_associative_references():
    text = SERVICE.read_text(encoding="utf-8")
    ast.parse(text)

    for token in (
        "SpatialElementBoundaryLocation.Finish",
        "HostObjectUtils.GetSideFaces",
        "ShellLayerType.Interior",
        "ShellLayerType.Exterior",
        "PlanarFace",
        "ReferenceArray",
        "NewDimension",
        "DimensionStyleType.Linear",
        "dominant_dimension_pairs",
    ):
        assert token in text


def test_dimension_service_targets_only_dependent_pdv_views():
    text = SERVICE.read_text(encoding="utf-8")
    assert "GetPrimaryViewId()" in text
    assert 'prefix = "PDV PROTO - {} - "' in text
    assert "ElementId.InvalidElementId" in text


def test_stage06_controller_api_is_outside_ui():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "self.dimension_service = dimension_service" in text
    assert "def dimension_types(" in text
    assert "def dimension_target_views(" in text
    assert "def create_dimensions(" in text
    assert "NewDimension" not in text


def test_stage06_ui_exposes_view_type_and_creation_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    for name in (
        "DimensionViewCombo",
        "DimensionTypeCombo",
        "DimensionInfoText",
        "CreateDimensionsButton",
    ):
        assert 'x:Name="{}"'.format(name) in xaml

    assert 'Click="CreateDimensions_Click"' in xaml
    assert 'SelectionChanged="DimensionChoiceChanged"' in xaml
    assert "def CreateDimensions_Click(" in window
    assert "def _load_dimension_views(" in window
    assert "def _load_dimension_types(" in window


def test_dimension_type_combo_uses_plain_strings_for_ironpython_wpf():
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    start = xaml.index('x:Name="DimensionTypeCombo"')
    snippet = xaml[start:start + 300]

    assert "DisplayMemberPath" not in snippet
    assert "self._dimension_type_labels" in window
    assert "self.DimensionTypeCombo.ItemsSource = self._dimension_type_labels" in window


def test_dimension_service_is_reloaded_by_pyrevit_entrypoint():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "import dimension_service as _dimension_service" in text
    assert "_reload_module(_dimension_service)" in text
    assert "DimensionService = _dimension_service.DimensionService" in text


def test_stage06_build_id_is_reported_on_runtime_error():
    service = SERVICE.read_text(encoding="utf-8")
    controller = CONTROLLER.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    assert 'DIMENSION_SERVICE_BUILD = "stage06f-dimensions-graphic-placement-v6"' in service
    assert "def dimension_build_id(" in controller
    assert "Moteur cotations : {}" in window


def test_documentation_closes_stage05_and_opens_stage06():
    text = DOC.read_text(encoding="utf-8")
    assert "Étape 05 — Étiquettes de pièces : VALIDÉE V1." in text
    assert "## Ouverture Étape 06 — Cotations" in text
    assert "feature/plans-de-vente-stage06-dimensions" in text



def test_non_parallel_room_gets_two_representative_length_directions():
    segments = [
        (0.0, 0.0, 6.0, 0.0),
        (6.0, 0.0, 5.0, 4.0),
        (5.0, 4.0, 0.8, 5.0),
        (0.8, 5.0, 0.0, 0.0),
    ]

    assert dominant_dimension_pairs(segments) == []

    indexes = representative_length_indexes(
        segments,
        angle_tolerance_degrees=12.0,
        max_results=2,
    )
    assert len(indexes) == 2
    assert indexes[0] == 0
    assert indexes[0] != indexes[1]


def test_stage06b_keeps_processing_when_one_room_is_atypical():
    service = SERVICE.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")

    assert "for room, boundary_candidates, pairs, fallback_indexes in room_plans" in service
    assert "with RevitTransaction(" in service
    assert "partial_room_count" in service
    assert "skipped_room_count" in service
    assert "une seule dimension principale fiable" in service
    assert "Une pièce atypique ne bloque plus les autres." in window


def test_stage06b_uses_endpoint_or_finish_face_edges_for_length_fallback():
    text = SERVICE.read_text(encoding="utf-8")

    assert "GetEndPointReference(0)" in text
    assert "GetEndPointReference(1)" in text
    assert "face.EdgeLoops" in text
    assert "edge.Reference" in text
    assert "_length_dimension_line" in text
    assert "room.IsPointInRoom(point)" in text



def test_parallel_pair_survives_when_one_room_boundary_is_not_linear():
    # Cas type : trois limites droites exploitables et une quatrième limite
    # courbe. Les deux horizontales doivent tout de même former une cote.
    segments = [
        (0.0, 0.0, 5.0, 0.0),
        (5.0, 0.0, 5.0, 3.0),
        (5.0, 3.0, 0.0, 3.0),
    ]

    pairs = dominant_dimension_pairs(segments)

    assert len(pairs) == 1
    assert round(pairs[0].distance, 6) == 3.0


def test_stage06c_reloads_wall_geometry_with_compute_references():
    text = SERVICE.read_text(encoding="utf-8")

    assert "Options()" in text
    assert "options.ComputeReferences = True" in text
    assert "wall.get_Geometry(options)" in text
    assert "GeometryInstance" in text
    assert "face.Reference" in text
    assert "edge.Reference" in text
    assert "_computed_side_face_with_references" in text



def test_stage06d_room_separation_lines_are_dimension_candidates():
    text = SERVICE.read_text(encoding="utf-8")

    assert "BuiltInCategory.OST_RoomSeparationLines" in text
    assert "def _room_separator_reference(" in text
    assert "element.GeometryCurve" in text
    assert "geometry_curve.Reference" in text
    assert "length_references=None" in text


def test_stage06d_keeps_room_separator_geometry_in_principal_pair_search():
    # Une séparation de pièce verticale et un mur vertical opposé doivent
    # pouvoir former la largeur principale d'une pièce extérieure.
    segments = [
        (0.0, 0.0, 6.0, 0.0),
        (6.0, 0.0, 6.0, 3.0),   # mur
        (6.0, 3.0, 0.0, 3.0),
        (0.0, 3.0, 0.0, 0.0),   # séparation de pièce
    ]

    pairs = dominant_dimension_pairs(segments)
    assert len(pairs) == 2
    assert sorted(round(pair.distance, 6) for pair in pairs) == [3.0, 6.0]



def test_floor_edge_matching_requires_parallel_close_and_overlapping_segments():
    boundary = (0.0, 0.0, 5.0, 0.0)

    match = segment_match_metrics(
        boundary,
        (0.2, 0.02, 4.8, 0.02),
        angle_tolerance_degrees=3.0,
        distance_tolerance=0.05,
        minimum_overlap_ratio=0.60,
    )
    assert match is not None
    assert match["overlap_ratio"] > 0.90

    too_far = segment_match_metrics(
        boundary,
        (0.2, 0.20, 4.8, 0.20),
        angle_tolerance_degrees=3.0,
        distance_tolerance=0.05,
        minimum_overlap_ratio=0.60,
    )
    assert too_far is None

    too_short = segment_match_metrics(
        boundary,
        (0.0, 0.01, 2.0, 0.01),
        angle_tolerance_degrees=3.0,
        distance_tolerance=0.05,
        minimum_overlap_ratio=0.60,
    )
    assert too_short is None


def test_stage06e_replaces_room_separator_reference_with_matching_floor_edge():
    text = SERVICE.read_text(encoding="utf-8")

    assert "def _matching_floor_edge_reference(" in text
    assert "def _floor_edges_for_room(" in text
    assert "FilteredElementCollector(self.document)" in text
    assert ".OfClass(Floor)" in text
    assert "options.ComputeReferences = True" in text
    assert "segment_match_metrics(" in text
    assert 'source_kind="floor_edge"' in text
    assert 'source_kind="separator"' in text


def test_stage06e_floor_edge_match_has_geometry_safety_thresholds():
    text = SERVICE.read_text(encoding="utf-8")

    assert "FLOOR_EDGE_ANGLE_TOLERANCE_DEGREES = 3.0" in text
    assert "FLOOR_EDGE_TOLERANCE_MM = 20.0" in text
    assert "FLOOR_EDGE_MIN_OVERLAP_RATIO = 0.60" in text
    assert "FLOOR_LEVEL_TOLERANCE_MM = 500.0" in text
    assert "FLOOR_EDGE_MIN_LENGTH_MM = 100.0" in text


def test_stage06e_warns_when_only_hidden_separator_reference_remains():
    text = SERVICE.read_text(encoding="utf-8")

    assert "separator_fallback_used" in text
    assert "aucune arête de sol superposée fiable" in text
    assert "La cote peut disparaître" in text
    assert "séparations sont" in text
    assert "masquées dans la vue" in text
