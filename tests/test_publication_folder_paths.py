# -*- coding: utf-8 -*-
"""Vérifie les chemins réels et prévisualisés sans moteur Revit."""
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for part in ('models', 'services'):
    sys.path.insert(0, str(PANEL / part))
from publication_folder import PublicationFolder, _folder_targets
from publication_set import PublicationSet
from publication_item import PublicationItem
from publication_settings import PublicationSettings
from publication_paths import publication_directory, safe_directory_name
from publication_service import PublicationService
from publication_preview_service import PublicationPreviewService


def folder_target():
    root = PublicationFolder('DCE', 'root')
    child = PublicationFolder('Architecture', 'child', 'root')
    carnet = PublicationSet('Plans', [PublicationItem('u1', 1, 'SHEET', 'A1', 'Plan')],
                            set_id='c1', folder_id='child')
    window = SimpleNamespace(_folders=[root, child], _carnets=[carnet])
    return carnet, _folder_targets(window, root)[0], window, child


@pytest.mark.parametrize('scope', ['folder', 'set', 'sheet'])
@pytest.mark.parametrize('pdf_combined', [True, False])
@pytest.mark.parametrize('dwg_combined', [True, False])
def test_preview_matches_export_and_creates_only_needed_folders(tmp_path, pdf_combined, dwg_combined, scope):
    original, target, _, _ = folder_target()
    if scope != "folder":
        target = original
    settings = PublicationSettings.defaults()
    settings.output_directory = str(tmp_path)
    settings.filename_template = '{carnet}-{numero}'
    settings.pdf_mode = 'COMBINED' if pdf_combined else 'SEPARATE'
    settings.dwg_mode = 'COMBINED' if dwg_combined else 'SEPARATE'
    target = target.with_settings(settings)
    view = SimpleNamespace(Id=1, CanBePrinted=True)
    service = PublicationService(SimpleNamespace(GetElement=lambda key: view))
    delivered = []
    class Exporter:
        def __init__(self, extension):
            self.extension = extension
        def export(self, ids, directory, filename, setup_name=None, **kwargs):
            path = Path(directory) / (filename + self.extension)
            assert path.parent.is_dir()
            path.write_text('export simulé')
            delivered.append(str(path))
            return True
        def export_named_separate(self, ids, directory, filenames, export_quality=300):
            assert export_quality == 300
            paths = []
            for filename in filenames:
                path = Path(directory) / filename
                path.write_text('export simulé')
                paths.append(str(path))
            delivered.extend(paths)
            return paths
    service.pdf_service = Exporter('.pdf')
    service.dwg_service = Exporter('.dwg')
    preview = PublicationPreviewService(service, service.filename_service).build(target, settings)
    assert preview['errors'] == []
    assert list(tmp_path.iterdir()) == []
    result = service.publish(target, str(tmp_path), export_pdf=True, export_dwg=True,
                             pdf_combined=pdf_combined, dwg_combined=dwg_combined)
    assert result['success'], result['errors']
    assert sorted(row.Path for row in preview['rows']) == sorted(delivered)
    assert sorted(row['path'] for row in result['results']) == sorted(delivered)
    base = tmp_path / 'DCE' / 'Architecture' if scope == 'folder' else tmp_path
    for extension, combined in (('.pdf', pdf_combined), ('.dwg', dwg_combined)):
        assert ((base if combined else base / 'Plans') / ('Plans-A1' + extension)).is_file()
    assert (base / 'Plans').exists() is (not pdf_combined or not dwg_combined)
    assert not hasattr(original, 'publication_folder_parts')


def test_selected_subfolder_and_custom_destination(tmp_path):
    original, target, window, child = folder_target()
    sub = _folder_targets(window, child)[0]
    assert publication_directory(sub, str(tmp_path / 'autre'), False) == str(tmp_path / 'autre/Architecture/Plans')
    assert publication_directory(original, str(tmp_path), False) == str(tmp_path / "Plans")


@pytest.mark.parametrize('name,expected', [('PC:09*', 'PC_09_'), ('../Plans', '.._Plans'),
                                          ('..', 'Sans_nom'), ('CON.txt', '_CON.txt'),
                                          ('LPT1', '_LPT1'), ('Plan. ', 'Plan')])
def test_windows_directory_names(name, expected):
    assert safe_directory_name(name) == expected


def test_cross_booklet_collision_blocks_confirmation():
    import ast
    import os
    source = (PANEL / 'services/publication_preview_integration.py').read_text(encoding='utf-8')
    function = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == '_merge_previews')
    namespace = {'os': os}
    exec(compile(ast.Module(body=[function], type_ignores=[]), 'integration.py', 'exec'), namespace)
    merged = namespace['_merge_previews']([
        {'rows': [SimpleNamespace(Path='/export/DCE/Plan.pdf')]},
        {'rows': [SimpleNamespace(Path='/export/DCE/plan.pdf')]}])
    assert any('Collision entre carnets' in message for message in merged['errors'])


def test_recursive_settings_follow_parents_and_preserve_overrides():
    from settings_resolver import SettingsResolver
    root = PublicationFolder('DCE', 'root', publication_settings=PublicationSettings(
        output_directory='sortie', pdf_mode='SEPARATE', dwg_enabled=False))
    child = PublicationFolder('Architecture', 'child', 'root', publication_settings=PublicationSettings(dwg_enabled=True))
    leaf = PublicationFolder('Etage', 'leaf', 'child', publication_settings=PublicationSettings())
    target = PublicationSet('Plans', publication_settings=PublicationSettings(pdf_enabled=False))
    folders = [root, child, leaf]
    resolver = SettingsResolver(SimpleNamespace(get=lambda name: None))
    effective = resolver.resolve(target, leaf, folders=folders)
    assert effective.output_directory == 'sortie'
    assert effective.pdf_mode == 'SEPARATE'
    assert effective.dwg_enabled is True
    assert effective.pdf_enabled is False
    assert resolver.source_for(target, 'output_directory', leaf, folders=folders) == 'Dossier'
    assert leaf.publication_settings.to_dict()['output_directory'] is None
    root.publication_settings.output_directory = 'nouvelle-sortie'
    assert resolver.resolve(None, leaf, folders=folders).output_directory == 'nouvelle-sortie'
    child.publication_settings.dwg_enabled = None
    assert resolver.resolve(target, leaf, folders=folders).dwg_enabled is False
    root.parent_id = 'leaf'
    with pytest.raises(ValueError, match='Cycle'):
        resolver.resolve(target, leaf, folders=folders)
