# -*- coding: utf-8 -*-
import pytest

from plans_vente.sheet_fit import (
    choose_fitting_scale,
    parse_allowed_scales,
    viewport_fits,
)


def test_parse_allowed_scales_accepts_commas_spaces_and_duplicates():
    assert parse_allowed_scales("100, 50 75;50") == [50, 75, 100]


def test_parse_allowed_scales_uses_default_when_empty():
    assert parse_allowed_scales("") == [25, 50, 75, 100]


def test_parse_allowed_scales_rejects_no_positive_value():
    with pytest.raises(ValueError):
        parse_allowed_scales("abc, 0")


def test_choose_fitting_scale_enlarges_when_smaller_denominator_fits():
    # Vue mesurée 100 x 50 à 1:100, zone modèle 180 x 100.
    # 1:50 donnerait environ 200 x 100 -> trop large ; 1:75 tient.
    assert choose_fitting_scale(
        current_scale=100,
        current_width=100.0,
        current_height=50.0,
        target_width=180.0,
        target_height=100.0,
        allowed_scales=[50, 75, 100],
    ) == 75


def test_choose_fitting_scale_keeps_smallest_allowed_when_it_fits():
    assert choose_fitting_scale(
        current_scale=50,
        current_width=80.0,
        current_height=40.0,
        target_width=90.0,
        target_height=60.0,
        allowed_scales=[50, 75, 100],
    ) == 50


def test_choose_fitting_scale_shrinks_when_current_view_overflows():
    assert choose_fitting_scale(
        current_scale=50,
        current_width=140.0,
        current_height=90.0,
        target_width=100.0,
        target_height=70.0,
        allowed_scales=[50, 75, 100],
    ) == 75


def test_choose_fitting_scale_returns_largest_if_nothing_can_fit():
    assert choose_fitting_scale(
        current_scale=50,
        current_width=500.0,
        current_height=300.0,
        target_width=100.0,
        target_height=70.0,
        allowed_scales=[50, 75, 100],
    ) == 100


def test_viewport_fits_checks_both_axes():
    assert viewport_fits(80, 60, 100, 70)
    assert not viewport_fits(101, 60, 100, 70)
    assert not viewport_fits(80, 71, 100, 70)
