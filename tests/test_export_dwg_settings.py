# -*- coding: utf-8 -*-
"""Contrat DWG, migration non destructive et aller-retour natif sans Revit/WPF."""
import ast
import json
import logging
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import xml.etree.ElementTree as ET

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for part in ('models', 'services'):
    sys.path.insert(0, str(PANEL / part))
from dwg_export_service import DwgExportService
from dwg_file_delivery import deliver_named_dwgs, reconcile_native_dwgs
from publication_settings import PublicationSettings
from publication_profile_service import PublicationProfileService
from settings_resolver import SettingsResolver
from carnet_repository import CarnetRepository
from publication_set import PublicationSet
from publication_item import PublicationItem
from publication_folder import PublicationFolder
from publication_service import PublicationService
from publication_batch_service import PublicationBatchService
from publication_preview_service import PublicationPreviewService
from carnet_controller import CarnetController
from dwg_setup_command import command_id, post_settings
from dwg_ui_session import DwgUiSession, capture, restore


def ui_methods(names, **namespace):
    cls = next(n for n in ast.parse((PANEL / 'export_window.py').read_text()).body
               if isinstance(n, ast.ClassDef) and n.name == 'ExportWindow')
    nodes = [n for n in cls.body if getattr(n, 'name', '') in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'export_window.py', 'exec'), namespace)
    return type('TestWindow', (), {name: namespace[name] for name in names})


@pytest.fixture
def dwg_api(monkeypatch):
    base = dict(Colors='native', MergedViews='native', LayerMapping='agency',
                TargetUnit='Millimeter', SharedCoords=True, FileVersion='R2018',
                ExportOfSolids='ACIS', TextTreatment='exact', HatchPatterns='agency')
    calls = []
    class Options:
        def __init__(self):
            self.__dict__.update(base)
        @staticmethod
        def GetPredefinedSetupNames(doc):
            calls.append(('names', doc))
            return ['TAA - DCE', 'TAA - PC']
        @staticmethod
        def GetPredefinedOptions(doc, name):
            calls.append(('preset', doc, name))
            return Options() if name == 'TAA - DCE' else None
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', NS(
        DWGExportOptions=Options, ExportColorMode=NS(TrueColor='rgb objects')))
    return base, calls


@pytest.mark.parametrize('merge', [False, True])
@pytest.mark.parametrize('color', [False, True])
def test_native_preset_only_two_explicit_overrides(dwg_api, merge, color):
    base, calls = dwg_api
    doc = object()
    options = DwgExportService(doc)._get_options('TAA - DCE', merge, color)
    expected = dict(base, MergedViews=merge)
    if color:
        expected['Colors'] = 'rgb objects'
    assert vars(options) == expected
    assert calls == [('preset', doc, 'TAA - DCE')]


def test_native_names_and_missing_preset_are_never_silently_replaced(dwg_api):
    service = DwgExportService('doc')
    assert service.get_predefined_setups() == ['TAA - DCE', 'TAA - PC']
    with pytest.raises(ValueError, match='introuvable'):
        service._get_options('deleted')
    assert service._get_options().MergedViews is True


def test_true_color_failure_is_visible(dwg_api, monkeypatch):
    monkeypatch.delattr(sys.modules['Autodesk.Revit.DB'], 'ExportColorMode')
    with pytest.raises(ImportError):
        DwgExportService(None)._get_options(true_color=True)
    assert DwgExportService(None)._get_options(true_color=False).Colors == 'native'


def target(tmp_path, mode='SEPARATE', merge=True):
    settings = PublicationSettings.defaults()
    settings.output_directory = str(tmp_path)
    settings.pdf_enabled = False
    settings.dwg_mode = mode
    settings.dwg_merge_views = merge
    settings.dwg_setup_name = 'TAA - DCE'
    settings.filename_template = '{carnet}-{numero}'
    return PublicationSet('Plans', [PublicationItem('u2', 2, 'SHEET', 'A2', 'Coupe'),
                                    PublicationItem('u1', 1, 'SHEET', 'A1', 'Plan')],
                          set_id='plans', folder_id='default', publication_settings=settings)


def simulated_native_batch(calls, item_names):
    def export(view_ids, directory, filename, setup_name=None, **kwargs):
        calls.append(((list(view_ids), directory, filename, setup_name), kwargs))
        for view_id in list(view_ids):
            number, name = item_names[int(view_id)]
            Path(
                directory,
                '{0} - Feuille - {1} - {2}.dwg'.format(
                    filename, number, name
                ),
            ).write_bytes(b'dwg')
        Path(directory, 'logo-export.png').write_bytes(b'image')
        return True
    return export


