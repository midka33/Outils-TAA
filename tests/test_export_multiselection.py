# -*- coding: utf-8 -*-
"""Périmètre Ctrl/Maj : vrais handlers et services exécutés sans WPF/Revit."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace, MethodType

from unittest.mock import MagicMock

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for directory in ('services', 'models'):
    sys.path.insert(0, str(PANEL / directory))
from publication_selection import publication_targets
from publication_set import PublicationSet
from publication_item import PublicationItem
from publication_folder import PublicationFolder, _folder_targets
from publication_settings import PublicationSettings
from publication_overview import summarize_publication
from publication_preview_service import PublicationPreviewService
from filename_service import FilenameService
from publication_history_service import PublicationHistoryService


def method(path, parent, name, namespace=None):
    source = (PANEL / path).read_text(encoding='utf-8')
    source = source.replace('DragDropEffects.None', "getattr(DragDropEffects, 'None')")
    tree = ast.parse(source)
    container = next(n for n in tree.body if getattr(n, 'name', None) == parent) if parent else tree
    node = next(n for n in container.body if getattr(n, 'name', None) == name)
    namespace = namespace if namespace is not None else {}
    exec(compile(ast.Module(body=[node], type_ignores=[]), path, 'exec'), namespace)
    return namespace[name]


def carnet(name='Plans', key='p'):
    settings = PublicationSettings.defaults()
    settings.filename_template = '{carnet}-{numero}'
    settings.dwg_enabled = True
    return PublicationSet(name, [PublicationItem(str(key) + str(i), i, 'SHEET', 'A' + str(i), 'Plan')
                                for i in (3, 1, 2)], set_id=key, folder_id='root',
                          persistent=True, publication_settings=settings)


def sheet(target, index):
    return ('SHEET', target.items[index], target)


def test_subset_preserves_business_order_identity_settings_and_original():
    parent = carnet()
    targets = publication_targets([sheet(parent, 2), sheet(parent, 0), sheet(parent, 2)], lambda f: [])
    assert len(targets) == 1
    target = targets[0]
    assert target is not parent and target.id == parent.id
    assert target.items == [parent.items[0], parent.items[2]]
    assert target.publication_settings is parent.publication_settings
    assert target.folder_id == parent.folder_id and len(parent.items) == 3


@pytest.mark.parametrize('reverse', [False, True])
def test_parent_carnet_overrides_partial_selection_without_duplicates(reverse):
    parent = carnet()
    tags = [sheet(parent, 1), ('CARNET', parent), sheet(parent, 2)]
    targets = publication_targets(tags[::-1] if reverse else tags, lambda f: [])
    assert len(targets) == 1 and targets[0].items == parent.items


def test_two_carnets_keep_same_sheet_as_separate_deliverables():
    first, second = carnet(), carnet('Coupes', 'c')
    second.items[0] = first.items[0]
    targets = publication_targets([sheet(first, 0), sheet(second, 0)], lambda f: [])
    assert [t.id for t in targets] == ['p', 'c']
    assert targets[0].items == targets[1].items == [first.items[0]]


def test_nested_folder_selection_keeps_root_paths_and_deduplicates_children():
    root = PublicationFolder('DCE', 'root')
    child = PublicationFolder('ARCHI', 'child', 'root')
    parent = carnet(); parent.folder_id = 'child'
    window = SimpleNamespace(_folders=[root, child], _carnets=[parent])
    tags = [('FOLDER', root), ('FOLDER', child), ('CARNET', parent), sheet(parent, 0)]
    targets = publication_targets(tags, lambda f: _folder_targets(window, f))
    assert len(targets) == 1 and targets[0].items == parent.items
    assert targets[0].publication_folder_parts == ('DCE', 'ARCHI')
    assert not hasattr(parent, 'publication_folder_parts')


def test_temporary_carnets_without_ids_are_not_merged():
    first, second = carnet(key=None), carnet('Autre', None)
    first.persistent = second.persistent = False
    targets = publication_targets([('CARNET', first), ('CARNET', second)], lambda f: [])
    assert len(targets) == 2


def test_empty_selection_produces_no_target():
    assert publication_targets([], lambda f: []) == []


@pytest.mark.parametrize('combined', [False, True])
def test_actual_preview_and_stage07_publish_use_same_subset_and_per_carnet_settings(tmp_path, combined):
    first, second = carnet(), carnet('Coupes', 'c')
    for index, parent in enumerate((first, second)):
        parent.publication_settings.output_directory = str(tmp_path / str(index))
        parent.publication_settings.pdf_mode = 'COMBINED' if combined else 'SEPARATE'
        parent.publication_settings.dwg_mode = 'COMBINED' if combined else 'SEPARATE'
        parent.publication_settings.dwg_merge_views = index == 1
    tags = [sheet(first, 0), sheet(first, 2), sheet(second, 1)]
    targets = publication_targets(tags, lambda f: [])
    service = SimpleNamespace(sort_items=lambda target: target.items,
        _resolve_current_sheet_id=lambda item: item.sheet_id,
        document=SimpleNamespace(GetElement=lambda key: SimpleNamespace(CanBePrinted=True)))
    history = PublicationHistoryService(str(tmp_path / 'history.json'))
    previews, published, reports = [], [], []
    preview_service = PublicationPreviewService(service, FilenameService())
    class Preview:
        def __init__(self, *args):
            pass
        def build(self, target, settings, **kwargs):
            previews.append((target.id, list(target.items), settings.output_directory))
            return preview_service.build(target, settings, **kwargs)
    def publish(target, directory, **kwargs):
        published.append((target.id, kwargs['items'], directory))
        assert kwargs['pdf_combined'] is combined and kwargs['dwg_combined'] is combined
        assert kwargs['dwg_merge_views'] is (target.id == second.id)
        return {'success': True, 'results': []}
    merge = method('services/publication_preview_integration.py', None, '_merge_previews', {'os': __import__('os')})
    flow = SimpleNamespace(PublicationProgressSession=lambda *args: MagicMock(), PublicationPreviewService=Preview, _merge_previews=merge,
        PublicationReportWindow=lambda report, owner: SimpleNamespace(ShowDialog=lambda: reports.append(report)))
    window = SimpleNamespace(_resolve_settings=lambda t: t.publication_settings,
        _folder_name=lambda t: 'DCE', filename_service=FilenameService(),
        controller=SimpleNamespace(publication_service=service, publish=publish))
    ns = {'publication_preview_integration': flow, '_history_service': lambda w: history,
          '_current_states': lambda w, t: {i.unique_id: {} for i in t.items}}
    build = method('Export.smartbutton/script.py', None, '_build_preview_stage07', ns)
    run = method('Export.smartbutton/script.py', None, '_publish_targets_stage07', ns)
    preview = build(window, targets)
    assert not preview['errors']
    assert preview['count'] == (4 if combined else 6)
    run(window, targets)
    assert previews == published
    assert [len(t[1]) for t in published] == [2, 1]
    assert all(str(tmp_path / str(i)) in reports[0]['output_directory'] for i in (0, 1))
    assert '3 mise(s)' in summarize_publication(targets, window._resolve_settings)
    assert len(first.items) == len(second.items) == 3


def test_collisions_across_selected_carnets_block_confirmation():
    merge = method('services/publication_preview_integration.py', None, '_merge_previews', {'os': __import__('os')})
    preview = merge([{'rows': [SimpleNamespace(Path='/exports/Plans.pdf')]},
                     {'rows': [SimpleNamespace(Path='/exports/plans.pdf')]}])
    assert len(preview['errors']) == 1 and 'Collision' in preview['errors'][0]


@pytest.mark.parametrize('confirmed', [False, True])
def test_publish_handler_passes_entire_selection_and_honors_cancel(confirmed):
    first, second = carnet(), carnet('Coupes', 'c')
    tags = [sheet(first, 0), sheet(first, 2), ('CARNET', second)]
    targets = publication_targets(tags, lambda f: [])
    observed = []
    ns = {'_build_preview': lambda w, ts: observed.append(('preview', ts)) or {},
          'PublicationPreviewWindow': lambda *args, **kwargs: SimpleNamespace(confirmed=confirmed, ShowDialog=lambda: None),
          '_publish_targets': lambda w, ts: observed.append(('publish', ts))}
    ns['_preview_then_publish_single'] = method('services/publication_preview_integration.py', None, '_preview_then_publish_single', ns)
    handler = method('services/publication_preview_integration.py', 'install_preview_on_export_window', 'publish_click_with_preview', ns)
    window = SimpleNamespace(_publication_selection_tags=lambda: tags, _publication_targets=lambda: targets)
    handler(window, None, None)
    assert [kind for kind, ts in observed] == (['preview', 'publish'] if confirmed else ['preview'])
    assert all(ts is targets for kind, ts in observed)


def test_preview_button_uses_all_selected_targets(monkeypatch):
    targets = publication_targets([('CARNET', carnet()), ('CARNET', carnet('Coupes', 'c'))], lambda f: [])
    calls = []
    dialog = SimpleNamespace(ConfirmButton=SimpleNamespace(), CancelButton=SimpleNamespace(), ShowDialog=lambda: None)
    flow = SimpleNamespace(_build_preview=lambda w, ts: calls.append(ts) or {},
                           PublicationPreviewWindow=lambda *args, **kwargs: dialog)
    monkeypatch.setitem(sys.modules, 'publication_preview_integration', flow)
    handler = method('export_window.py', 'ExportWindow', 'Preview_Click', {'Visibility': SimpleNamespace(Collapsed=0)})
    handler(SimpleNamespace(_publication_targets=lambda: targets), None, None)
    assert calls == [targets] and dialog.ConfirmButton.Visibility == 0


def test_ctrl_shift_and_empty_selection_refresh_publish_scope():
    # Simule les événements interceptés, qui ne lèvent pas SelectedItemChanged.
    first = carnet()
    nodes = [SimpleNamespace(Tag=sheet(first, i), ClearValue=lambda prop: None) for i in range(3)]
    keys = ['SHEET:p:' + n.Tag[1].unique_id for n in nodes]
    keyboard = SimpleNamespace(Modifiers=0)
    ns = {'Keyboard': keyboard, 'ModifierKeys': SimpleNamespace(Shift=1, Control=2),
          'TreeViewItem': SimpleNamespace(BackgroundProperty='bg', ForegroundProperty='fg')}
    manager = SimpleNamespace(selected=[], _selection_explicit=False, SELECTED_BRUSH='orange', selected_foreground='black',
        _all=lambda: nodes, _selection_nodes=lambda kind: nodes if kind == 'SHEET' else [],
        _key=lambda tag: 'SHEET:p:' + tag[1].unique_id, _item=lambda source: source,
        _valid_key=lambda node: 'SHEET:p:' + node.Tag[1].unique_id, _ordered=lambda node: keys)
    snapshots = []
    manager.window = SimpleNamespace(PublicationTree=SimpleNamespace(SelectedItem=nodes[0]),
        _publication_selection_changed=lambda: snapshots.append(manager.selected_tags()))
    for name in ('_select', 'selected_tags', '_mouse_down', '_key_down'):
        ns['Key'] = SimpleNamespace(Up=10, Down=11, Left=12, Right=13, Home=14, End=15)
        setattr(manager, name, MethodType(method('services/publication_tree_drag_drop.py', 'PublicationTreeDragDrop', name, ns), manager))
    manager._mouse_down(None, SimpleNamespace(OriginalSource=nodes[0]))
    keyboard.Modifiers = 1
    manager._mouse_down(None, SimpleNamespace(OriginalSource=nodes[2]))
    assert len(snapshots[-1]) == 3
    keyboard.Modifiers = 2
    for node in nodes:
        manager._mouse_down(None, SimpleNamespace(OriginalSource=node))
    assert snapshots[-1] == [] and manager.selected_tags() == []
    manager._key_down(None, SimpleNamespace(Key=10))
    assert manager.selected_tags() == [nodes[0].Tag]


def test_selection_info_counts_all_targets_and_disables_empty_selection():
    parent = carnet()
    tags = [sheet(parent, 0), sheet(parent, 2)]
    window = SimpleNamespace(_publication_selection_tags=lambda: tags,
        _publication_targets=lambda: publication_targets(tags, lambda f: []),
        SelectionInfo=SimpleNamespace(), PublishButton=SimpleNamespace(),
        _update_publication_overview=lambda: None)
    window._set_no_selection = lambda: setattr(window.PublishButton, 'IsEnabled', False)
    handler = method('services/publication_preview_integration.py', 'install_preview_on_export_window', 'update_selection_info')
    handler(window)
    assert '2 mise(s)' in window.SelectionInfo.Text
    assert window.PublishButton.Content == 'Publier la sélection'
    tags[:] = []
    handler(window)
    assert not window.PublishButton.IsEnabled
