# -*- coding: utf-8 -*-
"""Progression réelle : moteur, appels natifs simulés, livraison et hooks actifs."""
import ast
import logging
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for directory in ('services', 'models'):
    sys.path.insert(0, str(PANEL / directory))
from publication_progress import PublicationProgress, operation
from publication_service import PublicationService
from publication_batch_service import PublicationBatchService
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from publication_item import PublicationItem
from publication_history_service import PublicationHistoryService
from carnet_controller import CarnetController
from pdf_export_service import PdfExportService


def definitions(path, namespace, names):
    tree = ast.parse((PANEL / path).read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if getattr(n, 'name', None) in names]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def target(tmp_path, name='Plans', combined=True, dwg=False):
    settings = PublicationSettings.defaults()
    settings.output_directory = str(tmp_path / name)
    settings.pdf_mode = 'COMBINED' if combined else 'SEPARATE'
    settings.dwg_enabled = dwg
    settings.filename_template = '{carnet}-{numero}'
    items = [PublicationItem('u' + str(i), i, 'SHEET', 'A' + str(i), 'Plan') for i in (3, 1, 2)]
    return PublicationSet(name, items, set_id=name, publication_settings=settings)


def progress_for(targets, callback=None):
    return PublicationProgress(targets, [t.publication_settings for t in targets], callback)


@pytest.fixture
def native_api(monkeypatch):
    class Options:
        def SetNamingRule(self, rule):
            self.rule = rule
        def SetExportInBackground(self, value):
            self.background = value
    class NetList(list):
        def Add(self, value):
            self.append(value)
        @classmethod
        def __class_getitem__(cls, value):
            return cls
    db = SimpleNamespace(PDFExportOptions=Options, ElementId=lambda x: x,
        BuiltInCategory=SimpleNamespace(OST_Sheets=1), BuiltInParameter=SimpleNamespace(SHEET_NUMBER=2),
        TableCellCombinedParameterData=SimpleNamespace(Create=lambda: SimpleNamespace()))
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', db)
    monkeypatch.setitem(sys.modules, 'System.Collections.Generic', SimpleNamespace(List=NetList))
    monkeypatch.setattr(PdfExportService, '_to_export_quality', lambda self, value: value)


class NativeDocument:
    def __init__(self, progress=None, failure=None):
        self.progress = progress
        self.failure = failure
        self.calls = []
    def GetElement(self, key):
        number = int(str(key).lstrip('u'))
        return SimpleNamespace(Id=number, SheetNumber='A' + str(number), CanBePrinted=True)
    def Export(self, directory, ids, options):
        before = dict(self.progress.state) if self.progress else None
        self.calls.append((ids, options.Combine, threading.get_ident(), before))
        assert options.background is False
        if before:
            assert before['item_label'] == 'Export PDF Revit'
            assert before['phase'] == 'Export PDF' and before['percent'] < 100
        if self.failure == 'exception':
            raise RuntimeError('Diagnostic natif conservé')
        if self.failure == 'false':
            return False
        if options.Combine:
            Path(directory, options.FileName + '.pdf').write_bytes(bytes(ids))
        else:
            assert options.rule[0].Prefix == 'taa_'
            for index in ids:
                Path(directory, 'taa_A' + str(index) + '.pdf').write_bytes(bytes([index]))
        if before:
            assert self.progress.state == before  # aucun progrès à l'intérieur du natif
        return True


