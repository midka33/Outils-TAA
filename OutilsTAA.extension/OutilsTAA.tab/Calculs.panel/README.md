# Calculs

Module destiné aux fonctionnalités métier **Calculs des pièces**.

## Périmètre

Le module travaille toujours à partir de **toutes les pièces du projet Revit actif**.

Il n'expose pas de choix « vue active / toutes les pièces ».

Un filtre métier optionnel par paramètre peut ensuite réduire le jeu de pièces.

## Migration

La migration depuis l'ancien module RoomTools est en cours sur la branche `feature/calculs-pieces-migration`.

Le moteur métier pur de regroupement/somme est maintenant isolé dans `OutilsTAA.extension/lib/calculation/`.

La collecte complète du document, le filtre métier optionnel, l'identité des paramètres, leur validation et la gestion commune des unités sont maintenant préparés et testés hors Revit. L'écriture, la persistance et l'interface WPF restent à réaliser ; tous les accès Revit doivent encore être validés dans Revit 2025.4.
