# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Nommage pur des nomenclatures générées pour les plans de vente."""

try:
    text_type = unicode
except NameError:  # pragma: no cover - Python 3
    text_type = str


_INVALID_VIEW_NAME_CHARS = set('{}[]|;<>?`~\\/:*')


def _safe_token(value):
    text = text_type(value or "").strip()
    if not text:
        raise ValueError("Identifiant logement manquant.")

    chars = []
    previous_dash = False
    for char in text:
        out = "-" if char in _INVALID_VIEW_NAME_CHARS else char
        if out == "-":
            if previous_dash:
                continue
            previous_dash = True
        else:
            previous_dash = False
        chars.append(out)

    result = "".join(chars).strip(" -_.")
    if not result:
        raise ValueError("Identifiant logement inutilisable pour le nommage.")
    return result


def schedule_name(housing_key, role):
    role = text_type(role or "").strip().upper()
    if role not in ("INT", "EXT"):
        raise ValueError("Rôle de nomenclature inconnu : {}".format(role or "?"))
    return "PDV_{}_{}".format(_safe_token(housing_key), role)
