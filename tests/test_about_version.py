# -*- coding: utf-8 -*-
"""À propos — source unique de version et raccordement WPF hors Revit."""
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "OutilsTAA.extension"
PANEL = EXT / "OutilsTAA.tab" / "Export.panel"
sys.path.insert(0, str(EXT))

from lib.common.taa_version import (
    manifest_path, read_version, display_version, display_release, display_status
)


def test_installed_version_is_loaded_from_extension_manifest():
    metadata = json.loads((EXT / "version.json").read_text(encoding="utf-8"))
    loaded = read_version()
    assert loaded["available"]
    assert loaded["version"] == metadata["version"]
    assert loaded["last_published"] == metadata["last_published"]
    assert loaded["channel"] == metadata["channel"]
    assert manifest_path() == str(EXT / "version.json")
    assert loaded["channel"] == "stable"
    assert loaded["version"] == "1.5.0"
    assert loaded["last_published"] == loaded["version"]
    assert display_version(loaded) == "1.5.0"
    assert metadata["last_published"] in display_release(loaded)


def test_stable_release_needs_only_manifest_update(tmp_path):
    file = tmp_path / "version.json"
    file.write_text(json.dumps({
        "version": "7.8.9", "channel": "stable", "last_published": "7.8.9"
    }), encoding="utf-8")
    info = read_version(str(file))
    assert info["available"]
    assert display_version(info) == "7.8.9"
    assert display_status(info) == "Version stable publiée."
    assert "7.8.9" in display_release(info)


def test_missing_or_invalid_metadata_is_not_a_fake_version(tmp_path):
    missing = read_version(str(tmp_path / "absent.json"))
    assert not missing["available"]
    assert missing["version"] == "indisponible"
    file = tmp_path / "version.json"
    file.write_text("{broken", encoding="utf-8")
    assert not read_version(str(file))["available"]
    file.write_text(json.dumps({
        "version": "", "channel": "stable", "last_published": "1.4.1"
    }), encoding="utf-8")
    assert not read_version(str(file))["available"]


def test_button_and_modal_are_wired_without_touching_export_workflow():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")
    code = (PANEL / "export_window.py").read_text(encoding="utf-8")
    about_xaml = (PANEL / "about_window.xaml").read_text(encoding="utf-8")
    about_code = (PANEL / "about_window.py").read_text(encoding="utf-8")

    ns = {
        "w": "http://schemas.microsoft.com/winfx/2006/xaml/presentation",
        "x": "http://schemas.microsoft.com/winfx/2006/xaml"
    }
    root = ET.fromstring(xaml)
    buttons = [item for item in root.iter() if item.tag.endswith("}Button")]
    about = [item for item in buttons if
             item.get("{%s}Name" % ns["x"]) == "AboutButton"]
    assert len(about) == 1
    assert about[0].get("Content") == "À propos"
    assert about[0].get("Click") == "About_Click"
    assert about[0].get("DockPanel.Dock") == "Right"
    assert "def About_Click(self, sender, args):" in code
    assert "AboutWindow(owner=self).ShowDialog()" in code

    modal = ET.fromstring(about_xaml)
    assert modal.get("WindowStartupLocation") == "CenterOwner"
    assert modal.get("ResizeMode") == "NoResize"
    names = set(item.get("{%s}Name" % ns["x"]) for item in modal.iter())
    assert {"AboutVersionText", "AboutReleaseText", "AboutStatusText"}.issubset(names)
    assert 'Click="Close_Click"' in about_xaml
    assert "from lib.common.taa_version import (" in about_code
    assert "apply_theme(self)" in about_code
    assert "def Close_Click(self, sender, args):" in about_code


def test_no_non_ui_text_in_wpf_containers():
    for name in ("ui.xaml", "about_window.xaml"):
        root = ET.fromstring((PANEL / name).read_text(encoding="utf-8"))
        for element in root.iter():
            if element.tag.endswith(("}Grid", "}StackPanel", "}DockPanel")):
                assert not (element.text and element.text.strip())
                for child in element:
                    assert not (child.tail and child.tail.strip())
