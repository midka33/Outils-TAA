# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import struct
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PANEL_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "OutilsTAA.tab",
    "Export.panel",
)
BUTTON_DIR = os.path.join(PANEL_DIR, "Export.pushbutton")
ICON_DIR = os.path.join(
    ROOT,
    "OutilsTAA.extension",
    "resources",
    "ui",
    "icons",
)


def _read(path):
    with open(path, "r") as handle:
        return handle.read()


def _png_size(path):
    with open(path, "rb") as handle:
        header = handle.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    return struct.unpack(">II", header[16:24])


def test_export_button_keeps_internal_bundle_and_panel_names():
    assert os.path.basename(BUTTON_DIR) == "Export.pushbutton"
    assert os.path.basename(PANEL_DIR) == "Export.panel"
    assert os.path.exists(os.path.join(BUTTON_DIR, "script.py"))


def test_export_button_uses_visually_empty_bundle_title():
    metadata = _read(os.path.join(BUTTON_DIR, "bundle.yaml"))
    lines = [line.rstrip("\r\n") for line in metadata.splitlines()]
    assert 'title: " "' in lines
    assert any(line.startswith("tooltip:") for line in lines)
    assert 'title: ""' not in lines


def test_export_ribbon_icons_are_vector_derived_and_text_free():
    assert _png_size(os.path.join(BUTTON_DIR, "icon.png")) == (96, 96)
    assert _png_size(os.path.join(BUTTON_DIR, "icon.dark.png")) == (96, 96)
    assert _png_size(os.path.join(ICON_DIR, "export-16.png")) == (16, 16)
    assert _png_size(os.path.join(ICON_DIR, "export-32.png")) == (32, 32)
    assert _png_size(os.path.join(ICON_DIR, "export-96.png")) == (96, 96)

    svg_path = os.path.join(ICON_DIR, "export.svg")
    root = ET.parse(svg_path).getroot()
    svg_text = _read(svg_path)
    assert root.tag.endswith("svg")
    assert "<text" not in svg_text.lower()
    assert "#FA641F" in svg_text
    assert "#FFFFFF" in svg_text
