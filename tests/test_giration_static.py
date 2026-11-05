from pathlib import Path
import ast
from xml.etree import ElementTree as etree

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'OutilsTAA.extension'


def test_entry_ascii_clean():
    p = SRC / 'OutilsTAA.tab/Giration.panel/TracerGiration.pushbutton/script.py'
    assert p.read_bytes().isascii()
    ast.parse(p.read_text(encoding='utf-8'))


def test_all_python_parses():
    for base in (SRC / 'lib/giration', SRC / 'OutilsTAA.tab/Giration.panel'):
        for file in base.rglob('*.py'):
            ast.parse(file.read_text(encoding='utf-8'))


def test_xaml_wellformed_and_no_unresolved_static_resources():
    p = SRC / 'OutilsTAA.tab/Giration.panel/ui/giration_main_window.xaml'
    doc = etree.parse(str(p))
    assert doc.getroot().tag.endswith('Window')
    assert 'StaticResource Taa' not in p.read_text(encoding='utf-8')


def test_unverified_catalog():
    from giration.data.vehicles import get_all_vehicles
    vehicles = get_all_vehicles()
    assert len(vehicles) == 9
    assert all(not item.verified for item in vehicles)
    assert not any('SDIS 33' in item.reference for item in vehicles)
