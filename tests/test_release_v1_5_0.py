# -*- coding: utf-8 -*-
"""Contrat de préparation v1.5.0 : métadonnées, livraison, intégrité."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.5.0"
EXT = ROOT / "OutilsTAA.extension"
RELEASE = ROOT / "docs" / "release"


def test_manifest_is_stable_and_matches_release():
    data = json.loads((EXT / "version.json").read_text(encoding="utf-8"))
    assert data == {
        "version": VERSION,
        "channel": "stable",
        "last_published": VERSION,
    }


def test_release_notes_are_user_facing_and_cover_modules():
    notes = (RELEASE / "Notes_v1.5.0.md").read_text(encoding="utf-8")
    for topic in ("Dossiers automatiques", "Figer un seul sous-dossier",
                  "sous-dossier automatique", "configuration collaborative",
                  "À propos", "Calculs des pièces", "Plans de vente",
                  "Revit 2025.4", "pyRevit 5.x", "SHA-256"):
        assert topic.lower() in notes.lower(), topic
    for tool in ("Export", "Calculs_Pieces", "Plans_de_Vente"):
        assert (RELEASE / ("Tutoriel_" + tool + "_v1.5.0.md")).is_file()


def test_installer_downloads_and_hash_checks_correct_release():
    installer = (ROOT / ".github" / "release" /
                 "INSTALLER_Outils_TAA_v1.5.0.cmd").read_text(encoding="utf-8")
    assert "v1.5.0/Outils-TAA_v1.5.0.zip" in installer
    assert "v1.5.0/SHA256SUMS.txt" in installer
    assert "Outils-TAA_v1[.]5[.]0[.]zip$" in installer
    assert "Get-FileHash" in installer
    assert "$actual -ne $expected" in installer
    assert "$meta.version -ne '1.5.0'" in installer
    assert "$meta.channel -ne 'stable'" in installer
    assert "goto ERROR_ROLLBACK" in installer
    assert "OutilsTAA.extension_backup_v1.5.0" in installer
    assert "v1.4.0" not in installer and "v1.4.1" not in installer


def test_release_workflow_validates_on_pr_and_publishes_only_from_main():
    workflow = (ROOT / ".github" / "workflows" /
                "release-v1.5.0.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert 'branches: ["main"]' in workflow
    assert "needs: validate" in workflow
    assert "github.event_name != 'pull_request'" in workflow
    assert "github.ref == 'refs/heads/main'" in workflow
    assert '--target "$RELEASE_COMMIT"' in workflow
    assert 'gh release create "v1.5.0"' in workflow
    assert "sha256sum -c SHA256SUMS.txt" in workflow
    assert "OutilsTAA.extension/version.json" in workflow
    assert "APropos.pushbutton/icon.png" in workflow
    assert "manifest.get(\"channel\") != \"stable\"" in workflow
    assert "Outils-TAA_v1.5.0.zip" in workflow
    assert "INSTALLER_Outils_TAA_v1.5.0.cmd" in workflow
    assert "v1.4.0.zip" not in workflow and "v1.4.1.zip" not in workflow


def test_about_ribbon_and_export_use_same_version_manifest():
    assert (EXT / "OutilsTAA.tab" / "Informations.panel" /
            "APropos.pushbutton" / "script.py").is_file()
    assert (EXT / "OutilsTAA.tab" / "Export.panel" /
            "about_window.xaml").is_file()
    assert (EXT / "lib" / "common" / "taa_version.py").is_file()