@pytest.mark.parametrize('legacy_mode', ['COMBINED', 'SEPARATE'])
@pytest.mark.parametrize('merge', [True, False])
@pytest.mark.parametrize('entry', ['batch', 'controller', 'direct'])
def test_legacy_mode_is_ignored_and_multi_sheet_uses_one_native_batch(
        tmp_path, legacy_mode, merge, entry):
    value = target(tmp_path, legacy_mode, merge)
    value._publication_items = value.items
    doc = NS(GetElement=lambda key: NS(
        Id=int(str(key).lstrip('u')), CanBePrinted=True))
    service = PublicationService(doc)
    calls = []
    service.dwg_service = NS(
        export=simulated_native_batch(
            calls,
            {2: ('A2', 'Coupe'), 1: ('A1', 'Plan')},
        )
    )

    if entry == 'batch':
        result = PublicationBatchService(service).publish(
            [value], lambda t: t.publication_settings)
    elif entry == 'controller':
        controller = CarnetController(
            NS(document=doc), None, None, publication_service=service)
        result = controller.publish(
            value, str(tmp_path), export_pdf=False, export_dwg=True,
            dwg_combined=legacy_mode == 'COMBINED',
            dwg_merge_views=merge, dwg_setup_name='TAA - DCE',
            items=value.items)
    else:
        result = service.publish_dwg(
            value, str(tmp_path), 'TAA - DCE',
            combined=legacy_mode == 'COMBINED',
            dwg_merge_views=merge, items=value.items)

    assert result['success'], result.get('errors')
    assert len(calls) == 1
    assert calls[0][0][0] == [2, 1]
    assert calls[0][1]['merged_views'] is merge
    assert calls[0][0][3] == 'TAA - DCE'
    # Le natif travaille dans un staging interne au dossier DWG.
    assert Path(calls[0][0][1]).parent == tmp_path / 'Plans' / 'DWG'
    assert Path(calls[0][0][1]).name.startswith('.taa-dwg-')

    rows = result['results']
    assert [row['mode'] for row in rows] == [
        'batch-renamed', 'batch-renamed'
    ]
    assert [Path(row['path']).name for row in rows] == [
        'Plans-A2.dwg', 'Plans-A1.dwg'
    ]
    assert all(
        Path(row['path']).parent == tmp_path / 'Plans' / 'DWG'
        for row in rows
    )
    assert all(Path(row['path']).is_file() for row in rows)
    assert len(result.get('files', [])) == 2
    assert (tmp_path / 'Plans' / 'DWG' / 'logo-export.png').is_file()


def test_single_sheet_uses_one_simple_call_and_exact_target_path(tmp_path):
    value = target(tmp_path, 'COMBINED', True)
    value.items = value.items[:1]
    doc = NS(GetElement=lambda key: NS(
        Id=int(str(key).lstrip('u')), CanBePrinted=True))
    service = PublicationService(doc)
    calls = []
    service.dwg_service = NS(
        export=lambda *a, **kw: calls.append((a, kw)) or True)

    result = service.publish_dwg(
        value, str(tmp_path), 'TAA - DCE', items=value.items)

    assert result['success']
    assert len(calls) == 1
    assert list(calls[0][0][0]) == [2]
    assert calls[0][0][1] == str(tmp_path / 'Plans' / 'DWG')
    assert result['results'][0]['mode'] == 'single'
    assert result['results'][0]['path'].endswith(
        str(Path('Plans') / 'DWG' / 'Plans-A2.dwg'))


def test_native_dwg_names_are_reconciled_without_relying_on_feuille(tmp_path):
    staging = tmp_path / 'stage'
    staging.mkdir()
    (staging / 'préfixe quelconque - A1101 - Bât A Niveau 1.dwg').write_bytes(b'a')
    (staging / 'préfixe quelconque - A1102 - Bât A Niveau 2.dwg').write_bytes(b'b')
    items = [
        NS(sheet_number='A1101', sheet_name='Bât A Niveau 1'),
        NS(sheet_number='A1102', sheet_name='Bât A Niveau 2'),
    ]
    assert reconcile_native_dwgs(str(staging), items) == [
        'préfixe quelconque - A1101 - Bât A Niveau 1.dwg',
        'préfixe quelconque - A1102 - Bât A Niveau 2.dwg',
    ]


