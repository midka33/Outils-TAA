# -*- coding: utf-8 -*-
"""Contrats hors Revit de l'interface collaborative Export."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Export.panel"


def method(path, class_name, name):
    source = (PANEL / path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    return next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def source_segment(path, node):
    source = (PANEL / path).read_text(encoding="utf-8")
    lines = source.splitlines()
    end = getattr(node, "end_lineno", node.lineno)
    return "\n".join(lines[node.lineno - 1:end])


def test_xaml_exposes_storage_status_revision_path_and_refresh_button():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")

    assert 'x:Name="StorageStatusPanel"' in xaml
    assert 'x:Name="StorageModeText"' in xaml
    assert 'x:Name="StorageRevisionText"' in xaml
    assert 'x:Name="StoragePathText"' in xaml
    assert 'x:Name="StorageWarningText"' in xaml
    assert 'x:Name="StorageRefreshButton"' in xaml
    assert 'Click="StorageRefresh_Click"' in xaml
    assert 'Content="Actualiser"' in xaml


def test_export_window_accepts_storage_context_and_updates_status_on_start():
    init = method("export_window.py", "ExportWindow", "__init__")
    text = source_segment("export_window.py", init)

    assert any(arg.arg == "storage_context" for arg in init.args.args)
    assert "self.storage_context = storage_context" in text
    assert "self._update_storage_status()" in text


def test_storage_status_distinguishes_shared_local_and_fallback():
    func = method("export_window.py", "ExportWindow", "_update_storage_status")
    text = source_segment("export_window.py", func)

    assert "Configuration : Partagée" in text
    assert "Configuration : Locale — serveur indisponible" in text
    assert "Configuration : Locale" in text
    assert "Révision : {0}" in text
    assert '"Réessayer"' in text


def test_refresh_can_retry_server_and_swap_repository_without_reopening_window():
    func = method("export_window.py", "ExportWindow", "StorageRefresh_Click")
    text = source_segment("export_window.py", func)

    assert "context.retry()" in text
    assert "self.repository = new_context.repository" in text
    assert "self.controller.repository = self.repository" in text
    assert "self.repository.refresh()" in text
    assert "Connexion au stockage partagé rétablie." in text


def test_concurrent_modification_message_requires_explicit_refresh():
    func = method("export_window.py", "ExportWindow", "_show_storage_error")
    text = source_segment("export_window.py", func)

    assert "ConcurrentModificationError" in text
    assert "Vos modifications n'ont pas été enregistrées." in text
    assert "Actualiser" in text
    assert "Configuration momentanément verrouillée." in text


def test_storage_action_updates_revision_display_after_success():
    func = method("export_window.py", "ExportWindow", "_execute_storage_action")
    text = source_segment("export_window.py", func)

    assert "result = callback()" in text
    assert "self._update_storage_status()" in text
    assert "except StorageError" in text


def test_preview_integration_preserves_storage_context_constructor():
    source = (
        PANEL / "services" / "publication_preview_integration.py"
    ).read_text(encoding="utf-8")

    assert "storage_context=None" in source
    assert "storage_context=storage_context" in source


def test_drag_drop_delegates_storage_conflicts_to_window():
    source = (
        PANEL / "services" / "publication_tree_drag_drop.py"
    ).read_text(encoding="utf-8")

    assert '"_show_storage_error"' in source
    assert '"réorganiser les éléments"' in source


def test_delete_service_does_not_swallow_storage_errors():
    source = (
        PANEL / "services" / "publication_tree_delete.py"
    ).read_text(encoding="utf-8")

    assert "from shared_json_storage import StorageError" in source
    assert "except StorageError:" in source
    assert "raise" in source


def test_window_activation_reports_external_revision_without_auto_reload():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")
    assert 'Activated="Window_Activated"' in xaml

    func = method("export_window.py", "ExportWindow", "Window_Activated")
    text = source_segment("export_window.py", func)

    assert "self.repository.has_external_change()" in text
    assert "Une version plus récente est disponible" in text
    assert "Actualiser" in text
    assert "self.repository.refresh()" not in text
