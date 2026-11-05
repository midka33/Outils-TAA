import math
import pytest
from giration.geometry.vector2d import Vector2D
from giration.models.vehicle import Vehicle
from giration.services.kinematics import TrajectoryPoint
from giration.services.manual_solver import segment_to_rear_axle

VEHICLE=Vehicle('Test', length=5,width=2,wheelbase=3,rear_overhang=1,
                front_overhang=1,front_track=1.6,rear_track=1.5,
                max_steering_angle=math.pi/4)


def test_straight_manual():
    path = segment_to_rear_axle(VEHICLE, TrajectoryPoint((0,0),0), (6,0))
    assert path[-1].position.x == pytest.approx(5)


def test_curve_manual():
    path = segment_to_rear_axle(VEHICLE, TrajectoryPoint((0,0),0), (4,2))
    assert path[-1].angle > 0
    assert path[-1].position.x > 0


def test_reverse_manual():
    path = segment_to_rear_axle(VEHICLE, TrajectoryPoint((0,0),0), (-4,0),reverse=True)
    assert path[-1].position.x == pytest.approx(-5)


def test_unreachable_manual():
    with pytest.raises(ValueError):
        segment_to_rear_axle(VEHICLE, TrajectoryPoint((0,0),0), (1.1,3))


def test_wrong_gear_rejected():
    with pytest.raises(ValueError):
        segment_to_rear_axle(VEHICLE, TrajectoryPoint((0,0),0), (-3,1))
