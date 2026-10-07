# -*- coding: utf-8 -*-
"""Le retrait V1 ne doit pas laisser un filtre caché dans les anciens projets."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

from unittest.mock import MagicMock

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for directory in ('services', 'models'):
    sys.path.insert(0, str(PANEL / directory))
from publication_settings import PublicationSettings
from settings_resolver import SettingsResolver
from publication_history_service import PublicationHistoryService
from publication_set import PublicationSet
from publication_item import PublicationItem


@pytest.mark.parametrize('layer', ['profile', 'folder', 'set'])
def test_legacy_filter_is_ignored_at_every_level(layer, tmp_path):
    old = {'modified_only': True, 'output_directory': str(tmp_path)}
    settings = PublicationSettings.from_dict(old)
    target = PublicationSet('DCE', [], publication_settings=settings if layer == 'set' else None)
    folder = SimpleNamespace(id='folder', publication_settings=settings if layer == 'folder' else None)
    profiles = SimpleNamespace(get=lambda name: old if layer == 'profile' else {})
    resolved = SettingsResolver(profiles).resolve(target, folder, 'ancien')
    assert resolved.modified_only is False
    assert resolved.output_directory == str(tmp_path)
    assert 'modified_only' not in settings.to_dict()
    assert settings.copy().modified_only is False
    assert old['modified_only'] is True


def stage_functions(namespace):
    tree = ast.parse((PANEL / 'Export.smartbutton/script.py').read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in (
        '_build_preview_stage07', '_publish_targets_stage07', '_preview_then_publish_folder_stage07')]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'script.py', 'exec'), namespace)
    return namespace


@pytest.mark.parametrize('scope', ['sheet', 'set', 'folder'])
def test_unchanged_sheets_reach_preview_and_publication(scope, tmp_path):
    items = [PublicationItem('u1', 1, 'SHEET', 'A1', 'Plan'),
             PublicationItem('u2', 2, 'SHEET', 'A2', 'Coupe')]
    if scope == 'sheet':
        items = items[:1]
    settings = PublicationSettings.defaults()
    settings.output_directory = str(tmp_path)
    # Simule un ancien carnet avec l'option activée avant mise à jour.
    old = settings.to_dict()
    old['modified_only'] = True
    settings = PublicationSettings.from_dict(old)
    target = PublicationSet('DCE', items, set_id='set-1', persistent=True, publication_settings=settings)
    states = {item.unique_id: {'version_guid': 'v1'} for item in items}
    history = PublicationHistoryService(str(tmp_path / 'history.json'))
    history.record_publication(target, states)
    assert history.classify_items(target, states)['UNCHANGED'] == items
    observed = []
    class Preview:
        def __init__(self, *args):
            pass
        def build(self, actual, effective, **kwargs):
            candidates, _ = history.candidates(actual, states, kwargs['modified_only'])
            assert candidates == items
            observed.append('preview')
            return {'errors': []}
    class Dialog:
        confirmed = True
        def __init__(self, *args, **kwargs):
            pass
        def ShowDialog(self):
            pass
    def publish(actual, directory, **kwargs):
        assert kwargs['items'] == items
        observed.append('publish')
        return {'success': True}
    class Batch:
        def __init__(self, *args):
            pass
        def publish(self, targets, *args, **kwargs):
            assert targets[0]._publication_items == items
            observed.append('publish')
            return {'success': True}
    integration = SimpleNamespace(PublicationProgressSession=lambda *args: MagicMock(), PublicationPreviewService=Preview,
        PublicationPreviewWindow=Dialog, PublicationReportWindow=Dialog,
        PublicationBatchService=Batch, _merge_previews=lambda previews: previews[0])
    window = SimpleNamespace(_resolve_settings=lambda target: settings,
        _folder_name=lambda target: 'Dossier', _folder_for_set=lambda target: None,
        _selected_folder=SimpleNamespace(name='Dossier'), filename_service=None,
        controller=SimpleNamespace(publication_service=None, publish=publish))
    ns = stage_functions({'publication_preview_integration': integration,
        '_history_service': lambda window: history,
        '_current_states': lambda window, target: states})
    if scope == 'folder':
        ns['_preview_then_publish_folder_stage07'](window, [target])
    else:
        ns['_build_preview_stage07'](window, [target])
        ns['_publish_targets_stage07'](window, [target])
    assert observed == ['preview', 'publish']


def test_removed_control_has_no_dangling_ui_references():
    ET.parse(str(PANEL / 'ui.xaml'))
    for relative in ('ui.xaml', 'Export.smartbutton/script.py', 'services/publication_preview_integration.py'):
        source = (PANEL / relative).read_text(encoding='utf-8')
        assert 'ModifiedOnlyCheckBox' not in source
        assert 'ModifiedOnlyChanged' not in source
