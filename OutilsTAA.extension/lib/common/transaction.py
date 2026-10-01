# -*- coding: utf-8 -*-
"""Gestion centralisée des transactions Revit."""

try:
    from Autodesk.Revit.DB import Transaction
except ImportError:
    Transaction = None


class RevitTransaction(object):
    """Gestionnaire de contexte pour une transaction courte et explicite."""

    def __init__(self, document, name, transaction_factory=None):
        self.document = document
        self.name = name
        self._transaction = None
        self._transaction_factory = transaction_factory
        self.committed = False

    def __enter__(self):
        factory = self._transaction_factory or Transaction
        if factory is None:
            raise RuntimeError("L'API Revit n'est pas disponible.")
        self._transaction = factory(self.document, self.name)
        self._transaction.Start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            self._rollback_safely()
            return False

        try:
            self._transaction.Commit()
            self.committed = True
        except Exception:
            self._rollback_safely()
            raise

        return False

    def _rollback_safely(self):
        try:
            if self._transaction is not None:
                self._transaction.RollBack()
        except Exception:
            pass
