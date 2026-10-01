# -*- coding: utf-8 -*-
"""Nommage feuille/projet, identités durables et insertion : doubles API hors Revit."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace as NS
import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
sys.path.insert(0, str(PANEL / 'services'))
from filename_service import FilenameService


def parameter(name, value='', identifier=-1, storage='String', formatted=None, shared=None, has_value=True):
    return NS(Definition=NS(Name=name), Id=NS(Value=identifier), IsShared=shared is not None,
              GUID=shared, StorageType=NS(ToString=lambda: storage), HasValue=has_value,
              AsString=lambda: value, AsValueString=lambda: formatted,
              AsInteger=lambda: value, AsDouble=lambda: value, AsElementId=lambda: value)


def element(*parameters):
    return NS(Parameters=parameters,
              GetParameters=lambda name: [p for p in parameters if p.Definition.Name == name])


def service(sheets, project=None, definitions=None):
    def get(key):
        return (definitions or {}).get(key.Value) if hasattr(key, 'Value') else sheets.get(key)
    return FilenameService(NS(Title='Fichier.rvt', GetElement=get, ProjectInformation=project))


def test_catalogue_union_includes_empty_readonly_and_project_parameters():
    first = element(parameter('Numéro de feuille', 'A1'), parameter('Vide'))
    second = element(parameter('Numéro de feuille', 'A2'), parameter('Phase', 'DCE', -2))
    svc = service({'a': first, 'b': second}, element(parameter('Nom du projet', 'École')))
    tokens = [v.Token for v in svc.variable_catalogue([first, second])]
    assert tokens.count('{feuille:Numéro de feuille}') == 1
    assert '{feuille:Vide}' in tokens and '{feuille:Phase}' in tokens
    assert '{info_projet:Nom du projet}' in tokens and '{carnet}' in tokens


def test_scopes_legacy_unicode_and_first_sheet_context():
    svc = service({'a': element(parameter('Nom', 'Étage 01')), 'b': element(parameter('Nom', 'Étage 02'))},
                  element(parameter('Nom', 'École:Paris')))
    carnet = NS(items=[NS(unique_id='b'), NS(unique_id='a')], name='Plans')
    template = '{info_projet:Nom}-{feuille:Nom}-{parametre:Nom}'
    assert svc.validate_template(template) == []
    assert svc.filename(template, carnet) == ('École_Paris-Étage 02-Étage 02.pdf', [])
    assert svc.resolve('{feuille:Nom}', carnet, NS(unique_id='a')) == ('Étage 01', [])
    assert svc.resolve('{info_projet:Nom}', None) == ('École_Paris', [])


def test_duplicate_names_use_native_shared_or_project_durable_identity():
    sheet = element(parameter('Code', 'natif', -12), parameter('Code', 'partagé', 201, shared='abc'),
                    parameter('Code', 'projet', 202))
    svc = service({'a': sheet}, definitions={202: NS(UniqueId='definition-stable')})
    carnet = NS(items=[NS(unique_id='a')])
    variables = svc.parameters.catalogue([sheet])
    assert {v.Token for v in variables} == {'{feuille_id:builtin=-12}', '{feuille_id:guid=abc}',
                                         '{feuille_id:uid=definition-stable}'}
    assert {svc.resolve(v.Token, carnet)[0] for v in variables} == {'natif', 'partagé', 'projet'}
    for v in variables:
        assert svc.validate_template(v.Token) == []
    assert svc.resolve('{feuille:Code}', carnet)[1] == ['feuille:Code']
    # Les ElementId positifs ne sont jamais sérialisés dans les modèles.
    assert all('201' not in v.Token and '202' not in v.Token for v in variables)


@pytest.mark.parametrize('storage,value,formatted,expected', [
    ('Integer', 0, None, '0'), ('Double', 2.5, None, '2.5'),
    ('Double', 2.5, '2,50 m', '2,50 m'), ('ElementId', 'level', None, 'RDC')])
def test_typed_values(storage, value, formatted, expected):
    svc = service({'a': element(parameter('Valeur', value, storage=storage, formatted=formatted)),
                   'level': NS(Name='RDC')})
    assert svc.resolve('{feuille:Valeur}', NS(items=[NS(unique_id='a')])) == (expected, [])


def test_empty_missing_and_unset_values_are_reported():
    svc = service({'a': element(parameter('Vide'), parameter('Non défini', 0, storage='Integer', has_value=False))})
    carnet = NS(items=[NS(unique_id='a')])
    for token in ('feuille:Vide', 'feuille:Non défini', 'feuille:Absent', 'info_projet:Absent'):
        assert svc.resolve('{'+token+'}', carnet) == ('Sans_nom', [token])
    assert svc.validate_template('{info_projet:}')


def test_braces_in_parameter_name_have_insertable_identity():
    sheet = element(parameter('Code {ancien}', 'ok', -123))
    svc = service({'a': sheet})
    variable = svc.parameters.catalogue([sheet])[0]
    assert variable.Token == '{feuille_id:builtin=-123}'
    assert svc.resolve(variable.Token, NS(items=[NS(unique_id='a')])) == ('ok', [])


def ui_method(name):
    tree = ast.parse((PANEL / 'export_window.py').read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'ExportWindow')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {}
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(PANEL / 'export_window.py'), 'exec'), namespace)
    return namespace[name]


def test_picker_filter_and_insertion_replace_selection_at_caret():
    svc = service({}, element(parameter('Nom du projet', 'École')))
    variables = svc.variable_catalogue([])
    combo = NS(SelectedItem=None)
    ui = NS(_filename_variables=variables, FilenameTokenCombo=combo,
            FilenameVariableSearch=NS(Text='NOM DU PROJET'))
    ui_method('FilenameVariableSearchChanged')(ui, None, None)
    assert len(combo.ItemsSource) == 1
    combo.SelectedItem = combo.ItemsSource[0]
    box = NS(Text='Avant ancien Après', SelectionStart=6, SelectionLength=6, Focus=lambda: None)
    ui.FilenameTemplateTextBox = box
    ui_method('InsertFilenameToken_Click')(ui, None, None)
    assert box.Text == 'Avant {info_projet:Nom du projet} Après'
    assert box.CaretIndex == 6 + len(combo.SelectedItem.Token)