def test_delivery_renames_sheet_dwgs_and_keeps_auxiliaries(tmp_path):
    output = tmp_path / 'DWG'
    output.mkdir()
    items = [
        NS(sheet_number='A1101', sheet_name='Bât A Niveau 1'),
        NS(sheet_number='A1102', sheet_name='Bât A Niveau 2'),
    ]
    progress = []

    def export(staging):
        Path(
            staging,
            'taa_dwg - Feuille - A1101 - Bât A Niveau 1.dwg',
        ).write_bytes(b'1')
        Path(
            staging,
            'taa_dwg - Feuille - A1102 - Bât A Niveau 2.dwg',
        ).write_bytes(b'2')
        Path(staging, 'logo.png').write_bytes(b'img')
        return True

    result = deliver_named_dwgs(
        str(output),
        items,
        ['TAA_A1101_Bât A Niveau 1.dwg',
         'TAA_A1102_Bât A Niveau 2.dwg'],
        export,
        progress_callback=lambda i, n, item, path: progress.append(
            (i, n, item.sheet_number, Path(path).name)
        ),
    )

    assert [Path(path).name for path in result['paths']] == [
        'TAA_A1101_Bât A Niveau 1.dwg',
        'TAA_A1102_Bât A Niveau 2.dwg',
    ]
    assert all(Path(path).is_file() for path in result['paths'])
    assert [Path(path).name for path in result['auxiliary']] == ['logo.png']
    assert (output / 'logo.png').is_file()
    assert progress == [
        (1, 2, 'A1101', 'TAA_A1101_Bât A Niveau 1.dwg'),
        (2, 2, 'A1102', 'TAA_A1102_Bât A Niveau 2.dwg'),
    ]
    assert not any('Feuille' in path.name for path in output.glob('*.dwg'))


@pytest.mark.parametrize('merge', [True, False, None])
def test_settings_repository_and_profile_roundtrip(tmp_path, merge):
    value = target(tmp_path, merge=merge)
    repo = CarnetRepository(str(tmp_path / 'carnets.json'))
    folder = PublicationFolder('DCE', 'dce', publication_settings=PublicationSettings(dwg_merge_views=merge))
    repo.save_folder(folder)
    repo.save(value)
    reopened = CarnetRepository(repo.storage_path)
    assert reopened.get('plans').publication_settings.dwg_merge_views is merge
    assert next(f for f in reopened.list_folders() if f.id == 'dce').publication_settings.dwg_merge_views is merge
    assert value.publication_settings.copy().to_dict()['dwg_merge_views'] is merge
    profiles = PublicationProfileService(str(tmp_path / 'profiles.json'))
    profiles.save('Custom', value.publication_settings)
    saved_profile = PublicationProfileService(
        profiles.storage_path).get('Custom')
    assert saved_profile['dwg_merge_views'] is (merge is not False)
    assert 'dwg_mode' not in saved_profile


@pytest.mark.parametrize('mode', ['COMBINED', 'SEPARATE'])
def test_legacy_missing_field_inherits_true_without_materializing_override(tmp_path, mode):
    value = target(tmp_path, mode)
    repo = CarnetRepository(str(tmp_path / 'old.json'))
    repo.save(value)
    data = json.loads(Path(repo.storage_path).read_text())
    del data['sets'][0]['publication_settings']['dwg_merge_views']
    Path(repo.storage_path).write_text(json.dumps(data))
    before = Path(repo.storage_path).read_bytes()
    restored = repo.get('plans')
    resolver = SettingsResolver(NS(get=lambda name: {'dwg_mode': mode}))
    assert restored.publication_settings.dwg_merge_views is None
    assert resolver.resolve(restored, profile_name='Legacy').dwg_merge_views is True
    assert restored.publication_settings.dwg_mode == mode
    assert Path(repo.storage_path).read_bytes() == before
    assert restored.publication_settings.dwg_merge_views is None
    assert all(p['dwg_merge_views'] is True for p in PublicationProfileService.DEFAULT_PROFILES.values())


def test_profile_parent_child_carnet_false_and_return_to_inheritance():
    resolver = SettingsResolver(NS(get=lambda name: {'dwg_merge_views': False}))
    root = PublicationFolder('DCE', 'root', publication_settings=PublicationSettings())
    child = PublicationFolder('Plans', 'child', parent_id='root', publication_settings=PublicationSettings())
    value = PublicationSet('Plans', publication_settings=PublicationSettings())
    def resolved():
        return resolver.resolve(value, child, 'Custom', [root, child]).dwg_merge_views
    assert resolved() is False
    root.publication_settings.dwg_merge_views = True
    assert resolved() is True
    child.publication_settings.dwg_merge_views = False
    assert resolved() is False
    value.publication_settings.dwg_merge_views = True
    assert resolved() is True
    value.publication_settings.dwg_merge_views = None
    assert resolved() is False
    assert resolver.source_label(value, 'dwg_merge_views', child, [root, child]) == 'Dossier « Plans »'


