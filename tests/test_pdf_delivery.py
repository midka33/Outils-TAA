# -*- coding: utf-8 -*-
"""Non-régression du nommage PDF et de la livraison sans perte de fichiers."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

PANEL = Path(__file__).resolve().parents[1] / 'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
sys.path.insert(0, str(PANEL / 'services'))
sys.path.insert(0, str(PANEL / 'models'))
from pdf_file_delivery import deliver_named_pdfs
from pdf_export_service import PdfExportService


def test_maps_files_by_name_not_export_order_and_replaces_existing(tmp_path):
    (tmp_path / 'Plan RDC.pdf').write_bytes(b'old')
    calls = []
    def export(directory):
        calls.append(directory)
        Path(directory, 'taa_B.pdf').write_bytes(b'B')
        Path(directory, 'taa_A.pdf').write_bytes(b'A')
        return True
    paths = deliver_named_pdfs(str(tmp_path), ['taa_A.pdf', 'taa_B.pdf'],
                              ['Plan RDC.pdf', 'Plan étage.pdf'], export)
    assert len(calls) == 1
    assert [Path(p).read_bytes() for p in paths] == [b'A', b'B']
    assert sorted(p.name for p in tmp_path.iterdir()) == ['Plan RDC.pdf', 'Plan étage.pdf']


@pytest.mark.parametrize('names', [['Plan.pdf', 'plan.pdf'], ['../A.pdf', 'B.pdf'], ['CON.pdf', 'B.pdf']])
def test_invalid_names_prevent_export(tmp_path, names):
    calls = []
    with pytest.raises(ValueError):
        deliver_named_pdfs(str(tmp_path), ['taa_A.pdf', 'taa_B.pdf'], names, lambda d: calls.append(d))
    assert calls == []


@pytest.mark.parametrize('mode', ['false', 'missing', 'empty', 'exception'])
def test_failed_or_partial_export_preserves_existing_files(tmp_path, mode):
    old = tmp_path / 'A.pdf'
    old.write_bytes(b'old')
    def export(directory):
        if mode == 'exception':
            raise RuntimeError('Revit unavailable')
        Path(directory, 'taa_A.pdf').write_bytes(b'' if mode == 'empty' else b'new')
        return mode != 'false'
    with pytest.raises(RuntimeError, match='conservés'):
        deliver_named_pdfs(str(tmp_path), ['taa_A.pdf', 'taa_B.pdf'], ['A.pdf', 'B.pdf'], export)
    assert old.read_bytes() == b'old'
    assert not (tmp_path / 'B.pdf').exists()


def test_move_failure_rolls_back_already_replaced_files(tmp_path, monkeypatch):
    for name in ['A.pdf', 'B.pdf']:
        (tmp_path / name).write_bytes(b'old')
    def export(directory):
        for name in ['taa_A.pdf', 'taa_B.pdf']:
            Path(directory, name).write_bytes(b'new')
        return True
    rename = os.rename
    def locked(source, destination):
        if str(source).endswith('taa_B.pdf'):
            raise OSError('locked')
        return rename(source, destination)
    monkeypatch.setattr(os, 'rename', locked)
    with pytest.raises(RuntimeError, match='locked'):
        deliver_named_pdfs(str(tmp_path), ['taa_A.pdf', 'taa_B.pdf'], ['A.pdf', 'B.pdf'], export)
    assert [(tmp_path / n).read_bytes() for n in ['A.pdf', 'B.pdf']] == [b'old', b'old']


def test_native_export_one_call_explicit_sheet_naming_rule(tmp_path, monkeypatch):
    class Options:
        def SetNamingRule(self, rule):
            self.rule = rule
    class NetList(list):
        def Add(self, item):
            self.append(item)
    class ListFactory:
        def __getitem__(self, key):
            return NetList
    class Field:
        @staticmethod
        def Create():
            return Field()
    db = SimpleNamespace(PDFExportOptions=Options, TableCellCombinedParameterData=Field,
                         BuiltInParameter=SimpleNamespace(SHEET_NUMBER=-1),
                         BuiltInCategory=SimpleNamespace(OST_Sheets=-2), ElementId=lambda x: x)
    monkeypatch.setitem(sys.modules, 'Autodesk.Revit.DB', db)
    monkeypatch.setitem(sys.modules, 'System.Collections.Generic', SimpleNamespace(List=ListFactory()))
    calls = []
    class Document:
        def GetElement(self, element_id):
            return SimpleNamespace(SheetNumber='A' if element_id == 1 else 'B')
        def Export(self, directory, ids, options):
            calls.append((ids, options))
            assert options.Combine is False
            assert options.rule[0].ParamId == -1
            assert options.rule[0].CategoryId == -2
            assert options.rule[0].Prefix == 'taa_'
            for element_id in reversed(ids):
                Path(directory, 'taa_' + self.GetElement(element_id).SheetNumber + '.pdf').write_bytes(str(element_id).encode())
            return True
    service = PdfExportService(Document())
    monkeypatch.setattr(service, '_to_export_quality', lambda value: value)
    paths = service.export_named_separate([1, 2], str(tmp_path), ['RDC.pdf', 'Etage.pdf'])
    assert len(calls) == 1
    assert [Path(p).read_bytes() for p in paths] == [b'1', b'2']


def test_orchestrator_and_preview_use_the_same_effective_names(tmp_path):
    from publication_service import PublicationService
    from publication_preview_service import PublicationPreviewService
    from publication_item import PublicationItem
    from publication_set import PublicationSet
    from publication_settings import PublicationSettings
    items = [PublicationItem('u1', 1, 'SHEET', 'A1', 'RDC', 'DCE'),
             PublicationItem('u2', 2, 'SHEET', 'A2', 'Etage', 'DCE')]
    class Document:
        def GetElement(self, key):
            value = {'u1': 1, 'u2': 2}.get(key, key)
            return SimpleNamespace(Id=value, CanBePrinted=True)
    service = PublicationService(Document())
    native_calls = []
    def export(ids, directory, names):
        native_calls.append((ids, names))
        paths = []
        for name in names:
            path = Path(directory, name)
            path.write_bytes(b'PDF')
            paths.append(str(path))
        return paths
    service.pdf_service.export_named_separate = export
    settings = PublicationSettings.defaults()
    settings.pdf_mode, settings.dwg_enabled = 'SEPARATE', False
    settings.filename_template = '{numero}-{nom}'
    settings.output_directory = str(tmp_path)
    target = PublicationSet('Plans', items).with_settings(settings)
    preview_service = PublicationPreviewService(service, service.filename_service)
    preview = preview_service.build(target, settings)
    result = service.publish(target, str(tmp_path), pdf_combined=False)
    assert result['success']
    assert len(native_calls) == 1
    assert [row.Path for row in preview['rows']] == result['files']
    assert all(Path(path).is_file() for path in result['files'])
    settings.filename_template = '{carnet}'
    assert preview_service.build(target, settings)['errors']
