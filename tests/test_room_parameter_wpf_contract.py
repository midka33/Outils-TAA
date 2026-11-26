# -*- coding: utf-8 -*-
"""Contrats statiques uniquement : pas une validation d'exécution WPF/Revit."""

import ast
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "Parametres.panel"
STACK = PANEL / "Commandes.stack"


def test_both_buttons_open_same_window_with_distinct_mode():
    for folder, import_statement, launch_statement in (
        ("TAA_NumeroterPieces.pushbutton", "from room_parameters_window import launch", 'launch("number")'),
        ("TAA_ModifierTextePieces.pushbutton", "from text_rename_window import launch_rename", "launch_rename()"),
    ):
        script = (STACK / folder / "script.py").read_text(encoding="utf-8")
        ast.parse(script)
        assert import_statement in script
        assert launch_statement in script
        assert 'os.path.join(os.path.dirname(__file__), "..", "..")' in script


def test_two_stage_three_column_rename_contract():
    selection = ET.parse(PANEL / "ui" / "rename_selection.xaml").getroot()
    editor = ET.parse(PANEL / "ui" / "rename_editor.xaml").getroot()
    selection_names = {element.get("Name") for element in selection.iter()}
    editor_names = {element.get("Name") for element in editor.iter()}
    assert {"CategoryCombo", "ScopeCombo", "ParameterCombo",
            "ObjectsGrid", "ContinueButton"}.issubset(selection_names)
    assert {"ObjectsGrid", "ModeCombo", "OperationCombo", "InputText",
            "ExtraText", "PreviewGrid", "ConfirmCheck", "ApplyButton"}.issubset(editor_names)
    controller = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    ast.parse(controller)
    ast.parse(service)
    assert "selection.ShowDialog()" in controller
    assert "RenameEditorWindow(selection).ShowDialog()" in controller
    assert "DB.FamilyInstance" in service and "instance.Symbol" in service
    assert "transaction.RollBack()" in service


def test_rename_editor_exposes_four_distinct_operations():
    source = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    cls = next(node for node in module.body
               if isinstance(node, ast.ClassDef) and node.name == "RenameEditorWindow")
    assignments = {target.id: ast.literal_eval(node.value)
                   for node in cls.body if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)
                   and target.id in ("MODES", "ADD_CODES", "REMOVE_CODES")}
    assert assignments["MODES"] == ("Ajouter", "Supprimer", "Remplacer", "Formater")
    assert assignments["ADD_CODES"] == ("add_start", "add_end")
    assert assignments["REMOVE_CODES"] == ("remove_start", "remove_end")
    assert 'return "replace" if mode == 2 else "format"' in source


def test_rename_editor_displays_chosen_parameter_instead_of_element_name():
    source = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    assert 'parameter_name = selection.parameter_label.split(" [ID ")[0]' in source
    assert 'self.ObjectsGrid.Columns[1].Header = parameter_name' in source
    assert 'self.PreviewGrid.Columns[0].Header = parameter_name' in source
    assert '"Label": _parameter_display(obj, self.parameter_id)' in source
    assert '"Key": obj.UniqueId' in source  # identification interne inchangée
    assert 'parameter.AsString() or "(vide)"' in source


def test_format_mode_lists_and_inserts_available_revit_parameters():
    xaml = ET.parse(PANEL / "ui" / "rename_editor.xaml").getroot()
    names = {element.get("Name") for element in xaml.iter()}
    assert {"FormatFields", "FormatParameterCombo", "InsertParameterButton"}.issubset(names)
    source = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    assert "readable_parameters(self.elements)" in source
    assert 'self.FormatFields.Visibility = Visibility.Visible if mode == 3' in source
    assert 'self.InputText.SelectedText = "{" + option.FormatLabel + "}"' in source
    assert "parameter_aliases(" in source
    assert "self.format_aliases)" in source
    assert 'DisplayMemberPath="FormatLabel"' in (PANEL / "ui" / "rename_editor.xaml").read_text(encoding="utf-8")
    assert "parameter_token(id_value(candidate.Id))" in service
    assert "parameter_display_value(candidate)" in service
    assert "DB.StorageType.Integer" in service
    assert "DB.StorageType.Double" in service


