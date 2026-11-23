# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Séquences textuelles sans dépendance à Revit ni à WPF."""

import re
import unicodedata


def _validate(value):
    if value is None or not value.strip():
        raise ValueError("La valeur initiale ne peut pas être vide.")
    if any(unicodedata.category(char) in ("Cc", "Zl", "Zp") for char in value):
        raise ValueError("Les caractères de contrôle sont interdits.")
    return value


def _last_span(value, mode):
    begin = None
    last = None
    for index, char in enumerate(value):
        match = (char.isdigit() if mode == "digits" else
                 unicodedata.category(char)[0] in ("L", "M"))
        if match and begin is None:
            begin = index
        elif not match and begin is not None:
            last = (begin, index)
            begin = None
    return (begin, len(value)) if begin is not None else last


def _letters_to_int(text):
    result = 0
    for char in text.upper():
        result = result * 26 + ord(char) - ord("A") + 1
    return result


def _int_to_letters(number, lowercase=False):
    if number < 1:
        raise ValueError("Une séquence alphabétique ne peut pas descendre sous A.")
    letters = "abcdefghijklmnopqrstuvwxyz" if lowercase else "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    output = []
    while number:
        number, remainder = divmod(number - 1, 26)
        output.append(letters[remainder])
    return "".join(reversed(output))


def parse_sequence(start, mode="digits", step=1):
    """Identifie le dernier bloc entier du type demandé, jamais un fragment Unicode."""
    if mode not in ("digits", "letters"):
        raise ValueError("Mode de numérotation inconnu.")
    if not isinstance(step, int) or isinstance(step, bool) or step == 0:
        raise ValueError("Le pas doit être un entier non nul.")
    start = _validate(start)
    span = _last_span(start, mode)
    if span is None:
        raise ValueError("Aucun bloc à incrémenter.")
    begin, end = span
    block = start[begin:end]
    spec = {"mode": mode, "prefix": start[:begin], "suffix": start[end:], "step": step}
    if mode == "digits":
        if re.match(r"^[0-9]+\Z", block) is None:
            raise ValueError("Le bloc numérique doit contenir uniquement les chiffres ASCII 0-9.")
        spec.update(start=int(block), width=len(block))
    else:
        if re.match(r"^[A-Z]+\Z", block) is None and re.match(r"^[a-z]+\Z", block) is None:
            raise ValueError("Le bloc alphabétique doit être entièrement A-Z ou a-z.")
        spec.update(start=_letters_to_int(block), lowercase=block.islower())
    return spec


def sequence_value(spec, offset):
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("La position doit être un entier positif ou nul.")
    number = spec["start"] + offset * spec["step"]
    if number < (0 if spec["mode"] == "digits" else 1):
        raise ValueError("La séquence atteint une valeur négative ou hors alphabet.")
    if spec["mode"] == "digits":
        block = str(number).zfill(spec["width"])
    else:
        block = _int_to_letters(number, spec["lowercase"])
    return spec["prefix"] + block + spec["suffix"]


def proposed_assignments(room_keys, spec):
    """L'ordre d'entrée est l'ordre des clics ; doublons d'élément ignorés."""
    seen = set()
    assignments = []
    for key in room_keys:
        if key in seen:
            continue
        seen.add(key)
        assignments.append((key, sequence_value(spec, len(assignments))))
    return assignments
