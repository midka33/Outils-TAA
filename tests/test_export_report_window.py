# -*- coding: utf-8 -*-
"""Contrat du rapport avec une fenêtre WPF simulée, sans moteur Revit."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'


@pytest.fixture
def report_module(monkeypatch):
    class Window:
        def __init__(self, path):
            for name in ('ReportGrid', 'SummaryText', 'DestinationText', 'WarningsText'):
                setattr(self, name, SimpleNamespace())
    monkeypatch.setitem(sys.modules, 'pyrevit', SimpleNamespace(
        forms=SimpleNamespace(WPFWindow=Window)))
    spec = importlib.util.spec_from_file_location('report_under_test', PANEL / 'export_report_window.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_global_exception_visible_when_failed_rows_have_no_errors(report_module):
    error = 'PDF séparé — erreur : accès refusé. Fichiers temporaires conservés dans C:/Temp/taa'
    report = {'success': False, 'errors': [error], 'results': [
        {'success': False, 'format': 'PDF', 'mode': 'separate', 'count': 1}]}
    window = report_module.PublicationReportWindow(report)
    assert error in window.WarningsText.Text
    assert 'Export terminé.' not in window.ReportGrid.ItemsSource[0].Details
    assert window.ReportGrid.ItemsSource[0].Status == 'ERREUR'


def test_exception_before_any_deliverable_still_visible(report_module):
    window = report_module.PublicationReportWindow({
        'success': False, 'results': [], 'errors': ['Destination inaccessible']})
    assert window.ReportGrid.ItemsSource == []
    assert 'Destination inaccessible' in window.WarningsText.Text


def test_mixed_results_keep_own_carnet_path_and_status(report_module):
    window = report_module.PublicationReportWindow({
        'success': False, 'carnet': 'Publication multiple', 'errors': ['B : échec'],
        'results': [{'carnet': 'A', 'success': True, 'path': 'C:/A.pdf'},
                    {'carnet': 'B', 'success': False, 'errors': ['Fichier verrouillé']}]})
    first, second = window.ReportGrid.ItemsSource
    assert (first.Carnet, first.Path, first.Status, first.Details) == (
        'A', 'C:/A.pdf', 'OK', 'Export terminé.')
    assert second.Carnet == 'B'
    assert 'Fichier verrouillé' in second.Details
    assert 'B : échec' in window.WarningsText.Text


def test_success_keeps_full_warnings_visible(report_module):
    window = report_module.PublicationReportWindow({
        'success': True, 'warnings': ['Variable inconnue : indice'], 'results': []})
    assert window.WarningsText.Text == 'AVERTISSEMENT : Variable inconnue : indice'


def test_failure_without_diagnostic_is_never_reported_as_success(report_module):
    window = report_module.PublicationReportWindow({'success': False})
    assert 'Échec' in window.WarningsText.Text


def test_diagnostic_text_is_selectable_and_scrollable():
    import xml.etree.ElementTree as ET
    root = ET.parse(str(PANEL / 'publication_report.xaml')).getroot()
    name = '{http://schemas.microsoft.com/winfx/2006/xaml}Name'
    diagnostic = next(node for node in root.iter() if node.get(name) == 'WarningsText')
    assert diagnostic.tag.endswith('TextBox')
    assert diagnostic.get('IsReadOnly') == 'True'
    assert diagnostic.get('VerticalScrollBarVisibility') == 'Auto'
