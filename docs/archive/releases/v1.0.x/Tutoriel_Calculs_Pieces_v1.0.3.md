# Tutoriel — Calculs des pièces

**Release 1.0.3 — Revit 2025.4 / pyRevit 5.x**

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
8. Contrôler le nombre de pièces traitées, les groupes et les éventuels messages d'erreur.

## Exemple
Pour calculer la surface totale de chaque logement :
- regroupement : identifiant du logement ;
- valeur à sommer : Surface ;
- paramètre cible : Surface totale du logement.

## Pièces dans des groupes
Les pièces placées dans des groupes Revit sont prises en charge.

Si le paramètre destination est configuré pour rester **aligné par type de groupe**, Outils TAA :
1. autorise temporairement l'écriture dans la transaction ;
2. écrit les résultats ;
3. restaure l'alignement ;
4. annule la transaction si Revit signale qu'un réalignement modifierait des valeurs divergentes.

Cette sécurité évite d'écraser silencieusement des résultats différents entre occurrences d'un même type de groupe.

> La résolution interactive des divergences de groupes n'est pas incluse dans cette release.

## Performance — nouveauté v1.0.3
L'ouverture du module a été optimisée pour les projets comportant beaucoup de logements/pièces.

Avant cette version, la liste des paramètres était reconstruite plusieurs fois. La v1.0.3 :
- ne parcourt les pièces/paramètres qu'une seule fois à l'ouverture ;
- dérive ensuite en mémoire les listes numériques et les destinations ;
- réutilise les métadonnées invariantes des paramètres pendant ce scan.

Sur le projet de validation d'environ **80 logements**, l'ouverture a été constatée autour de **3 secondes**.

## Bonnes pratiques
- Vérifier que les paramètres existent sur les pièces.
- Vérifier le filtre si certaines pièces ne doivent pas participer au calcul.
- Pour un paramètre cible aligné par groupe, les occurrences d'un même type doivent produire le même résultat si l'on veut conserver l'alignement.
- En cas d'échec ou de rollback, consulter le rapport avant de relancer.
