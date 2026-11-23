# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Formatage littéral de paramètres texte : pas d'évaluation arbitraire."""

from string import Formatter


def format_value(value, template, index, family_name=""):
    allowed = {"valeur": value, "index": str(index), "famille": family_name}
    for _, field, format_spec, conversion in Formatter().parse(template):
        if field is not None and (field not in allowed or format_spec or conversion):
            raise ValueError("Jeton de format inconnu : {}".format(field))
    result = template.format(**allowed)
    return result if result.strip() else value
