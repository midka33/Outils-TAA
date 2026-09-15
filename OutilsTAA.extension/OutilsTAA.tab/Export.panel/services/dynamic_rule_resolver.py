# -*- coding: utf-8 -*-
"""Résolution et comparaison hors Revit des règles dynamiques de publication.

Ce module reste indépendant de Revit, WPF et du moteur PDF/DWG.
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


class DynamicChange(object):
    """Évolution d'un élément entre deux résolutions."""

    STATES = ("ADDED", "REMOVED", "UNCHANGED", "EXCLUDED", "REINCLUDED")

    def __init__(self, key, state, previous=None, current=None):
        self.key = key
        self.state = state
        self.previous = previous
        self.current = current


class DynamicResolution(object):
    """Résultat complet, consommable plus tard par la prévisualisation."""

    def __init__(self, candidates=None, diagnostics=None):
        self.candidates = list(candidates or [])
        self.diagnostics = list(diagnostics or [])

    @property
    def included(self):
        return [item for item in self.candidates if item.included and not item.excluded]

    @property
    def excluded(self):
        return [item for item in self.candidates if item.excluded]

    @property
    def included_keys(self):
        return set(item.key for item in self.included)

    @property
    def excluded_keys(self):
        return set(item.key for item in self.excluded)

    def compare(self, previous):
        """Compare cette résolution à une résolution précédente.

        La comparaison porte sur le périmètre résultant, pas sur les éléments
        non sélectionnés par les règles. Un élément qui quitte le périmètre est
        donc ``REMOVED`` ; une exclusion qui disparaît devient ``REINCLUDED``.
        """
        if not isinstance(previous, DynamicResolution):
            raise TypeError("La résolution précédente doit être une DynamicResolution.")

        changes = []
        previous_map = dict((item.key, item) for item in previous.candidates)
        current_map = dict((item.key, item) for item in self.candidates)
        all_keys = set(previous_map.keys()) | set(current_map.keys())

        for key in sorted(all_keys):
            old = previous_map.get(key)
            new = current_map.get(key)
            old_included = bool(old and old.included and not old.excluded)
            new_included = bool(new and new.included and not new.excluded)
            old_excluded = bool(old and old.excluded)
            new_excluded = bool(new and new.excluded)

            if old is None and new_included:
                state = "ADDED"
            elif new is None and old_included:
                state = "REMOVED"
            elif old_included and not new_included:
                state = "REMOVED"
            elif not old_included and new_included and old_excluded:
                state = "REINCLUDED"
            elif new_excluded:
                state = "EXCLUDED"
            elif old_included and new_included:
                state = "UNCHANGED"
            else:
                continue

            changes.append(DynamicChange(key, state, old, new))

        return changes


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
