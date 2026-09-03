"""Résultat de résolution d'un carnet persistant dans le document courant."""


class CarnetResolution(object):
    """Contient les éléments retrouvés et ceux devenus introuvables."""

    def __init__(self, items=None, missing_items=None):
        self.items = list(items or [])
        self.missing_items = list(missing_items or [])

    @property
    def resolved_count(self):
        return len(self.items)

    @property
    def missing_count(self):
        return len(self.missing_items)

    @property
    def is_complete(self):
        return self.missing_count == 0

    @property
    def total_count(self):
        return self.resolved_count + self.missing_count
