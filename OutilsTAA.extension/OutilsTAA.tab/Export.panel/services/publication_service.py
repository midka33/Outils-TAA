"""Service de préparation d'une publication."""


class PublicationService(object):
    """Valide et normalise un carnet avant son export."""

    def validate_publication_set(self, publication_set):
        """Retourne une liste d'erreurs fonctionnelles."""
        errors = []

        if publication_set is None:
            return ["Le carnet de publication est manquant."]

        if not publication_set.name:
            errors.append("Le carnet doit avoir un nom.")

        if not publication_set.items:
            errors.append("Le carnet ne contient aucun élément à publier.")

        return errors

    def sort_items(self, publication_set):
        """Retourne les éléments triés par numéro de feuille."""
        if publication_set is None:
            return []

        return sorted(
            publication_set.items,
            key=lambda item: (item.sheet_number or "", item.sheet_name or "")
        )
