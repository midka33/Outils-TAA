# -*- coding: utf-8 -*-
"""Contrôles métier des compléments UI : périmètre, qualité et suppression."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for part in ('services', 'models'):
    sys.path.insert(0, str(PANEL / part))
from publication_settings import PublicationSettings
from publication_folder import PublicationFolder, _folder_targets
from publication_set import PublicationSet
from publication_item import PublicationItem
from settings_resolver import SettingsResolver
from publication_profile_service import PublicationProfileService
from publication_service import PublicationService
from publication_tree_delete import deletion_targets, delete_selected
from publication_overview import formats_for, summarize_publication
from carnet_repository import CarnetRepository


def test_quality_inherits_roundtrips_and_profiles(tmp_path):
    root = PublicationFolder('DCE', 'root', publication_settings=PublicationSettings(pdf_quality=600))
    child = PublicationFolder('Plans', 'child', 'root')
    carnet = PublicationSet('Carnet', set_id='c', persistent=True, folder_id='child', publication_settings=PublicationSettings())
    resolver = SettingsResolver(None)
    resolve = lambda: resolver.resolve(carnet, child, folders=[root, child])
    assert resolve().pdf_quality == 600
    assert carnet.publication_settings.pdf_quality is None
    carnet.publication_settings.pdf_quality = 1200
    repo = CarnetRepository(str(tmp_path/'sets.json'))
    repo.save(carnet)
    assert repo.list_all()[0].publication_settings.pdf_quality == 1200
    profiles = PublicationProfileService(str(tmp_path/'profiles.json'))
    profiles.save('Haute qualité', resolve())
    assert profiles.get('Haute qualité')['pdf_quality'] == 1200
    carnet.publication_settings.pdf_quality = None
    assert resolve().pdf_quality == 600
    assert resolver.resolve(PublicationSet('Ancien', publication_settings=PublicationSettings.from_dict({}))).pdf_quality == 300
    settings = resolve(); settings.pdf_quality = 999
    assert 'La qualité PDF est invalide.' in settings.validate()


@pytest.mark.parametrize('combined', [True, False])
@pytest.mark.parametrize('quality', PublicationSettings.PDF_QUALITIES)
def test_quality_reaches_pdf_exporter(tmp_path, combined, quality):
    settings = PublicationSettings.defaults(); settings.pdf_quality = quality
    item = PublicationItem('uid', 1, 'SHEET', 'A01', 'Plan')
    target = PublicationSet('Plans', [item], publication_settings=settings)
    service = PublicationService(SimpleNamespace(GetElement=lambda key: SimpleNamespace(Id=1, CanBePrinted=True)))
    calls = []
    def export(ids, directory, filename, combined, export_quality, settings=None):
        calls.append(export_quality); return True
    def separate(ids, directory, filenames, export_quality, settings=None):
        calls.append(export_quality); return [str(Path(directory)/n) for n in filenames]
    service.pdf_service = SimpleNamespace(export=export, export_named_separate=separate)
    result = service.publish(target, str(tmp_path), export_pdf=True, export_dwg=False, pdf_combined=combined)
    assert result['success'], result['errors']
    assert calls == [quality]


def test_summary_nested_folder_mixed_formats_and_sheet():
    root = PublicationFolder('DCE', 'root', publication_settings=PublicationSettings(pdf_enabled=True, dwg_enabled=False))
    child = PublicationFolder('Plans', 'child', 'root')
    first = PublicationSet('PDF', [1, 2], set_id='c1', folder_id='child')
    second = PublicationSet('DWG', [3], set_id='c2', folder_id='root', publication_settings=PublicationSettings(pdf_enabled=False, dwg_enabled=True))
    window = SimpleNamespace(_folders=[root, child], _carnets=[first, second])
    by_id = {f.id:f for f in window._folders}
    resolver = SettingsResolver(None)
    resolve = lambda c: resolver.resolve(c, by_id[c.folder_id], folders=window._folders)
    assert formats_for(resolve(first)) == ['PDF']
    assert formats_for(resolve(second)) == ['DWG']
    text = summarize_publication(_folder_targets(window, root), resolve)
    assert '3 mise(s)' in text and 'PDF + DWG' in text
    assert '1 mise(s)' in summarize_publication([first], resolve, selected_item=1)
    root.publication_settings.dwg_enabled = True
    assert formats_for(resolve(first)) == ['PDF', 'DWG']
    root.publication_settings.pdf_enabled = False
    root.publication_settings.dwg_enabled = False
    assert formats_for(resolve(first)) == []
    assert '2 sans format' in summarize_publication([first], resolve)


def test_multiple_delete_preserves_unselected_and_orders_children(tmp_path):
    repo = CarnetRepository(str(tmp_path/'sets.json'))
    root = PublicationFolder('DCE', 'root'); child = PublicationFolder('Plans', 'child', 'root')
    for f in (root, child): repo.save_folder(f)
    carnet = PublicationSet('Carnet', set_id='c', persistent=True, folder_id='child')
    repo.save(carnet)
    controller = SimpleNamespace(delete_folder=repo.delete_folder)
    tags = [('FOLDER', root), ('FOLDER', child), ('CARNET', carnet), ('CARNET', carnet)]
    targets = deletion_targets(tags)
    assert len(targets) == 3
    _, blocked = delete_selected([('FOLDER',root)], controller, repo, [], [root,child])
    assert blocked and len(repo.list_all()) == 1
    _, blocked = delete_selected(targets, controller, repo, [], [root,child])
    assert not blocked and not repo.list_all()
    assert [f.id for f in repo.list_folders()] == ['default']
    general = repo.list_folders()[0]
    _, blocked = delete_selected([('FOLDER',general)], controller, repo, [], [general])
    assert blocked


def test_session_carnet_blocks_folder_deletion(tmp_path):
    repo = CarnetRepository(str(tmp_path/'sets.json'))
    folder = PublicationFolder('DCE', 'root'); repo.save_folder(folder)
    carnet = PublicationSet('Session', set_id='s', persistent=False, folder_id='root')
    controller = SimpleNamespace(delete_folder=repo.delete_folder)
    remaining, blocked = delete_selected([('FOLDER',folder)], controller, repo, [carnet], [folder])
    assert remaining == [carnet] and blocked
    remaining, blocked = delete_selected([('FOLDER',folder),('CARNET',carnet)], controller, repo, [carnet], [folder])
    assert not remaining and not blocked


def test_ui_removed_folder_control_and_quality_summary_wiring():
    text = (PANEL/'export_window.py').read_text()
    xaml = (PANEL/'ui.xaml').read_text()
    integration = (PANEL/'services/publication_preview_integration.py').read_text()
    assert 'FolderCombo' not in text+xaml+integration
    assert 'FolderChanged' not in xaml+integration
    assert 'PdfQualityCombo' in xaml and 'PublicationSummaryText' in xaml
    tree = ast.parse(text)
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=='ExportWindow')
    for name in ('_load_selected_settings','_load_folder_settings','_save_selected_field','_apply_profile_values'):
        fn = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name)
        assert any(isinstance(n,ast.Attribute) and n.attr=='_update_publication_overview' for n in ast.walk(fn))


def load_method(relative, class_name, method_name):
    tree = ast.parse((PANEL/relative).read_text().replace('DragDropEffects.None', "getattr(DragDropEffects, 'None')"))
    parent = next(n for n in tree.body if getattr(n,'name',None)==class_name)
    fn = next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name==method_name)
    return fn


def test_overview_refreshes_actual_sheet_headers_and_scope():
    fn = load_method('export_window.py', 'ExportWindow', '_update_publication_overview')
    namespace = {'_folder_targets':_folder_targets, 'summarize_publication':summarize_publication, 'formats_for':formats_for}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), 'ui.py', 'exec'), namespace)
    root = PublicationFolder('DCE','root',publication_settings=PublicationSettings(pdf_enabled=True,dwg_enabled=False))
    item = PublicationItem('u',1,'SHEET','A01','Plan')
    carnet = PublicationSet('Plans',[item],set_id='c',folder_id='root')
    node = SimpleNamespace(Tag=('SHEET',item,carnet),Items=[],Header=None)
    resolver = SettingsResolver(None)
    window = SimpleNamespace(PublicationTree=SimpleNamespace(Items=[node]),
        _selected_kind='FOLDER',_selected_folder=root,_selected_set=None,_selected_item=None,
        _folders=[root],_carnets=[carnet],PublicationSummaryText=SimpleNamespace(),
        _resolve_settings=lambda c:resolver.resolve(c,root),_sheet_header=lambda i,s:formats_for(s),
        settings_resolver=resolver,_folder_for_set=lambda c:root)
    from publication_selection import publication_targets
    tags = [('FOLDER', root)]
    window._publication_selection_tags = lambda: tags
    window._publication_targets = lambda: publication_targets(tags, lambda f: _folder_targets(window, f))
    refresh = lambda:namespace['_update_publication_overview'](window)
    refresh()
    assert node.Header==['PDF'] and 'dossier et sous-dossiers' in window.PublicationSummaryText.Text
    root.publication_settings.dwg_enabled=True
    refresh(); assert node.Header==['PDF','DWG']
    tags[:] = [('SHEET', item, carnet)]
    window._selected_kind='SHEET';window._selected_set=carnet;window._selected_item=item
    refresh();assert 'cette mise en page' in window.PublicationSummaryText.Text
    assert '1 mise(s)' in window.PublicationSummaryText.Text
    header = SimpleNamespace(ToolTip='PDF + DWG')
    node.Header = header
    refresh()
    assert node.Header is header


def test_delete_handler_cancel_does_not_mutate():
    fn = load_method('services/publication_preview_integration.py','install_preview_on_export_window','delete_node_click')
    called=[]
    namespace={'deletion_targets':deletion_targets,'delete_selected':lambda *a:called.append(a),
               'forms':SimpleNamespace(alert=lambda *a,**kw:False)}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'integration.py','exec'),namespace)
    carnet=PublicationSet('Plans',set_id='c')
    window=SimpleNamespace(_drag_drop_manager=SimpleNamespace(selected_tags=lambda:[('CARNET',carnet)]))
    namespace['delete_node_click'](window,None,None)
    assert not called


def test_selected_tags_uses_multiselection_then_keyboard_fallback():
    fn=load_method('services/publication_tree_drag_drop.py','PublicationTreeDragDrop','selected_tags')
    namespace={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'selection.py','exec'),namespace)
    nodes=[SimpleNamespace(Tag=('CARNET',PublicationSet(str(i),set_id=str(i)))) for i in range(3)]
    manager=SimpleNamespace(_all=lambda:nodes,selected=['0','2'],_key=lambda t:t[1].id, _selection_explicit=False,
        window=SimpleNamespace(PublicationTree=SimpleNamespace(SelectedItem=nodes[1])))
    assert namespace['selected_tags'](manager)==[nodes[0].Tag,nodes[2].Tag]
    manager.selected=[]
    assert namespace['selected_tags'](manager)==[nodes[1].Tag]

    manager._selection_explicit = True
    assert namespace['selected_tags'](manager) == []
