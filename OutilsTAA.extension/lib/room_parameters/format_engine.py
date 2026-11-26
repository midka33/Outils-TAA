# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Formatage littéral de paramètres texte : pas d'évaluation arbitraire."""

from string import Formatter


def parameter_token(parameter_id):
    """Jeton stable, y compris pour les identifiants Revit natifs négatifs."""
    return "param_{}{}".format("m" if parameter_id < 0 else "", abs(parameter_id))


def parameter_aliases(named_tokens):
    """Noms lisibles et uniques, liés aux jetons techniques stables."""
    aliases = {}
    for name, token in named_tokens:
        label = name.strip() or "Paramètre sans nom"
        if label in ("valeur", "index", "famille") or label.startswith("param_"):
            label = "Paramètre : " + label
        candidate = label
        suffix = 2
        while candidate in aliases:
            candidate = "{} ({})".format(label, suffix)
            suffix += 1
        aliases[candidate] = token
    return aliases


def format_value(value, template, index, family_name="", parameters=None, aliases=None):
    allowed = {"valeur": value, "index": str(index), "famille": family_name}
    if parameters:
        for key, text in parameters.items():
            if not key.startswith("param_") or not key[6:].replace("m", "", 1).isdigit():
                raise ValueError("Identifiant de paramètre invalide.")
            allowed[key] = text
    if aliases:
        for name, token in aliases.items():
            if name in allowed or token not in allowed:
                if token not in allowed:
                    # Le paramètre peut être absent sur un élément du lot.
                    continue
                raise ValueError("Nom de paramètre ambigu : {}".format(name))
            allowed[name] = allowed[token]
    for _, field, format_spec, conversion in Formatter().parse(template):
        if field is not None and (field not in allowed or format_spec or conversion):
            raise ValueError("Jeton de format inconnu : {}".format(field))
    result = template.format(**allowed)
    return result if result.strip() else value
