# -*- coding: utf-8 -*-
"""Prévisualisation hors Revit d'une résolution dynamique.

Ce service transforme une résolution courante et, si disponible, une résolution
précédente en données structurées destinées à une future UI. Il ne déclenche
aucune publication et ne dépend ni de Revit ni de WPF.
"""

from services.dynamic_rule_resolver import DynamicResolution


class DynamicPreviewRow(object):
    """Ligne stable de prévisualisation pour un candidat dynamique."""

    def __init__(self, key, status, included, excluded, reasons=None):
        self.key = key
        self.status = status
        self.included = bool(included)
        self.excluded = bool(excluded)
        self.reasons = list(reasons or [])


class DynamicPreview(object):
    """Résultat structuré de prévisualisation, sans effet de bord."""

    def __init__(self, rows=None, diagnostics=None, changes=None):
        self.rows = list(rows or [])
        self.diagnostics = list(diagnostics or [])
        self.changes = list(changes or [])

    @property
    def publishable_rows(self):
        """Lignes correspondant au périmètre actuellement publiable."""
        return [row for row in self.rows if row.included and not row.excluded]

    @property
    def added(self):
        return [row for row in self.rows if row.status == "ADDED"]

    @property
    def removed(self):
        return [row for row in self.rows if row.status == "REMOVED"]

    @property
    def excluded(self):
        return [row for row in self.rows if row.status == "EXCLUDED"]

    @property
    def reincluded(self):
        return [row for row in self.rows if row.status == "REINCLUDED"]

    @property
    def unchanged(self):
        return [row for row in self.rows if row.status == "UNCHANGED"]

    @property
    def not_matched(self):
        return [row for row in self.rows if row.status == "NOT_MATCHED"]


class DynamicPreviewBuilder(object):
    """Construit une prévisualisation déterministe d'une résolution dynamique."""

    def build(self, current, previous=None):
        if not isinstance(current, DynamicResolution):
            raise TypeError("La résolution courante doit être une DynamicResolution.")
        if previous is not None and not isinstance(previous, DynamicResolution):
            raise TypeError("La résolution précédente doit être une DynamicResolution.")

        changes = current.compare(previous) if previous is not None else []
        change_map = dict((change.key, change) for change in changes)
        rows = []

        # Le premier aperçu décrit le périmètre courant. Lorsqu'un snapshot
        # précédent existe, les changements restent déterminés par compare().
        for candidate in current.candidates:
            change = change_map.get(candidate.key)
            status = change.state if change is not None else self._initial_status(candidate)
            rows.append(DynamicPreviewRow(
                candidate.key,
                status,
                candidate.included,
                candidate.excluded,
                candidate.reasons,
            ))

        # Les éléments supprimés du périmètre courant doivent rester visibles
        # afin que l'utilisateur comprenne ce qui a disparu depuis le snapshot.
        if previous is not None:
            current_keys = set(candidate.key for candidate in current.candidates)
            for change in changes:
                if change.state != "REMOVED" or change.key in current_keys:
                    continue
                old = change.previous
                rows.append(DynamicPreviewRow(
                    change.key,
                    "REMOVED",
                    False,
                    bool(old and old.excluded),
                    list(old.reasons if old else []) + ["Absent de la résolution courante"],
                ))

        return DynamicPreview(rows, current.diagnostics, changes)

    def _initial_status(self, candidate):
        if candidate.excluded:
            return "EXCLUDED"
        if candidate.included:
            return "ADDED"
        return "NOT_MATCHED"
