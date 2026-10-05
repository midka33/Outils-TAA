# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Nommage pur du plan de repérage Plans de vente."""

try:
    text_type = unicode
except NameError:  # pragma: no cover - Python 3
    text_type = str


_INVALID_VIEW_NAME_CHARS = set('{}[]|;<>?`~\\/:*')


def location_view_name(housing_key):
    text = text_type(housing_key or "").strip()
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

    token = "".join(chars).strip(" -_.")
    if not token:
        raise ValueError("Identifiant logement inutilisable pour le nommage.")
    return "PDV_{}_REP".format(token)
