# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Transformations exactes des valeurs texte ; ne convertit jamais en nombres."""

import unicodedata


OPERATIONS = ("add_start", "add_end", "remove_start", "remove_end")


def _validate_literal(text, allow_blank=False):
    if text is None or (not allow_blank and not text.strip()):
        raise ValueError("Texte manquant.")
    if any(unicodedata.category(char) in ("Cc", "Zl", "Zp") for char in text):
        raise ValueError("Les caractères de contrôle sont interdits.")
    return text


def transform(value, operation, affix, separator="", add_once=False):
    """Ne modifie pas une valeur vide et ne crée jamais une valeur vide."""
    if operation not in OPERATIONS:
        raise ValueError("Opération inconnue.")
    _validate_literal(affix)
    _validate_literal(separator, allow_blank=True)
    if value is None or not value.strip():
        return value
    at_start = operation.endswith("start")
    token = affix + separator if at_start else separator + affix
    if operation.startswith("add"):
        if add_once and (value.startswith(token) if at_start else value.endswith(token)):
            return value
        return token + value if at_start else value + token
    matches = value.startswith(token) if at_start else value.endswith(token)
    if not matches:
        return value
    remaining = value[len(token):] if at_start else value[:-len(token)]
    return remaining if remaining.strip() else value
