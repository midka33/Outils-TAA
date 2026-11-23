# -*- coding: utf-8 -*-
"""Contrat pyRevit 5.x : bouton À propos au niveau du ruban OutilsTAA."""
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "OutilsTAA.extension"
TAB = EXTENSION / "OutilsTAA.tab"
PANEL = TAB / "Informations.panel"
BUTTON = PANEL / "APropos.pushbutton"


def test_about_exists_as_standalone_ribbon_pushbutton():
    assert BUTTON.is_dir(), "Commande À propos absente du ruban"
    bundle = (BUTTON / "bundle.yaml").read_text(encoding="utf-8")
    assert 'title: "À propos"' in bundle
    assert "suite Outils TAA" in bundle


def test_ribbon_command_reuses_shared_dialog_without_revit_document():
    script = (BUTTON / "script.py").read_text(encoding="utf-8")
    assert "from about_window import AboutWindow" in script
    assert "AboutWindow().ShowDialog()" in script
    assert 'os.path.join(TAB_DIR, "Export.panel")' in script
    assert "EXTENSION_DIR" in script and "EXPORT_SERVICES_DIR" in script
    assert "__revit__.ActiveUIDocument" not in script
    assert "ActiveDocument" not in script
    assert "import export_window" not in script


def test_ribbon_icon_is_a_real_png():
    icon = BUTTON / "icon.png"
    assert icon.is_file(), "Le bouton doit être visible avec son icône TAA"
    content = icon.read_bytes()
    assert content[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", content[16:24])
    assert width >= 32 and height >= 32


def test_version_centralized_for_ribbon_and_export_dialog():
    # Une seule fenêtre / source de version pour les deux points d'entrée.
    dialog = (TAB / "Export.panel" / "about_window.py").read_text(
        encoding="utf-8")
    assert "from lib.common.taa_version import (" in dialog
    assert "read_version()" in dialog
    assert (EXTENSION / "version.json").is_file()

def test_about_panel_is_first_in_tab_layout_without_hiding_modules():
    """L'ordre des panneaux est explicite et les modules métier restent présents."""
    tab_manifest = (TAB / "bundle.yaml").read_text(encoding="utf-8")
    lines = [line.strip()[2:].strip() for line in tab_manifest.splitlines()
             if line.strip().startswith("- ")]
    assert lines[0] == "Informations[beforeall:]"
    assert lines[1:] == ["Calculs", "Parametres", "Export", "PlansDeVente"]
    declared = set(item.split("[", 1)[0] for item in lines)
    existing = set(path.name[:-len(".panel")] for path in TAB.glob("*.panel"))
    assert declared == existing, (
        "Un panneau OutilsTAA non listé pourrait disparaître du ruban : {}"
        .format(existing - declared))


def test_about_icon_matches_taa_brand_orange():
    """Icône harmonisée exactement sur l'orange officiel de Plans de vente.

    Test à empreinte : détecte la réintroduction du fond orange plus foncé
    tout en évitant une dépendance à Pillow dans le workflow CI.
    """
    import hashlib
    result = hashlib.sha256((BUTTON / "icon.png").read_bytes()).hexdigest()
    assert result == "cfde0ed9fa9f16599b590248b1f301907674aaf81c528a31180fe9a5b1068c60"
