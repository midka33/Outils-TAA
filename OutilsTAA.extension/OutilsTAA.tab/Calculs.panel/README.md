# Calculs

Module **Calculs des pièces** pour Revit 2025.4 / pyRevit 5.x.

## Périmètre

Le module part toujours de **toutes les pièces du projet Revit actif**.

Il n'expose pas de choix « Vue active / Toutes les pièces ».

Un filtre métier optionnel par paramètre peut ensuite réduire le jeu de pièces.

## État

La migration depuis l'ancien RoomTools est implémentée sur :

```text
feature/calculs-pieces-migration
```

Sont désormais présents :

- moteur de regroupement/somme ;
- collecte projet entière ;
- filtre optionnel ;
- identités et validation des paramètres ;
- unités Revit ;
- écriture contrôlée et transaction ;
- persistance ;
- interface WPF ;
- rapport ;
- bouton pyRevit ;
- tests automatisés.

La CI hors Revit valide actuellement :

```text
68 passed
```

Le module doit maintenant être **validé dans Revit 2025.4 réel** avant fusion dans `main`.

Voir :

```text
docs/18_Calculs_Pieces_Tests_Revit.md
```
