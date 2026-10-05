# -*- coding: utf-8 -*-
import math
import pytest
from plans_vente import local_crop_geometry as geo

U = [(0, 0), (10, 0), (10, 10), (6, 10), (6, 9), (5, 9), (5, 10), (0, 10)]
CORNER = [(0, 0), (10, 0), (10, 8), (9, 8), (9, 9), (8, 9), (8, 10), (0, 10)]
STEP = [(0, 0), (10, 0), (10, 10), (7, 10), (7, 8), (5, 8), (5, 11), (0, 11)]


def clean(ring, **kwargs):
    return geo.close_pockets(ring, 3.5, 2.0, 5.0, 3.5, **kwargs)


def assert_safe(original, result):
    assert geo.is_simple(result)
    assert geo.contains_ring(result, original)
    assert abs(geo.signed_area(result)) >= abs(geo.signed_area(original))
    assert geo.signed_area(result) * geo.signed_area(original) > 0


def test_a_collinear_pocket_is_fused():
    result, stats = clean(U)
    assert len(result) == 4
    assert abs(geo.signed_area(result)) == 100
    assert stats['collinear'] == 1
    assert_safe(U, result)


def test_b_right_angle_trim_has_single_corner():
    paths = geo.support_paths((10, 0), (10, 8), (8, 10), (0, 10), 3.5)
    assert paths == [('trim', [(10.0, 10.0)])]
    result, stats = clean(CORNER)
    assert (10.0, 10.0) in result
    assert len(result) == 4
    assert stats['trim'] == 1
    assert_safe(CORNER, result)


def test_c_non_orthogonal_trim():
    # Affine shear retains the supporting lines but makes their angle oblique.
    ring = [(x + .3 * y, y) for x, y in CORNER]
    result, stats = clean(ring)
    assert (13.0, 10.0) in result
    assert stats['trim'] == 1
    assert_safe(ring, result)


def test_d_offset_parallel_supports_use_perpendicular_step():
    result, stats = clean(STEP)
    assert stats['perpendicular'] == 1
    assert_safe(STEP, result)
    assert abs(geo.signed_area(result)) == 105
    for i, a in enumerate(result):
        b = result[(i + 1) % len(result)]
        assert abs(a[0] - b[0]) < 1e-7 or abs(a[1] - b[1]) < 1e-7


def test_e_remote_intersection_is_rejected():
    assert geo.support_paths((-2000, 0), (1, 0), (2, 1), (3, 1.001), 3.5) == []
    assert geo.support_paths((-2000, 0), (1, 0), (2, 1), (3, 1.001), 2000)


@pytest.mark.parametrize('ring', [
    [(0, 0), (3, 3), (0, 3), (3, 0)],
    [(0, 0), (3, 0), (3, 3), (1, 0), (0, 3)],
    [(0, 0), (3, 0), (1, 0), (1, 3), (0, 3)],
    [(0, 0), (3, 0), (3, 0), (3, 3), (0, 3)],
])
def test_f_crossings_touches_zero_edges_and_overlaps_are_rejected(ring):
    assert not geo.is_simple(ring)
    assert not geo.valid_replacement(U, ring, 100)


def test_g_larger_area_does_not_allow_cutting_rooms():
    original = [(0, 0), (2, 0), (2, 2), (0, 2)]
    candidate = [(1, -1), (4, -1), (4, 3), (1, 3)]
    assert geo.signed_area(candidate) > geo.signed_area(original)
    assert not geo.valid_replacement(original, candidate, 100)


def test_g_containment_checks_edges_not_just_vertices():
    candidate = [(0, 0), (4, 0), (4, 4), (2.1, 4), (2.1, 1), (1.9, 1), (1.9, 4), (0, 4)]
    original = [(0.5, .5), (3.5, .5), (3.5, 3.5), (.5, 3.5)]
    assert all(geo.inside(p, candidate) for p in original)
    assert geo.signed_area(candidate) > geo.signed_area(original)
    assert not geo.contains_ring(candidate, original)
    assert not geo.valid_replacement(original, candidate, 10)


def test_h_diagonal_chord_is_not_a_support_path():
    paths = geo.support_paths((10, 10), (7, 10), (5, 11), (0, 11), 3.5)
    assert len(paths) == 2
    for kind, path in paths:
        assert kind == 'perpendicular'
        assert path[0][0] == path[1][0]
    result, _ = clean(STEP)
    assert (7, 10) not in result or (5, 11) not in result


@pytest.mark.parametrize('ring', [U, CORNER, STEP])
@pytest.mark.parametrize('reverse', [False, True])
def test_ring_start_and_winding_do_not_change_area(ring, reverse):
    expected, _ = clean(ring)
    for shift in range(len(ring)):
        source = ring[shift:] + ring[:shift]
        if reverse:
            source = source[::-1]
        result, _ = clean(source)
        assert abs(geo.signed_area(result)) == pytest.approx(abs(geo.signed_area(expected)))
        assert_safe(source, result)


