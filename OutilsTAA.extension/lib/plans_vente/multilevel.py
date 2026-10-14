# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Helpers métier purs pour les logements multi-niveaux."""

import re

from plans_vente.housing import Housing


def _safe_level_token(value):
    text = str(value or "").strip()
    if not text:
        return "NIVEAU"
    text = re.sub(r"[^0-9A-Za-zÀ-ÿ_-]+", "-", text, flags=re.UNICODE)
    text = re.sub(r"-+", "-", text).strip("-_")
    return text or "NIVEAU"


def split_housing_by_level(housing):
    """Retourne un Housing mono-niveau par niveau du logement.

    La clé de sortie est unique par niveau (ex. A101-RDC), mais filter_key
    conserve l'identifiant logement original (A101) pour les nomenclatures.
    """
    if housing is None:
        return []

    groups = {}
    display = {}
    for room in list(getattr(housing, "rooms", []) or []):
        level_name = str(getattr(room, "level_name", "") or "").strip()
        normalized = level_name.lower()
        groups.setdefault(normalized, []).append(room)
        if normalized not in display:
            display[normalized] = level_name or "Niveau"

    if len(groups) <= 1:
        return [housing]

    used = {}
    result = []
    source_key = str(
        getattr(housing, "filter_key", None)
        or getattr(housing, "key", "")
        or ""
    )
    for normalized in sorted(groups.keys()):
        label = display.get(normalized, "") or "Niveau"
        token = _safe_level_token(label)
        lowered = token.lower()
        used[lowered] = used.get(lowered, 0) + 1
        if used[lowered] > 1:
            token = "{}-{}".format(token, used[lowered])

        output_key = "{}-{}".format(
            getattr(housing, "key", "") or source_key,
            token,
        )
        result.append(
            Housing(
                key=output_key,
                rooms=groups[normalized],
                filter_key=source_key,
            )
        )
    return result