def test_refresh_preserves_preset_and_inheritance_guard():
    messages, calls = [], []
    cls = ui_methods(['_load_dwg_setups', '_select_dwg_setup', 'RefreshDwgSetups_Click'],
                     script=NS(get_logger=lambda: logging.getLogger(__name__)),
                     forms=NS(alert=lambda *a, **kw: messages.append(a)))
    window = cls()
    window._loading_settings = False
    class Combo:
        SelectedItem = 'TAA - DCE'
        @property
        def ItemsSource(self):
            return self.values
        @ItemsSource.setter
        def ItemsSource(self, value):
            assert window._loading_settings
            self.values = value
    window.DwgSetupCombo = Combo()
    names = ['TAA - DCE']
    def setups():
        calls.append(1)
        return names
    window.controller = NS(publication_service=NS(dwg_service=NS(get_predefined_setups=setups)))
    window.RefreshDwgSetups_Click(None, None)
    names[:] = ['TAA - DCE sans XRef']  # preset d'origine supprimé/renommé
    window.RefreshDwgSetups_Click(None, None)
    assert calls == [1, 1] and not messages
    assert window.DwgSetupCombo.SelectedItem == 'TAA - DCE'
    assert window.DwgSetupCombo.ItemsSource == ['', 'TAA - DCE sans XRef', 'TAA - DCE']
    assert window._loading_settings is False
    window.controller.publication_service.dwg_service.get_predefined_setups = lambda: 1 / 0
    window.RefreshDwgSetups_Click(None, None)
    assert messages and window.DwgSetupCombo.SelectedItem == 'TAA - DCE'
    assert window._loading_settings is False


@pytest.fixture
def command_api(monkeypatch):
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.UI', NS(
        PostableCommand=NS(ExportOptionsExportSetupsDWGOrDXF=33251),
        RevitCommandId=NS(LookupPostableCommandId=lambda cmd: ('id', cmd))))


def test_native_command_lookup_and_post(command_api):
    posted = []
    app = NS(CanPostCommand=lambda cmd: True, PostCommand=posted.append)
    assert command_id(app) == ('id', 33251)
    assert posted == []
    post_settings(app)
    assert posted == [('id', 33251)]


@pytest.mark.parametrize('failure', ['missing_enum', 'lookup_none', 'cannot_post', 'post_exception'])
def test_native_command_failure_is_not_swallowed(command_api, failure):
    api = sys.modules['Autodesk.Revit.UI']
    app = NS(CanPostCommand=lambda cmd: failure != 'cannot_post', PostCommand=lambda cmd: None)
    if failure == 'missing_enum':
        del api.PostableCommand.ExportOptionsExportSetupsDWGOrDXF
    elif failure == 'lookup_none':
        api.RevitCommandId.LookupPostableCommandId = lambda cmd: None
    elif failure == 'post_exception':
        app.PostCommand = lambda cmd: (_ for _ in ()).throw(RuntimeError('command already posted'))
    with pytest.raises(RuntimeError):
        post_settings(app)


@pytest.mark.parametrize('can_save', [True, False])
def test_gear_closes_only_after_command_check_and_state_save(can_save):
    events = []
    def save(state):
        events.append('save')
        if not can_save:
            raise IOError('read only')
    cls = ui_methods(['DwgSettings_Click'], command_id=lambda app: events.append('check'),
                     capture=lambda w: {'selection': ['a', 'b']},
                     script=NS(get_logger=lambda: logging.getLogger(__name__)),
                     forms=NS(alert=lambda *a, **kw: events.append('alert')))
    window = cls()
    window._ui_application = object()
    window._dwg_ui_session = NS(save=save)
    window.Close = lambda: events.append('close')
    window.DwgSettings_Click(None, None)
    assert events == ['check', 'save', 'close' if can_save else 'alert']
    assert window._open_dwg_settings is can_save


