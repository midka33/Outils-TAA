# Calculs

Module destiné aux fonctionnalités métier **Calculs des pièces**.

## Périmètre

Le module travaille toujours à partir de **toutes les pièces du projet Revit actif**.

Il n'expose pas de choix « vue active / toutes les pièces ».

Un filtre métier optionnel par paramètre peut ensuite réduire le jeu de pièces.

## Migration

La migration depuis l'ancien module RoomTools est en cours sur la branche `feature/calculs-pieces-migration`.

Le moteur métier pur de regroupement/somme est maintenant isolé dans `OutilsTAA.extension/lib/calculation/`.

Le raccordement Revit, l'écriture des paramètres et l'interface WPF restent à réaliser et à valider dans Revit 2025.4.