def test_rotated_translated_geometry_preserves_local_directions():
    angle = .421
    def transform(p):
        x, y = p
        return (10000 + x * math.cos(angle) - y * math.sin(angle),
                20000 + x * math.sin(angle) + y * math.cos(angle))
    ring = [transform(p) for p in STEP]
    result, stats = clean(ring)
    assert stats['perpendicular'] == 1
    assert_safe(ring, result)
    assert abs(geo.signed_area(result)) == pytest.approx(105)


@pytest.mark.parametrize('limits', [(0.5, 2, 5, 3.5), (3.5, .5, 5, 3.5), (3.5, 2, .5, 3.5)])
def test_thresholds_keep_oversized_pocket(limits):
    result, stats = geo.close_pockets(U, *limits)
    assert result == U
    assert stats['collinear'] == 0


def test_unchanged_convex_and_large_l_shapes():
    for ring in [[(0, 0), (10, 0), (10, 10), (0, 10)],
                 [(0, 0), (10, 0), (10, 4), (4, 4), (4, 10), (0, 10)]]:
        result, _ = clean(ring)
        assert result == ring


def test_budget_exhaustion_keeps_valid_input_and_reports_it():
    result, stats = clean(U, max_validations=0)
    assert result == U
    assert stats['budget_exhausted']
    assert stats['validations'] == 0


def test_local_scan_has_bounded_work_and_is_idempotent():
    # Multiple physically separated pockets, not 50 repeated global searches.
    top = []
    for x in range(100, 0, -5):
        top.extend([(x, 10), (x - 1, 10), (x - 1, 9), (x - 2, 9), (x - 2, 10)])
    ring = [(0, 0), (105, 0), (105, 10)] + top + [(0, 10)]
    result, stats = clean(ring)
    assert stats['collinear'] == 20
    assert stats['validations'] <= geo.MAX_VALIDATIONS
    assert_safe(ring, result)
    again, _ = clean(result)
    assert again == result



def test_context_normalization_absorbs_short_left_support_edge():
    ring = [
        (6.0, 9.8), (6.0, 9.0), (5.0, 9.0), (5.0, 10.0),
        (0.0, 10.0), (0.0, 0.0), (10.0, 0.0), (10.0, 10.0),
        (6.2, 10.0),
    ]
    context = geo.normalize_support_context(
        ring, 3, 3.5, 2.0,
    )
    assert context["left_absorbed"] == 1
    assert context["right_absorbed"] == 0
    assert context["absorbed"] == 1
    assert context["a"] == (6.2, 10.0)
    assert context["previous"] == (10.0, 10.0)


def test_context_normalization_absorbs_short_right_support_edge():
    ring = [
        (6.0, 10.0), (6.0, 9.0), (5.0, 9.0), (5.0, 9.8),
        (4.8, 10.0), (0.0, 10.0), (0.0, 0.0), (10.0, 0.0),
        (10.0, 10.0),
    ]
    context = geo.normalize_support_context(
        ring, 3, 3.5, 2.0,
    )
    assert context["left_absorbed"] == 0
    assert context["right_absorbed"] == 1
    assert context["absorbed"] == 1
    assert context["b"] == (4.8, 10.0)
    assert context["following"] == (0.0, 10.0)


def test_context_normalization_does_not_absorb_short_structural_edge():
    ring = [
        (6.0, 9.8), (6.0, 9.0), (5.0, 9.0), (5.0, 10.0),
        (0.0, 10.0), (0.0, 0.0), (10.0, 0.0), (6.5, 10.0),
        (6.2, 10.0),
    ]
    context = geo.normalize_support_context(
        ring, 3, 3.5, 2.0,
    )
    # 0.28 m is not short relative to the 0.30 m outer edge.
    assert context["left_absorbed"] == 0
    assert context["a"] == ring[0]


def test_context_normalization_is_bounded_to_two_segments_per_side():
    ring = [
        (6.0, 9.8), (6.0, 9.0), (5.0, 9.0), (5.0, 10.0),
        (0.0, 10.0), (0.0, 0.0), (10.0, 0.0), (10.0, 10.0),
        (7.2, 10.0), (6.4, 10.0), (6.1, 9.9),
    ]
    context = geo.normalize_support_context(
        ring, 3, 3.5, 2.0,
    )
    assert context["left_absorbed"] <= geo.MAX_CONTEXT_SEGMENTS
    assert context["right_absorbed"] <= geo.MAX_CONTEXT_SEGMENTS


def test_residual_lip_segments_are_absorbed_before_support_repair():
    ring = [
        (0.0, 0.0), (10.0, 0.0), (10.0, 10.0),
        (6.2, 10.0), (6.0, 9.8), (6.0, 9.0),
        (5.0, 9.0), (5.0, 9.8), (4.8, 10.0), (0.0, 10.0),
    ]
    result, stats = clean(ring)
    assert stats["absorbed"] >= 1
    assert stats["collinear"] + stats["trim"] + stats["perpendicular"] >= 1
    assert_safe(ring, result)
