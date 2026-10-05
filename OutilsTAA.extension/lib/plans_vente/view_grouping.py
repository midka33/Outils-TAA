# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Règles pures de regroupement des vues principales Plans de vente."""

try:
    text_type = unicode
except NameError:  # pragma: no cover - Python 3
    text_type = str


def normalize_scale(value):
    """Retourne le dénominateur entier d'une échelle Revit."""
    if isinstance(value, bool):
        raise ValueError("L'échelle doit être un nombre entier positif.")

    text = text_type(value if value is not None else "").strip()
    if text.startswith("1:"):
        text = text[2:].strip()

    if not text or not text.isdigit():
        raise ValueError("L'échelle doit être saisie sous la forme 50 ou 1:50.")

    scale = int(text)
    if scale <= 0 or scale > 24000:
        raise ValueError("L'échelle doit être comprise entre 1:1 et 1:24000.")
    return scale


def _safe_label(value):
    text = text_type(value or "").strip()
    chars = []
    previous_dash = False
    for char in text:
        allowed = char.isalnum() or char in (" ", "-", "_", ".")
        out = char if allowed else "-"
        if out == "-":
            if previous_dash:
                continue
            previous_dash = True
        else:
            previous_dash = False
        chars.append(out)
    result = "".join(chars).strip(" -_.")
    return result or "Niveau"


def _source_token(source_unique_id):
    text = "".join(
        char for char in text_type(source_unique_id or "")
        if char.isalnum()
    )
    if not text:
        raise ValueError("Identité de la vue source manquante.")
    return text[-8:]


def master_view_name(level_name, target_scale, source_unique_id):
    """Nom déterministe d'une vue principale technique PDV."""
    scale = normalize_scale(target_scale)
    return "PDV MASTER - {} - 1-{} - {}".format(
        _safe_label(level_name),
        scale,
        _source_token(source_unique_id),
    )
