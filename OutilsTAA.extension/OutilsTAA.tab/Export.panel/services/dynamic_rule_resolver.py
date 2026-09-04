# -*- coding: utf-8 -*-
"""Résolution hors Revit des règles dynamiques de publication.

Le résolveur reçoit des dictionnaires de propriétés normalisées. Il ne connaît
ni Document Revit, ni WPF, ni le moteur PDF/DWG. Cette séparation permet de
tester la logique métier sans perturber les étapes de publication existantes.
"""

from models.dynamic_rule import DynamicRule, DynamicRuleGroup, DynamicRuleDefinition


class DynamicCandidate(object):
    """Résultat de résolution pour un élément candidat."""

    def __init__(self, key, included, excluded=False, reasons=None):
        self.key = key
        self.included = bool(included)
        self.excluded = bool(excluded)
        self.reasons = list(reasons or [])


class DynamicDiagnostic(object):
    """Diagnostic explicite produit pendant la résolution."""

    def __init__(self, severity, code, message, key=None):
        self.severity = severity
        self.code = code
        self.message = message
        self.key = key


class DynamicResolution(object):
    """Résultat complet, consommable plus tard par la prévisualisation."""

    def __init__(self, candidates=None, diagnostics=None):
        self.candidates = list(candidates or [])
        self.diagnostics = list(diagnostics or [])

    @property
    def included(self):
        return [item for item in self.candidates if item.included]

    @property
    def excluded(self):
        return [item for item in self.candidates if item.excluded]


class DynamicRuleResolver(object):
    """Évalue une définition dynamique sur une collection de propriétés."""

    def resolve(self, definition, items):
        if not isinstance(definition, DynamicRuleDefinition):
            raise TypeError("La définition doit être une DynamicRuleDefinition.")

        diagnostics = []
        candidates = []
        excluded_keys = set(definition.exclusions)

        for item in items or []:
            key = self._key(item)
            if key is None:
                diagnostics.append(DynamicDiagnostic(
                    "warning", "MISSING_KEY",
                    "Élément ignoré : aucune clé persistante disponible."
                ))
                continue

            properties = self._properties(item)
            matched, reasons = self._evaluate(definition.root, properties)
            is_excluded = key in excluded_keys

            if is_excluded:
                candidates.append(DynamicCandidate(
                    key, included=False, excluded=True,
                    reasons=reasons + ["Exclusion explicite"]
                ))
            else:
                candidates.append(DynamicCandidate(
                    key, included=matched, excluded=False, reasons=reasons
                ))

        for key in excluded_keys:
            if not any(candidate.key == key for candidate in candidates):
                diagnostics.append(DynamicDiagnostic(
                    "warning", "EXCLUSION_NOT_FOUND",
                    "Une exclusion explicite ne correspond à aucun élément courant.",
                    key=key
                ))

        return DynamicResolution(candidates, diagnostics)

    def _evaluate(self, node, properties):
        if isinstance(node, DynamicRule):
            result = self._evaluate_rule(node, properties)
            return result, [node.label] if result else []

        if not isinstance(node, DynamicRuleGroup):
            raise TypeError("Nœud de règle dynamique inconnu.")

        results = []
        reasons = []
        for child in node.children:
            result, child_reasons = self._evaluate(child, properties)
            results.append(result)
            if result:
                reasons.extend(child_reasons)

        if not results:
            return False, []

        matched = all(results) if node.logic == "all" else any(results)
        return matched, reasons

    def _evaluate_rule(self, rule, properties):
        exists = rule.field in properties and properties.get(rule.field) is not None
        actual = properties.get(rule.field)
        expected = rule.value

        if rule.operator == "exists":
            return exists
        if rule.operator == "not_exists":
            return not exists
        if not exists:
            return False

        if rule.operator == "equals":
            return actual == expected
        if rule.operator == "not_equals":
            return actual != expected
        if rule.operator == "contains":
            return str(expected).lower() in str(actual).lower()
        if rule.operator == "not_contains":
            return str(expected).lower() not in str(actual).lower()
        if rule.operator == "starts_with":
            return str(actual).lower().startswith(str(expected).lower())
        if rule.operator == "ends_with":
            return str(actual).lower().endswith(str(expected).lower())
        if rule.operator == "in":
            return actual in (expected or [])
        if rule.operator == "not_in":
            return actual not in (expected or [])
        return False

    def _key(self, item):
        if isinstance(item, dict):
            return item.get("key") or item.get("unique_id")
        return getattr(item, "key", None) or getattr(item, "unique_id", None)

    def _properties(self, item):
        if isinstance(item, dict):
            return item.get("properties", item)
        return getattr(item, "properties", {})
