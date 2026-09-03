# Calculs des pièces

## Statut

Spécification architecturale initiale.

## Responsabilité

Le module **Calculs des pièces** regroupe les traitements métier portant sur les pièces Revit : calculs, agrégations et mise à jour contrôlée des paramètres associés.

## Architecture

```text
UI
 │
 ▼
Services métier
 │
 ├── Modèles métier
 └── Adaptateurs Revit
        │
        ▼
     API Revit
```

L'UI ne réalise aucun calcul métier et ne manipule pas directement les transactions Revit.

## Principes

- Une responsabilité par service.
- Réutilisation de `lib/common`.
- Pas de dépendance vers Export.
- Transactions courtes et explicites.
- Validation des pièces avant modification.
- Journalisation des erreurs et opérations significatives.
- Compatibilité Revit 2025.4 / pyRevit 5.x.

## Évolution prévue

Les fonctionnalités existantes seront migrées progressivement dans cette architecture sans modifier leur comportement fonctionnel sans décision explicite.
