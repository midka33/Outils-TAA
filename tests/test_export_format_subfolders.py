# -*- coding: utf-8 -*-
"""Organisation PDF/DWG découplée du dossier de publication, sans Revit/WPF."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace

import pytest

PANEL = Path(__file__).resolve().parents[1] / (
    "OutilsTAA.extension/OutilsTAA.tab/Export.panel")
for part in ("models", "services"):
    sys.path.insert(0, str(PANEL / part))

from publication_settings import PublicationSettings
from publication_folder import PublicationFolder
from publication_set import PublicationSet
from publication_paths import publication_directory
from settings_resolver import SettingsResolver
from publication_profile_service import PublicationProfileService
from carnet_repository import CarnetRepository


@pytest.mark.parametrize("publication_folder", [False, True])
@pytest.mark.parametrize("format_folder", [False, True])
def test_four_independent_output_combinations(tmp_path, publication_folder, format_folder):
    target = PublicationSet("A2100_Façades_Collectif_A")
    target.publication_folder_parts = ("A2000 Plans des façades",)
    settings = PublicationSettings.defaults()
    settings.separate_carnet_subfolder = publication_folder
    settings.separate_format_subfolders = format_folder
    root = tmp_path / "A2000 Plans des façades"
    if publication_folder:
        root = root / "A2100_Façades_Collectif_A"
    for fmt in ("PDF", "DWG"):
        directory = publication_directory(
            target, str(tmp_path), settings=settings, format_name=fmt)
        assert directory == str(root / fmt if format_folder else root)
    assert publication_directory(target, str(tmp_path),
                                 settings=settings, format_name=None) == str(root)


@pytest.mark.parametrize("legacy_folder", [False, True])
def test_legacy_json_without_new_field_keeps_output_identical(tmp_path, legacy_folder):
    legacy = PublicationSettings.from_dict({
        "separate_carnet_subfolder": legacy_folder,
    })
    assert legacy.separate_format_subfolders is None
    target = PublicationSet("Plans")
    expected = tmp_path / "Plans" / "PDF" if legacy_folder else tmp_path
    assert publication_directory(
        target, str(tmp_path), settings=legacy,
        format_name="PDF") == str(expected)

    # Réenregistrement via le repository conserve l'absence de surcharge :
    repo = CarnetRepository(str(tmp_path / "publication.json"))
    target.id = "plans"
    target.persistent = True
    target.publication_settings = legacy
    repo.save(target)
    restored = next(s for s in repo.list_all() if s.id == "plans")
    assert restored.publication_settings.separate_format_subfolders is None
    assert publication_directory(restored, str(tmp_path),
                                 settings=restored.publication_settings,
                                 format_name="PDF") == str(expected)


def test_resolver_keeps_new_option_independent_across_ancestor_and_child():
    root = PublicationFolder("DCE", "root",
                             publication_settings=PublicationSettings(
                                 separate_carnet_subfolder=False,
                                 separate_format_subfolders=True))
    child = PublicationFolder("Architecture", "child", "root",
                              publication_settings=PublicationSettings(
                                  separate_carnet_subfolder=True))
    target = PublicationSet("Plans", set_id="plans", folder_id="child",
                            publication_settings=PublicationSettings())
    resolver = SettingsResolver(None)
    actual = resolver.resolve_node(
        target, folders=[root, child], publication_sets=[target])
    assert actual.separate_carnet_subfolder is True
    assert actual.separate_format_subfolders is True

    child.publication_settings.separate_format_subfolders = False
    actual = resolver.resolve_node(
        target, folders=[root, child], publication_sets=[target])
    assert actual.separate_carnet_subfolder is True
    assert actual.separate_format_subfolders is False
    assert resolver.source_for_node(
        target, "separate_format_subfolders", folders=[root, child],
        publication_sets=[target]) is child


def test_resolver_legacy_default_is_coupled_until_new_option_explicitly_set():
    root = PublicationFolder("DCE", "root", publication_settings=PublicationSettings(
        separate_carnet_subfolder=False))
    child = PublicationSet("Plans", set_id="plans", folder_id="root",
                           publication_settings=PublicationSettings())
    resolver = SettingsResolver(None)
    assert resolver.resolve_node(
        child, folders=[root], publication_sets=[child]
    ).separate_format_subfolders is False
    assert resolver.resolve(child, root, folders=[root]).separate_format_subfolders is False
    # Nouvelle option explicite : on peut avoir PDF/DWG sans dossier Plans.
    child.publication_settings.separate_format_subfolders = True
    actual = resolver.resolve_node(
        child, folders=[root], publication_sets=[child])
    assert actual.separate_carnet_subfolder is False
    assert actual.separate_format_subfolders is True


def test_profiles_save_independent_output_options(tmp_path):
    profiles = PublicationProfileService(str(tmp_path / "profiles.json"))
    settings = PublicationSettings.defaults()
    settings.separate_carnet_subfolder = False
    settings.separate_format_subfolders = True
    profiles.save("Façades", settings)
    saved = profiles.get("Façades")
    assert saved["separate_carnet_subfolder"] is False
    assert saved["separate_format_subfolders"] is True
    assert PublicationSettings.from_dict(saved).separate_format_subfolders is True

    # Les profils prédéfinis anciens ne changent pas la valeur explicite
    # d'un dossier lorsqu'ils ne possèdent pas les nouveaux champs.
    builtin = profiles.get("PDF + DWG")
    assert "separate_format_subfolders" not in builtin
    assert "separate_carnet_subfolder" not in builtin


def test_xaml_and_event_map_have_two_distinct_options():
    root = ET.parse(str(PANEL / "ui.xaml")).getroot()
    ns = "{http://schemas.microsoft.com/winfx/2006/xaml/presentation}"
    xml_ns = "{http://schemas.microsoft.com/winfx/2006/xaml}"
    names = {
        element.attrib.get(xml_ns + "Name"): element.attrib
        for element in root.iter(ns + "CheckBox")
    }
    assert "CarnetSubfolderCheckBox" in names
    assert "FormatSubfoldersCheckBox" in names
    assert names["CarnetSubfolderCheckBox"]["Checked"] == "SettingsChanged"
    assert names["FormatSubfoldersCheckBox"]["Unchecked"] == "SettingsChanged"

    window = (PANEL / "export_window.py").read_text(encoding="utf-8")
    assert '"FormatSubfoldersCheckBox": "separate_format_subfolders"' in window
    assert '"separate_format_subfolders": bool(self.FormatSubfoldersCheckBox.IsChecked)' in window
    assert "self.FormatSubfoldersCheckBox.IsChecked = effective.separate_format_subfolders" in window


def test_first_edit_of_legacy_publication_folder_preserves_other_checkbox():
    """Désactiver le dossier ne doit plus désactiver silencieusement PDF/DWG."""
    import ast
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    cls = next(
        n for n in ast.parse(source).body
        if isinstance(n, ast.ClassDef) and n.name == "ExportWindow")
    node = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "_freeze_legacy_format_folder_setting")
    namespace = {}
    exec(compile(ast.Module(body=[node], type_ignores=[]),
                 "export_window.py", "exec"), namespace)
    method = namespace[node.name]

    publication = PublicationSet(
        "Plans", set_id="plans", persistent=True,
        publication_settings=PublicationSettings(
            separate_carnet_subfolder=True))
    current = publication.publication_settings
    resolver = SettingsResolver(None)
    window = SimpleNamespace(
        _setting_source=lambda target, field: "Défaut",
        _resolve_container_settings=lambda target: resolver.resolve_node(
            target, publication_sets=[publication]))

    method(window, publication, current, "separate_carnet_subfolder")
    assert current.separate_format_subfolders is True
    current.separate_carnet_subfolder = False
    resolved = resolver.resolve_node(
        publication, publication_sets=[publication])
    assert resolved.separate_carnet_subfolder is False
    assert resolved.separate_format_subfolders is True

    # Éditer les autres réglages ne transforme pas les anciennes valeurs.
    other = PublicationSettings(separate_carnet_subfolder=True)
    method(window, publication, other, "pdf_mode")
    assert other.separate_format_subfolders is None


def test_first_edit_does_not_freeze_explicit_inherited_format_rule():
    import ast
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    cls = next(
        n for n in ast.parse(source).body
        if isinstance(n, ast.ClassDef) and n.name == "ExportWindow")
    fn = next(
        n for n in cls.body
        if isinstance(n, ast.FunctionDef)
        and n.name == "_freeze_legacy_format_folder_setting")
    namespace = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]),
                 "export_window.py", "exec"), namespace)
    parent = PublicationFolder(
        "DCE", "root",
        publication_settings=PublicationSettings(separate_format_subfolders=False))
    child = PublicationSet(
        "Plans", set_id="plans", folder_id="root", persistent=True,
        publication_settings=PublicationSettings(separate_carnet_subfolder=True))
    settings = child.publication_settings
    resolver = SettingsResolver(None)
    window = SimpleNamespace(
        _setting_source=lambda target, field: resolver.source_for_node(
            target, field, folders=[parent], publication_sets=[child]),
        _resolve_container_settings=lambda target: resolver.resolve_node(
            target, folders=[parent], publication_sets=[child]))
    namespace[fn.name](window, child, settings, "separate_carnet_subfolder")
    assert settings.separate_format_subfolders is None
    settings.separate_carnet_subfolder = False
    effective = resolver.resolve_node(
        child, folders=[parent], publication_sets=[child])
    assert effective.separate_format_subfolders is False
