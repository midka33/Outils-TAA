# -*- coding: utf-8 -*-
from __future__ import unicode_literals

"""Option d'unité affichable dans l'interface Calculs des pièces."""


class UnitOption(object):
    def __init__(self, label, type_id=None):
        self.label = label or ""
        self.type_id = type_id

    @property
    def is_automatic(self):
        return self.type_id is None

    def __str__(self):
        return self.label
