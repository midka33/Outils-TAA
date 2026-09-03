# -*- coding: utf-8 -*-
"""Contrat commun de progression."""


class ProgressReporter(object):
    """Abstraction minimale pour permettre une UI de progression uniforme."""

    def report(self, current, total, message=""):
        raise NotImplementedError

    def is_cancelled(self):
        return False
