# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Modèles runtime pour résoudre les divergences de paramètres dans les groupes."""


class GroupAlignmentCandidate(object):
    """Valeur possible pour un membre correspondant entre occurrences de groupe."""

    def __init__(self, value, count=0, display_value=None):
        self.value = value
        self.count = int(count)
        self.display_value = (
            str(display_value)
            if display_value is not None
            else str(value)
        )

    @property
    def display_label(self):
        return "{}  —  {} occurrence(s)".format(
            self.display_value,
            self.count,
        )


class GroupAlignmentConflict(object):
    """Divergence sur un même membre entre instances d'un type de groupe."""

    def __init__(
        self,
        key,
        group_type_name,
        member_label,
        candidates,
        elements,
    ):
        self.key = str(key)
        self.group_type_name = group_type_name or "Type de groupe"
        self.member_label = member_label or "Pièce"
        self.candidates = list(candidates or [])
        self.elements = list(elements or [])

    @property
    def recommended_index(self):
        if not self.candidates:
            return -1

        best_index = 0
        best_count = self.candidates[0].count
        for index, candidate in enumerate(self.candidates[1:], 1):
            if candidate.count > best_count:
                best_index = index
                best_count = candidate.count
        return best_index


class GroupAlignmentAnalysis(object):
    """Résultat de l'analyse avant écriture."""

    def __init__(self, conflicts=None):
        self.conflicts = list(conflicts or [])

    @property
    def has_conflicts(self):
        return bool(self.conflicts)

    @property
    def conflict_count(self):
        return len(self.conflicts)


class GroupAlignmentResolution(object):
    """Choix utilisateur appliqué lorsque des valeurs divergent."""

    KEEP_VARIABLE = "KEEP_VARIABLE"
    ALIGN_SELECTED = "ALIGN_SELECTED"
    CANCEL = "CANCEL"

    def __init__(self, mode, selections=None):
        self.mode = mode
        self.selections = dict(selections or {})

    @classmethod
    def keep_variable(cls):
        return cls(cls.KEEP_VARIABLE)

    @classmethod
    def align_selected(cls, selections):
        return cls(cls.ALIGN_SELECTED, selections=selections)

    @classmethod
    def cancel(cls):
        return cls(cls.CANCEL)

    def selected_value(self, conflict):
        if conflict is None:
            return None
        return self.selections.get(conflict.key)
