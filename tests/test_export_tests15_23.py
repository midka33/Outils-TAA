# -*- coding: utf-8 -*-
"""Régressions constatées dans Revit : collection DWG et aperçu principal."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
sys.path.insert(0, str(PANEL / 'services'))
from dwg_export_service import DwgExportService
from filename_service import FilenameService


@pytest.mark.parametrize('combined', [False, True])
@pytest.mark.parametrize('true_color', [False, True])
def test_dwg_export_passes_typed_ids_and_preserves_order(tmp_path, monkeypatch, combined, true_color):
    class ElementId:
        pass
    class NetList(list):
        def Add(self, item):
            assert isinstance(item, ElementId)
            self.append(item)
    class ListFactory:
        def __getitem__(self, kind):
            assert kind is ElementId
            return NetList
    class Options:
        Colors = 'setup color'
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', SimpleNamespace(
        ElementId=ElementId, DWGExportOptions=Options,
        ExportColorMode=SimpleNamespace(TrueColor='true color')))
    monkeypatch.setitem(sys.modules, 'System.Collections.Generic', SimpleNamespace(List=ListFactory()))
    ids = [ElementId(), ElementId()]
    calls = []
    class Document:
        def Export(self, directory, filename, native_ids, options):
            assert type(native_ids) is NetList
            assert list(native_ids) == ids
            assert options.MergedViews is combined
            assert options.Colors == ('true color' if true_color else 'setup color')
            calls.append(filename)
            return True
    assert DwgExportService(Document()).export(ids, str(tmp_path), 'COM',
                                              merged_views=combined, true_color=true_color)
    assert calls == ['COM']


def preview_method():
    # Exécute la vraie méthode UI sans charger WPF ni recréer sa logique.
    tree = ast.parse((PANEL / 'export_window.py').read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'ExportWindow')
    method = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == '_update_filename_preview')
    namespace = {}
    exec(compile(ast.Module(body=[method], type_ignores=[]), 'export_window.py', 'exec'), namespace)
    return namespace['_update_filename_preview']


@pytest.mark.parametrize('selection,expected', [('CARNET', 'A1'), ('SHEET', 'A2')])
def test_main_preview_resolves_number_parameter_and_folder(selection, expected):
    items = [SimpleNamespace(sheet_number=number, sheet_name='Plan', unique_id=number)
             for number in ['A1', 'A2']]
    class Document:
        Title = 'Projet'
        def GetElement(self, key):
            parameter = SimpleNamespace(StorageType=SimpleNamespace(ToString=lambda: 'String'),
                                        AsString=lambda: 'Sous-titre ' + key)
            return SimpleNamespace(LookupParameter=lambda name: parameter)
    service = FilenameService(Document())
    carnet = SimpleNamespace(name='COM', items=items)
    window = SimpleNamespace(_selected_set=carnet, _selected_kind=selection,
                             _selected_item=items[1], filename_service=service,
                             _folder_for_set=lambda target: SimpleNamespace(name='DCE'),
                             FilenamePreviewText=SimpleNamespace(Text='—'))
    template = '{dossier}-{carnet}-{numero}-{parametre:Sous-titre}'
    preview_method()(window, SimpleNamespace(filename_template=template))
    assert window.FilenamePreviewText.Text == 'DCE-COM-{0}-Sous-titre {0}'.format(expected)


def test_main_preview_exposes_failure_instead_of_silent_dash():
    class BrokenService:
        def resolve(self, *args, **kwargs):
            raise RuntimeError('Erreur de nommage')
    window = SimpleNamespace(_selected_set=object(), _selected_kind='CARNET',
                             filename_service=BrokenService(),
                             _folder_for_set=lambda target: None,
                             FilenamePreviewText=SimpleNamespace(Text='—'))
    preview_method()(window, SimpleNamespace(filename_template='{carnet}'))
    assert 'Erreur de nommage' in window.FilenamePreviewText.Text
