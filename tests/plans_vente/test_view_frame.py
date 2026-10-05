# -*- coding: utf-8 -*-
import math

from plans_vente.view_frame import ViewFrame


def test_project_and_rebuild_point_in_rotated_view_frame():
    c = math.sqrt(0.5)
    frame = ViewFrame(
        origin=(10.0, 20.0, 3.0),
        right=(c, c, 0.0),
        up=(-c, c, 0.0),
    )

    world = frame.to_world(4.0, 2.0)
    u, v = frame.project(world)

    assert abs(u - 4.0) < 1e-9
    assert abs(v - 2.0) < 1e-9
    assert abs(world[2] - 3.0) < 1e-9


def test_view_frame_normalizes_axes():
    frame = ViewFrame(
        origin=(0.0, 0.0, 0.0),
        right=(10.0, 0.0, 0.0),
        up=(0.0, 5.0, 0.0),
    )

    assert frame.right == (1.0, 0.0, 0.0)
    assert frame.up == (0.0, 1.0, 0.0)


def test_view_frame_rejects_non_orthogonal_axes():
    try:
        ViewFrame(
            origin=(0.0, 0.0, 0.0),
            right=(1.0, 0.0, 0.0),
            up=(1.0, 1.0, 0.0),
        )
    except ValueError as error:
        assert "orthogonaux" in str(error)
    else:
        raise AssertionError("Un repère non orthogonal doit être refusé.")
