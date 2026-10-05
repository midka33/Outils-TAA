# Export — Étape 06 : publication multiple

**Statut :** Implémentée  
**Cible :** Revit 2025.4 / pyRevit 5.x

## Objectif

L'étape 06 ajoute la publication d'un **Dossier** comme unité d'action Publisher TAA.

```text
Dossier
├── Carnet Plans
├── Carnet Coupes
└── Carnet Façades
        ↓
   Prévisualisation globale
        ↓
   Confirmation unique
        ↓
   Publication des carnets
        ↓
   Rapport global
```

## Comportement utilisateur

### Dossier sélectionné

Le bouton devient :

`Publier le dossier « Nom du dossier »`

Il est activé uniquement si le dossier contient au moins un carnet publiable.

### Périmètre

La publication inclut les carnets du dossier sélectionné ainsi que ceux de ses sous-dossiers.

Les carnets restent des unités de publication indépendantes : chacun conserve ses réglages effectifs, sa destination et son nommage.

### Prévisualisation

Avant tout export Revit, une prévisualisation globale présente les livrables de tous les carnets sélectionnés.

Elle conserve pour chaque ligne :

- carnet ;
- mise en page lorsque le livrable est séparé ;
- format ;
- mode combiné/séparé ;
- nom final ;
- chemin complet ;
- état.

Les collisions entre carnets sont détectées au même titre que les collisions internes à un carnet.

Si plusieurs destinations sont utilisées, l'en-tête de prévisualisation indique explicitement qu'il existe plusieurs destinations ; les chemins complets restent visibles sur les lignes.

## Exécution

Après confirmation, `PublicationBatchService` exécute chaque carnet avec ses réglages résolus par `SettingsResolver`.

Le moteur PDF/DWG existant n'est pas dupliqué : la publication multiple orchestre le service de publication déjà utilisé par la publication simple.

Un rapport unique est présenté à la fin avec :

- résultats par carnet ;
- erreurs ;
- avertissements ;
- destinations utilisées.

Une erreur sur un carnet n'efface pas les résultats déjà produits par les autres carnets.

## Cas particuliers

- Dossier vide : confirmation impossible.
- Carnet vide : bloqué par la prévisualisation.
- Feuille manquante : signalée avant publication.
- Feuille non imprimable : signalée avant publication.
- Fichier existant : avertissement.
- Nom en collision : avertissement.
- Destination différente entre carnets : affichée explicitement.

## Anti-régression

Tester au minimum :

1. un dossier avec deux carnets dans la même destination ;
2. un dossier avec deux destinations différentes ;
3. un dossier avec un sous-dossier ;
4. un carnet contenant une feuille manquante ;
5. annulation de la prévisualisation : aucun export ;
6. confirmation : un rapport global est affiché ;
7. PDF combiné + PDF séparé sur des carnets différents ;
8. PDF + DWG sur des carnets différents ;
9. collisions de noms entre deux carnets ;
10. dossier sans carnet publiable.

## Extension du 2026-10-05 : sélection indépendante

La sélection Ctrl/Maj de feuilles et de carnets est raccordée au résumé,
à l'aperçu global et à la publication. Le service `publication_selection`
regroupe les feuilles par carnet, évite les doublons parent/enfant et conserve
l'ordre métier. Le flux direct existant, étendu à plusieurs cibles, utilise
les hooks Stage 07 ; le flux dossier conserve `PublicationBatchService`.
Les deux flux consomment les mêmes copies de périmètre et le même moteur PDF/DWG.

Voir `09_Export.md`, `20_Export_Tutoriel.md` et `21_Export_Recette_Selection_Multiple.md`.
Le fonctionnement a été confirmé par l’utilisateur dans Revit le 2026-10-05
(PR #11). La recette détaillée reste distincte de cette validation fonctionnelle.