def test_format_layout_places_parameter_picker_above_format_and_hides_unused_row():
    ET.parse(PANEL / "ui" / "rename_editor.xaml")
    # L'ordre visuel suit l'ordre du XAML dans le panneau des opérations.
    xml_source = (PANEL / "ui" / "rename_editor.xaml").read_text(encoding="utf-8")
    assert xml_source.index('Name="FormatFields"') < xml_source.index('Name="InputLabel"')
    source = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    assert "NON UTILISÉ" not in source
    assert 'self.ExtraLabel.Visibility = Visibility.Collapsed if mode == 3 else Visibility.Visible' in source
    assert 'self.ExtraText.Visibility = Visibility.Collapsed if mode == 3 else Visibility.Visible' in source


def test_format_defaults_to_selected_destination_parameter():
    source = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    assert 'self.default_format_token = "{valeur}"' in source
    assert 'if option.Id == self.parameter_id:' in source
    assert 'self.default_format_token = "{" + option.FormatLabel + "}"' in source
    assert 'self.FormatParameterCombo.SelectedIndex = index' in source
    assert 'self.InputText.Text, self.ExtraText.Text = self.default_format_token, ""' in source


def test_text_notes_bypass_parameter_selection_and_use_text_note_content():
    selection_xaml = ET.parse(PANEL / "ui" / "rename_selection.xaml").getroot()
    assert "ParameterFields" in {node.get("Name") for node in selection_xaml.iter()}
    assert "LevelCombo" not in {node.get("Name") for node in selection_xaml.iter()}
    controller = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    assert 'self.CategoryCombo.Items.Add("Pièces")' in controller
    assert 'self.CategoryCombo.Items.Add("Textes")' in controller
    assert 'self.CategoryCombo.Items.Add("Familles")' not in controller
    assert "self.LevelCombo" not in controller
    assert 'self.level = "instance"' in controller
    assert 'self.ParameterFields.IsEnabled = self.category != "Textes"' in controller
    assert 'if option is None and self.category != "Textes":' in controller
    assert 'options or self.category == "Textes"' in controller
    assert 'self.parameter_id = None if self.category == "Textes" else option.Id' in controller
    assert 'elif category == "Textes":' in service
    assert 'collector.OfClass(DB.TextNote)' in service
    assert 'is_text_note = isinstance(element, DB.TextNote)' in service
    assert 'element.Text = after' in service
    assert 'if (element.Text or "") != before' in service


def test_rename_supports_six_model_categories_with_instance_text_parameters():
    controller = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    expected = {
        "Fenêtres": "OST_Windows",
        "Sols": "OST_Floors",
        "Plafonds": "OST_Ceilings",
        "Toits": "OST_Roofs",
        "Murs": "OST_Walls",
        "Portes": "OST_Doors",
    }
    for label, bic in expected.items():
        assert '"{}": DB.BuiltInCategory.{}'.format(label, bic) in service
        assert '"{}"'.format(label) in controller
    assert 'if self.category != "Textes":' in controller
    assert 'options = writable_text_parameters(self.elements)' in controller
    assert '.WhereElementIsNotElementType().ToElements()' in service
    assert 'item.GroupId == DB.ElementId.InvalidElementId' in service
    assert 'if element.GroupId != DB.ElementId.InvalidElementId:' in service


def test_windows_doors_use_family_instance_collector_and_explain_empty_selection():
    controller = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    assert 'if category in ("Fenêtres", "Portes"):' in service
    assert 'candidates = _family_instances(scope)' in service
    assert 'collector.OfClass(DB.FamilyInstance).ToElements()' in service
    assert 'if self.ScopeCombo.SelectedItem == "Sélection actuelle":' in controller
    assert 'choisissez « Vue active » / « Projet entier »' in controller


def test_family_names_use_revit_element_descriptor_for_ironpython():
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    assert 'DB.Element.Name.GetValue(element)' in service
    assert '_element_name(element.Symbol)' in service
    assert '_element_name(element.Symbol.Family)' in service
    assert 'element.Symbol.Name' not in service
    assert 'element.Symbol.Family.Name' not in service


