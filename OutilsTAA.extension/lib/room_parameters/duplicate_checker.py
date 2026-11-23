# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Détection des collisions dans un périmètre explicite de valeurs de pièce."""


def detect_collisions(assignments, existing, allow_shared=False):
    """Retourne {room_key: [autres clés en conflit]}.

    assignments: [(room_key, new_value)] ; existing: [(room_key, old_value)].
    Les valeurs initiales des pièces remplacées ne constituent pas des collisions.
    """
    if allow_shared:
        return {}
    proposed = dict(assignments)
    by_value = {}
    for key, value in existing:
        if key not in proposed and value is not None and value != "":
            by_value.setdefault(value, set()).add(key)
    for key, value in assignments:
        by_value.setdefault(value, set()).add(key)
    return {key: sorted(by_value[value] - set([key]), key=str)
            for key, value in assignments if len(by_value[value]) > 1}
