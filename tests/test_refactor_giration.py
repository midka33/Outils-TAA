import math
import pytest
from giration.geometry.vector2d import Vector2D
from giration.models.vehicle import Vehicle
from giration.services.kinematics import AckermannKinematics, TrajectoryPoint


def vehicle(**kw):
    params = dict(name='Essai', length=5.0, width=2.0, wheelbase=3.0,
                  rear_overhang=1.0, front_overhang=1.0, front_track=1.5,
                  rear_track=1.5, max_steering_angle=math.pi / 4)
    params.update(kw)
    return Vehicle(**params)


def test_straight_forward_and_reverse():
    k = AckermannKinematics(vehicle())
    for reverse, expected in [(False, 7.0), (True, -7.0)]:
        path = k.calculate_trajectory((0, 0), 0, 0, 7, reverse)
        assert path[-1].position.x == pytest.approx(expected)
        assert path[-1].angle == pytest.approx(0)


def test_roundtrip_arc_and_rear_axle_radius():
    v = vehicle()
    k = AckermannKinematics(v)
    steering = math.atan(v.wheelbase / 6.0)
    arc = k.calculate_trajectory((0, 0), 0, steering, math.pi * 3, False, 200)
    rear_end = arc[-1].position + Vector2D.from_angle(arc[-1].angle, v.rear_overhang)
    assert arc[0].position == Vector2D(0, 0)
    assert arc[0].angle == pytest.approx(0)
    assert arc[-1].angle == pytest.approx(math.pi / 2)
    assert rear_end.x == pytest.approx(7.0)
    assert rear_end.y == pytest.approx(6.0)


def test_right_turn_orientation_and_continuity():
    k = AckermannKinematics(vehicle())
    a = k.calculate_path((1, 2), 0.7, [dict(distance=5, steering_angle=-0.3),
                                      dict(distance=4, steering_angle=0.2)])
    b = k.calculate_trajectory(a[10].position, a[10].angle, 0.2, 4)
    assert a[11].position.distance_to(b[1].position) < 1e-9
    assert a[10].angle == pytest.approx(.7 - 5 * math.tan(.3) / 3)
    assert a[20].angle == pytest.approx(a[10].angle + 4 * math.tan(.2) / 3)


def test_reverse_curvature_changes_heading_sign():
    k = AckermannKinematics(vehicle())
    path = k.calculate_trajectory((0, 0), 0, .3, 3, True)
    assert path[-1].angle < 0


def test_input_validation():
    k = AckermannKinematics(vehicle())
    for kwargs in [dict(distance=-1), dict(steering_angle=2), dict(num_points=0),
                   dict(distance=float('nan')), dict(start_angle=float('nan'))]:
        with pytest.raises(ValueError):
            k.calculate_trajectory((0, 0), **kwargs)


def test_vehicle_footprint_and_wheelbase():
    v = vehicle()
    axle = v.get_wheel_positions(2, 3, .7)
    assert axle['rear_left'].distance_to(axle['front_left']) == pytest.approx(v.wheelbase)
    assert len(v.get_corners(2, 3, .7)) == 4


def test_envelopes_not_mislabeled_union():
    k = AckermannKinematics(vehicle())
    track = k.calculate_trajectory((0, 0), 0, .3, 5, num_points=12)
    assert len(k.calculate_swept_area(track)) == len(track)
    assert len(k.calculate_swept_mesh(track)) == len(track) + 4 * (len(track) - 1)


def test_vehicle_geometry_invalid():
    with pytest.raises(ValueError):
        vehicle(front_overhang=8)
    with pytest.raises(ValueError):
        vehicle(front_track=2.5)


def test_roundtrip_serialization():
    v = vehicle()
    assert Vehicle.from_dict(v.to_dict()).wheelbase == v.wheelbase
    p = TrajectoryPoint((2, 3), .7, is_reverse=True)
    assert TrajectoryPoint.from_dict(p.to_dict()).to_dict() == p.to_dict()


def test_nonverified_is_explicit():
    v = vehicle(source='exemple')
    assert not v.verified
