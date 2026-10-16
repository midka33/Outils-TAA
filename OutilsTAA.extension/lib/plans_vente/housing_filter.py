# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Filtrage pur des logements pour l'interface finale Plans de vente."""


FILTER_OPERATORS = (
    ("starts_with", "commence par"),
    ("equals", "est égal à"),
    ("contains", "contient"),
    ("ends_with", "se termine par"),
    ("not_equals", "est différent de"),
    ("is_empty", "est vide"),
    ("is_not_empty", "n'est pas vide"),
)


def normalize_filter_text(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def matches_value(value, operator_key, expected=""):
    value = normalize_filter_text(value)
    expected = normalize_filter_text(expected)

    if operator_key == "starts_with":
        return value.startswith(expected)
    if operator_key == "equals":
        return value == expected
    if operator_key == "contains":
        return expected in value
    if operator_key == "ends_with":
        return value.endswith(expected)
    if operator_key == "not_equals":
        return value != expected
    if operator_key == "is_empty":
        return not value
    if operator_key == "is_not_empty":
        return bool(value)

    raise ValueError("Condition de filtre inconnue : {}.".format(operator_key))


def matches_any(values, operator_key, expected=""):
    values = list(values or [])
    if not values:
        values = [""]

    if operator_key == "not_equals":
        return all(
            matches_value(value, operator_key, expected)
            for value in values
        )

    return any(
        matches_value(value, operator_key, expected)
        for value in values
    )
