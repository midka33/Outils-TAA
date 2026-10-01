# -*- coding: utf-8 -*-
"""Contrats de la refonte graphique, sans prétendre valider WPF hors Windows."""
from pathlib import Path
import importlib.util
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
THEME = ROOT / 'OutilsTAA.extension/resources/ui/Theme.xaml'
X = '{http://schemas.microsoft.com/winfx/2006/xaml}'


@pytest.mark.parametrize('filename,primary', [('ui.xaml','PublishButton'),
    ('carnet_manager.xaml','AddButton'), ('publication_preview.xaml','ConfirmButton'),
    ('carnet_sheets_window.xaml',None), ('publication_report.xaml',None)])
def test_window_resources_and_primary_action(filename, primary):
    root = ET.parse(PANEL / filename).getroot()
    theme = ET.parse(THEME).getroot()
    keys = {node.get(X+'Key') for node in theme}
    names = [node.get(X+'Name') for node in root.iter() if node.get(X+'Name')]
    assert len(names) == len(set(names))
    assert root.get('FontFamily') == 'Segoe UI'
    for node in root.iter():
        for value in node.attrib.values():
            if value.startswith('{DynamicResource '):
                assert value[len('{DynamicResource '):-1] in keys
    if primary:
        action = next(node for node in root.iter() if node.get(X+'Name') == primary)
        assert action.get('Style') == '{DynamicResource TaaPrimaryButton}'
    if filename == 'publication_report.xaml':
        diagnostic = next(n for n in root.iter() if n.get(X+'Name') == 'WarningsText')
        assert diagnostic.get('IsReadOnly') == 'True'
        assert diagnostic.get('VerticalScrollBarVisibility') == 'Auto'


def test_theme_loader_uses_absolute_packaged_path(monkeypatch):
    loaded = []
    class Dictionary(dict):
        def __init__(self):
            super().__init__(TaaBackground='background', TaaText='text')
    monkeypatch.setitem(sys.modules, 'System', SimpleNamespace(Uri=lambda path, kind: path, UriKind=SimpleNamespace(Absolute=1)))
    monkeypatch.setitem(sys.modules, 'System.Windows', SimpleNamespace(ResourceDictionary=Dictionary))
    monkeypatch.setitem(sys.modules, 'System.Windows.Media', SimpleNamespace(FontFamily=lambda value: value))
    spec = importlib.util.spec_from_file_location('theme_under_test', PANEL/'services/taa_ui_theme.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    window = SimpleNamespace(Resources=SimpleNamespace(MergedDictionaries=SimpleNamespace(Add=loaded.append)))
    module.apply_theme(window)
    assert Path(loaded[0].Source).resolve() == THEME.resolve()
    assert window.FontFamily == 'Segoe UI'
    assert window.UseLayoutRounding is True
