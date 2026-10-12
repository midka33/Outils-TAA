# -*- coding: utf-8 -*-
"""Reproduit DCE → Plan → A405 avec surcharge au dossier intermédiaire."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for part in ('services', 'models'):
    sys.path.insert(0, str(PANEL / part))
from publication_folder import PublicationFolder
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from settings_resolver import SettingsResolver
from carnet_repository import CarnetRepository
from pdf_options import PDF_OPTIONS


def ui_class():
    tree = ast.parse((PANEL / 'export_window.py').read_text(encoding='utf-8'))
    original = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ExportWindow')
    names = ('_inheritance_description', '_update_folder_inheritance_info', '_field_label',
             'RevertInheritance_Click', '_set_inheritance_ui', '_update_inheritance_info')
    nodes = [n for n in original.body if isinstance(n, ast.FunctionDef) and n.name in names]
    cls = ast.ClassDef(name='Window', bases=[], keywords=[], body=nodes, decorator_list=[])
    namespace = {"PDF_OPTIONS":PDF_OPTIONS,"Visibility":SimpleNamespace(Visible=1,Collapsed=0)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), 'export_window.py', 'exec'), namespace)
    return namespace['Window']


def test_inheritance_crosses_old_publication_set_parent():
    root = PublicationFolder(
        'DCE',
        'root',
        publication_settings=PublicationSettings(
            pdf_mode='SEPARATE',
            output_directory='Root',
        ),
    )
    parent = PublicationSet(
        'A1000',
        set_id='set-parent',
        folder_id='root',
        persistent=True,
        publication_settings=PublicationSettings(
            pdf_mode='COMBINED',
        ),
    )
    child_folder = PublicationFolder(
        'DETAILS',
        'details',
        'set-parent',
        publication_settings=PublicationSettings(),
    )
    nested = PublicationSet(
        'A1100',
        set_id='nested',
        folder_id='details',
        persistent=True,
        publication_settings=PublicationSettings(),
    )

    resolver = SettingsResolver(None)
    folders = [root, child_folder]
    sets = [parent, nested]

    child_settings = resolver.resolve_node(
        child_folder,
        folders=folders,
        publication_sets=sets,
    )
    nested_settings = resolver.resolve_node(
        nested,
        folders=folders,
        publication_sets=sets,
    )

    assert child_settings.pdf_mode == 'COMBINED'
    assert child_settings.output_directory == 'Root'
    assert nested_settings.pdf_mode == 'COMBINED'
    assert resolver.source_label_node(
        nested,
        'pdf_mode',
        folders=folders,
        publication_sets=sets,
    ) == 'Dossier « A1000 »'


def test_intermediate_folder_reverts_and_persists_without_touching_children(tmp_path):
    root = PublicationFolder('DCE', 'root', publication_settings=PublicationSettings(pdf_mode='SEPARATE', output_directory='Pictures'))
    child = PublicationFolder('Plan', 'child', 'root', publication_settings=PublicationSettings(pdf_mode='COMBINED', output_directory='Documents'))
    carnet = PublicationSet('A405', publication_settings=PublicationSettings())
    resolver = SettingsResolver(None)
    repo = CarnetRepository(str(tmp_path / 'carnets.json'))
    repo.save_folder(root)
    repo.save_folder(child)
    folders = [root, child]
    assert resolver.resolve(carnet, child, folders=folders).pdf_mode == 'COMBINED'
    assert resolver.source_label(carnet, 'pdf_mode', child, folders) == 'Dossier « Plan »'
    window = ui_class()()
    window.INHERITABLE_FIELDS = PublicationSettings.FIELDS
    window.settings_resolver = resolver
    window._folders = folders
    window._selected_kind = 'FOLDER'
    window._selected_folder = child
    window.RevertInheritanceButton = SimpleNamespace()
    window.InheritanceInfoText = SimpleNamespace()
    window.InheritanceRow = SimpleNamespace()
    window.controller = SimpleNamespace(save_folder=repo.save_folder)
    window._load_folder_settings = lambda: window._update_folder_inheritance_info(child)
    window._load_folder_settings()
    assert window.RevertInheritanceButton.IsEnabled
    assert 'Plan' in window.InheritanceInfoText.Text
    window.RevertInheritance_Click(None, None)
    assert not window.RevertInheritanceButton.IsEnabled
    assert 'DCE' in window.InheritanceInfoText.ToolTip
    effective = resolver.resolve(carnet, child, folders=folders)
    assert (effective.pdf_mode, effective.output_directory) == ('SEPARATE', 'Pictures')
    reloaded = next(f for f in repo.list_folders() if f.id == 'child')
    assert all(getattr(reloaded.publication_settings, f) is None for f in PublicationSettings.FIELDS)
    assert root.publication_settings.pdf_mode == 'SEPARATE'
    assert carnet.publication_settings.pdf_mode is None
    window._update_folder_inheritance_info(root)
    assert not window.RevertInheritanceButton.IsEnabled
