# -*- coding: utf-8 -*-
"""Options natives PDF, héritage et contrats XAML, sans prétendre charger Revit."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import pytest

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT/'OutilsTAA.extension/OutilsTAA.tab/Export.panel'
for folder in ('services','models'):
    sys.path.insert(0,str(PANEL/folder))
from pdf_options import PDF_OPTIONS, PDF_OPTION_FIELDS, defaults, apply_options, capabilities, changed_options
from publication_settings import PublicationSettings
from publication_set import PublicationSet
from publication_folder import PublicationFolder
from publication_item import PublicationItem
from settings_resolver import SettingsResolver
from publication_profile_service import PublicationProfileService
from carnet_repository import CarnetRepository
from pdf_export_service import PdfExportService
from publication_paths import publication_directory
from publication_preview_service import PublicationPreviewService
from publication_service import PublicationService


@pytest.mark.parametrize('field,prop,default,label', PDF_OPTIONS)
def test_each_option_is_inherited_persisted_and_profiled(tmp_path,field,prop,default,label):
    raw=PublicationSettings();setattr(raw,field,not default)
    folder=PublicationFolder('DCE','root',publication_settings=raw)
    target=PublicationSet('Plans',set_id='c',persistent=True,folder_id='root',publication_settings=PublicationSettings())
    resolver=SettingsResolver(None)
    assert getattr(resolver.resolve(target,folder),field) is not default
    assert getattr(target.publication_settings,field) is None
    setattr(target.publication_settings,field,False)
    repo=CarnetRepository(str(tmp_path/'sets.json'));repo.save(target)
    assert getattr(repo.list_all()[0].publication_settings,field) is False
    profiles=PublicationProfileService(str(tmp_path/'profiles.json'))
    profiles.save('Technique',resolver.resolve(target,folder))
    assert profiles.get('Technique')[field] is False
    setattr(target.publication_settings,field,None)
    assert getattr(resolver.resolve(target,folder),field) is not default


@pytest.mark.parametrize('combined',[True,False])
def test_options_reach_native_export_in_both_modes(tmp_path,monkeypatch,combined):
    class Options:
        def __init__(self):
            for f,prop,d,label in PDF_OPTIONS:setattr(self,prop,d)
        def SetExportInBackground(self,value): self.background=value
    monkeypatch.setitem(sys.modules,'Autodesk.Revit.DB',SimpleNamespace(PDFExportOptions=Options))
    calls=[]
    service=PdfExportService(SimpleNamespace(Export=lambda directory,ids,options:calls.append(options) or True))
    service._to_export_quality=lambda q:('DPI',q)
    settings=PublicationSettings.defaults()
    for f,prop,d,label in PDF_OPTIONS:setattr(settings,f,not d)
    assert service.export([1],str(tmp_path),'Plans',combined=combined,settings=settings)
    assert len(calls)==1 and calls[0].background is False
    for f,prop,d,label in PDF_OPTIONS:assert getattr(calls[0],prop) is (not d)


def test_named_separate_forwards_settings_before_safe_delivery(tmp_path,monkeypatch):
    service=PdfExportService(SimpleNamespace(GetElement=lambda key:SimpleNamespace(SheetNumber='A1')))
    settings=PublicationSettings.defaults();settings.pdf_raster=True
    calls=[]
    def separate(ids,directory,quality,use_sheet_numbers,settings=None):
        calls.append(settings);Path(directory,'taa_A1.pdf').write_bytes(b'PDF');return True
    monkeypatch.setattr(service,'export_separate',separate)
    paths=service.export_named_separate([1],str(tmp_path),['Plan.pdf'],settings=settings)
    assert calls==[settings] and Path(paths[0]).read_bytes()==b'PDF'


def test_capability_probe_and_missing_option_are_explicit(monkeypatch):
    disposed=[]
    class Options:
        AlwaysUseRaster=False
        def Dispose(self):disposed.append(True)
    monkeypatch.setitem(sys.modules,'Autodesk.Revit.DB',SimpleNamespace(PDFExportOptions=Options))
    supported=capabilities()
    assert supported['pdf_raster'] and not supported['pdf_links_blue'] and disposed
    settings=PublicationSettings.defaults()
    apply_options(Options(),settings)
    settings.pdf_links_blue=True
    with pytest.raises(ValueError,match='indisponible'):apply_options(Options(),settings)


def test_apply_only_changed_fields_keeps_inheritance():
    initial=defaults();current=dict(initial)
    assert changed_options(initial,current)=={}
    current['pdf_raster']=True
    assert changed_options(initial,current)=={'pdf_raster':True}


@pytest.mark.parametrize('combined',[True,False])
@pytest.mark.parametrize('subfolder',[True,False])
def test_subfolder_preview_and_export_use_effective_setting(tmp_path,combined,subfolder):
    item=PublicationItem('u',1,'SHEET','A1','Plan')
    raw=PublicationSet('Plans',[item],publication_settings=PublicationSettings())
    settings=PublicationSettings.defaults();settings.output_directory=str(tmp_path)
    settings.separate_carnet_subfolder=subfolder;settings.dwg_enabled=False
    settings.pdf_mode='COMBINED' if combined else 'SEPARATE'
    service=PublicationService(SimpleNamespace(GetElement=lambda key:SimpleNamespace(Id=1,CanBePrinted=True)))
    preview=PublicationPreviewService(service,service.filename_service).build(raw,settings)
    expected=tmp_path/'Plans' if subfolder and not combined else tmp_path
    assert Path(preview['rows'][0].Path).parent==expected
    assert Path(publication_directory(raw.with_settings(settings),str(tmp_path),combined))==expected
    assert raw.publication_settings.separate_carnet_subfolder is None


def test_new_xaml_handlers_exist_and_common_settings_are_not_in_expander():
    ns={'w':'http://schemas.microsoft.com/winfx/2006/xaml/presentation'}
    x='{http://schemas.microsoft.com/winfx/2006/xaml}'
    events={'Click','Checked','Unchecked','SelectionChanged','TextChanged','LostFocus','SelectedItemChanged','MouseDoubleClick'}
    main=ast.parse((PANEL/'export_window.py').read_text())
    integration=ast.parse((PANEL/'services/publication_preview_integration.py').read_text())
    names={n.name for n in ast.walk(main) if isinstance(n,ast.FunctionDef)}
    names.update(n.attr for n in ast.walk(integration) if isinstance(n,ast.Attribute))
    for xml,py in [('ui.xaml',None),('pdf_settings.xaml','pdf_settings_window.py')]:
        tree=ET.parse(PANEL/xml)
        handlers=names if py is None else {n.name for n in ast.walk(ast.parse((PANEL/py).read_text())) if isinstance(n,ast.FunctionDef)}
        for node in tree.iter():
            for event in events:
                if node.get(event):assert node.get(event) in handlers,(xml,node.get(event))
    tree=ET.parse(PANEL/'ui.xaml')
    advanced=next(n for n in tree.iter() if n.get(x+'Name')=='AdvancedOptions')
    assert advanced.get('IsExpanded')=='False'
    assert not {'PdfCheckBox','DwgCheckBox','OutputDirectoryTextBox','FilenameTemplateTextBox'} & {n.get(x+'Name') for n in advanced.iter()}
    inheritance=next(n for n in tree.iter() if n.get(x+'Name')=='InheritanceRow')
    assert not list(inheritance.iterfind('.//w:StackPanel',ns))
    assert next(n for n in inheritance.iter() if n.get(x+'Name')=='InheritanceInfoText').get('TextTrimming')=='CharacterEllipsis'
    assert next(n for n in tree.iter() if n.get(x+'Name')=='SettingsPanel').tag.endswith('StackPanel')
    assert float(tree.getroot().get('Height')) <= 760


def extract_method(file,cls,name,namespace):
    tree=ast.parse((PANEL/file).read_text())
    parent=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls)
    fn=next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[fn],type_ignores=[]),file,'exec'),namespace)
    return namespace[name]


def test_dialog_cancel_defaults_and_apply_do_not_mutate_initial():
    namespace={'defaults':defaults,'changed_options':changed_options}
    cancel=extract_method('pdf_settings_window.py','PdfSettingsWindow','Cancel_Click',namespace)
    reset=extract_method('pdf_settings_window.py','PdfSettingsWindow','Defaults_Click',namespace)
    apply=extract_method('pdf_settings_window.py','PdfSettingsWindow','Apply_Click',namespace)
    initial=defaults();initial['pdf_raster']=True
    window=SimpleNamespace(initial=initial,result=None,controls={f:SimpleNamespace(IsChecked=v) for f,v in initial.items() if f!='pdf_raster'},
        supported={f:True for f in initial},RasterRadio=SimpleNamespace(IsChecked=True),Close=lambda:None)
    window._display=lambda values:[setattr(window.RasterRadio,'IsChecked',values['pdf_raster'])]
    cancel(window,None,None);assert window.result is None and window.initial['pdf_raster'] is True
    reset(window,None,None);assert window.result is None and window.initial['pdf_raster'] is True
    apply(window,None,None);assert window.result=={'pdf_raster':False}


def test_manual_destination_saves_only_destination_at_active_level():
    fn=extract_method('export_window.py','ExportWindow','SettingsChanged',{})
    saved=[]
    window=SimpleNamespace(_loading_settings=False,_selected_kind='FOLDER',
        _save_folder_settings=lambda field:saved.append(('folder',field)),
        _save_selected_field=lambda field:saved.append(('carnet',field)))
    fn(window,SimpleNamespace(Name='OutputDirectoryTextBox'),None)
    window._selected_kind='CARNET';fn(window,SimpleNamespace(Name='OutputDirectoryTextBox'),None)
    assert saved==[('folder','output_directory'),('carnet','output_directory')]
    tree=ET.parse(PANEL/'ui.xaml')
    control=next(n for n in tree.iter() if n.get('{http://schemas.microsoft.com/winfx/2006/xaml}Name')=='OutputDirectoryTextBox')
    assert control.get('LostFocus')=='SettingsChanged'


def test_preview_only_hides_confirmation_and_never_publishes(monkeypatch):
    calls=[]
    dialog=SimpleNamespace(ConfirmButton=SimpleNamespace(),CancelButton=SimpleNamespace(),ShowDialog=lambda:calls.append('show'))
    flow=SimpleNamespace(_build_preview=lambda window,targets:calls.append(targets) or {},
        PublicationPreviewWindow=lambda data,owner:dialog)
    monkeypatch.setitem(sys.modules,'publication_preview_integration',flow)
    fn=extract_method('export_window.py','ExportWindow','Preview_Click',{'Visibility':SimpleNamespace(Collapsed=0)})
    window=SimpleNamespace(_selected_kind='CARNET',_selected_set='target')
    fn(window,None,None)
    assert calls==[['target'],'show']
    assert dialog.ConfirmButton.Visibility==0 and dialog.ConfirmButton.IsDefault is False
    assert dialog.CancelButton.Content=='Fermer'
