# Tutoriel — Calculs des pièces

**Release 1.5.0 — Revit 2025.4 / pyRevit 5.x**

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
6. Lancer le calcul ; les unités de sortie sont déterminées automatiquement.
7. Contrôler les groupes, les variantes, la revue avant écriture et les éventuels messages d'erreur.

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

## Nouveautés et précautions v1.5.0 — Groupes et variantes

- La fenêtre principale explique le comportement lorsque les paramètres de destination sont liés aux **groupes Revit**. Le mode est décidé automatiquement à partir des données constatées.
- Les appartements appartenant à plusieurs variantes sont contrôlés avant l'écriture ; la fenêtre de revue indique les éléments à modifier et propose la confirmation adaptée.
- Dans certains cas, Outils TAA **désactive durablement** l'alignement entre occurrences pour conserver des valeurs d'appartement différentes. Cette modification porte sur la définition du paramètre dans Revit : vérifier l'avertissement avant de confirmer.
- Les résultats s'affichent dans la fenêtre principale ; le rapport peut être consulté sur demande, tandis qu'un échec produit son diagnostic et annule la transaction correspondante.
- L'ancienne option de sélection manuelle de l'**unité de sortie** a été retirée. La conversion est déterminée par les types source/destination ; ne pas chercher à forcer une unité par un contrôle caché.
- Les tentatives d'imposer de nouvelles valeurs communes incompatibles avec l'alignement Revit ne sont **pas forcées silencieusement**. Les scénarios nécessitant une édition du type de groupe peuvent demander une opération manuelle sur copie du modèle.

**Recette recommandée :** avant utilisation en production sur de nouveaux types de groupes ou variantes, effectuer un essai sur une copie RVT et contrôler les valeurs des pièces, les occurrences homologues et la possibilité de `Ctrl+Z`. 
