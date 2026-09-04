# -*- coding: utf-8 -*-
"""Tests unitaires hors Revit pour l'architecture Stage 08."""

from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition
from services.dynamic_rule_resolver import DynamicRuleResolver


def _items():
    return [
        {"key": "A-101", "properties": {"discipline": "Architecture", "sheet_number": "A-101", "phase": "PRO"}},
        {"key": "A-201", "properties": {"discipline": "Architecture", "sheet_number": "A-201", "phase": "PRO"}},
        {"key": "S-201", "properties": {"discipline": "Structure", "sheet_number": "S-201", "phase": "PRO"}},
        {"key": "A-301", "properties": {"discipline": "Architecture", "sheet_number": "A-301", "phase": "DCE"}},
    ]


def _keys(resolution):
    return [candidate.key for candidate in resolution.included]


def test_equals_rule():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("discipline", "equals", "Architecture")])
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == ["A-101", "A-201", "A-301"]


def test_combined_all_rules():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [
            DynamicRule("discipline", "equals", "Architecture"),
            DynamicRule("phase", "equals", "PRO"),
        ])
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == ["A-101", "A-201"]


def test_combined_any_rules():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("any", [
            DynamicRule("sheet_number", "equals", "S-201"),
            DynamicRule("sheet_number", "equals", "A-301"),
        ])
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == ["S-201", "A-301"]


def test_explicit_exclusion_overrides_matching_rule():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("discipline", "equals", "Architecture")]),
        exclusions=["A-201"],
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == ["A-101", "A-301"]
    assert [item.key for item in result.excluded] == ["A-201"]


def test_missing_exclusion_is_diagnostic():
    definition = DynamicRuleDefinition(exclusions=["A-999"])
    result = DynamicRuleResolver().resolve(definition, _items())
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "EXCLUSION_NOT_FOUND"


def test_missing_property_does_not_match_equals():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("package", "equals", "DCE")])
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == []


def test_contains_is_case_insensitive():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("sheet_number", "contains", "a-2")])
    )
    result = DynamicRuleResolver().resolve(definition, _items())
    assert _keys(result) == ["A-201"]
