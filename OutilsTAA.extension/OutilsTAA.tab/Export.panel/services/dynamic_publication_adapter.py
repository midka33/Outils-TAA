# -*- coding: utf-8 -*-
"""Adaptateur Stage 08 vers le modèle PublicationItem existant.

Ce module ne déclenche aucune publication et ne dépend pas de Revit ou WPF.
Il transforme uniquement une résolution dynamique en sélection d'instances
PublicationItem déjà présentes dans un carnet.
"""


class DynamicPublicationDiagnostic(object):
    """Diagnostic produit pendant l'adaptation d'une résolution dynamique."""

    def __init__(self, severity, code, message, key=None):
        self.severity = severity
        self.code = code
        self.message = message
        self.key = key


class DynamicPublicationSelection(object):
    """Sélection de PublicationItem issue d'une résolution dynamique."""

    def __init__(self, items=None, diagnostics=None):
        self.items = list(items or [])
        self.diagnostics = list(diagnostics or [])

    @property
    def valid(self):
        return not any(
            diagnostic.severity == "error"
            for diagnostic in self.diagnostics
        )


class DynamicPublicationAdapter(object):
    """Relie DynamicResolution au modèle PublicationItem sans le dupliquer."""

    def build_selection(self, resolution, publication_items):
        """Construit une sélection avec les instances PublicationItem existantes.

        L'ordre de la résolution est conservé. Les éléments exclus ou non
        inclus ne sont jamais transmis. Aucun objet source n'est modifié.
        """
        if resolution is None:
            raise TypeError("La résolution dynamique est obligatoire.")

        diagnostics = []
        item_map = {}
        duplicate_keys = set()

        for item in publication_items or []:
            key = getattr(item, "unique_id", None)
            if not key:
                diagnostics.append(DynamicPublicationDiagnostic(
                    "warning",
                    "MISSING_PUBLICATION_ITEM_KEY",
                    "PublicationItem ignoré : unique_id manquant."
                ))
                continue
            if key in item_map:
                duplicate_keys.add(key)
                continue
            item_map[key] = item

        for key in sorted(duplicate_keys):
            diagnostics.append(DynamicPublicationDiagnostic(
                "error",
                "DUPLICATE_PUBLICATION_ITEM_KEY",
                "Plusieurs PublicationItem utilisent la même clé unique.",
                key=key
            ))

        selected = []
        for candidate in getattr(resolution, "candidates", []):
            if not candidate.included or candidate.excluded:
                continue

            item = item_map.get(candidate.key)
            if item is None:
                diagnostics.append(DynamicPublicationDiagnostic(
                    "error",
                    "PUBLICATION_ITEM_NOT_FOUND",
                    "La résolution dynamique référence un élément absent du carnet source.",
                    key=candidate.key
                ))
                continue

            selected.append(item)

        return DynamicPublicationSelection(selected, diagnostics)
