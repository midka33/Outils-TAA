# -*- coding: utf-8 -*-
import math

import pytest

from plans_vente.dimension_geometry import (
    branched_dimension_pairs,
    pronounced_branched_shape_metrics,
)
from plans_vente.dimension_positioning import (
    placement_candidates,
    select_placements,
)


def segments(points):
    return [
        a + b
        for a, b in zip(points, points[1:] + points[:1])
    ]


def contains_polygon(points):
    def contains(point):
        inside = False
        for left, right in zip(
            points,
            points[1:] + points[:1],
        ):
            if (left[1] > point[1]) != (right[1] > point[1]):
                x_value = left[0] + (
                    (point[1] - left[1])
                    * (right[0] - left[0])
                    / (right[1] - left[1])
                )
                if point[0] < x_value:
                    inside = not inside
        return inside
    return contains


def branched_pairs(points):
    return branched_dimension_pairs(
        segments(points),
        contains_polygon(points),
        minimum_dimension=0.6,
        minimum_overlap=0.3,
        minimum_missing_ratio=0.12,
        max_results=5,
    )


def test_rectangle_is_not_classified_as_branched():
    points = [(0., 0.), (6., 0.), (6., 4.), (0., 4.)]
    metrics = pronounced_branched_shape_metrics(segments(points))

    assert metrics["is_branched"] is False
    assert metrics["reflex_count"] == 0
    assert branched_pairs(points) == []


def test_small_recess_is_not_pronounced_enough():
    points = [
        (0., 0.), (6., 0.), (6., 4.),
        (3.2, 4.), (3.2, 3.7), (2.8, 3.7),
        (2.8, 4.), (0., 4.),
    ]
    metrics = pronounced_branched_shape_metrics(
        segments(points),
        minimum_missing_ratio=0.12,
    )

    assert metrics["reflex_count"] == 2
    assert metrics["missing_ratio"] < 0.12
    assert metrics["is_branched"] is False


def test_pronounced_l_produces_four_useful_dimensions():
    points = [
        (0., 0.), (5.2, 0.), (5.2, 3.4),
        (4., 3.4), (4., 1.2), (0., 1.2),
    ]

    metrics = pronounced_branched_shape_metrics(segments(points))
    result = branched_pairs(points)

    assert metrics["is_branched"] is True
    assert metrics["reflex_count"] == 1
    assert len(result) == 4
    assert sorted(round(pair.distance, 6) for pair in result) == [
        1.2, 1.2, 3.4, 5.2,
    ]


def test_pronounced_t_produces_multiple_local_dimensions_without_name():
    points = [
        (0., 0.), (6., 0.), (6., 1.4),
        (3.8, 1.4), (3.8, 5.0), (2.2, 5.0),
        (2.2, 1.4), (0., 1.4),
    ]

    metrics = pronounced_branched_shape_metrics(segments(points))
    result = branched_pairs(points)

    assert metrics["is_branched"] is True
    assert metrics["reflex_count"] == 2
    assert 3 <= len(result) <= 5
    assert any(pair.distance == pytest.approx(1.4) for pair in result)
    assert any(pair.distance == pytest.approx(1.6) for pair in result)
    assert any(pair.distance == pytest.approx(5.0) for pair in result)


def test_rotated_l_is_still_detected_by_oriented_area_metric():
    angle = math.radians(27.0)
    source = [
        (0., 0.), (5.2, 0.), (5.2, 3.4),
        (4., 3.4), (4., 1.2), (0., 1.2),
    ]

    def rotate(point):
        return (
            point[0] * math.cos(angle) - point[1] * math.sin(angle),
            point[0] * math.sin(angle) + point[1] * math.cos(angle),
        )

    points = [rotate(point) for point in source]
    metrics = pronounced_branched_shape_metrics(segments(points))

    assert metrics["is_branched"] is True
    assert metrics["reflex_count"] == 1


def test_four_branched_dimensions_can_be_placed_without_combinatorial_failure():
    points = [
        (0., 0.), (5.2, 0.), (5.2, 3.4),
        (4., 3.4), (4., 1.2), (0., 1.2),
    ]
    contains = contains_polygon(points)
    pairs = branched_pairs(points)

    groups = [
        placement_candidates(
            (pair.line_start, pair.line_end),
            pair.placement_points,
            contains,
            clearance=.25,
            text_width=.5,
            text_height=.15,
            padding=.015,
            witness_length=.075,
        )
        for pair in pairs
    ]

    result = select_placements(groups)

    assert len(result) == 4
    assert all(item.outside_count == 0 for item in result)


def test_geometry_engine_caps_complex_room_at_five_dimensions():
    points = [
        (0., 0.), (8., 0.), (8., 2.),
        (6., 2.), (6., 4.),
        (5., 4.), (5., 6.),
        (3., 6.), (3., 4.),
        (2., 4.), (2., 2.),
        (0., 2.),
    ]

    result = branched_dimension_pairs(
        segments(points),
        contains_polygon(points),
        minimum_dimension=.6,
        minimum_overlap=.3,
        minimum_missing_ratio=.10,
        max_results=5,
    )

    assert 3 <= len(result) <= 5
