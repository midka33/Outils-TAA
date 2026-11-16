# -*- coding: utf-8 -*-
"""Anti-régression : saisie du nommage DWG en mode PDF combiné."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS

PANEL = Path(__file__).resolve().parents[1] / (
    "OutilsTAA.extension/OutilsTAA.tab/Export.panel"
)


def export_method(name):
    source = (PANEL / "export_window.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "ExportWindow"
    )
    method = next(
        node for node in cls.body
        if isinstance(node, ast.FunctionDef)
        and node.name == name
    )
    namespace = {}
    module = ast.Module(body=[method], type_ignores=[])
    exec(
        compile(module, str(PANEL / "export_window.py"), "exec"),
        namespace,
    )
    return namespace[name]


def test_dwg_naming_is_not_saved_on_every_keystroke():
    xaml = (PANEL / "ui.xaml").read_text(encoding="utf-8")
    start = xaml.index('x:Name="DwgFilenameTemplateTextBox"')
    fragment = xaml[start:start + 420]

    assert 'LostFocus="SettingsChanged"' in fragment
    assert 'TextChanged="SettingsChanged"' not in fragment


def test_combined_pdf_keeps_dwg_naming_field_editable():
    ui = NS(
        _loading_settings=False,
        DwgFilenameIndependentCheckBox=NS(
            IsChecked=False,
            IsEnabled=True,
        ),
        DwgFilenameTemplateTextBox=NS(
            IsEnabled=False,
            Text="",
        ),
    )
    settings = NS(
        pdf_mode="COMBINED",
        dwg_filename_independent=False,
        dwg_filename_template="{numero}-{nom}",
        filename_template="{nom_dossier}",
    )

    export_method("_sync_dwg_naming")(ui, settings)

    assert ui.DwgFilenameIndependentCheckBox.IsChecked is True
    assert ui.DwgFilenameIndependentCheckBox.IsEnabled is False
    assert ui.DwgFilenameTemplateTextBox.IsEnabled is True
    assert ui.DwgFilenameTemplateTextBox.Text == "{numero}-{nom}"


def test_combined_pdf_keeps_default_dwg_naming_when_no_override_exists():
    ui = NS(
        _loading_settings=False,
        DwgFilenameIndependentCheckBox=NS(
            IsChecked=False,
            IsEnabled=True,
        ),
        DwgFilenameTemplateTextBox=NS(
            IsEnabled=False,
            Text="",
        ),
    )
    settings = NS(
        pdf_mode="COMBINED",
        dwg_filename_independent=False,
        dwg_filename_template=None,
        filename_template="{nom_dossier}",
    )

    export_method("_sync_dwg_naming")(ui, settings)

    assert ui.DwgFilenameTemplateTextBox.IsEnabled is True
    assert ui.DwgFilenameTemplateTextBox.Text == "{numero} {nom}"


def test_dwg_naming_fields_are_editable_on_publication_sets():
    """La sauvegarde par champ ne doit pas ignorer le nommage DWG."""
    settings_source = (
        PANEL / "services" / "publication_settings.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(settings_source)
    cls = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PublicationSettings"
    )
    active = next(
        node.value for node in cls.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "ACTIVE_FIELDS"
                for t in node.targets)
    )
    assert isinstance(active, ast.BinOp)
    names = ast.literal_eval(active.left)
    assert "dwg_filename_independent" in names
    assert "dwg_filename_template" in names


def test_dwg_template_is_saved_before_combined_pdf_sync():
    """La règle saisie doit être transmise à la persistance puis relue."""
    selected = NS(
        publication_settings=NS(dwg_filename_template=None),
        persistent=True,
        output_directory=None,
    )
    state = NS(
        _selected_set=selected,
        _loading_settings=False,
        INHERITABLE_FIELDS=("dwg_filename_template",),
        _control_value=lambda field: "DWG_{numero}_{nom}",
        _freeze_legacy_format_folder_setting=lambda *args: None,
        _execute_storage_action=lambda callback, action: (True, callback()),
        controller=NS(save_persistent=lambda value: value.publication_settings.dwg_filename_template),
        _update_inheritance_info=lambda value: None,
        _resolve_settings=lambda value: value.publication_settings,
        _update_filename_preview=lambda settings: None,
        _update_publication_overview=lambda: None,
    )

    export_method("_save_selected_field")(state, "dwg_filename_template")

    assert selected.publication_settings.dwg_filename_template == "DWG_{numero}_{nom}"