@pytest.mark.parametrize('combined', [True, False])
@pytest.mark.parametrize('with_callback', [True, False])
@pytest.mark.parametrize('dwg', [True, False])
def test_batch_global_plan_and_real_delivery(tmp_path, native_api, combined, with_callback, dwg):
    targets = [target(tmp_path, name, combined, dwg) for name in ('Plans', 'Coupes')]
    snapshots = []
    progress = progress_for(targets, snapshots.append if with_callback else None)
    document = NativeDocument(progress)
    service = PublicationService(document)
    dwg_calls = []
    service.dwg_service = SimpleNamespace(export=lambda *args, **kw: dwg_calls.append(args) or True)
    for value in targets:
        value._publication_items = value.items  # ordre métier de la sélection
        value._history_info = {'states': {}}
    history = PublicationHistoryService(str(tmp_path / 'history.json'))
    progress.start()
    report = PublicationBatchService(service).publish(targets, lambda t: t.publication_settings,
                                                     history_service=history, progress=progress)
    assert progress.state['percent'] < 100
    progress.finish(report)
    assert report['success'] and not report['errors']
    assert len(document.calls) == 2  # un seul appel PDF par carnet, dans les deux modes
    assert all(call[0] == [3, 1, 2] for call in document.calls)
    assert all(call[2] == threading.get_ident() for call in document.calls)
    assert len(dwg_calls) == (6 if dwg else 0)
    pdf_rows = [r for r in report['results'] if r['format'] == 'PDF']
    assert all(Path(row['path']).is_file() for row in pdf_rows)
    for value in targets:
        if combined:
            assert Path(value.publication_settings.output_directory, value.name + '-A3.pdf').read_bytes() == bytes([3, 1, 2])
        else:
            for i in (3, 1, 2):
                assert Path(value.publication_settings.output_directory, value.name,
                            value.name + '-A' + str(i) + '.pdf').read_bytes() == bytes([i])
    assert Path(tmp_path / 'history.json').is_file()
    assert progress.state['current'] == progress.state['total']
    assert progress.state['percent'] == 100
    if snapshots:
        percentages = [s['percent'] for s in snapshots]
        assert percentages[0] == 0 and percentages[-1] == 100
        assert percentages == sorted(percentages) and all(0 <= p <= 100 for p in percentages)
        assert all(s['total'] == snapshots[0]['total'] for s in snapshots)
        assert document.calls[1][3]['percent'] > document.calls[0][3]['percent']
        assert any(s['phase_key'] == 'delivery' for s in snapshots) is (not combined)


@pytest.mark.parametrize('failure', ['exception', 'false', 'delivery', 'validation'])
def test_errors_are_processed_and_diagnosed_without_success_history(tmp_path, native_api, monkeypatch, failure):
    value = target(tmp_path, combined=False)
    states = []
    progress = progress_for([value], states.append)
    document = NativeDocument(progress, failure)
    if failure == 'validation':
        value.publication_settings.output_directory = ''
    if failure == 'delivery':
        import pdf_export_service
        monkeypatch.setattr(pdf_export_service, 'reconcile_native_pdfs',
                            lambda *args: (_ for _ in ()).throw(RuntimeError('Livraison refusée')))
    history_calls = []
    value._history_info = {'states': {}}
    progress.start()
    report = PublicationBatchService(PublicationService(document)).publish(
        [value], lambda t: t.publication_settings,
        history_service=SimpleNamespace(record_publication=lambda *a, **kw: history_calls.append(a)),
        progress=progress)
    progress.finish(report)
    assert not report['success'] and report['errors'] and not history_calls
    assert progress.state['percent'] == 100
    assert len(document.calls) == (0 if failure == 'validation' else 1)
    if failure == 'exception':
        assert any('Diagnostic natif conservé' in e for e in report['errors'])
    if failure == 'delivery':
        assert any('Livraison refusée' in e for e in report['errors'])
        assert any('Échec de livraison' in s['message'] for s in states)
    else:
        assert any('Non exécutée après erreur' in s['message'] for s in states)


def test_missing_units_cannot_be_declared_finished(tmp_path):
    progress = progress_for([target(tmp_path)])
    with pytest.raises(RuntimeError, match='incomplet'):
        progress.finish({})
    with pytest.raises(RuntimeError, match='non traitée'):
        progress.target(0).finalize(True)
    with pytest.raises(ValueError, match='non commencée'):
        progress.target(0).end('pdf')
    with pytest.raises(ValueError, match='absente'):
        progress.target(0).begin('invented')
    assert progress.state['percent'] == 0


def test_duplicate_completion_does_not_inflate_percentage(tmp_path):
    progress = progress_for([target(tmp_path)])
    unit = progress.target(0)
    unit.begin('prepare')
    unit.end('prepare')
    before = dict(progress.state)
    unit.end('prepare')
    assert progress.state == before


