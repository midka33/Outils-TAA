# -*- coding: utf-8 -*-
"""Tests hors Revit de la prévisualisation dynamique Stage 08."""

import os
import sys

EXPORT_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..",
    "OutilsTAA.extension", "OutilsTAA.tab", "Export.panel"
))
if EXPORT_DIR not in sys.path:
    sys.path.insert(0, EXPORT_DIR)

from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition
from services.dynamic_preview import DynamicPreviewBuilder
from services.dynamic_rule_resolver import DynamicRuleResolver


def _definition(exclusions=None):
    return DynamicRuleDefinition(
        DynamicRuleGroup("all", [
            DynamicRule("discipline", "equals", "Architecture", "Discipline Architecture")
        ]),
        exclusions=exclusions or [],
    )


def _resolve(definition, items):
    return DynamicRuleResolver().resolve(definition, items)


def test_current_preview_marks_matching_items_as_added_and_non_matching_as_not_matched():
    resolution = _resolve(_definition(), [
        {"key": "A", "properties": {"discipline": "Architecture"}},
        {"key": "S", "properties": {"discipline": "Structure"}},
    ])
    preview = DynamicPreviewBuilder().build(resolution)

    assert [(row.key, row.status) for row in preview.rows] == [
        ("A", "ADDED"), ("S", "NOT_MATCHED")
    ]
    assert [row.key for row in preview.publishable_rows] == ["A"]
    assert [row.key for row in preview.added] == ["A"]


def test_preview_keeps_explicit_exclusion_visible_and_non_publishable():
    resolution = _resolve(_definition(["A"]), [
        {"key": "A", "properties": {"discipline": "Architecture"}},
    ])
    preview = DynamicPreviewBuilder().build(resolution)

    assert preview.rows[0].status == "EXCLUDED"
    assert preview.rows[0].excluded
    assert preview.publishable_rows == []
    assert "Exclusion explicite" in preview.rows[0].reasons


def test_preview_reports_added_removed_unchanged_and_reincluded():
    previous = _resolve(_definition(["B"]), [
        {"key": "A", "properties": {"discipline": "Architecture"}},
        {"key": "B", "properties": {"discipline": "Architecture"}},
        {"key": "C", "properties": {"discipline": "Architecture"}},
    ])
    current = _resolve(_definition(), [
        {"key": "A", "properties": {"discipline": "Architecture"}},
        {"key": "B", "properties": {"discipline": "Architecture"}},
        {"key": "D", "properties": {"discipline": "Architecture"}},
    ])
    preview = DynamicPreviewBuilder().build(current, previous)

    statuses = dict((row.key, row.status) for row in preview.rows)
    assert statuses["A"] == "UNCHANGED"
    assert statuses["B"] == "REINCLUDED"
    assert statuses["D"] == "ADDED"
    assert statuses["C"] == "REMOVED"
    assert [row.key for row in preview.removed] == ["C"]
    assert [row.key for row in preview.reincluded] == ["B"]


def test_preview_preserves_current_candidate_order_and_removed_rows_are_appended():
    previous = _resolve(_definition(), [
        {"key": "OLD", "properties": {"discipline": "Architecture"}},
    ])
    current = _resolve(_definition(), [
        {"key": "B", "properties": {"discipline": "Architecture"}},
        {"key": "A", "properties": {"discipline": "Architecture"}},
    ])
    preview = DynamicPreviewBuilder().build(current, previous)

    assert [row.key for row in preview.rows] == ["B", "A", "OLD"]
    assert preview.rows[-1].status == "REMOVED"


def test_preview_propagates_diagnostics_without_mutating_resolution():
    resolution = _resolve(_definition(["MISSING"]), [
        {"key": "A", "properties": {"discipline": "Architecture"}},
    ])
    original_candidates = list(resolution.candidates)
    preview = DynamicPreviewBuilder().build(resolution)

    assert preview.diagnostics is resolution.diagnostics
    assert preview.diagnostics[0].code == "EXCLUSION_NOT_FOUND"
    assert resolution.candidates == original_candidates


def test_preview_rejects_invalid_resolution_types():
    try:
        DynamicPreviewBuilder().build(None)
    except TypeError:
        pass
    else:
        raise AssertionError("Une résolution invalide doit lever TypeError.")
