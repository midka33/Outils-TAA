# -*- coding: utf-8 -*-
"""Gestion centralisée des transactions Revit."""

try:
    from Autodesk.Revit.DB import Transaction
except ImportError:
    Transaction = None


class RevitTransaction(object):
    """Gestionnaire de contexte pour une transaction courte et explicite."""

    def __init__(self, document, name):
        self.document = document
        self.name = name
        self._transaction = None

    def __enter__(self):
        if Transaction is None:
            raise RuntimeError("L'API Revit n'est pas disponible.")
        self._transaction = Transaction(self.document, self.name)
        self._transaction.Start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self._transaction.Commit()
        else:
            self._transaction.RollBack()
        return False