def test_callback_failure_does_not_interrupt_file_delivery(tmp_path, native_api):
    value = target(tmp_path, combined=False)
    def broken_callback(state):
        if state['phase_key'] == 'delivery':
            raise RuntimeError('WPF indisponible')
    progress = progress_for([value], broken_callback)
    doc = NativeDocument(progress)
    result = PublicationBatchService(PublicationService(doc)).publish(
        [value], lambda t: t.publication_settings, progress=progress)
    progress.finish(result)
    assert result['success'] and len(doc.calls) == 1
    assert all(Path(row['path']).is_file() for row in result['results'])
    assert len(result['warnings']) == 1 and 'WPF indisponible' in result['warnings'][0]


@pytest.mark.parametrize('combined', [True, False])
def test_reporter_absent_preserves_outputs(tmp_path, native_api, combined):
    value = target(tmp_path, combined=combined)
    document = NativeDocument()
    result = PublicationService(document).publish(value, value.publication_settings.output_directory,
                                                  pdf_combined=combined, items=value.items)
    assert result['success'] and len(document.calls) == 1
    assert all(Path(row['path']).is_file() for row in result['results'])


def session_class(events, failure=None):
    class Window:
        def __init__(self, owner, **kwargs):
            self.owner = owner
        def Show(self):
            events.append('show')
            assert self.owner.IsEnabled is False
            if failure == 'show':
                raise RuntimeError('Ouverture impossible')
        def update(self, state):
            events.append(dict(state))
        def close_progress(self):
            events.append('close')
    namespace = definitions('publication_progress_window.py',
        {'PublicationProgress': PublicationProgress, 'PublicationProgressWindow': Window, 'logging': logging},
        ['PublicationProgressSession'])
    return namespace['PublicationProgressSession']


@pytest.mark.parametrize('failure', ['show', 'history', None])
@pytest.mark.parametrize('enabled', [True, False])
def test_session_restores_owner_and_closes_on_fatal_error(tmp_path, failure, enabled):
    events = []
    cls = session_class(events, failure)
    value = target(tmp_path)
    owner = SimpleNamespace(IsEnabled=enabled, _resolve_settings=lambda t: t.publication_settings)
    try:
        with cls(owner, [value]) as progress:
            assert events[0] == 'show' and events[1]['percent'] == 0
            with pytest.raises(RuntimeError, match='déjà'):
                cls(owner, [value]).__enter__()
            if failure:
                raise RuntimeError('Historique impossible')
            for key in ('prepare', 'pdf'):
                with operation(progress.target(0), key):
                    pass
            progress.target(0).finalize(True)
            progress.finish({})
    except RuntimeError as exc:
        assert failure and ('impossible' in str(exc))
    assert owner.IsEnabled is enabled and owner._publication_in_progress is False
    assert events[-1] == 'close'
    if failure == 'history':
        assert events[-2]['status'] == 'interrupted' and events[-2]['percent'] < 100
    elif failure is None:
        assert events[-2]['percent'] == 100


@pytest.mark.parametrize('folder', [True, False])
@pytest.mark.parametrize('confirmed', [True, False])
def test_active_hooks_confirmation_progress_close_then_report(tmp_path, native_api, folder, confirmed):
    events, reports = [], []
    targets = [target(tmp_path, name, combined=False) for name in ('Plans', 'Coupes')]
    document = NativeDocument()
    service = PublicationService(document)
    controller = CarnetController.__new__(CarnetController)
    controller.publication_service = service
    window = SimpleNamespace(IsEnabled=True, controller=controller,
        _resolve_settings=lambda t: t.publication_settings, _folder_for_set=lambda t: None,
        _selected_folder=SimpleNamespace(name='DCE'))
    def report_dialog(report, owner):
        assert events[-1] == 'close' and owner.IsEnabled is True
        assert events[-2]['percent'] == 100
        reports.append(report)
        return SimpleNamespace(ShowDialog=lambda: events.append('report'))
    flow = SimpleNamespace(PublicationProgressSession=session_class(events),
        PublicationBatchService=PublicationBatchService, PublicationReportWindow=report_dialog,
        PublicationPreviewWindow=lambda *a, **kw: SimpleNamespace(confirmed=confirmed,
            ShowDialog=lambda: events.append('preview')))
    history = PublicationHistoryService(str(tmp_path / 'history.json'))
    ns = definitions('Export.smartbutton/script.py', {'publication_preview_integration': flow,
        '_history_service': lambda w: history, '_current_states': lambda w, t: {'version': '1'},
        '_build_preview_stage07': lambda *args: {'errors': []}},
        ['_publish_targets_stage07', '_preview_then_publish_folder_stage07', '_install_stage07_hooks'])
    ns['_install_stage07_hooks']()
    assert flow._publish_targets is ns['_publish_targets_stage07']
    if folder:
        flow._preview_then_publish_folder(window, targets)
    else:
        entry = definitions('services/publication_preview_integration.py', {
            '_build_preview': lambda *args: {'errors': []},
            'PublicationPreviewWindow': flow.PublicationPreviewWindow,
            '_publish_targets': flow._publish_targets}, ['_preview_then_publish_single'])
        entry['_preview_then_publish_single'](window, targets)
    if not confirmed:
        assert events == ['preview'] and not document.calls and not reports
    else:
        assert events[:2] == ['preview', 'show'] and events[-1] == 'report'
        assert len(document.calls) == 2 and reports[0]['success']
        snapshots = [e for e in events if isinstance(e, dict)]
        assert snapshots[0]['percent'] == 0 and snapshots[-1]['percent'] == 100
        assert [e['percent'] for e in snapshots] == sorted(e['percent'] for e in snapshots)


