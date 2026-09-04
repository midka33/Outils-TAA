# -*- coding: utf-8 -*-
"""Modèle pur Python des règles dynamiques de publication.

Ce module est volontairement indépendant de Revit, WPF et du moteur de publication.
Il constitue le contrat de données de l'Étape 08 sans modifier le workflow existant.
"""


class DynamicRule(object):
    """Décrit un critère atomique appliqué à une mise en page.

    ``field`` correspond à une propriété normalisée fournie au résolveur
    (ex. ``discipline``, ``sheet_number`` ou ``phase``).
    """

    OPERATORS = (
        "equals",
        "not_equals",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "in",
        "not_in",
        "exists",
        "not_exists",
    )

    def __init__(self, field, operator="equals", value=None, label=None):
        if not field:
            raise ValueError("Une règle dynamique doit définir un champ.")
        if operator not in self.OPERATORS:
            raise ValueError("Opérateur dynamique inconnu : {0}".format(operator))
        self.field = field
        self.operator = operator
        self.value = value
        self.label = label or "{0} {1}".format(field, operator)

    def to_dict(self):
        return {
            "type": "rule",
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
            "label": self.label,
        }


class DynamicRuleGroup(object):
    """Groupe de règles combinées avec une logique ``all`` ou ``any``."""

    LOGICS = ("all", "any")

    def __init__(self, logic="all", children=None, label=None):
        if logic not in self.LOGICS:
            raise ValueError("Logique dynamique inconnue : {0}".format(logic))
        self.logic = logic
        self.children = list(children or [])
        self.label = label or ("Toutes les conditions" if logic == "all" else "Au moins une condition")

    def add(self, child):
        self.children.append(child)

    def to_dict(self):
        return {
            "type": "group",
            "logic": self.logic,
            "label": self.label,
            "children": [child.to_dict() for child in self.children],
        }


class DynamicRuleDefinition(object):
    """Définition complète d'une source dynamique de carnet."""

    VERSION = 1

    def __init__(self, root=None, exclusions=None, name=None):
        self.root = root or DynamicRuleGroup("all")
        self.exclusions = list(exclusions or [])
        self.name = name or "Règle dynamique"

    def to_dict(self):
        return {
            "schema_version": self.VERSION,
            "name": self.name,
            "root": self.root.to_dict(),
            "exclusions": list(self.exclusions),
        }