def test_xaml_and_modal_command_order_contract():
    root = ET.parse(PANEL / 'ui.xaml').getroot()
    names = {e.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name'): e for e in root.iter()}
    assert 'DwgSeparateRadio' not in names
    assert 'DwgCombinedRadio' not in names
    assert root.get('Height') == '760'
    assert float(root.get('Height')) <= 800
    assert names['CarnetSubfolderCheckBox'].get('Content') == 'Créer un dossier au nom du carnet'
    assert names['DwgSettingsButton'].get('Click') == 'DwgSettings_Click'
    assert names['DwgRefreshButton'].get('Click') == 'RefreshDwgSetups_Click'
    assert names['DwgMergeViewsCheckBox'].get('Checked') == 'SettingsChanged'
    assert names['DwgMergeViewsCheckBox'].get('Unchecked') == 'SettingsChanged'
    source = (PANEL / 'Export.smartbutton/script.py').read_text()
    tree = ast.parse(source)
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
    calls = [n for n in ast.walk(main) if isinstance(n, ast.Call)]
    show = next(n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'ShowDialog')
    post = next(n for n in calls if isinstance(n.func, ast.Name) and n.func.id == 'post_settings')
    assert show.lineno < post.lineno
    assert 'CreateAddInCommandBinding' not in source and '.Idling +=' not in source
    for path in ['Export.smartbutton/script.py', 'services/publication_preview_integration.py',
                 'services/publication_batch_service.py']:
        assert 'dwg_merge_views=settings.dwg_merge_views' in (PANEL / path).read_text()


def test_session_cache_is_small_scoped_and_consumed(tmp_path):
    values = {}
    env = NS(get_envvar=values.get, set_envvar=lambda k, v: values.__setitem__(k, v))
    repo = NS(storage_path=str(tmp_path / 'project.json'))
    session = DwgUiSession(repo, NS(GetHashCode=lambda: 1), env)
    other = DwgUiSession(repo, NS(GetHashCode=lambda: 2), env)
    state = {'selection': ['CARNET:a', 'CARNET:b'], 'carnets': [{'name': 'Élévation'}]}
    session.save(state)
    path = Path(values[session.key])
    assert path.is_file() and other.load() is None
    assert DwgUiSession(repo, NS(GetHashCode=lambda: 1), env).load() == state
    session.clear()
    assert not path.exists() and session.load() is None


def test_roundtrip_restores_temporary_booklets_selection_and_order(tmp_path):
    value = target(tmp_path, merge=False)
    selected = ['SHEET:plans:u2', 'SHEET:plans:u1']
    nodes = [NS(Tag=('CARNET', value), IsExpanded=True, IsSelected=False)]
    events = []
    def key(tag):
        return tag[0] + ':' + tag[1].id
    manager = NS(_key=key, _all=lambda: nodes, selected_tags=lambda: [nodes[0].Tag],
                 _select=lambda keys: events.append(keys))
    window = NS(session_carnets=[value], _drag_drop_manager=manager,
                PublicationTree=NS(SelectedItem=nodes[0]), _refresh_tree=lambda: events.append('refresh'))
    state = json.loads(json.dumps(capture(window)))
    state['selection'] = selected
    restore(window, state)
    restored = window.session_carnets[0]
    assert restored is not value and restored.persistent is False
    assert restored.publication_settings.dwg_merge_views is False
    assert [i.unique_id for i in restored.items] == ['u2', 'u1']
    assert nodes[0].IsSelected and nodes[0].IsExpanded
    assert events == ['refresh', selected]
    assert value.source is None  # sérialisation non destructive


def test_preview_explains_automatic_batch_and_references(tmp_path):
    value = target(tmp_path, 'COMBINED', False)
    service = PublicationService(
        NS(GetElement=lambda key: NS(Id=key, CanBePrinted=True)))
    preview = PublicationPreviewService(
        service, service.filename_service).build(
            value, value.publication_settings)

    assert [row.Mode for row in preview['rows']] == [
        'Automatique', 'Automatique'
    ]
    assert [Path(row.Path).name for row in preview['rows']] == [
        'Plans-A2.dwg', 'Plans-A1.dwg'
    ]
    assert all(
        Path(row.Path).parent == tmp_path / 'Plans' / 'DWG'
        for row in preview['rows']
    )
    assert any('stratégie automatique' in w for w in preview['warnings'])
    assert any(
        'TAA - DCE' in w and 'références externes' in w
        for w in preview['warnings']
    )


@pytest.mark.parametrize('kind', ['FOLDER', 'CARNET'])
def test_new_checkbox_uses_canonical_single_field_handler(kind):
    changes = []
    cls = ui_methods(['SettingsChanged'])
    window = cls()
    window._loading_settings = False
    window._selected_kind = kind
    window._save_folder_settings = lambda field: changes.append(('FOLDER', field))
    window._save_selected_field = lambda field: changes.append(('CARNET', field))
    window.SettingsChanged(NS(Name='DwgMergeViewsCheckBox'), None)
    assert changes == [(kind, 'dwg_merge_views')]
    window._loading_settings = True
    window.SettingsChanged(NS(Name='DwgMergeViewsCheckBox'), None)
    assert len(changes) == 1
