# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "OutilsTAA.extension" / "lib"))

from room_parameters.numbering_engine import parse_sequence, sequence_value, proposed_assignments
from room_parameters.text_transform_engine import transform
from room_parameters.duplicate_checker import detect_collisions
from room_parameters.format_engine import format_value, parameter_token, parameter_aliases


@pytest.mark.parametrize("start,mode,expected", [
    ("BAT-A-009", "digits", "BAT-A-010"),
    ("B1-009-A", "digits", "B1-010-A"),
    ("ÉTAGE-Z", "letters", "ÉTAGE-AA"),
    ("001-z", "letters", "001-aa"),
    ("A1", "letters", "B1"),
])
def test_sequence(start, mode, expected):
    assert sequence_value(parse_sequence(start, mode), 1) == expected


def test_step_and_selection_deduplication():
    spec = parse_sequence("R-010", step=-2)
    assert proposed_assignments(["a", "a", "b", "c"], spec) == [
        ("a", "R-010"), ("b", "R-008"), ("c", "R-006")]


@pytest.mark.parametrize("start,mode", [
    ("ÉTAGE", "letters"), ("Ｅ01", "letters"), ("１２３", "digits"),
    ("aB", "letters"), ("A\n1", "digits"),
])
def test_invalid_sequence(start, mode):
    with pytest.raises(ValueError):
        parse_sequence(start, mode)


def test_sequence_underflow():
    with pytest.raises(ValueError):
        sequence_value(parse_sequence("A", "letters", -1), 1)


@pytest.mark.parametrize("operation,old,expected", [
    ("add_start", "001", "BAT-001"),
    ("add_end", "001", "001-BAT"),
    ("remove_start", "BAT-001", "001"),
    ("remove_end", "001-BAT", "001"),
])
def test_text_operations(operation, old, expected):
    assert transform(old, operation, "BAT", "-") == expected


def test_add_once_preserves_value():
    assert transform("BAT-001", "add_start", "BAT", "-", True) == "BAT-001"
    assert transform("BAT-001", "add_start", "BAT", "-", False) == "BAT-BAT-001"


def test_replace_literal_all_occurrences_and_preserve_nonblank():
    assert transform("BAT-C101-BAT", "replace", "BAT", "LOG") == "LOG-C101-LOG"
    assert transform("BAT-C101", "replace", "ABSENT", "LOG") == "BAT-C101"
    assert transform("BAT", "replace", "BAT", "") == "BAT"
    assert transform("BAT-C101", "replace", "BAT-", "") == "C101"


def test_no_blank_write_and_no_partial_match():
    assert transform("BAT", "remove_start", "BAT") == "BAT"
    assert transform("BATIMENT", "remove_start", "BAT", "-") == "BATIMENT"
    assert transform("", "add_start", "BAT") == ""


def test_format_engine_explicit_tokens_and_literals():
    assert format_value("C101", "{famille}-{valeur}-{index}", 4, "Porte") == "Porte-C101-4"
    assert format_value("X", "{{valeur}}-{index}", 2) == "{valeur}-2"
    assert format_value("X", "", 1) == "X"
    with pytest.raises(ValueError):
        format_value("X", "{valeur.__class__}", 1)
    with pytest.raises(ValueError):
        format_value("X", "{index:03d}", 1)


def test_format_engine_inserts_revit_parameters_by_stable_identifier():
    assert parameter_token(954978) == "param_954978"
    assert parameter_token(-1006900) == "param_m1006900"
    values = {"param_954978": "C101", "param_m1006900": "Séjour"}
    assert (format_value("", "{param_954978}-{param_m1006900}-{index}", 2,
                         parameters=values) == "C101-Séjour-2")
    with pytest.raises(ValueError):
        format_value("X", "{param_954978}", 1, parameters={})
    with pytest.raises(ValueError):
        format_value("X", "{valeur}", 1, parameters={"commande": "invalide"})


def test_format_engine_displays_names_and_resolves_underlying_parameter_ids():
    names = parameter_aliases([
        ("N° Appartement", "param_954978"),
        ("Nom de pièce", "param_m1006900"),
        ("N° Appartement", "param_123"),
    ])
    assert names == {"N° Appartement": "param_954978",
                     "Nom de pièce": "param_m1006900",
                     "N° Appartement (2)": "param_123"}
    values = {"param_954978": "A002", "param_m1006900": "Séjour", "param_123": "AUTRE"}
    assert format_value("", "{N° Appartement}-{Nom de pièce}", 1,
                        parameters=values, aliases=names) == "A002-Séjour"
    with pytest.raises(ValueError):
        format_value("X", "{N° Appartement}", 1, parameters={}, aliases=names)


def test_duplicate_checker_ignores_replaced_old_values():
    assignments = [("a", "002"), ("b", "003")]
    existing = [("a", "001"), ("b", "002"), ("c", "003")]
    assert detect_collisions(assignments, existing) == {"b": ["c"]}


def test_duplicate_checker_detects_new_collisions_and_can_allow_shared():
    assignments = [("a", "LOG-1"), ("b", "LOG-1")]
    assert detect_collisions(assignments, []) == {"a": ["b"], "b": ["a"]}
    assert detect_collisions(assignments, [], allow_shared=True) == {}
