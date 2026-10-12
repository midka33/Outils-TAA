# -*- coding: utf-8 -*-
"""Separate PDF/DWG naming: settings, export naming, and WPF contract."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET

PANEL = Path(__file__).resolve().parents[1] / "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
sys.path.insert(0, str(PANEL / "services"))
from publication_settings import PublicationSettings
from settings_resolver import SettingsResolver


def _filename_method():
    path = PANEL / "services/publication_service.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    cls = next(n for n in module.body if getattr(n, "name", None) == "PublicationService")
    fn = next(n for n in cls.body if getattr(n, "name", None) == "_filename")
    code = compile(ast.Module(body=[fn], type_ignores=[]), str(path), "exec")
    namespace = {}
    exec(code, namespace)
    return namespace["_filename"]


def _render_filename(settings, ext):
    captured = []
    class FakeFilename(object):
        def filename(self, template, publication_set, item=None, folder_name=None, extension=None):
            captured.append((template, extension))
            return "ok", []
    owner = SimpleNamespace(filename_service=FakeFilename())
    owner._folder_name = lambda publication_set: None
    publication = SimpleNamespace(publication_settings=settings)
    _filename_method()(owner, publication, SimpleNamespace(), ext)
    return captured[0][0]


def test_shared_mode_reuses_pdf_template_for_separate_dwgs():
    settings = PublicationSettings.defaults()
    settings.pdf_mode = "SEPARATE"
    settings.filename_template = "PDF-{numero}"
    assert _render_filename(settings, ".pdf") == "PDF-{numero}"
    assert _render_filename(settings, ".dwg") == "PDF-{numero}"


def test_combined_pdf_forces_separate_dwg_filename():
    settings = PublicationSettings.defaults()
    settings.filename_template = "DOSSIER-{carnet}"
    settings.dwg_filename_independent = False
    assert settings.pdf_mode == "COMBINED"
    assert _render_filename(settings, ".dwg") == "{numero} {nom}"
    assert _render_filename(settings, ".pdf") == "DOSSIER-{carnet}"


def test_explicit_independence_and_persistence():
    settings = PublicationSettings.defaults()
    settings.pdf_mode = "SEPARATE"
    settings.filename_template = "P-{carnet}"
    settings.dwg_filename_independent = True
    settings.dwg_filename_template = "DWG-{numero}"
    restored = PublicationSettings.from_dict(settings.to_dict())
    assert restored.dwg_filename_independent is True
    assert _render_filename(restored, ".dwg") == "DWG-{numero}"
    assert _render_filename(restored, ".pdf") == "P-{carnet}"


def test_old_settings_load_without_new_fields():
    settings = PublicationSettings.from_dict({
        "filename_template": "{carnet}", "pdf_mode": "SEPARATE",
    })
    assert settings.dwg_filename_independent is None
    assert _render_filename(settings, ".dwg") == "{carnet}"


def test_wpf_has_both_controls_and_handlers():
    xml = ET.parse(str(PANEL / "ui.xaml"))
    names = set(node.get("{http://schemas.microsoft.com/winfx/2006/xaml}Name")
                for node in xml.iter())
    assert "DwgFilenameTemplateTextBox" in names
    assert "DwgFilenameIndependentCheckBox" in names
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert 'self.DwgFilenameTemplateTextBox.IsEnabled = independent' in source
    assert 'self.DwgFilenameIndependentCheckBox.IsEnabled = not combined' in source
