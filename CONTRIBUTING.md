# Contribuer à Outils TAA

## Avant de modifier le code

- Lire `ARCHITECTURE.md`.
- Lire `docs/03_Standards_Developpement.md` et `docs/07_Git_Workflow.md`.
- Vérifier la compatibilité Revit 2025.4 / pyRevit 5.x.
- Identifier si le besoin relève d'un module métier ou de `lib/common`.

## Règles

- Ne pas dupliquer une fonction déjà présente dans `lib/common`.
- Ne pas mettre de logique métier dans l'UI.
- Ne pas créer de dépendance entre modules métier.
- Documenter les changements structurants.
- Ajouter ou mettre à jour les tests pertinents.
- Utiliser des commentaires et docstrings en français.

## Pull request

Une PR doit préciser :

1. le problème traité ;
2. la solution retenue ;
3. les fichiers concernés ;
4. les tests réalisés ;
5. les éventuelles limites Revit/pyRevit.
