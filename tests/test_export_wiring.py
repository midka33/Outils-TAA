# -*- coding: utf-8 -*-
"""Contrats anti-régression du raccordement Export."""
import ast
import sys
from pathlib import Path
PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
sys.path.insert(0, str(PANEL / 'services'))
sys.path.insert(0, str(PANEL / 'models'))
from publication_set import PublicationSet
from publication_settings import PublicationSettings
from publication_batch_service import PublicationBatchService


def test_drag_drop_has_one_constructor_owner():
    sites = []
    for relative in ['export_window.py', 'Export.pushbutton/script.py', 'services/publication_preview_integration.py']:
        tree = ast.parse((PANEL / relative).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'PublicationTreeDragDrop':
                sites.append(relative)
    assert sites == ['export_window.py']


def test_batch_passes_effective_settings_without_persisting_inheritance(tmp_path):
    target = PublicationSet('Plans', publication_settings=PublicationSettings())
    settings = PublicationSettings.defaults()
    settings.output_directory = str(tmp_path)
    settings.filename_template = '{numero}-{nom}'
    received = []
    class Service:
        def publish(self, current, directory, **kwargs):
            received.append(current)
            return {'success': True, 'results': []}
    report = PublicationBatchService(Service()).publish([target], lambda t: settings)
    assert report['success']
    assert received[0] is not target
    assert received[0].publication_settings.filename_template == '{numero}-{nom}'
    assert target.publication_settings.filename_template is None
