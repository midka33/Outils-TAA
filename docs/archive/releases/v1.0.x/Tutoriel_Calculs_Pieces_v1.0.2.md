# Tutoriel — Calculs des pièces

**Release 1.0.2 — Revit 2025.4 / pyRevit 5.x**

## Objectif
**Calculs des pièces** regroupe les pièces selon un paramètre commun, additionne un paramètre numérique puis écrit le résultat dans un paramètre cible.

## Périmètre
L'outil traite **toutes les pièces du projet**. Un filtre optionnel permet de limiter les pièces prises en compte.

## Réaliser un calcul
1. Ouvrir **Outils TAA > Calculs des pièces**.
2. Choisir le **paramètre de regroupement**.
3. Choisir le **paramètre à sommer**.
4. Choisir le **paramètre cible**.
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

## Pièces dans des groupes
Les pièces placées dans des groupes Revit sont prises en charge.

Si le paramètre destination est configuré pour rester **aligné par type de groupe**, Outils TAA :
1. autorise temporairement l'écriture pendant la transaction ;
2. écrit les résultats ;
3. restaure automatiquement l'alignement avant de valider la transaction.

Si Revit détecte que le retour à l'alignement modifierait des valeurs divergentes entre occurrences, la transaction est annulée afin de ne pas écraser silencieusement des résultats différents.

> La résolution interactive des divergences entre groupes est encore en cours de validation et n'est pas incluse dans cette release.

## Bonnes pratiques
- Vérifier que les paramètres existent sur les pièces.
- Pour les groupes, les occurrences d'un même type doivent produire le même résultat métier lorsque le paramètre cible suit le groupe.
- Si un résultat semble incomplet, contrôler le filtre et les valeurs du paramètre de regroupement.
- Consulter le rapport en cas d'échec ou d'annulation de transaction.
