# -*- coding: utf-8 -*-
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
BUTTON = PANEL / "PlansDeVente.pushbutton"


def test_python_files_keep_ironpython_encoding_header():
    python_files = list(PANEL.rglob("*.py"))
    python_files += list(
        (ROOT / "OutilsTAA.extension" / "lib" / "plans_vente").rglob("*.py")
    )

    assert python_files
    for path in python_files:
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "# -*- coding: utf-8 -*-", str(path)


def test_xaml_is_well_formed_and_handlers_exist():
    xaml_path = PANEL / "ui" / "plans_vente.xaml"
    py_path = PANEL / "ui" / "plans_vente_window.py"

    ET.parse(str(xaml_path))
    python_text = py_path.read_text(encoding="utf-8")

    assert "def Analyze_Click(" in python_text
    assert "def Close_Click(" in python_text


def test_button_has_non_empty_title():
    yaml_text = (BUTTON / "bundle.yaml").read_text(encoding="utf-8")
    assert "title: Plans de vente" in yaml_text