def test_type_parameters_are_listed_and_applied_once_per_unique_type():
    controller = (PANEL / "ui" / "text_rename_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "text_rename_service.py").read_text(encoding="utf-8")
    assert 'def collect_target_types(elements):' in service
    assert 'type_id = element.GetTypeId()' in service
    assert 'found[element_type.UniqueId] = element_type' in service
    assert 'if isinstance(element_type, DB.ElementType):' in service
    assert 'option.Label = "[Instance] " + option.Label' in controller
    assert 'option.Label = "[Type] " + option.Label' in controller
    assert 'self.types = collect_target_types(self.elements)' in controller
    assert 'self.level = option.Level if option is not None else "instance"' in controller
    assert 'self.selection = collect_target_types(self.selection)' in controller
    assert 'if selection.level == "type":' in controller
    assert 'toutes ses' in controller and 'occurrences dans le projet' in controller


def test_compact_revit_ribbon_stack_structure():
    assert (PANEL / "bundle.yaml").read_text(encoding="utf-8").strip().endswith("- Commandes")
    stack = (STACK / "bundle.yaml").read_text(encoding="utf-8")
    assert "- TAA_NumeroterPieces" in stack and "- TAA_ModifierTextePieces" in stack
    assert len(list(STACK.glob("*.pushbutton"))) == 2
    assert not (PANEL / "Numeroter.pushbutton").exists()
    assert not (PANEL / "ModifierTexte.pushbutton").exists()
    assert not (STACK / "Numeroter.pushbutton").exists()
    assert not (STACK / "ModifierTexte.pushbutton").exists()


def test_two_independent_windows_have_preview_and_confirmation_controls():
    required = {"ModeCombo", "ParameterCombo", "OperationCombo", "InputText",
                "ExtraText", "PreviewGrid", "ApplyButton", "ConfirmCheck",
                "SelectButton", "MessageText"}
    required.remove("ModeCombo")
    for filename in ("numbering_parameters.xaml", "text_parameters.xaml"):
        tree = ET.parse(PANEL / "ui" / filename)
        names = set()
        for element in tree.iter():
            names.update(value for key, value in element.attrib.items()
                         if key == "Name" or key.endswith("}Name"))
        assert required.issubset(names)
        assert "ModeCombo" not in names
    assert len(list(PANEL.glob("ui/*.xaml"))) == 4  # 2 outils, dont 2 étapes pour le renommage


def test_editable_fields_replace_choice_and_compact_preview():
    for filename in ("numbering_parameters.xaml", "text_parameters.xaml"):
        root = ET.parse(PANEL / "ui" / filename).getroot()
        controls = {element.get("Name"): element for element in root.iter() if element.get("Name")}
        for name in ("InputText", "ExtraText"):
            assert controls[name].get("IsReadOnly") == "False"
            assert controls[name].get("Focusable") == "True"
            assert controls[name].get("IsEnabled") == "True"
            assert int(controls[name].get("Height")) <= 26
        assert int(controls["PreviewGrid"].get("RowHeight")) <= 20
        assert int(controls["OperationCombo"].get("Height")) <= 28
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    assert '"Remplacer un texte"' in source
    assert '"replace"' in source
    assert '== "n° appartement"' in source
    assert 'Keyboard.Focus(self.InputText)' in source
    assert 'self.ContentRendered +=' in source
    assert '"numbering_parameters.xaml" if self.numbering else "text_parameters.xaml"' in source


def test_revit_writer_blocks_stale_preview_and_rolls_back():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    service = (PANEL / "services" / "room_parameter_edit_service.py").read_text(encoding="utf-8")
    ast.parse(source)
    ast.parse(service)
    assert "self.preview_signature != self._signature()" in source
    assert "self.ConfirmCheck.IsChecked" in source
    assert "transaction.RollBack()" in service
    assert "parameter.AsString() or \"\"" in service
    assert "room.GroupId != DB.ElementId.InvalidElementId" in service


def test_taa_theme_and_business_separation():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    xaml = (PANEL / "ui" / "numbering_parameters.xaml").read_text(encoding="utf-8")
    assert "load_resource_dictionary(self, theme)" in source
    assert "TAAPrimaryButton" in xaml
    assert "TAAOrangeBrush" in xaml
    assert "#D97128" not in xaml
    assert "DB.Transaction(" not in source
    assert "commit_changes(selected)" in source
    assert "check_collisions(" in source
    assert "self.settings.set(" in source


def test_system_data_assembly_loaded_before_import():
    source = (PANEL / "ui" / "room_parameters_window.py").read_text(encoding="utf-8")
    assert 'clr.AddReference("System.Data")' in source
    assert source.index('clr.AddReference("System.Data")') < source.index("from System.Data import DataTable")
