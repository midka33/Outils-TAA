# -*- coding: utf-8 -*-
from pathlib import Path
import ast
import xml.etree.ElementTree as ET

from plans_vente.defaults import (
    DEFAULT_HOUSING_PARAMETER_NAME,
    preferred_housing_parameter_index,
)
from plans_vente.schedule_naming import schedule_name


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "OutilsTAA.extension" / "OutilsTAA.tab" / "PlansDeVente.panel"
SERVICE = PANEL / "services" / "schedule_service.py"
CONTROLLER = PANEL / "services" / "plans_vente_controller.py"
WINDOW = PANEL / "ui" / "plans_vente_window.py"
XAML = PANEL / "ui" / "plans_vente.xaml"


def test_schedule_naming_is_deterministic_and_sanitized():
    assert schedule_name("A001", "INT") == "PDV_A001_INT"
    assert schedule_name("A001", "EXT") == "PDV_A001_EXT"
    assert schedule_name("A/01", "INT") == "PDV_A-01_INT"


def test_schedule_naming_rejects_invalid_role():
    try:
        schedule_name("A001", "OTHER")
    except ValueError:
        pass
    else:
        raise AssertionError("Un rôle de nomenclature inconnu a été accepté.")


def test_schedule_service_parses_and_uses_revit_schedule_contract():
    text = SERVICE.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# -*- coding: utf-8 -*-"
    ast.parse(text)
    for token in (
        "ViewSchedule", "ViewDuplicateOption.Duplicate", "GetFieldOrder",
        "GetSchedulableField", "ParameterId", "ScheduleFilter",
        "ScheduleFilterType.Equal", "SetFilter", "AddFilter",
        "RemoveFilter", "CanFilterByValue", "RevitTransaction",
    ):
        assert token in text


def test_schedule_service_preserves_stable_parameter_identity_rules():
    text = SERVICE.read_text(encoding="utf-8")
    assert 'kind == "SHARED_GUID"' in text
    assert "GuidValue" in text
    assert 'kind == "BUILT_IN"' in text
    assert "ParameterUtils.IsBuiltInParameter" in text
    assert "ParameterUtils.GetParameterTypeId" in text
    assert 'kind == "DEFINITION"' in text
    assert "GetDefinition" in text
    assert "GetTypeId" in text


def test_stage04_ui_exposes_two_models_and_one_creation_action():
    ET.parse(str(XAML))
    xaml = XAML.read_text(encoding="utf-8")
    window = WINDOW.read_text(encoding="utf-8")
    for name in ("InteriorScheduleCombo", "ExteriorScheduleCombo", "CreateSchedulesButton", "ScheduleInfoText"):
        assert 'x:Name="{}"'.format(name) in xaml
    assert 'Click="CreateSchedules_Click"' in xaml
    assert 'SelectionChanged="ScheduleTemplateChanged"' in xaml
    assert "def CreateSchedules_Click(" in window
    assert "def ScheduleTemplateChanged(" in window


def test_controller_exposes_schedule_service_without_mixing_revit_logic():
    text = CONTROLLER.read_text(encoding="utf-8")
    assert "self.schedule_service = schedule_service" in text
    assert "def schedule_templates(" in text
    assert "def create_schedule_prototype(" in text
    assert "ScheduleFilter" not in text


def test_generated_schedule_names_are_collision_checked_not_incremented():
    text = SERVICE.read_text(encoding="utf-8")
    assert "_ensure_name_available" in text
    assert "La mise à jour des éléments existants sera traitée à l'Étape 08." in text
    assert "_unique_schedule_name" not in text


class _Descriptor(object):
    def __init__(self, name, identity_kind):
        self.name = name
        self.identity_kind = identity_kind


def test_shared_numero_appartement_is_default_housing_parameter():
    descriptors = [
        _Descriptor("Appartement", "NAME"),
        _Descriptor(DEFAULT_HOUSING_PARAMETER_NAME, "DEFINITION"),
        _Descriptor(DEFAULT_HOUSING_PARAMETER_NAME, "SHARED_GUID"),
        _Descriptor("Niveau", "BUILT_IN"),
    ]
    assert preferred_housing_parameter_index(descriptors) == 2


def test_default_parameter_falls_back_without_shared_numero_appartement():
    descriptors = [
        _Descriptor(DEFAULT_HOUSING_PARAMETER_NAME, "DEFINITION"),
        _Descriptor("Autre", "SHARED_GUID"),
    ]
    assert preferred_housing_parameter_index(descriptors) == 0
    assert preferred_housing_parameter_index([]) == -1


def test_window_uses_default_parameter_selector():
    text = WINDOW.read_text(encoding="utf-8")
    assert "preferred_housing_parameter_index" in text
    assert "context.parameters" in text
