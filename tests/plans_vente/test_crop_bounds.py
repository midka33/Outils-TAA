# -*- coding: utf-8 -*-
from plans_vente.crop_bounds import CropBounds


def test_bounds_from_points_and_margin():
    bounds = CropBounds.from_points([
        (1.0, 2.0, 0.0),
        (5.0, 8.0, 0.0),
        (3.0, 4.0, 0.0),
    ])
    assert bounds.min_x == 1.0
    assert bounds.min_y == 2.0
    assert bounds.max_x == 5.0
    assert bounds.max_y == 8.0
    assert bounds.width == 4.0
    assert bounds.height == 6.0

    expanded = bounds.expanded(0.5)
    assert expanded.min_x == 0.5
    assert expanded.min_y == 1.5
    assert expanded.max_x == 5.5
    assert expanded.max_y == 8.5


def test_bounds_reject_empty_points():
    try:
        CropBounds.from_points([])
    except ValueError as error:
        assert "Aucun point" in str(error)
    else:
        raise AssertionError("Une emprise vide doit être refusée.")


def test_bounds_reject_negative_margin():
    bounds = CropBounds(0, 0, 5, 5)
    try:
        bounds.expanded(-1)
    except ValueError as error:
        assert "négative" in str(error)
    else:
        raise AssertionError("Une marge négative doit être refusée.")
