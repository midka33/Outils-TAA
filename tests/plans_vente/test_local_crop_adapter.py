# -*- coding: utf-8 -*-
"""Run the actual adapter with a stand-in for CurveLoop creation only."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import pytest
from plans_vente.view_frame import ViewFrame

PATH = Path(__file__).resolve().parents[2] / 'OutilsTAA.extension/OutilsTAA.tab/PlansDeVente.panel/services/crop_geometry_service.py'
spec = importlib.util.spec_from_file_location('pv_crop_adapter', str(PATH))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


@pytest.fixture
def service():
    value = module.CropGeometryService(object())
    value._frame_from_view = lambda view: ViewFrame((0, 0, 0), (1, 0, 0), (0, 1, 0))
    value._tessellated_loop_points = lambda loop: [SimpleNamespace(X=x, Y=y, Z=0) for x, y in loop]
    value._remove_near_duplicates = lambda points: points
    value._short_curve_tolerance = lambda: .001
    value._millimeters_to_internal = lambda mm: mm / 1000.
    value._curve_loop_from_uv_points = lambda points, frame: points
    return value


RING = [(0, 0), (10, 0), (10, 10), (6, 10), (6, 9), (5, 9), (5, 10), (0, 10)]


def test_real_adapter_reports_only_successful_reconstruction(service):
    result = service._close_small_recesses(RING, object(), 3.5, 2, 5)
    assert len(result) == 4
    assert service._last_closed_recess_count == 1
    assert '1 fermeture(s) colinéaire(s)' in service._recess_diagnostic()


def test_reconstruction_failure_keeps_original_and_zero_counts(service):
    def fail(*args):
        raise ValueError('CurveLoop rejected')
    service._curve_loop_from_uv_points = fail
    assert service._close_small_recesses(RING, object(), 3.5, 2, 5) is RING
    assert service._last_closed_recess_count == 0


def test_post_offset_cleanup_does_not_cut_outward_feature(service):
    bump = [(0, 0), (10, 0), (10, 10), (6, 10), (6, 11), (5, 11), (5, 10), (0, 10)]
    assert service._cleanup_small_notches(bump, object(), .6) is bump


def test_crop_capability_with_diagnostic_suffix_uses_rectangle(service):
    manager = SimpleNamespace(CanHaveShape=False, IsCropRegionShapeValid=lambda loop: True)
    applied = []
    manager.SetCropShape = applied.append
    view = SimpleNamespace(GetCropRegionShapeManager=lambda: manager)
    service._try_release_scope_box = lambda view: (False, 'locked')
    result = module.OptimizedCropResult('optimized', 'Contour optimisé — 1 fermeture', fallback_curve_loop='rectangle')
    service.apply_to_view(view, result)
    assert applied == ['rectangle']
    assert result.mode == 'Rectangle de secours'



def test_adapter_reports_absorbed_residual_segments(service):
    ring = [
        (0.0, 0.0), (10.0, 0.0), (10.0, 10.0),
        (6.2, 10.0), (6.0, 9.8), (6.0, 9.0),
        (5.0, 9.0), (5.0, 9.8), (4.8, 10.0), (0.0, 10.0),
    ]
    result = service._close_small_recesses(
        ring,
        object(),
        3.5,
        2.0,
        5.0,
    )
    assert result is not ring
    assert service._last_recess_counts["absorbed"] >= 1
    assert "segment(s) parasite(s) absorbé(s)" in service._recess_diagnostic()
