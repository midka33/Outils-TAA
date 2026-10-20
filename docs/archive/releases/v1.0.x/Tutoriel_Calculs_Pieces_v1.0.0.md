# Tutoriel — Calculs des pièces

**Release 1.0.0 — Revit 2025.4 / pyRevit 5.x**

## Objectif
**Calculs des pièces** regroupe les pièces selon un paramètre commun, additionne un paramètre numérique puis écrit le résultat dans un paramètre cible.

## Périmètre
La release traite **toutes les pièces du projet**. Il n'existe pas de choix « Vue active / Toutes les pièces ». Un filtre optionnel permet de limiter les pièces prises en compte.

## Réaliser un calcul
1. Ouvrir **Outils TAA > Calculs des pièces**.
2. Choisir le **paramètre de regroupement**. Les pièces ayant la même valeur sont calculées ensemble.
3. Choisir le **paramètre à sommer** : surface ou autre donnée numérique compatible.
4. Choisir le **paramètre cible** dans lequel le résultat doit être écrit.
5. Si nécessaire, ajouter un **filtre texte optionnel**.
6. Choisir l'unité adaptée.
7. Lancer le calcul.
8. Contrôler le nombre de pièces traitées, le nombre de groupes et les éventuels messages d'erreur.

## Exemple
Pour calculer la surface totale de chaque logement :
- regroupement : identifiant du logement ;
- valeur à sommer : Surface ;
- filtre : optionnel ;
- paramètre cible : Surface totale du logement.

L'outil additionne les surfaces des pièces partageant le même identifiant puis écrit la somme dans le paramètre cible.

## Bonnes pratiques
- Vérifier que les paramètres existent sur les pièces.
- Vérifier que le paramètre cible est inscriptible.
- Si un résultat semble incomplet, contrôler le filtre et les valeurs du paramètre de regroupement.
