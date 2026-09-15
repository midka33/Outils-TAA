# -*- coding: utf-8 -*-
"""Tests hors Revit du pont Stage 08 vers PublicationItem."""

import os
import sys

EXPORT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel"
))
if EXPORT_DIR not in sys.path:
    sys.path.insert(0, EXPORT_DIR)

from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition
from models.publication_item import PublicationItem
from services.dynamic_publication_adapter import DynamicPublicationAdapter
from services.dynamic_rule_resolver import DynamicRuleResolver


def _publication_items():
    return [
        PublicationItem("uid-A101", "101", "sheet", "A-101", "Plan RDC"),
        PublicationItem("uid-A201", "201", "sheet", "A-201", "Plan R+1"),
        PublicationItem("uid-S201", "301", "sheet", "S-201", "Structure"),
    ]


def _resolution():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [
            DynamicRule("discipline", "equals", "Architecture")
        ])
    )
    candidates = [
        {"key": "uid-A201", "properties": {"discipline": "Architecture"}},
        {"key": "uid-A101", "properties": {"discipline": "Architecture"}},
        {"key": "uid-S201", "properties": {"discipline": "Structure"}},
    ]
    return DynamicRuleResolver().resolve(definition, candidates)


def test_maps_included_keys_to_existing_publication_items():
    selection = DynamicPublicationAdapter().build_selection(
        _resolution(), _publication_items()
    )
    assert [item.unique_id for item in selection.items] == ["uid-A201", "uid-A101"]
    assert selection.valid


def test_preserves_resolution_order():
    selection = DynamicPublicationAdapter().build_selection(
        _resolution(), _publication_items()
    )
    assert [item.sheet_number for item in selection.items] == ["A-201", "A-101"]


def test_reuses_existing_instances_without_cloning_or_mutating():
    source = _publication_items()
    selection = DynamicPublicationAdapter().build_selection(_resolution(), source)
    assert selection.items[0] is source[1]
    assert selection.items[1] is source[0]
    assert [item.unique_id for item in source] == ["uid-A101", "uid-A201", "uid-S201"]


def test_excluded_items_are_not_selected():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("discipline", "equals", "Architecture")]),
        exclusions=["uid-A201"],
    )
    resolution = DynamicRuleResolver().resolve(definition, [
        {"key": "uid-A101", "properties": {"discipline": "Architecture"}},
        {"key": "uid-A201", "properties": {"discipline": "Architecture"}},
    ])
    selection = DynamicPublicationAdapter().build_selection(resolution, _publication_items())
    assert [item.unique_id for item in selection.items] == ["uid-A101"]


def test_reports_missing_publication_item():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("discipline", "equals", "Architecture")])
    )
    resolution = DynamicRuleResolver().resolve(definition, [
        {"key": "uid-A999", "properties": {"discipline": "Architecture"}},
    ])
    selection = DynamicPublicationAdapter().build_selection(resolution, _publication_items())
    assert selection.items == []
    assert not selection.valid
    assert selection.diagnostics[0].code == "PUBLICATION_ITEM_NOT_FOUND"
    assert selection.diagnostics[0].key == "uid-A999"


def test_reports_duplicate_publication_item_key():
    source = _publication_items()
    source.append(PublicationItem("uid-A101", "999", "sheet", "A-999", "Doublon"))
    selection = DynamicPublicationAdapter().build_selection(_resolution(), source)
    assert not selection.valid
    assert any(
        diagnostic.code == "DUPLICATE_PUBLICATION_ITEM_KEY"
        and diagnostic.key == "uid-A101"
        for diagnostic in selection.diagnostics
    )


def test_empty_resolution_returns_empty_selection():
    definition = DynamicRuleDefinition(
        DynamicRuleGroup("all", [DynamicRule("discipline", "equals", "Architecture")])
    )
    resolution = DynamicRuleResolver().resolve(definition, [])
    selection = DynamicPublicationAdapter().build_selection(resolution, _publication_items())
    assert selection.items == []
    assert selection.diagnostics == []