def test_window_contract_handlers_and_same_thread_repaint():
    source = (PANEL / 'publication_progress_window.py').read_text(encoding='utf-8')
    root = ET.parse(PANEL / 'publication_progress.xaml').getroot()
    names = {node.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name') for node in root.iter()}
    class Base:
        pass
    ns = definitions('publication_progress_window.py', {'forms': SimpleNamespace(WPFWindow=Base),
        'Action': lambda action: action, 'DispatcherPriority': SimpleNamespace(Loaded=6)},
        ['PublicationProgressWindow'])
    cls = ns['PublicationProgressWindow']
    assert hasattr(cls, root.get('Closing'))
    instance = cls.__new__(cls)
    for name in names - {None}:
        setattr(instance, name, SimpleNamespace())
    calls = []
    instance.UpdateLayout = lambda: calls.append('layout')
    instance.Dispatcher = SimpleNamespace(Invoke=lambda priority, action: calls.append(priority))
    state = {'percent': 68, 'current': 17, 'total': 25, 'carnet_name': 'Plans DCE',
             'item_label': 'Export PDF Revit', 'phase': 'Export PDF', 'phase_key': 'pdf',
             'message': 'Export PDF Revit en cours…'}
    instance.update(state)
    assert instance.PercentText.Text == '68 %' and instance.ProgressBar.Value == 68
    assert instance.UnitsText.Text == '17 / 25 unités'
    assert calls == ['layout', 6]
    args = SimpleNamespace(Cancel=False)
    instance._allow_close = False
    instance.Window_Closing(None, args)
    assert args.Cancel
    instance.Close = lambda: calls.append('close')
    instance.close_progress()
    instance.Window_Closing(None, args)
    assert not args.Cancel and calls[-1] == 'close'
    assert 'ShowDialog(' not in source and 'sleep(' not in source


def test_business_layers_have_no_ui_import_or_background_thread():
    filenames = ['publication_progress.py', 'publication_service.py', 'publication_batch_service.py',
                 'pdf_export_service.py', 'pdf_file_delivery.py', 'carnet_controller.py']
    for name in filenames:
        tree = ast.parse((PANEL / 'services' / name).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert not any(part in node.module for part in ('Windows', 'pyrevit', 'threading', 'concurrent'))
            if isinstance(node, ast.Import):
                assert all(n.name not in ('threading', 'wpf') for n in node.names)
    options = (PANEL / 'services/pdf_options.py').read_text(encoding='utf-8')
    assert 'SetExportInBackground(False)' in options


def test_delivery_progress_completes_only_after_rollback(tmp_path, native_api):
    value = target(tmp_path, combined=False)
    value._publication_items = value.items
    output = Path(value.publication_settings.output_directory, value.name)
    output.mkdir(parents=True)
    existing = output / 'Plans-A3.pdf'
    existing.write_bytes(b'ancien PDF')
    (output / 'Plans-A1.pdf').mkdir()  # échec après le premier déplacement
    restored = []
    def callback(state):
        if 'Échec de livraison' in state['message']:
            restored.append(existing.read_bytes())
    progress = progress_for([value], callback)
    document = NativeDocument(progress)
    report = PublicationBatchService(PublicationService(document)).publish(
        [value], lambda t: t.publication_settings, progress=progress)
    progress.finish(report)
    assert restored == [b'ancien PDF']
    assert existing.read_bytes() == b'ancien PDF'
    assert (output / 'Plans-A1.pdf').is_dir()
    assert not (output / 'Plans-A2.pdf').exists()
    assert len(document.calls) == 1 and not report['success']
    assert 'Fichiers temporaires conservés' in report['errors'][0]


def test_fatal_history_error_in_active_hook_stops_below_100(tmp_path, native_api):
    events = []
    value = target(tmp_path)
    controller = CarnetController.__new__(CarnetController)
    controller.publication_service = PublicationService(NativeDocument())
    window = SimpleNamespace(IsEnabled=True, controller=controller,
        _resolve_settings=lambda t: t.publication_settings)
    history = PublicationHistoryService(str(tmp_path / 'history.json'))
    def broken_history(*args, **kwargs):
        raise RuntimeError('Historique inaccessible')
    history.record_publication = broken_history
    flow = SimpleNamespace(PublicationProgressSession=session_class(events),
        PublicationReportWindow=lambda *a, **kw: pytest.fail('Pas de rapport de succès après erreur fatale'))
    ns = definitions('Export.smartbutton/script.py', {'publication_preview_integration': flow,
        '_history_service': lambda w: history, '_current_states': lambda w, t: {}},
        ['_publish_targets_stage07'])
    with pytest.raises(RuntimeError, match='Historique inaccessible'):
        ns['_publish_targets_stage07'](window, [value])
    assert events[-1] == 'close'
    assert events[-2]['message'] == 'Publication interrompue' and events[-2]['percent'] < 100
    assert window.IsEnabled and not window._publication_in_progress


def test_dwg_only_waits_for_group_before_finishing(tmp_path):
    value = target(tmp_path, dwg=True)
    value.publication_settings.pdf_enabled = False
    progress = progress_for([value])
    service = PublicationService(NativeDocument(progress))
    snapshots = []
    service.dwg_service = SimpleNamespace(export=lambda *a, **kw: snapshots.append(dict(progress.state)) or True)
    report = PublicationBatchService(service).publish([value], lambda t: t.publication_settings, progress=progress)
    progress.finish(report)
    assert report['success'] and len(snapshots) == 3
    assert all(s['phase'] == 'Export DWG' and s['percent'] < 100 for s in snapshots)
    assert len({s['percent'] for s in snapshots}) == 1


def test_cleanup_error_preserves_original_exception(tmp_path, caplog):
    events = []
    cls = session_class(events)
    value = target(tmp_path)
    owner = SimpleNamespace(IsEnabled=True, _resolve_settings=lambda t: t.publication_settings)
    with pytest.raises(RuntimeError, match='Erreur origine'):
        with cls(owner, [value]) as progress:
            # Seconde panne pendant le nettoyage, journalisée sans masquer l'origine.
            def close_fails(self):
                raise RuntimeError('Fermeture impossible')
            cls._close_after_error.__globals__['PublicationProgressWindow'].close_progress = close_fails
            raise RuntimeError('Erreur origine')
    assert owner.IsEnabled and not owner._publication_in_progress
    assert 'Fermeture impossible' in caplog.text


def test_production_syntax_avoids_python3_only_constructs():
    files = ['publication_progress_window.py', 'Export.smartbutton/script.py',
             'services/publication_progress.py', 'services/publication_service.py',
             'services/publication_batch_service.py', 'services/pdf_export_service.py',
             'services/carnet_controller.py', 'services/publication_preview_integration.py']
    for name in files:
        source = (PANEL / name).read_text(encoding='utf-8')
        assert source.startswith('# -*- coding: utf-8 -*-')
        tree = ast.parse(source, filename=name)
        compile(tree, name, 'exec')
        for node in ast.walk(tree):
            assert not isinstance(node, (ast.AsyncFunctionDef, ast.Await, ast.JoinedStr,
                                         ast.AnnAssign, ast.NamedExpr, ast.YieldFrom))
            if isinstance(node, ast.FunctionDef):
                assert not node.returns and not node.args.kwonlyargs
                assert all(arg.annotation is None for arg in node.args.args)
